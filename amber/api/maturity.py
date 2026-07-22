"""
自我审视 — /api/v1/console/maturity 成熟度评估
/maturity  当前系统成熟度指标
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


@router.get("/maturity")
async def get_maturity(pool: asyncpg.Pool = Depends(get_pool)) -> dict:
    """系统成熟度评估：数据完整性 + 覆盖率 + 健康度"""
    now = _now()
    async with pool.acquire() as conn:
        # 1. 记忆总量与分类覆盖
        total = await conn.fetchval("SELECT COUNT(*) FROM memories WHERE is_deleted=FALSE")
        with_emb = await conn.fetchval(
            "SELECT COUNT(*) FROM memories WHERE is_deleted=FALSE AND embedding IS NOT NULL")
        durable_cnt = await conn.fetchval(
            "SELECT COUNT(*) FROM memories WHERE is_deleted=FALSE AND scope_target='durable'")
        general_cnt = await conn.fetchval(
            "SELECT COUNT(*) FROM memories WHERE is_deleted=FALSE AND scope_target='general'")

        # 2. TMT 层级分布
        tmt_rows = await conn.fetch(
            "SELECT tmt_level, COUNT(*) AS cnt FROM memories WHERE is_deleted=FALSE GROUP BY tmt_level ORDER BY tmt_level"
        )

        # 3. Tier 分布
        tier_rows = await conn.fetch(
            "SELECT tier, COUNT(*) AS cnt FROM memories WHERE is_deleted=FALSE GROUP BY tier ORDER BY tier"
        )

        # 4. Category 覆盖度（前 10）
        cat_rows = await conn.fetch(
            "SELECT category, COUNT(*) AS cnt FROM memories WHERE is_deleted=FALSE GROUP BY category ORDER BY cnt DESC LIMIT 10"
        )

        # 5. 近 30 天写入活跃度
        active_30d = await conn.fetchval(
            "SELECT COUNT(*) FROM memories WHERE created_at >= NOW() - INTERVAL '30 days' AND is_deleted=FALSE"
        )

        # 6. 平均热值
        avg_heat = await conn.fetchval(
            "SELECT AVG(heat_score) FROM memories WHERE is_deleted=FALSE"
        ) or 0.5

    # 计算覆盖率
    embed_rate = round(with_emb / total * 100, 1) if total > 0 else 0
    durable_rate = round(durable_cnt / total * 100, 1) if total > 0 else 0

    # 成熟度评分（0-100）
    # 向量覆盖率 40% + durable 覆盖 20% + 30 天活跃 20% + TMT 层级丰富度 20%
    embed_score = min(embed_rate, 100) * 0.4
    durable_score = min(durable_rate * 2, 100) * 0.2  # durable 占比 50% 即满分
    activity_score = min(active_30d / max(total, 1) * 100, 100) * 0.2
    tmt_score = min(len(tmt_rows) * 20, 100) * 0.2  # 5 层即满分

    maturity_score = round(embed_score + durable_score + activity_score + tmt_score, 1)

    return ok({
        "maturity_score": maturity_score,
        "total_memories": total,
        "with_embedding": with_emb,
        "embedding_rate": embed_rate,
        "durable_count": durable_cnt,
        "durable_rate": durable_rate,
        "general_count": general_cnt,
        "active_30d": active_30d,
        "avg_heat": round(float(avg_heat), 3),
        "tmt_levels": [{"level": r["tmt_level"], "count": r["cnt"]} for r in tmt_rows],
        "tier_distribution": [{"tier": r["tier"], "count": r["cnt"]} for r in tier_rows],
        "top_categories": [{"category": r["category"], "count": r["cnt"]} for r in cat_rows],
        "generated_at": now.isoformat(),
    })
