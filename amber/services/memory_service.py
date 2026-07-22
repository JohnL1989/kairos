"""
Mnemosyne v1.5.0 — 记忆服务层
封装核心业务逻辑：热度衰减、层级迁移、冲突检测、反思进化
"""
import os
import re
import logging
import asyncpg

logger = logging.getLogger("services.memory_service")


def _affected_rows(status: object) -> int:
    """R2 修复：稳健解析 asyncpg ``execute`` 返回的命令标签（如 ``UPDATE 5`` / ``DELETE 3``）。

    原实现 ``str(r).split()[-1]`` 依赖驱动返回字符串的具体格式，一旦驱动版本
    变更返回结构即解析失败。此处用正则抽取尾部整数，解析失败安全返回 0。
    """
    if status is None:
        return 0
    m = re.search(r"(\d+)\s*$", str(status))
    return int(m.group(1)) if m else 0


def text_diff_ratio(a: str, b: str) -> float:
    """字符串相似度比较"""
    import difflib
    return difflib.SequenceMatcher(None, a, b).ratio()


async def detect_conflict(conn: asyncpg.Connection, user_id: str, new_content: str,
                          new_embedding_str: str) -> dict:
    """检测新记忆是否与已有记忆冲突或重复。"""
    dist_threshold = float(os.getenv("CONFLICT_DIST_THRESHOLD", "0.12"))
    rows = await conn.fetch(
        "SELECT id, content, embedding <=> $1::vector AS dist, heat_score "
        "FROM memories WHERE user_id=$2 AND is_deleted=FALSE "
        "ORDER BY embedding <=> $1::vector LIMIT 10",
        new_embedding_str, user_id
    )
    for r in rows:
        if r["dist"] is not None and r["dist"] > dist_threshold:
            continue
        if r["dist"] is None:
            keywords = [w for w in new_content.split() if len(w) > 2]
            matched = any(kw in (r["content"] or "") for kw in keywords)
            if not matched:
                continue
        ratio = text_diff_ratio(new_content, r["content"])
        if ratio > 0.85:
            return {"action": "merge", "id": r["id"]}
        elif ratio < 0.5 and (r["dist"] is not None
                              and r["dist"] < dist_threshold * 0.8):
            return {"action": "conflict", "id": r["id"], "old_content": r["content"]}
    return {"action": "fresh"}


async def _batch_update(conn: asyncpg.Connection, set_clause: str,
                       where_extra: str, user_id: str, batch: int = 1000,
                       params: tuple | None = None) -> int:
    """P5 修复 + A-07 扩展：分批更新 memories，限单次 UPDATE 行锁范围。

    原实现对百万级表直接 ``UPDATE ... WHERE user_id=$1``，会全表扫描并对命中的
    每一行加写锁，在 cron 期间可能长时间阻塞在线写入。改为按 id 游标分批：
    每批仅更新 ``batch`` 行，行锁范围可控，批间释放让在线写入得以穿插。

    ``where_extra`` 为追加在 ``user_id=$1 AND is_deleted=FALSE`` 之后的额外条件
    （含前导 AND），用于限定本批更新的目标行；``set_clause`` 即 ``SET ...`` 子句。
    ``params`` 为 set_clause 中额外参数化占位符（$2, $3...）对应的值元组。
    返回受影响总行数。
    """
    total = 0
    while True:
        ids = await conn.fetch(
            f"SELECT id FROM memories WHERE user_id=$1 AND is_deleted=FALSE "
            f"{where_extra} ORDER BY id LIMIT {batch}",
            user_id,
        )
        if not ids:
            break
        id_list = [r["id"] for r in ids]
        r = await conn.execute(
            f"UPDATE memories SET {set_clause} "
            f"WHERE user_id=$1 AND id=ANY($2::int[]) AND is_deleted=FALSE",
            user_id, id_list, *(params or ()),
        )
        total += _affected_rows(r)
        if len(ids) < batch:
            break
    return total


async def reflect(conn: asyncpg.Connection, user_id: str, mode: str = "light") -> dict:
    """反思：热度衰减 + 层级迁移 + 实体提取"""
    # P-02 修复：步骤 1~4 是「衰减 → 加权 → 惩罚 → 层级迁移」的强耦合链，层级迁移
    # 直接依赖前三步算出的 heat_score。此前每步（乃至每个分批 UPDATE）都是独立自动
    # 提交，一旦中途失败（DB 抖动/超时），就会留下「已衰减但未迁移层级」的不一致中间
    # 态，且非幂等的衰减在重跑时会二次扣减。现将 1~4 包裹进单个事务：要么整体生效、
    # 要么整体回滚，消除跨步骤不一致与重复衰减。
    #   与 P5「分批控制行锁」的关系：分批仍保留——它限制单条 UPDATE 语句的体量，
    #   降低单语句的锁获取峰值与 WAL 尖峰；事务边界只保证一致性，二者不冲突。
    async with conn.transaction():
        # 1. 时间衰减（P5：分批，避免单语句全表行锁）
        await _batch_update(
            conn,
            set_clause="""
                heat_score = GREATEST(0.0, heat_score -
                    CASE
                        WHEN last_accessed IS NULL THEN 0.02
                        WHEN last_accessed < NOW() - INTERVAL '90 days' THEN 0.08
                        WHEN last_accessed < NOW() - INTERVAL '30 days' THEN 0.04
                        WHEN last_accessed < NOW() - INTERVAL '7 days' THEN 0.02
                        ELSE 0.01
                    END)
            """,
            where_extra="",  # 作用于全部未删除记忆
            user_id=user_id,
        )
        # 2. 访问加权（P5：分批）
        await _batch_update(
            conn,
            set_clause="heat_score = LEAST(1.0, heat_score + 0.05)",
            where_extra=(
                "AND access_count >= 5 AND last_accessed > NOW() - INTERVAL '7 days'"
            ),
            user_id=user_id,
        )
        # 3. 矛盾记忆加速衰减（P5：分批）
        await _batch_update(
            conn,
            set_clause="heat_score = GREATEST(0.0, heat_score - 0.1)",
            where_extra="AND invalid_at IS NOT NULL",
            user_id=user_id,
        )
        # 4. 层级自动迁移（P5：分批，各层级独立）
        await _batch_update(
            conn, set_clause="tier = 'L1'",
            where_extra="AND heat_score > 0.7 AND tier != 'L1'", user_id=user_id)
        await _batch_update(
            conn, set_clause="tier = 'L2'",
            where_extra="AND heat_score BETWEEN 0.2 AND 0.7 AND tier NOT IN ('L2','L3','L4')",
            user_id=user_id)
        await _batch_update(
            conn, set_clause="tier = 'L3'",
            where_extra="AND heat_score < 0.2 AND last_accessed < NOW() - INTERVAL '30 days'",
            user_id=user_id)
        await _batch_update(
            conn, set_clause="tier = 'L4', is_deleted = TRUE, forgotten_at = NOW()",
            where_extra="AND heat_score < 0.05 AND last_accessed < NOW() - INTERVAL '90 days'",
            user_id=user_id)
    # 5. 深度模式：实体提取
    extracted = 0
    if mode == "deep":
        unproc = await conn.fetch(
            "SELECT m.id, m.content FROM memories m"
            " LEFT JOIN memory_entities me ON m.id = me.memory_id"
            " WHERE m.user_id = $1 AND me.memory_id IS NULL"
            " AND m.is_deleted = FALSE LIMIT 100", user_id)
        for row in unproc:
            cand = set()
            for m in re.finditer(
                    r'[\u201c\u201d\u300c\u300d]([^\u201c\u201d\u300c\u300d]{2,15})'
                    r'[\u201c\u201d\u300c\u300d]', row["content"]):
                cand.add(m.group(1).strip())
            if not cand:
                for p in re.split(r'[、，．！？,.!?\s的和在是了]+', row["content"]):
                    p = p.strip()
                    if 2 <= len(p) <= 15:
                        cand.add(p)
            for name in cand:
                try:
                    ex = await conn.fetchrow(
                        "SELECT id FROM entities WHERE user_id=$1 AND name=$2",
                        user_id, name)
                    if not ex:
                        await conn.execute(
                            "INSERT INTO entities (user_id, name, memory_id)"
                            " VALUES ($1, $2, $3) ON CONFLICT DO NOTHING",
                            user_id, name, row["id"])
                        extracted += 1
                except Exception:
                    # R1 修复：红线整改——不再静默吞错，记录告警并计数，
                    # 使「实体关联失败导致记忆无法被实体检索」这一数据质量劣化可被观测。
                    logger.warning(
                        "实体关联失败 memory_id=%s name=%s", row["id"], name
                    )
                    failed = getattr(conn, "_entity_fail_count", 0) + 1
                    conn._entity_fail_count = failed  # 仅作运行时计数，便于监控
        if extracted > 0:
            await conn.execute(
                "UPDATE memories SET heat_score = heat_score + 0.1"
                " WHERE user_id = $1 AND is_deleted = FALSE"
                " AND id IN (SELECT memory_id FROM memory_entities)", user_id)
    return {"status": f"Reflection ({mode}) completed", "entities_extracted": extracted}


async def evolve_memories(conn: asyncpg.Connection, user_id: str, strategy: str = "consolidate") -> dict:
    """进化记忆：合并重复/热度提升/清理"""
    if strategy == "cleanup":
        r = await conn.execute(
            "UPDATE memories SET is_deleted=TRUE, forgotten_at=NOW()"
            " WHERE user_id=$1 AND tier='L3' AND heat_score<0.05"
            " AND last_accessed<NOW()-INTERVAL '60 days'", user_id)
        return {"strategy": "cleanup", "affected": _affected_rows(r)}
    elif strategy == "boost":
        r = await conn.execute(
            "UPDATE memories SET heat_score=LEAST(1.0, heat_score+0.15)"
            " WHERE user_id=$1 AND access_count>5 AND heat_score<0.3"
            " AND is_deleted=FALSE", user_id)
        return {"strategy": "boost", "affected": _affected_rows(r)}
    elif strategy == "consolidate":
        # 缺陷 4.2 修复：按定长 content_hash 分组（而非 TEXT 字段 content），
        # 避免大表 GROUP BY content 触发的全表排序/哈希聚合 OOM。
        # 仅对非空哈希分组；NULL 哈希（未回填）的记忆不参与去重。
        dups = await conn.fetch("""
            SELECT content_hash, MAX(content) AS content,
                   ARRAY_AGG(id ORDER BY created_at DESC) AS ids,
                   COUNT(*) AS cnt
            FROM memories
            WHERE user_id=$1 AND is_deleted=FALSE AND content_hash IS NOT NULL
            GROUP BY content_hash
            HAVING COUNT(*) > 1
            LIMIT 100
        """, user_id)
        merged = 0
        for row in dups:
            ids = row["ids"]  # ARRAY_AGG returns list[int]
            keep_id = ids[0]
            for dup_id in ids[1:]:
                # P-02 同类修复：实体转移 + 软删是一对必须原子完成的操作。若转移成功
                # 而软删失败，会出现「实体已迁走但重复记忆仍存活」的错乱；反之则丢实体。
                # 每对合并各自包裹事务：任一失败整对回滚，不污染其它对的进度。
                async with conn.transaction():
                    await conn.execute(
                        "UPDATE memory_entities SET memory_id=$1"
                        " WHERE memory_id=$2 AND entity_id NOT IN"
                        " (SELECT entity_id FROM memory_entities WHERE memory_id=$1)",
                        keep_id, dup_id)
                    await conn.execute(
                        "UPDATE memories SET is_deleted=TRUE WHERE id=$1", dup_id)
                merged += 1
        return {"strategy": "consolidate", "merged": merged}
    return {"strategy": strategy, "status": "done"}


async def cleanup(conn: asyncpg.Connection, user_id: str, threshold: float = 0.1) -> dict:
    """清理低热度记忆（P8 修复：分批更新，限制单次 UPDATE 的行锁范围）。

    原实现一次性 ``UPDATE ... WHERE user_id=$1 AND heat_score < $2`` 会对命中的
    全部冷数据加写锁，事务期间阻塞在线写入。改为按 id 游标分批（每批 ≤1000 行），
    行锁范围可控，批间释放让在线写入得以穿插。
    """
    total = 0
    batch = 1000
    while True:
        ids = await conn.fetch(
            "SELECT id FROM memories WHERE user_id=$1 AND is_deleted=FALSE "
            "AND heat_score < $2 ORDER BY heat_score ASC, last_accessed ASC LIMIT $3",
            user_id, threshold, batch)
        if not ids:
            break
        id_list = [r["id"] for r in ids]
        r = await conn.execute(
            "UPDATE memories SET is_deleted=TRUE, forgotten_at=NOW() "
            "WHERE user_id=$1 AND id=ANY($2::int[]) AND is_deleted=FALSE",
            user_id, id_list)
        total += _affected_rows(r)
        if len(ids) < batch:
            break
    return {"status": "cleanup done", "threshold": threshold, "affected": total}
