"""
记忆驾驶舱 — 5 个只读聚合端点
/services       当前服务健康快照（ServiceRegistry 并发探测 + health_log 异步写入）
/stats          记忆库统计
/trends         近 7 天写入趋势
/events         最近操作事件流（memory_traces）
/health-history 24h 健康时间线（health_log）
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import APIRouter, Depends, Query
import asyncpg

from api.shared import get_pool
from api.response import ok
from core.service_client import registry

logger = logging.getLogger("amber.console")

router = APIRouter(prefix="/api/v1/console")


def _now() -> datetime:
    return datetime.now(timezone.utc)


# ── 状态映射：ServiceRegistry → 前端兼容 ──────────────────────
_STATUS_MAP = {
    "healthy": "up",
    "degraded": "degraded",
    "unreachable": "down",
}


# ── /services ─────────────────────────────────────────────────
@router.get("/services")
async def list_services(pool: asyncpg.Pool = Depends(get_pool)) -> dict:
    """
    并发探测所有注册服务，返回健康快照。
    ServiceRegistry.check_all() 使用 asyncio.gather 并发检测，
    health_log 异步写入不阻塞响应返回。
    """
    result = await registry.check_all(pool)

    # 将 dict 格式转为前端期望的 array 格式
    services_list: list[dict[str, Any]] = []
    for name, info in result["services"].items():
        services_list.append({
            "name": name,
            "kind": info.get("kind", ""),
            "status": _STATUS_MAP.get(info["status"], info["status"]),
            "latency_ms": info.get("latency_ms"),
            "last_check": info.get("last_checked", _now().isoformat()),
            **({"error": info["error"]} if info.get("error") else {}),
        })

    overall = _STATUS_MAP.get(result["overall"], result["overall"])
    return ok({"services": services_list, "overall": overall})


# ── /stats ─────────────────────────────────────────────────────
@router.get("/stats")
async def get_stats(pool: asyncpg.Pool = Depends(get_pool)) -> dict:
    """
    关键指标聚合：总量、分布、今日增量。
    响应格式遵循架构文档§5.3.2：memories/beliefs/wiki_pages 三组。
    """
    async with pool.acquire() as conn:
        # ── memories ──
        mem_total = await conn.fetchval("SELECT COUNT(*) FROM memories WHERE is_deleted=FALSE")
        mem_today = await conn.fetchval(
            "SELECT COUNT(*) FROM memories "
            "WHERE is_deleted=FALSE AND created_at > DATE_TRUNC('day', NOW() AT TIME ZONE 'UTC')"
        )
        by_scope = await conn.fetch(
            "SELECT scope_target, COUNT(*) AS cnt FROM memories WHERE is_deleted=FALSE GROUP BY scope_target"
        )
        by_tier = await conn.fetch(
            "SELECT tier, COUNT(*) AS cnt FROM memories WHERE is_deleted=FALSE GROUP BY tier ORDER BY tier"
        )
        by_cat = await conn.fetch(
            "SELECT category, COUNT(*) AS cnt FROM memories WHERE is_deleted=FALSE GROUP BY category ORDER BY cnt DESC LIMIT 8"
        )

        # ── beliefs ──
        bel_total = await conn.fetchval("SELECT COUNT(*) FROM beliefs")
        bel_today = await conn.fetchval(
            "SELECT COUNT(*) FROM beliefs WHERE created_at > DATE_TRUNC('day', NOW() AT TIME ZONE 'UTC')"
        )

        # ── wiki_pages ──
        wiki_total = await conn.fetchval("SELECT COUNT(*) FROM wiki_pages")
        wiki_today = await conn.fetchval(
            "SELECT COUNT(*) FROM wiki_pages WHERE created_at > DATE_TRUNC('day', NOW() AT TIME ZONE 'UTC')"
        )

        # ── traces (操作轨迹) ──
        traces = await conn.fetchval("SELECT COUNT(*) FROM memory_traces")

    return ok({
        "memories": {
            "total": mem_total,
            "today_new": mem_today,
            "scope": {r["scope_target"]: r["cnt"] for r in by_scope},
            "tier": {r["tier"]: r["cnt"] for r in by_tier},
        },
        "beliefs": {
            "total": bel_total,
            "today_new": bel_today,
        },
        "wiki_pages": {
            "total": wiki_total,
            "today_new": wiki_today,
        },
        "total_traces": traces,
        "by_category": {r["category"]: r["cnt"] for r in by_cat},
    })


# ── /trends ────────────────────────────────────────────────────
@router.get("/trends")
async def get_trends(pool: asyncpg.Pool = Depends(get_pool)) -> dict:
    """
    时间序列数据：7天daily趋势 + 今日hourly活跃度。
    响应格式遵循架构文档§5.3.3：daily[] + hourly_today[]。
    """
    since = _now() - timedelta(days=7)
    today_start = _now().replace(hour=0, minute=0, second=0, microsecond=0)

    async with pool.acquire() as conn:
        # ── daily: 近7天每日新增 ──
        daily_rows = await conn.fetch(
            "SELECT DATE(created_at) AS day, COUNT(*) AS cnt "
            "FROM memories WHERE created_at >= $1 AND is_deleted=FALSE "
            "GROUP BY DATE(created_at) ORDER BY day",
            since,
        )

        # ── hourly_today: 今日按小时活跃度 ──
        hourly_rows = await conn.fetch(
            "SELECT EXTRACT(HOUR FROM created_at)::INT AS hour, COUNT(*) AS cnt "
            "FROM memories WHERE created_at >= $1 AND is_deleted=FALSE "
            "GROUP BY EXTRACT(HOUR FROM created_at) ORDER BY hour",
            today_start,
        )

    # ── 组装 daily ──
    labels: list[str] = []
    values: list[int] = []
    by_day = {r["day"]: r["cnt"] for r in daily_rows}
    for i in range(7):
        d = (_now() - timedelta(days=6 - i)).date()
        labels.append(d.isoformat())
        values.append(int(by_day.get(d, 0)))

    # ── 组装 hourly_today ──
    hourly_today: list[dict[str, int]] = []
    by_hour = {r["hour"]: r["cnt"] for r in hourly_rows}
    current_hour = _now().hour
    for h in range(current_hour + 1):
        hourly_today.append({"hour": h, "count": int(by_hour.get(h, 0))})

    return ok({
        "daily": [{"date": labels[i], "memories_created": values[i]} for i in range(len(labels))],
        "hourly_today": hourly_today,
        # 向后兼容旧前端
        "labels": labels,
        "values": values,
        "window_days": 7,
    })


# ── /events ────────────────────────────────────────────────────
@router.get("/events")
async def get_events(
    pool: asyncpg.Pool = Depends(get_pool),
    limit: int = Query(default=20, ge=1, le=100),
) -> dict:
    """
    最近操作事件流（来自 memory_traces）。
    读取权威列 action / created_at（schema.sql 定义）。
    executed_at 为前端兼容别名，由 created_at 映射。
    """
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT t.id, t.action, t.memory_id, "
            "LEFT(m.content, 50) AS preview, t.created_at "
            "FROM memory_traces t LEFT JOIN memories m ON m.id = t.memory_id "
            "AND m.is_deleted=FALSE "
            "ORDER BY t.created_at DESC LIMIT $1",
            limit,
        )

    events = [
        {
            "id": r["id"],
            "action": r["action"],
            "memory_id": r["memory_id"],
            "preview": r["preview"] or "",
            "executed_at": r["created_at"].isoformat() if r["created_at"] else None,
        }
        for r in rows
    ]
    return ok({"events": events, "count": len(events)})


# ── /health-history ────────────────────────────────────────────
@router.get("/health-history")
async def get_health_history(
    pool: asyncpg.Pool = Depends(get_pool),
    hours: int = Query(default=24, ge=1, le=168),
) -> dict:
    """
    健康检查时间线（来自 health_log）。
    返回按小时聚合的时间线 + 可用性摘要。
    """
    since = _now() - timedelta(hours=hours)

    async with pool.acquire() as conn:
        # 按小时+服务聚合
        rows = await conn.fetch(
            "SELECT service, status, "
            "date_trunc('hour', checked_at) AS hour, "
            "AVG(latency_ms) AS avg_latency, "
            "COUNT(*) AS checks "
            "FROM health_log WHERE checked_at >= $1 "
            "GROUP BY service, status, date_trunc('hour', checked_at) "
            "ORDER BY hour",
            since,
        )

        # 可用性摘要
        total_checks = await conn.fetchval(
            "SELECT COUNT(*) FROM health_log WHERE checked_at >= $1", since
        )
        healthy_checks = await conn.fetchval(
            "SELECT COUNT(*) FROM health_log WHERE checked_at >= $1 AND status = 'healthy'",
            since,
        )
        outage_periods = await conn.fetch(
            "SELECT service, MIN(checked_at) AS start_at, MAX(checked_at) AS end_at "
            "FROM health_log WHERE checked_at >= $1 AND status != 'healthy' "
            "GROUP BY service, date_trunc('hour', checked_at) "
            "ORDER BY start_at",
            since,
        )

    # 构建时间线
    timeline: list[dict[str, Any]] = []
    for r in rows:
        timeline.append({
            "time": r["hour"].isoformat() if r["hour"] else None,
            "service": r["service"],
            "status": _STATUS_MAP.get(r["status"], r["status"]),
            "avg_latency_ms": round(r["avg_latency"], 1) if r["avg_latency"] else None,
            "checks": r["checks"],
        })

    # 可用性摘要
    uptime_24h = round(healthy_checks / max(total_checks, 1) * 100, 1)
    outages = len(outage_periods)
    longest_outage_min = 0.0
    if outage_periods:
        longest = max(
            (r["end_at"] - r["start_at"]).total_seconds() / 60
            for r in outage_periods
            if r["start_at"] and r["end_at"]
        )
        longest_outage_min = round(longest, 1)

    return ok({
        "timeline": timeline,
        "summary": {
            "uptime_24h": uptime_24h,
            "outages": outages,
            "longest_outage_min": longest_outage_min,
        },
    })
