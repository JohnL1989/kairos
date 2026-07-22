#!/usr/bin/env python3
"""
Reflector — Amber 定时反思引擎 v1.0

用法:
  python3 reflector.py --mode light    # 每小时执行：热度衰减 + 冗余合并
  python3 reflector.py --mode deep     # 每天凌晨执行：同上 + 实体提取

设计文档: 文件14 §6 Reflector 反思引擎
"""

import argparse
import asyncio
import json
import logging
from datetime import datetime, timezone

import asyncpg
# S9/A9 修复：移除独立的 httpx 嵌入客户端（见 get_embedding），
# 嵌入改走核心层；reflector 数据库连接优先使用受限 DSN（见 main）。

# 优先调用服务层合并（精确匹配），再二次相似度合并
from services.memory_service import evolve_memories, reflect

# ── 配置（统一从环境变量读取，与 API 服务共享）──
import os
API_BASE = os.getenv("MNEMOSYNE_URL", "http://127.0.0.1:8010")
PG_DSN = os.getenv("PG_DSN", f"postgresql://{os.getenv('PGUSER','postgres')}:{os.getenv('PGPASSWORD','')}@{os.getenv('PGHOST','127.0.0.1')}:{os.getenv('PGPORT','5432')}/{os.getenv('PGDATABASE','amber')}")
# S9 修复：reflector 直连数据库，绕过 FastAPI 认证/限流/审计中间件。
# 生产应配置仅授予 SELECT/UPDATE 的最小权限 DSN（禁止 DELETE/INSERT），
# 通过 MNEMOSYNE_REFLECTOR_DSN 覆盖默认全权限 PG_DSN。未设置时回退 PG_DSN 并告警。
REFLECTOR_DSN = os.getenv("MNEMOSYNE_REFLECTOR_DSN", "")
EMBED_URL = os.getenv("EMBEDDING_ENDPOINT", "")
EMBED_MODEL = os.getenv("EMBEDDING_MODEL", "")
SIM_THRESHOLD = float(os.getenv("REFLECTOR_SIM_THRESHOLD", "0.92"))
BATCH_SIZE = int(os.getenv("REFLECTOR_BATCH_SIZE", "200"))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("reflector")


# ── 工具函数 ──

async def get_embedding(text: str) -> list[float]:
    """获取单条文本 embedding；复用核心嵌入层（共享客户端+缓存+断路器）。

    A9 修复：不再自实现 httpx 客户端（timeout=30、无缓存、无断路器、
    失败返回空列表而非抛异常），与 core.embedding 行为保持一致。
    嵌入不可用时返回空列表（与调用方约定一致）。
    """
    if not EMBED_URL:
        return []
    from core.embedding import get_embedding_async, EmbeddingUnavailableError
    try:
        result = await get_embedding_async([text])
        return result[0] if result else []
    except EmbeddingUnavailableError:
        return []


async def get_all_users(pool: asyncpg.Pool) -> list[str]:
    rows = await pool.fetch(
        "SELECT DISTINCT user_id FROM memories WHERE is_deleted = FALSE"
    )
    return [r["user_id"] for r in rows]


# ── 冗余检测与合并 ──

async def detect_redundancy(pool: asyncpg.Pool, user_id: str) -> int:
    # 1. 优先调用服务层精确去重
    try:
        result = await evolve_memories(pool, user_id, strategy="consolidate")
        log.info("  ├─ service.evolve_memories(consolidate): merged=%s", result.get("merged", 0))
    except Exception as e:
        log.warning("  ├─ evolve_memories failed: %s", e)

    # 2. 检测余弦相似度 > SIM_THRESHOLD 的记忆并合并。使用 pgvector <=> 近似搜索替代 O(n²)。
    # 缺陷 3.2 修复：一次性批量获取 embedding（含 LIMIT 上限），
    # 避免循环内逐条 fetchval("SELECT embedding::text ...") 产生 N 次额外查询。
    rows = await pool.fetch(
        """SELECT id, heat_score, embedding::text AS embedding
           FROM memories
           WHERE user_id = $1 AND is_deleted = FALSE
             AND embedding IS NOT NULL
           ORDER BY heat_score DESC
           LIMIT $2""",
        user_id, BATCH_SIZE,
    )
    if len(rows) < 2:
        return 0
    # P-05 修复：此前的 `FROM memories a, memories b` 自连接是显式笛卡尔积，
    # 即使用 ANY($ids) 约束在批内，复杂度仍是 O(BATCH_SIZE²)（默认 200×200=4 万对），
    # 且 `(a.embedding <=> b.embedding) < $3` 无法命中 HNSW 索引（索引仅对
    # 「ORDER BY embedding <=> 常量」的近邻搜索有效，不能用于连接谓词）。
    # 改为 CROSS JOIN LATERAL：对批内每条记忆 a，用相关子查询按 `<=> a.embedding`
    # 取 top-K 近邻，此时 ORDER BY 的左侧是外层常量向量，pgvector 可走 HNSW 索引，
    # 整体复杂度降为 O(BATCH_SIZE × K × log N)。K 由 REFLECTOR_NN_K 配置（默认 5）。
    ids = [r["id"] for r in rows]
    threshold = 1.0 - SIM_THRESHOLD
    nn_k = int(os.getenv("REFLECTOR_NN_K", "5"))
    pairs = await pool.fetch(
        """SELECT a.id AS id_a, a.heat_score AS heat_a,
                  nn.id AS id_b, nn.heat_score AS heat_b,
                  nn.dist AS dist
           FROM memories a
           CROSS JOIN LATERAL (
               SELECT b.id, b.heat_score,
                      (b.embedding <=> a.embedding) AS dist
               FROM memories b
               WHERE b.user_id = $1 AND b.is_deleted = FALSE
                 AND b.embedding IS NOT NULL AND b.id != a.id
               ORDER BY b.embedding <=> a.embedding
               LIMIT $4
           ) nn
           WHERE a.user_id = $1 AND a.is_deleted = FALSE
             AND a.embedding IS NOT NULL AND a.id = ANY($2::int[])
             AND nn.dist < $3
           ORDER BY dist ASC
           LIMIT 500""",
        user_id, ids, threshold, nn_k,
    )
    checked: set[int] = set()
    merged = 0
    for s in pairs:
        if merged >= BATCH_SIZE:
            break
        aid, bid = s["id_a"], s["id_b"]
        if aid in checked or bid in checked:
            continue
        sim = 1.0 - s["dist"]
        keep_id = aid if (s["heat_a"] or 0) >= (s["heat_b"] or 0) else bid
        del_id = bid if keep_id == aid else aid
        # 转移 entities（高热记忆保留）
        await pool.execute(
            """UPDATE memory_entities
               SET memory_id = $1
               WHERE memory_id = $2
                 AND entity_id NOT IN (
                   SELECT entity_id FROM memory_entities WHERE memory_id = $1
                 )""",
            keep_id, del_id,
        )
        # 软删冗余记忆
        await pool.execute(
            "UPDATE memories SET is_deleted = TRUE WHERE id = $1", del_id
        )
        checked.add(del_id)
        merged += 1
        log.info("  └─ Merged #%d → #%d  (sim=%.3f)", del_id, keep_id, sim)
    return merged

# ── 运行模式 ──

async def run_light(pool: asyncpg.Pool, users: list[str]) -> None:
    """Light 模式：热度衰减 + 冗余合并"""
    for uid in users:
        log.info("[light] Processing user=%s", uid)
        # 1. 直接调用服务层 reflect（缺陷 4.4：消除 HTTP 回环依赖与认证开销）
        # R13 修复：加总体超时，避免 DB 慢查询/异常时 reflector 长时间阻塞连接。
        try:
            async with pool.acquire() as conn:
                result = await asyncio.wait_for(
                    reflect(conn, uid, mode="light"), timeout=300
                )
                log.info("  ├─ reflect(light) direct: %s", result.get("status", "ok"))
        except asyncio.TimeoutError:
            log.error("  ├─ reflect(light) 超时 (300s)，跳过 user=%s", uid)
        except Exception as e:
            log.error("  ├─ reflect(light) direct failed: %s", e)

        # 2. 冗余检测
        try:
            n = await asyncio.wait_for(
                detect_redundancy(pool, uid), timeout=600
            )
        except asyncio.TimeoutError:
            log.error("  └─ 冗余检测超时 (600s)，跳过 user=%s", uid)
            n = 0
        if n:
            log.info("  └─ Merged %d redundant memories", n)
        else:
            log.info("  └─ No redundancy found")


async def run_deep(pool: asyncpg.Pool, users: list[str]) -> None:
    """Deep 模式：热度衰减 + 实体提取 + 冗余合并"""
    for uid in users:
        log.info("[deep] Processing user=%s", uid)
        # 1. 直接调用服务层 reflect（缺陷 4.4：消除 HTTP 回环依赖与认证开销）
        # R13 修复：加总体超时（见 run_light 说明）。
        try:
            async with pool.acquire() as conn:
                result = await asyncio.wait_for(
                    reflect(conn, uid, mode="deep"), timeout=300
                )
                log.info("  ├─ reflect(deep) direct: %s", result.get("status", "ok"))
        except asyncio.TimeoutError:
            log.error("  ├─ reflect(deep) 超时 (300s)，跳过 user=%s", uid)
        except Exception as e:
            log.error("  ├─ reflect(deep) direct failed: %s", e)

        # 2. 冗余检测
        try:
            n = await asyncio.wait_for(
                detect_redundancy(pool, uid), timeout=600
            )
        except asyncio.TimeoutError:
            log.error("  └─ 冗余检测超时 (600s)，跳过 user=%s", uid)
            n = 0
        if n:
            log.info("  └─ Merged %d redundant memories", n)
        else:
            log.info("  └─ No redundancy found")


# ── 入口 ──

async def main() -> None:
    parser = argparse.ArgumentParser(description="Amber Reflector — 定时反思引擎")
    parser.add_argument(
        "--mode",
        choices=["light", "deep"],
        default="light",
        help="light=每小时(热度+冗余), deep=每日(含实体提取)",
    )
    args = parser.parse_args()

    log.info("Reflector starting — mode=%s", args.mode)
    start = datetime.now(timezone.utc)

    # A-03 修复：reflector 直连数据库、绕过 API 认证/限流/审计，必须以最小权限角色运行。
    # 此前仅在缺少 MNEMOSYNE_REFLECTOR_DSN 时「告警而非阻断」，等于默认以全权限
    # PG_DSN 运行——一旦 reflector 逻辑或依赖被攻破，攻击者即拥有 DELETE/DROP 全权。
    # 现在改为默认阻断：未配置受限 DSN 直接拒绝启动；仅当显式设置
    # MNEMOSYNE_REFLECTOR_ALLOW_FULL_DSN=1（开发/本地）时才允许回退全权限并告警。
    if REFLECTOR_DSN:
        dsn = REFLECTOR_DSN
    else:
        in_dev = os.getenv("MNEMOSYNE_DEV_INSECURE", "0") == "1"
        if in_dev and os.getenv("MNEMOSYNE_REFLECTOR_ALLOW_FULL_DSN", "0") == "1":
            dsn = PG_DSN
            log.warning(
                "安全告警[A-03]：未设置 MNEMOSYNE_REFLECTOR_DSN，已按显式开关回退全权限 "
                "PG_DSN 运行。此模式仅限开发/本地，生产严禁使用。"
            )
        else:
            log.error(
                "安全阻断[A-03]：reflector 未配置最小权限 DSN。请设置 "
                "MNEMOSYNE_REFLECTOR_DSN（仅授予 SELECT/UPDATE，禁止 DELETE/INSERT/DDL）；"
                "确需以全权限运行请显式设置 MNEMOSYNE_REFLECTOR_ALLOW_FULL_DSN=1。拒绝启动。"
            )
            raise SystemExit(2)

    pool = await asyncpg.create_pool(dsn, min_size=1, max_size=2)
    # A-03 长期整改：核心循环已提炼为 run_reflector_cycle（见下方定义），
    # 供 API 内置调度器与独立 CLI 共享；advisory lock 互斥保证不双跑。
    try:
        await run_reflector_cycle(pool, args.mode)
    finally:
        await pool.close()


async def run_reflector_cycle(pool: asyncpg.Pool, mode: str = "light",
                             users: list[str] | None = None) -> None:
    """A-03 长期整改：将 reflector 核心循环提炼为可复用单元。

    两条触发路径共享同一实现：
      1) API 进程内置调度器（main._background_scheduler）直接调用，复用同一
         连接池与租户状态，消除「独立进程 + 独立连接 + 绕过认证/限流/审计」
         的架构旁路；
      2) 独立 CLI（__main__）调用，作为开发/应急手动触发。

    分布式互斥：沿用 PostgreSQL 会话级 advisory lock（键由 mode 派生，
    light/deep 各一把）。无论哪条路径触发，同一 mode 全局仅一个实例运行；
    另一条路径探测到锁被持有时直接退出，杜绝双跑导致的重复合并/衰减。
    锁随连接关闭或进程崩溃自动释放。
    """
    log.info("Reflector cycle 启动 (mode=%s)", mode)
    start = datetime.now(timezone.utc)
    if users is None:
        users = await get_all_users(pool)
    if not users:
        log.info("No users found, nothing to do.")
        return
    log.info("Found %d active user(s)", len(users))
    lock_key = 0x4D454D00 + (1 if mode == "deep" else 0)  # 'MEM' + mode
    lock_conn = await pool.acquire()
    try:
        got = await lock_conn.fetchval("SELECT pg_try_advisory_lock($1)", lock_key)
        if not got:
            log.warning(
                "R-04：已有 reflector(mode=%s) 实例在运行（advisory lock 未获取），本次退出。",
                mode,
            )
            return
        try:
            if mode == "light":
                await run_light(pool, users)
            else:
                await run_deep(pool, users)
            elapsed = (datetime.now(timezone.utc) - start).total_seconds()
            log.info("Reflector cycle 完成 in %.1fs", elapsed)
        finally:
            try:
                await lock_conn.fetchval("SELECT pg_advisory_unlock($1)", lock_key)
            except Exception:
                pass
    finally:
        await pool.release(lock_conn)


if __name__ == "__main__":
    asyncio.run(main())
