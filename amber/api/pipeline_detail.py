"""
Pipeline Detail — /api/v1/console/pipeline/detail/{scope_target}
按 scope_target 下钻：分类分布 + TMT 层级
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, Path
import asyncpg

from api.shared import get_pool
from api.response import ok

router = APIRouter(prefix="/api/v1/console")


def _now() -> datetime:
    return datetime.now(timezone.utc)


@router.get("/pipeline/detail/{scope_target}")
async def get_pipeline_detail(
    scope_target: str = Path(..., description="scope_target 值，如 durable/general"),
    pool: asyncpg.Pool = Depends(get_pool),
) -> dict:
    """单个 scope_target 的详细分类 + TMT 分布"""
    now = _now()
    async with pool.acquire() as conn:
        # scope 统计
        scope_row = await conn.fetchrow(
            "SELECT COUNT(*) AS cnt, SUM(CASE WHEN is_deleted THEN 1 ELSE 0 END) AS deleted, AVG(heat_score) AS avg_heat "
            "FROM memories WHERE scope_target = $1", scope_target
        )

        # 分类分布
        cat_rows = await conn.fetch(
            "SELECT category, COUNT(*) AS cnt FROM memories "
            "WHERE scope_target = $1 AND is_deleted = FALSE "
            "GROUP BY category ORDER BY cnt DESC", scope_target
        )

        # TMT 层级
        tmt_rows = await conn.fetch(
            "SELECT tmt_level, COUNT(*) AS cnt FROM memories "
            "WHERE scope_target = $1 AND is_deleted = FALSE "
            "GROUP BY tmt_level ORDER BY tmt_level", scope_target
        )

    if not scope_row or scope_row["cnt"] == 0:
        return ok({"scope_target": scope_target, "count": 0, "categories": [], "tmt_levels": []})

    return ok({
        "scope_target": scope_target,
        "count": int(scope_row["cnt"]),
        "deleted": int(scope_row["deleted"] or 0),
        "avg_heat": round(float(scope_row["avg_heat"] or 0.5), 3),
        "categories": [{"category": r["category"], "count": int(r["cnt"])} for r in cat_rows],
        "tmt_levels": [{"level": int(r["tmt_level"]) if r["tmt_level"] else 0, "count": int(r["cnt"])} for r in tmt_rows],
        "generated_at": now.isoformat(),
    })
