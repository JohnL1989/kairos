"""
Aion Memory — 记忆写入服务层（A4 重构）

将 api/memories.py 中原内联的「创建记忆」编排逻辑（内容哈希去重、容量门禁、
异步 embedding 生成、memory_traces 双写）下沉到服务层，使路由保持「鉴权 + 参数
校验 + 调用」的薄封装。该服务可被多个入口复用：
  - REST 路由（api/memories.py）
  - TMT 管道（tmt/router.py）写入沉淀记忆
  - 批量导入 / 迁移脚本
不再把去重与 embedding 编排锁死在 HTTP 层，便于单测与复用。
"""
import asyncio
import hashlib
import json
import logging
from datetime import datetime, timezone
from typing import Optional

import asyncpg
from fastapi import HTTPException
from pydantic import BaseModel, Field

from api.response import ok, error as api_error
from api import shared
from api.shared import vec_to_str, track_background_task
from config import settings  # A8 修复：容量配额统一走集中配置，消除散落 os.getenv 分叉

logger = logging.getLogger("amber.write")


class MemoryCreate(BaseModel):
    """记忆创建入参（与 REST 契约对齐；移至此服务层以便多入口复用）。"""
    content: str = Field(..., max_length=10000, description="记忆内容，最长10000字符")
    category: str = "general"
    scope_target: str = "general"  # 'durable' | 'general'
    scope_session_id: Optional[str] = None  # general 时记录所属会话
    # 结构化字段（存入 metadata JSONB）
    memory_type: Optional[str] = None  # error / success / rule / lesson / fact
    task_type: Optional[str] = None    # AUDIT_FIX / FRONTEND_DEV / ...
    severity: Optional[str] = None     # critical / high / medium / low
    decay_months: Optional[int] = None  # 有效期（月）
    linked_skills: Optional[list[str]] = None


async def create_memory(
    pool: asyncpg.Pool,
    user_id: str,
    mem: MemoryCreate,
) -> dict:
    """创建一条记忆（编排版，供路由/管道/导入复用）。

    返回与 REST 契约一致的 dict：ok({"id", "created", "scope", "dedup"}) 或
    api_error(...)（invalid scope_target）。异常上抛由调用方（路由）转为 500。
    """
    if mem.scope_target not in ("durable", "general"):
        return api_error(message=f"无效 scope_target: {mem.scope_target}", code=400)

    # 结构化字段序列化到 metadata JSONB
    metadata_json = json.dumps({
        "memory_type": mem.memory_type,
        "task_type": mem.task_type,
        "severity": mem.severity,
        "decay_months": mem.decay_months,
        "linked_skills": mem.linked_skills,
        # R2 修复：创建即写入 embedding_status='pending'，使「写入后、后台嵌入完成前」
        # 崩溃的记忆进入可被补偿扫描识别的状态，而非介于 ready/failed 之外的幽灵状态。
        "embedding_status": "pending",
    })
    # 内容哈希：用于写时去重（A2）和 evolve_memories 的重复检测
    content_hash = hashlib.sha256(mem.content.encode()).hexdigest()[:64]

    # P4 修复：硬上限 + 自动冷数据归档。超过 settings.max_memories 时，
    # 先软删除最冷的一批（带缓冲），而非仅告警或拒绝写入，避免 durable 无界增长。
    # A8 修复：容量配额统一从集中配置 AmberSettings 读取，
    # 与启动校验（_validate）同源，消除与散落 os.getenv 的行为分叉。
    max_memories = settings.max_memories

    # A-01 修复：移除冗余的「读-判-写」去重前置 SELECT（CHECK-THEN-ACT 存在 TOCTOU 竞态，
    # 且与下方原子 ON CONFLICT 重复）。去重统一由唯一约束 + ON CONFLICT DO UPDATE 原子完成
    # （见下方 RETURNING (XMAX=0) AS inserted 判定），热点写入路径少一次网络往返。
    # P4：容量门禁——超限时软删除最冷的溢出批次（保留缓冲，避免每次写入都触发）
    async with pool.acquire() as conn:
        if max_memories > 0:
            # P10 修复：不再每次写入都 COUNT(*) 全表/索引扫描。
            # 改为读 user_memory_counts 计数器表（由触发器实时维护），
            # 仅在计数器表缺失（未跑迁移）时回退到精确 COUNT(*)，
            # 高频写入场景下热路径延迟从 O(扫描) 降为 O(主键点查)。
            cur = await conn.fetchval(
                "SELECT cnt FROM user_memory_counts WHERE user_id=$1", user_id
            )
            if cur is None:
                cur = await conn.fetchval(
                    "SELECT COUNT(*) FROM memories WHERE user_id=$1 AND is_deleted=FALSE",
                    user_id,
                )
            if cur >= max_memories:
                overflow = cur - max_memories + 50  # 一次多清 50 条作缓冲
                await conn.execute(
                    "UPDATE memories SET is_deleted=TRUE, forgotten_at=NOW() "
                    "WHERE user_id=$1 AND is_deleted=FALSE AND id IN ("
                    "  SELECT id FROM memories WHERE user_id=$1 AND is_deleted=FALSE "
                    "  ORDER BY heat_score ASC, last_accessed ASC LIMIT $2"
                    ")",
                    user_id, overflow,
                )

        # R3 修复：原子去重——在唯一约束 (user_id, content_hash) WHERE is_deleted=FALSE
        # 保护下，并发相同内容请求只会成功插入一条，其余落入 ON CONFLICT 归一为热度+1，
        # 消除「读-判-写」CHECK-THEN-ACT 的 TOCTOU 竞态。
        try:
            row = await conn.fetchrow(
                "INSERT INTO memories (user_id, content, content_hash, category, scope_target, scope_session_id, metadata) "
                "VALUES ($1, $2, $3, $4, $5, $6, $7::jsonb) "
                "ON CONFLICT (user_id, content_hash) WHERE is_deleted=FALSE "
                "DO UPDATE SET access_count=memories.access_count+1, last_accessed=NOW() "
                "RETURNING id, created_at, scope_target, (XMAX = 0) AS inserted",
                user_id, mem.content, content_hash, mem.category,
                mem.scope_target, mem.scope_session_id,
                metadata_json,
            )
            if not row["inserted"]:
                # 唯一约束命中：视为去重命中
                return ok({
                    "id": row["id"], "created": str(row["created_at"]),
                    "scope": row["scope_target"], "dedup": True,
                })
            memory_id = row["id"]
        except asyncpg.UniqueViolationError:
            # 极端竞态兜底：约束尚未建好或边界情况，回退到查重归一
            exist = await conn.fetchrow(
                "SELECT id, created_at, scope_target FROM memories "
                "WHERE user_id=$1 AND content_hash=$2 AND is_deleted=FALSE LIMIT 1",
                user_id, content_hash,
            )
            if exist:
                return ok({
                    "id": exist["id"], "created": str(exist["created_at"]),
                    "scope": exist["scope_target"], "dedup": True,
                })
            raise

    # 异步生成 embedding（后台任务，不阻塞返回）
    _schedule_embedding(pool, mem.content, memory_id)
    # memory_traces 双写（Layer 1 自我管理，后台异步不阻塞返回）
    _schedule_trace(pool, user_id, memory_id, mem)

    return ok({
        "id": memory_id, "created": str(row["created_at"]),
        "scope": row["scope_target"],
    })


def _schedule_embedding(pool: asyncpg.Pool, content: str, memory_id: int) -> None:
    """后台异步生成 embedding，失败时标记 embedding_status='failed' 供补偿扫描。"""
    async def _generate_embedding(retry_count: int = 0, max_retries: int = 3) -> None:
        try:
            fn = shared.get_cached_embedding_fn()
            if fn:
                raw = (await fn([content[:2000]]))[0]
                if raw and len(raw) > 0:
                    v_str = vec_to_str(raw)
                    async with pool.acquire() as conn:
                        await conn.execute(
                            "UPDATE memories SET embedding=$1::vector, "
                            "metadata = COALESCE(metadata,'{}'::jsonb) "
                            "|| '{\"embedding_status\":\"ready\"}'::jsonb "
                            "WHERE id=$2",
                            v_str, memory_id,
                        )
                    return
        except Exception:
            if retry_count < max_retries:
                delay = 2 ** retry_count
                await asyncio.sleep(delay)
                return await _generate_embedding(retry_count + 1, max_retries)
            logger.exception("embedding 重试耗尽 id=%d", memory_id)
        # 最终失败，标记供补偿扫描
        try:
            async with pool.acquire() as conn:
                await conn.execute(
                    "UPDATE memories SET metadata = COALESCE(metadata,'{}'::jsonb) "
                    "|| '{\"embedding_status\":\"failed\"}'::jsonb WHERE id=$1",
                    memory_id,
                )
        except Exception:
            logger.warning("embedding 失败状态标记异常 id=%d", memory_id)
    try:
        task = asyncio.create_task(_generate_embedding())
        track_background_task(task)
    except Exception:
        logger.exception("create_memory 后台 embedding 任务启动失败")


def _schedule_trace(pool: asyncpg.Pool, user_id: str, memory_id: int, mem: MemoryCreate) -> None:
    """后台异步双写 memory_traces（Layer 1 自我管理）。"""
    async def _log_trace() -> None:
        try:
            async with pool.acquire() as _conn:
                await _conn.execute(
                    "INSERT INTO memory_traces (user_id, memory_id, action, metadata) "
                    "VALUES ($1, $2, $3, $4::jsonb)",
                    user_id, memory_id, "create",
                                    json.dumps({
                    # S8 修复：审计表不再记录明文内容前 200 字（GDPR 被遗忘权合规）。
                    # 仅记 content_hash 前缀（可关联到原记忆但不可还原明文）+ 长度（供统计）。
                    "content_hash": content_hash[:16],
                    "content_length": len(mem.content),
                    "scope_target": mem.scope_target,
                    "category": mem.category,
                }),
                )
        except Exception:
            logger.warning(
                "trace 写入失败：Layer 1 自我管理数据丢失 (memory_id=%s)", memory_id
            )
    try:
        task = asyncio.create_task(_log_trace())
        track_background_task(task)
    except Exception:
        logger.debug("trace 后台任务启动失败（静默忽略）")
