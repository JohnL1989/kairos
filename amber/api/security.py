"""
Mnemosyne v5.0 — 安全 API 路由
审计 + 哈希净化端点
"""
import asyncpg
from .response import ok, error as api_error
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from .shared import get_current_user, get_pool

router = APIRouter(prefix="/api/v1/security", tags=["security"])



class DeleteRequest(BaseModel):
    memory_id: int
    reason: str = "user_request"


@router.post("/audit/run")
async def run_audit(limit: int = 5, user_id: str = Depends(get_current_user),
                    pool: asyncpg.Pool = Depends(get_pool)) -> dict:
    """运行异构审计 — 绑定当前租户"""
    from security.audit import schedule_audit
    async with pool.acquire() as conn:
        results = await schedule_audit(conn, user_id, limit)
        return ok({"audited": len(results), "results": results})


@router.post("/purify")
async def purify_memory(req: DeleteRequest, user_id: str = Depends(get_current_user),
                        pool: asyncpg.Pool = Depends(get_pool)) -> dict:
    """哈希净化一条记忆 (不可逆删除) — 验证所有权"""
    from security.purifier import soft_delete_memory
    async with pool.acquire() as conn:
        # 验证记忆属于当前租户
        row = await conn.fetchval(
            "SELECT id FROM memories WHERE id=$1 AND user_id=$2",
            req.memory_id, user_id
        )
        if not row:
            return api_error(message="memory not found", code=404, status_code=404)
        result = await soft_delete_memory(conn, req.memory_id, req.reason)
        return ok(result)


@router.get("/fossils")
async def list_fossils(limit: int = 20, user_id: str = Depends(get_current_user),
                       pool: asyncpg.Pool = Depends(get_pool)) -> dict:
    """列出化石节点 — 绑定当前租户"""
    from security.purifier import get_fossil_nodes
    async with pool.acquire() as conn:
        fossils = await get_fossil_nodes(conn, user_id, limit)
        return ok({"fossils": fossils, "count": len(fossils)})


@router.get("/costs")
async def get_costs() -> dict:
    """查询成本统计"""
    from core.llm import get_cost_stats, get_cache_stats
    return ok({
        "costs": get_cost_stats(),
        "cache": get_cache_stats(),
    })
