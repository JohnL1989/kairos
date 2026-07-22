"""
Aion Memory — RAG Chunk 搜索路由
"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from . import shared
from .response import ok
from .shared import get_current_user, get_pool, vec_to_str

router = APIRouter()


class ChunkSearchRequest(BaseModel):
    q: str
    top_k: int = Field(default=10, ge=1, le=200)


@router.post("/api/v1/memories/chunk-all")
async def chunk_all_endpoint(batch_size: int = 50, user_id: str = Depends(get_current_user)) -> dict:
    """为所有未分块的记忆生成分块"""
    pool = await get_pool()
    from core.chunker import chunk_all_unprocessed
    from core.embedding import get_embedding
    result = await chunk_all_unprocessed(pool, user_id, get_embedding, batch_size)
    return result


@router.post("/api/v1/memories/{memory_id}/chunk")
async def chunk_memory_endpoint(memory_id: int) -> dict:
    """为单条记忆生成分块"""
    pool = await get_pool()
    from core.chunker import chunk_memory as chunk_memory_fn
    from core.embedding import get_embedding
    result = await chunk_memory_fn(pool, memory_id, get_embedding)
    return result

@router.get("/api/v1/memories/chunks/stats")
async def chunk_stats_endpoint(user_id: str = Depends(get_current_user)) -> dict:
    """分块统计"""
    pool = await get_pool()
    async with pool.acquire() as conn:
        total = await conn.fetchval(
            "SELECT count(*) FROM memories WHERE user_id=$1 AND is_deleted=FALSE", user_id)
        chunked = await conn.fetchval(
            "SELECT count(DISTINCT m.id) FROM memories m "
            "JOIN memory_chunks mc ON m.id=mc.memory_id "
            "WHERE m.user_id=$1 AND m.is_deleted=FALSE", user_id)
        total_chunks = await conn.fetchval(
            "SELECT count(*) FROM memory_chunks mc JOIN memories m ON m.id=mc.memory_id "
            "WHERE m.user_id=$1 AND m.is_deleted=FALSE", user_id)
    return ok({"total_memories": total, "chunked": chunked or 0, "total_chunks": total_chunks or 0})


@router.post("/api/v1/memories/search-chunks")
async def search_chunks(req: ChunkSearchRequest, user_id: str = Depends(get_current_user)) -> dict:
    """Chunk级语义搜索 — 比全记忆搜索更精准"""
    pool = await get_pool()
    if not shared.get_cached_embedding_fn():
        return {"query": req.q, "total": 0, "results": []}
    import logging
    q_str = None
    try:
        r_q = (await shared.get_cached_embedding_fn()([req.q]))[0]
        if r_q and len(r_q) > 0:
            q_str = vec_to_str(r_q)
    except Exception:
        logging.getLogger("amber").warning(
            "chunks search: embedding 生成失败，返回空结果"
        )
    if not q_str:
        return {"query": req.q, "total": 0, "results": []}
    async with pool.acquire() as conn:
        chunk_rows = await conn.fetch(
            "SELECT mc.id, mc.content, mc.memory_id, m.content as full_content, "
            "mc.embedding <=> $2::vector AS dist "
            "FROM memory_chunks mc JOIN memories m ON m.id = mc.memory_id "
            "WHERE m.user_id=$1 AND m.is_deleted=FALSE ORDER BY dist LIMIT $3",
            user_id, q_str, req.top_k
        )
        mem_rows = await conn.fetch(
            "SELECT id, content, embedding <=> $2::vector AS dist "
            "FROM memories WHERE user_id=$1 AND is_deleted=FALSE "
            "ORDER BY dist LIMIT $3",
            user_id, q_str, req.top_k
        )
    results = []
    seen = set()
    for r in chunk_rows:
        mid = r["memory_id"]
        if mid not in seen:
            seen.add(mid)
            results.append({
                "type": "chunk", "memory_id": mid, "chunk_id": r["id"],
                "chunk_content": r["content"][:300],
                "full_content": r["full_content"][:500],
                "dist": round(float(r["dist"]), 4)
            })
    for r in mem_rows:
        if r["id"] not in seen and len(results) < req.top_k:
            results.append({
                "type": "memory", "memory_id": r["id"],
                "content": r["content"][:500],
                "dist": round(float(r["dist"]), 4)
            })
    return ok({"query": req.q, "total": len(results), "results": results})
