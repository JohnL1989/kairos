"""Aion Memory — 共享状态与依赖注入

pool 和 get_embedding_fn 由 main.py lifespan 经 setup() 写入模块级全局变量，
该全局变量是【唯一权威源】；app.state 仅作为请求上下文的镜像。
所有路由模块通过 FastAPI Depends() 获取，禁止直接读写模块级变量。
"""
import asyncio
import logging
from typing import Optional, Callable
from fastapi import HTTPException, Request
import asyncpg

logger = logging.getLogger("amber.shared")

# ── 模块级全局（由 setup() 初始化一次，唯一权威源；后台任务与路由均从此读取） ──
# A-04 修复：全局 _pool/_get_embedding_fn 为唯一可写权威源，app.state 仅作镜像。
# 所有读取路径（get_pool/get_embedding 请求上下文、get_cached_pool/...
# 后台任务）均以全局为准，消除双源真相分叉（测试仅 mock 一处导致另一处拿到 None）。
_pool: Optional[asyncpg.Pool] = None
_get_embedding_fn: Optional[Callable] = None

# ── 后台任务追踪集合（缺陷 4.1/R1：防止 Task was destroyed but pending 警告） ──
# A4 重构：由 api/memories.py 上提到共享层，供 memory_write_service 与路由共用，
# 也使 main.py 关闭期的任务排空逻辑有唯一权威来源。
# P12 修复：集合设上限，嵌入服务持续不可达时避免无界增长导致内存泄漏。
BACKGROUND_TASKS: set = set()
MAX_BACKGROUND_TASKS = 1000


def track_background_task(task) -> None:
    """登记一个 asyncio 后台任务，完成时自动从集合中移除并上报异常。

    P12 修复：超上限时仅告警并不再追踪（任务仍会执行），防止嵌入服务
    持续不可达时集合无界增长造成内存泄漏。
    R15 修复：done 回调检查 task.exception()，异常不再被静默吞掉，
    embedding 失败等会被结构化记录，便于补偿扫描与告警。
    """
    if len(BACKGROUND_TASKS) >= MAX_BACKGROUND_TASKS:
        logger.warning(
            "后台任务数已达上限 (%d)，本任务将不被追踪（仍会执行）", MAX_BACKGROUND_TASKS
        )
        return
    BACKGROUND_TASKS.add(task)

    def _on_done(t: asyncio.Task) -> None:
        BACKGROUND_TASKS.discard(t)
        if t.cancelled():
            return
        exc = t.exception()
        if exc:
            logger.error("后台任务 %s 失败: %s", t.get_name(), exc, exc_info=exc)

    task.add_done_callback(_on_done)


def setup(pool: asyncpg.Pool, get_embedding_fn: Callable) -> None:
    """在 lifespan 中调用一次，初始化 app.state 和模块级缓存。"""
    global _pool, _get_embedding_fn
    _pool = pool
    _get_embedding_fn = get_embedding_fn


def get_cached_pool() -> asyncpg.Pool:
    """供后台任务（非请求上下文）获取连接池。"""
    if _pool is None:
        raise HTTPException(status_code=503, detail="database not ready")
    return _pool


def get_cached_embedding_fn() -> Callable:
    """供后台任务（非请求上下文）获取嵌入函数。"""
    if _get_embedding_fn is None:
        raise HTTPException(status_code=503, detail="embedding not ready")
    return _get_embedding_fn


# ── FastAPI Depends（从 app.state 读取，请求上下文用） ──


async def get_pool(request: Request) -> asyncpg.Pool:
    """FastAPI 依赖：获取数据库连接池。

    A-04 修复：模块级 _pool 为【唯一权威源】，app.state.pool 仅作请求内镜像。
    读取时以全局 _pool 为准、回退到 app.state（兼容 lifespan 前极早请求），
    并始终回填 app.state，确保两处一致；任何写入只发生在全局（setup），
    消除「两处均可写导致真相分叉」的架构隐患。
    """
    pool = _pool or request.app.state.pool
    if pool is None:
        raise HTTPException(status_code=503, detail="database not ready")
    request.app.state.pool = pool
    return pool


async def get_embedding(request: Request) -> Callable:
    """FastAPI 依赖：获取嵌入函数（同 get_pool 的单一权威源语义）。"""
    fn = _get_embedding_fn or request.app.state.get_embedding_fn
    if fn is None:
        raise HTTPException(status_code=503, detail="embedding not ready")
    request.app.state.get_embedding_fn = fn
    return fn


async def get_current_user(request: Request) -> str:
    """FastAPI 依赖：从认证中间件获取当前租户 ID"""
    return request.state.tenant_id


def vec_to_str(raw: list) -> str:
    """将嵌入向量列表转换为 PostgreSQL 向量字符串"""
    return "[" + ",".join(str(x) for x in raw) + "]"
