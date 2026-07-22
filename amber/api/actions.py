"""
诊断干预 — /api/v1/actions/* 端点（Phase 3：只读，不修改数据）
/get      诊断建议列表
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends
import asyncpg

from api.shared import get_pool
from api.response import ok

router = APIRouter(prefix="/api/v1/actions")


def _now() -> datetime:
    return datetime.now(timezone.utc)


@router.get("/")
async def list_actions(pool: asyncpg.Pool = Depends(get_pool)) -> dict:
    """诊断建议列表（只读，不修改数据）"""
    now = _now()
    async with pool.acquire() as conn:
        # 1. 低热记忆（长期未访问）
        cold_rows = await conn.fetch(
            """
            SELECT id, content, category, tier, heat_score, access_count, created_at
            FROM memories
            WHERE is_deleted = FALSE AND access_count < 3 AND heat_score < 0.3
            ORDER BY heat_score ASC LIMIT 10
            """
        )

        # 2. 孤立记忆（无 embedding 且 tier=L2 超过 30 天）
        orphan_rows = await conn.fetch(
            """
            SELECT id, content, category, tier, created_at
            FROM memories
            WHERE is_deleted = FALSE
              AND embedding IS NULL
              AND tier = 'L2'
              AND created_at < NOW() - INTERVAL '30 days'
            ORDER BY created_at ASC LIMIT 10
            """
        )

        # 3. 高访问但低 tier（可以升级）
        upgrade_rows = await conn.fetch(
            """
            SELECT id, content, category, tier, heat_score, access_count
            FROM memories
            WHERE is_deleted = FALSE
              AND access_count >= 10
              AND tier IN ('L2', 'L3')
              AND heat_score >= 0.7
            ORDER BY access_count DESC LIMIT 10
            """
        )

    return ok({
        "generated_at": now.isoformat(),
        "cold_memories": [dict(r) for r in cold_rows],
        "orphan_memories": [dict(r) for r in orphan_rows],
        "upgrade_candidates": [dict(r) for r in upgrade_rows],
    })
