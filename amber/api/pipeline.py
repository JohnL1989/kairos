"""
知识流转可视化 — 记忆流转管道聚合端点
/pipeline  记忆流转管道（按 scope_target + tmt_level 聚合）
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends
import asyncpg

from api.shared import get_pool
from api.response import ok

router = APIRouter(prefix="/api/v1/console")


def _now() -> datetime:
    return datetime.now(timezone.utc)


@router.get("/pipeline")
async def get_pipeline(pool: asyncpg.Pool = Depends(get_pool)) -> dict:
    """知识流转管道聚合：按 scope_target + tmt_level 分组统计"""
    now = _now()

    async with pool.acquire() as conn:
        # 1. 按 scope_target 分组
        scope_rows = await conn.fetch(
            """
            SELECT scope_target, COUNT(*) AS cnt,
                   SUM(CASE WHEN is_deleted THEN 1 ELSE 0 END) AS deleted_cnt,
                   AVG(heat_score) AS avg_heat
            FROM memories
            GROUP BY scope_target
            ORDER BY scope_target
            """
        )

        # 2. 按 tmt_level 分组（含 tier 交叉）
        tmt_rows = await conn.fetch(
            """
            SELECT tmt_level, tier, COUNT(*) AS cnt,
                   AVG(heat_score) AS avg_heat
            FROM memories
            WHERE is_deleted = FALSE
            GROUP BY tmt_level, tier
            ORDER BY tmt_level, tier
            """
        )

        # 3. 按 category 分组（前 10）
        cat_rows = await conn.fetch(
            """
            SELECT category, COUNT(*) AS cnt
            FROM memories
            WHERE is_deleted = FALSE
            GROUP BY category
            ORDER BY cnt DESC
            LIMIT 10
            """
        )

        # 4. 近 7 天写入趋势（按 scope_target 拆分）
        since = now.replace(hour=0, minute=0, second=0, microsecond=0)
        trend_rows = await conn.fetch(
            """
            SELECT DATE(created_at) AS day,
                   scope_target,
                   COUNT(*) AS cnt
            FROM memories
            WHERE created_at >= $1 AND is_deleted = FALSE
            GROUP BY DATE(created_at), scope_target
            ORDER BY day, scope_target
            """,
            since,
        )

    # 5. 聚合趋势：按天 → scope_target 映射
    trend_map: dict[str, dict[str, int]] = {}
    for r in trend_rows:
        day = r["day"].isoformat() if r["day"] else ""
        scope = r["scope_target"] or "unknown"
        cnt = int(r["cnt"])
        trend_map.setdefault(day, {})[scope] = cnt

    # 6. TMT 层级聚合
    tmt_map: dict[int, dict[str, Any]] = {}
    for r in tmt_rows:
        lvl = int(r["tmt_level"]) if r["tmt_level"] is not None else 0
        if lvl not in tmt_map:
            tmt_map[lvl] = {"count": 0, "avg_heat": 0.0, "tiers": {}}
        tmt_map[lvl]["count"] += int(r["cnt"])
        tier = r["tier"] or "L2"
        tmt_map[lvl]["tiers"][tier] = int(r["cnt"])
        if r["avg_heat"] is not None:
            tmt_map[lvl]["avg_heat"] = round(
                (tmt_map[lvl]["avg_heat"] * (tmt_map[lvl]["count"] - int(r["cnt"])) + float(r["avg_heat"]) * int(r["cnt"]))
                / tmt_map[lvl]["count"], 3
            ) if tmt_map[lvl]["count"] > 0 else 0.0

    return ok({
        "scope": [{"scope_target": r["scope_target"], "count": int(r["cnt"]),
                    "deleted": int(r["deleted_cnt"]), "avg_heat": round(float(r["avg_heat"]), 3) if r["avg_heat"] else 0.0}
                   for r in scope_rows],
        "tmt_levels": [{"level": lvl, **data} for lvl, data in sorted(tmt_map.items())],
        "categories": [{"category": r["category"], "count": int(r["cnt"])} for r in cat_rows],
        "trend": [{"day": day, **counts} for day, counts in sorted(trend_map.items())],
        "window_days": 7,
        "generated_at": now.isoformat(),
    })
