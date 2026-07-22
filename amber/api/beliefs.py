"""
Aion Memory — 信念管理路由
"""
import json
from typing import Optional
import asyncpg
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from . import shared
from .shared import get_current_user, get_pool, vec_to_str
from .response import ok, error as api_error

router = APIRouter()


class BeliefCreate(BaseModel):
    content: str
    confidence: float = 0.5
    evidence_memories: list = []
    status: str = "tentative"


class BeliefSearch(BaseModel):
    query: str
    top_k: int = 5
    status_filter: Optional[str] = None


@router.post("/api/v1/beliefs")
async def create_belief(bel: BeliefCreate, user_id: str = Depends(get_current_user),
                        pool: asyncpg.Pool = Depends(get_pool)) -> dict:

    import logging
    vec_str = None
    if shared.get_cached_embedding_fn():
        try:
            raw_vec = (await shared.get_cached_embedding_fn()([bel.content]))[0]
            if raw_vec and len(raw_vec) > 0:
                vec_str = vec_to_str(raw_vec)
        except Exception:
            logging.getLogger("amber").warning(
                "beliefs: embedding 生成失败，写入 NULL 向量（不影响记忆创建）"
            )
    async with pool.acquire() as conn:
        existing = await conn.fetchrow(
            "SELECT id, confidence, trajectory FROM beliefs WHERE user_id=$1 AND content=$2 AND status!='contradicted'",
            user_id, bel.content
        )
        if existing:
            new_conf = (existing["confidence"] + bel.confidence) / 2
            await conn.execute(
                "UPDATE beliefs SET confidence=$1, updated_at=NOW() WHERE id=$2",
                new_conf, existing["id"]
            )
            return ok({"status": "updated_confidence", "id": existing["id"], "confidence": new_conf})
        row = await conn.fetchrow(
            "INSERT INTO beliefs (user_id, content, confidence, evidence_memories, embedding, status) "
            "VALUES ($1,$2,$3,$4,$5::vector,$6) RETURNING id",
            user_id, bel.content, bel.confidence, bel.evidence_memories, vec_str, bel.status
        )
    return ok({"status": "created", "id": row["id"]})


@router.post("/api/v1/beliefs/search")
async def search_beliefs(req: BeliefSearch, user_id: str = Depends(get_current_user),
                         pool: asyncpg.Pool = Depends(get_pool)) -> dict:

    import logging
    q_str = ""
    if shared.get_cached_embedding_fn():
        try:
            r_q = (await shared.get_cached_embedding_fn()([req.query]))[0]
            if r_q and len(r_q) > 0:
                q_str = vec_to_str(r_q)
        except Exception:
            logging.getLogger("amber").warning(
                "beliefs search: embedding 生成失败，降级为按创建时间召回"
            )

    conditions = ["user_id = $1"]
    params = [user_id]
    idx = 2
    if req.status_filter:
        conditions.append(f"status = ${idx}")
        params.append(req.status_filter)
        idx += 1
    where = " AND ".join(conditions)
    async with pool.acquire() as conn:
        if q_str:
            rows = await conn.fetch(
                f"SELECT id, content, confidence, status, trajectory, valid_from, "
                f"embedding <=> ${idx}::vector AS dist FROM beliefs WHERE {where} "
                f"ORDER BY dist LIMIT ${idx+1}",
                *params, q_str, req.top_k
            )
        else:
            # 嵌入不可用时降级：按创建时间返回最近信念
            rows = await conn.fetch(
                f"SELECT id, content, confidence, status, trajectory, valid_from, "
                f"NULL::real AS dist FROM beliefs WHERE {where} "
                f"ORDER BY created_at DESC LIMIT ${idx}",
                *params, req.top_k
            )
    return ok([dict(r) for r in rows])


@router.get("/api/v1/beliefs/{belief_id}")
async def get_belief(belief_id: int, user_id: str = Depends(get_current_user),
                     pool: asyncpg.Pool = Depends(get_pool)) -> dict:
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM beliefs WHERE id=$1 AND user_id=$2", belief_id, user_id
        )
        if not row:
            return api_error(message="Belief not found", code=404, status_code=404)
    return ok(dict(row))


@router.post("/api/v1/beliefs/{belief_id}/evolve")
async def evolve_belief(belief_id: int, new_confidence: float = None, evidence_id: int = None,
                        user_id: str = Depends(get_current_user),
                        pool: asyncpg.Pool = Depends(get_pool)) -> dict:
    """更新信念: 调整置信度/添加证据/状态自动演化"""
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT id, confidence, evidence_memories, status FROM beliefs WHERE id=$1 AND user_id=$2",
            belief_id, user_id
        )
        if not row:
            return api_error(message="Belief not found", code=404, status_code=404)
        new_status = row["status"]
        new_conf = row["confidence"] if new_confidence is None else new_confidence
        evidences = row["evidence_memories"] or []
        if evidence_id and evidence_id not in evidences:
            evidences.append(evidence_id)
            new_conf = min(1.0, new_conf + 0.1)
        if new_conf >= 0.7:
            new_status = "established"
        elif new_conf >= 0.4:
            new_status = "tentative"
        elif new_conf < 0.3:
            new_status = "hypothesis"
        # 状态合法性护栏：确保写入值满足 beliefs 表的 status CHECK 约束，
        # 否则回退到原状态，避免 IntegrityError 导致 500。
        # 注：原逻辑在 new_conf<0.3 时置 'hypothesis'，但该值不在 CHECK 约束内，
        # 会导致写入失败。建议后续在 schema 中将 'hypothesis' 纳入合法状态枚举。
        _VALID_STATUS = {"active", "tentative", "established", "contradicted"}
        if new_status not in _VALID_STATUS:
            new_status = row["status"]

        # 缺陷 1.3 修复：asyncpg 对 JSONB 可能返回 str 或已反序列化的 list/dict，
        # 直接 .append() 在返回 str 时会抛 AttributeError。统一类型守卫后再追加。
        raw_traj = row.get("trajectory")
        if isinstance(raw_traj, str):
            try:
                trajectory = json.loads(raw_traj)
            except (json.JSONDecodeError, ValueError):
                trajectory = []
        elif isinstance(raw_traj, list):
            trajectory = raw_traj
        else:
            trajectory = []
        if new_status != row["status"]:
            trajectory.append(f"{row['status']}→{new_status}")
        await conn.execute(
            "UPDATE beliefs SET confidence=$1, evidence_memories=$2, status=$3, trajectory=$4::jsonb WHERE id=$5",
            new_conf, evidences, new_status, json.dumps(trajectory), belief_id
        )
    return ok({"id": belief_id, "confidence": new_conf, "status": new_status})
