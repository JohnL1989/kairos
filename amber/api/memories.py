"""
Aion Memory — 信念与记忆管理路由
"""
import json
import os
from datetime import datetime, timezone
from typing import Any, Optional
import asyncpg
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field

from . import shared
from .shared import get_current_user, get_pool
from .response import ok, error as api_error
# A4 重构：记忆写入编排下沉到服务层，路由仅做鉴权 + 参数校验 + 调用。
from services.memory_write_service import create_memory as svc_create_memory
from services.memory_write_service import MemoryCreate

router = APIRouter()

@router.post("/api/v1/memories")
async def create_memory(mem: MemoryCreate, user_id: str = Depends(get_current_user),
                        pool: asyncpg.Pool = Depends(get_pool)) -> dict:
    """创建一条新记忆（薄路由：去重/容量/embedding/trace 编排见 services/memory_write_service）。"""
    return await svc_create_memory(pool, user_id, mem)


@router.get("/api/v1/memories")
async def list_memories(
    limit: int = Query(20, ge=1, le=200),
    tier: Optional[str] = None,
    category: Optional[str] = None,
    scope_session_id: str = None,
    user_id: str = Depends(get_current_user),
    pool: asyncpg.Pool = Depends(get_pool),
) -> dict:
    """列出最近的记忆（支持作用域 + 层级 + 分类过滤）"""
    conditions = ["user_id = $1", "is_deleted = FALSE"]
    params = [user_id]
    idx = 2

    if tier:
        conditions.append(f"tier = ${idx}")
        params.append(tier)
        idx += 1
    if category:
        conditions.append(f"category = ${idx}")
        params.append(category)
        idx += 1
    if scope_session_id:
        conditions.append(
            "(scope_target='durable' OR (scope_target='general' AND scope_session_id=$" + str(idx) + "))"
        )
        params.append(scope_session_id)
        idx += 1
    else:
        conditions.append("scope_target='durable'")

    where = " AND ".join(conditions)
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            f"SELECT id, content, category, tier, heat_score, created_at, scope_target "
            f"FROM memories WHERE {where} ORDER BY created_at DESC LIMIT ${idx}",
            *params, limit
        )
    return ok({"memories": [
        {"id": r["id"], "content": r["content"][:200], "category": r["category"],
         "tier": r["tier"], "heat": r["heat_score"],
         "created": str(r["created_at"])[:19],
         "scope": r["scope_target"] or "general"}
        for r in rows
        ]})

@router.get("/api/v1/memories/heat-top")
async def heat_top_memories(limit: int = 10, min_heat: float = 0.0,
                            user_id: str = Depends(get_current_user),
                            pool: asyncpg.Pool = Depends(get_pool)) -> dict:
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT id, content, category, tier, heat_score, access_count, created_at "
            "FROM memories WHERE user_id=$1 AND is_deleted=FALSE AND heat_score>=$2 "
            "ORDER BY heat_score DESC LIMIT $3", user_id, min_heat, limit)
    return ok({"memories": [dict(r) for r in rows]})


@router.get("/api/v1/memories/stats")
async def get_memory_stats(user_id: str = Depends(get_current_user),
                           pool: asyncpg.Pool = Depends(get_pool)) -> dict:
    async with pool.acquire() as conn:
        total = await conn.fetchval("SELECT COUNT(*) FROM memories WHERE user_id=$1 AND is_deleted=FALSE", user_id)
        by_cat = await conn.fetch("SELECT category, COUNT(*) AS cnt FROM memories WHERE user_id=$1 AND is_deleted=FALSE GROUP BY category ORDER BY cnt DESC", user_id)
        by_tier = await conn.fetch("SELECT tier, COUNT(*) AS cnt FROM memories WHERE user_id=$1 AND is_deleted=FALSE GROUP BY tier ORDER BY tier", user_id)
        avg_h = await conn.fetchval("SELECT COALESCE(AVG(heat_score), 0) FROM memories WHERE user_id=$1 AND is_deleted=FALSE", user_id)
        deleted = await conn.fetchval("SELECT COUNT(*) FROM memories WHERE user_id=$1 AND is_deleted=TRUE", user_id)
        total_all = await conn.fetchval("SELECT COUNT(*) FROM memories WHERE user_id=$1", user_id)
    return ok({"total": total, "total_including_deleted": total_all, "deleted": deleted,
            "avg_heat_score": float(avg_h),
            "by_category": {r["category"]: r["cnt"] for r in by_cat},
            "by_tier": {r["tier"]: r["cnt"] for r in by_tier}})


@router.get("/api/v1/memories/{memory_id}")
async def get_memory(memory_id: int, user_id: str = Depends(get_current_user),
                     pool: asyncpg.Pool = Depends(get_pool)) -> dict:
    """获取单条记忆"""
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT id, content, category, tier, heat_score, reliability, "
            "tmt_level, importance, entities, access_count, "
            "created_at, updated_at, scope_target "
            "FROM memories WHERE id=$1 AND user_id=$2 AND is_deleted=FALSE",
            memory_id, user_id
        )
        if not row:
            return api_error(message="memory not found", code=404, status_code=404)
        return ok({
            "id": row["id"], "content": row["content"], "category": row["category"],
            "tier": row["tier"], "heat": row["heat_score"],
            "reliability": row["reliability"],
            "tmt_level": row["tmt_level"],
            "importance": row["importance"],
            "entities": list(row["entities"] or []),
            "access_count": row["access_count"] or 0,
            "scope": row["scope_target"] or "general",
            "created": str(row["created_at"])[:19],
            "updated": str(row["updated_at"])[:19],
        })


@router.delete("/api/v1/memories/{memory_id}")
async def delete_memory(memory_id: int, purge: bool = False,
                        user_id: str = Depends(get_current_user),
                        pool: asyncpg.Pool = Depends(get_pool)) -> dict:
    """软删除记忆。当 purge=True 或类别为敏感类别时，执行哈希净化（不可逆）。"""
    SENSITIVE_CATEGORIES = {"credential", "secret", "password", "token", "key"}
    async with pool.acquire() as conn:
        # 先查当前记忆的 category 和 content
        row = await conn.fetchrow(
            "SELECT category, content FROM memories WHERE id=$1 AND user_id=$2 AND is_deleted=FALSE",
            memory_id, user_id
        )
        if not row:
            return api_error(message="memory not found or already deleted", code=404, status_code=404)
        
        should_purge = purge or (row["category"] or "").lower() in SENSITIVE_CATEGORIES
        
        if should_purge:
            # 哈希净化（不可逆）
            from security.purifier import soft_delete_memory
            result = await soft_delete_memory(conn, memory_id, f"delete{' (purge)' if purge else ' (sensitive auto-purge)'}")
            return ok(result)
        else:
            # 普通软删除
            await conn.execute(
                "UPDATE memories SET is_deleted=TRUE WHERE id=$1 AND user_id=$2",
                memory_id, user_id
            )
            return ok({"status": "deleted", "id": memory_id})


class MemoryUpdate(BaseModel):
    content: Optional[str] = Field(None, max_length=10000)
    category: Optional[str] = None
    tier: Optional[str] = None
    importance: Optional[float] = None
    reliability: Optional[float] = None
    # R5 修复：乐观并发校验。传入调用方最后读取到的 updated_at，
    # 若与库内不一致（期间被其它写入修改），则拒绝本次更新并返回 409，
    # 防止「后写覆盖」静默丢失并发修改。可选；不传则保持原行为。
    if_match_updated_at: Optional[str] = None


@router.put("/api/v1/memories/{memory_id}")
async def update_memory(
    memory_id: int,
    upd: MemoryUpdate,
    user_id: str = Depends(get_current_user),
    pool: asyncpg.Pool = Depends(get_pool),
) -> dict:
    """更新记忆字段（仅更新传入的非空字段）"""
    fields: list[str] = []
    params: list[Any] = [memory_id, user_id]
    idx = 3
    if upd.content is not None:
        fields.append(f"content=${idx}"); params.append(upd.content); idx += 1
    if upd.category is not None:
        fields.append(f"category=${idx}"); params.append(upd.category); idx += 1
    if upd.tier is not None:
        fields.append(f"tier=${idx}"); params.append(upd.tier); idx += 1
    if upd.importance is not None:
        fields.append(f"importance=${idx}"); params.append(upd.importance); idx += 1
    if upd.reliability is not None:
        fields.append(f"reliability=${idx}"); params.append(upd.reliability); idx += 1
    if not fields:
        return ok({"status": "noop", "id": memory_id})
    # R5 修复：乐观锁——将 if_match_updated_at 并入 WHERE
    # R7 修复：强乐观锁（见文件头部说明）。
    # 受保护字段（content/category/tier）并发修改风险最高。MNEMOSYNE_STRICT_OCC=1 时，
    # 这些字段的更新「必须」携带 if_match_updated_at（调用方先 GET 取当前版本再 PUT），
    # 缺失返回 428 Precondition Required 并附库内当前版本，迫使客户端合并而非静默后写覆盖。
    # 默认（非严格）模式保持 LWW 兼容旧客户端，但在成功响应中回传最新 updated_at 供感知。
    touching_protected = (
        upd.content is not None or upd.category is not None or upd.tier is not None
    )
    strict_occ = os.getenv("MNEMOSYNE_STRICT_OCC", "0") == "1"
    if strict_occ and touching_protected and upd.if_match_updated_at is None:
        async with pool.acquire() as conn:
            cur = await conn.fetchval(
                "SELECT updated_at FROM memories WHERE id=$1 AND user_id=$2 AND is_deleted=FALSE",
                memory_id, user_id,
            )
        if cur is None:
            return api_error(message="memory not found", code=404, status_code=404)
        return api_error(
            message="缺少乐观锁版本：更新 content/category/tier 须携带 if_match_updated_at（先 GET 取 updated_at）",
            code=428, status_code=428,
            data={"current_version": str(cur)[:19]},
        )

    # R5 修复：乐观锁——将 if_match_updated_at 并入 WHERE
    version_clause = ""
    if upd.if_match_updated_at is not None:
        version_clause = f" AND updated_at=${idx}"
        params.append(upd.if_match_updated_at)
        idx += 1
    fields.append("updated_at=NOW()")
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            f"UPDATE memories SET {', '.join(fields)} "
            f"WHERE id=$1 AND user_id=$2{version_clause} RETURNING id, updated_at",
            *params,
        )
        if not row:
            if upd.if_match_updated_at is not None:
                # 命中 0 行：可能是版本不匹配（并发写），也可能是 id 不存在
                return api_error(
                    message="版本冲突：updated_at 不匹配，记忆可能已被并发修改",
                    code=409, status_code=409,
                )
            return api_error(message="memory not found", code=404, status_code=404)
    # 默认 LWW 模式下也回传最新版本，供客户端感知潜在并发覆盖
    return ok({
        "status": "updated", "id": memory_id,
        "updated_at": str(row["updated_at"])[:19],
    })

# ── memory_traces 端点（Layer 1 自我管理） ──
class MemoryTraceCreate(BaseModel):
    memory_id: Optional[int] = None
    action: str  # create/delete/update/search（与 schema.sql 的 action 列对齐）
    metadata: Optional[dict] = None
    scope_target: Optional[str] = "general"
    category: Optional[str] = "general"

@router.post("/api/v1/memory-traces")
async def create_memory_trace(trace: MemoryTraceCreate, user_id: str = Depends(get_current_user),
                                pool: asyncpg.Pool = Depends(get_pool)) -> dict:
    """创建 memory_trace 记录（记忆操作审计日志）。

    写入列对齐 schema.sql 权威定义（action / metadata / created_at）。
    响应同时返回 executed_at（由 created_at 映射，兼容前端字段名）。
    """
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "INSERT INTO memory_traces (user_id, memory_id, action, metadata) "
            "VALUES ($1, $2, $3, $4::jsonb) RETURNING id, created_at",
            user_id, trace.memory_id, trace.action,  # 使用服务端身份，忽略客户端 user_id（S1 修复）
            json.dumps(trace.metadata or {}) if trace.metadata else None,
        )
    return ok({"id": row["id"], "executed_at": str(row["created_at"])[:19]})


# ── embedding 补偿（缺陷 4.1） ──
async def _backfill_failed_embeddings(pool: asyncpg.Pool, limit: int = 50) -> int:
    """补全 embedding_status='failed' 的记忆向量。

    写入时若 embedding 服务短暂不可用，记忆会被标记为 failed 而缺失向量。
    本函数扫描失败记忆并重新生成向量，使其可被向量检索召回。
    返回成功补全的条数。
    """
    if not shared.get_cached_embedding_fn():
        return 0
    # R2 修复：补偿扫描覆盖 embedding=NULL 或 embedding_status 为 pending/failed 的记忆，
    # 使「写入后、嵌入完成前崩溃」的孤儿记忆（既非 ready 也非 failed 的幽灵状态）也能被回收。
    rows = await pool.fetch(
        "SELECT id, content FROM memories "
        "WHERE is_deleted=FALSE AND (embedding IS NULL "
        "OR metadata->>'embedding_status' IN ('pending','failed')) "
        "ORDER BY id LIMIT $1",
        limit,
    )
    # P7 修复：批量嵌入——将候选集按 32 条一批通过 get_embedding_async(list) 一次请求，
    # 降低 embedding API 调用次数与串行延迟（原实现每条单独触发一次 API）。
    done = 0
    BATCH = 32
    for i in range(0, len(rows), BATCH):
        chunk = rows[i:i + BATCH]
        contents = [r["content"][:2000] for r in chunk]
        try:
            embs = await shared.get_cached_embedding_fn()(contents)
        except Exception:
            import logging
            logging.getLogger("amber").warning("backfill embedding 批次失败（跳过本批）")
            continue
        for r, raw in zip(chunk, embs):
            if raw and len(raw) > 0:
                v_str = vec_to_str(raw)
                async with pool.acquire() as conn:
                    await conn.execute(
                        "UPDATE memories SET embedding=$1::vector, "
                        "metadata = COALESCE(metadata,'{}'::jsonb) "
                        "|| '{\"embedding_status\":\"ready\"}'::jsonb WHERE id=$2",
                        v_str, r["id"],
                    )
                done += 1
    return done


@router.post("/api/v1/memories/embeddings/backfill")
async def backfill_embeddings(
    limit: int = 50,
    user_id: str = Depends(get_current_user),
    pool: asyncpg.Pool = Depends(get_pool),
) -> dict:
    """补全失败（embedding_status='failed'）的记忆向量。

    可由 cron / 运维脚本定期调用，修复因 embedding 服务短暂不可用而缺失向量的记忆。
    返回本次成功补全的条数。
    """
    done = await _backfill_failed_embeddings(pool, limit)
    return ok({"backfilled": done})
