"""
Aion Memory - 搜索与检索路由
"""
import re
import time
import os
import asyncpg
from dataclasses import dataclass, field, asdict
from typing import Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from . import shared
from .shared import get_current_user, get_pool, vec_to_str
from .response import ok

router = APIRouter()

# P3 修复：两阶段路径候选集硬上限，防止 Python 层内存爆炸
MAX_CANDIDATES = 500


# ── Recall Funnel Trace ──

@dataclass
class SearchTrace:
    """召回追踪记录：每个搜索请求各阶段的状态快照。"""
    query: str = ""
    scope_session_id: str = ""
    total_candidates: int = 0
    keyword_match: int = 0
    vector_match: int = 0
    has_vector: bool = False
    final_returned: int = 0
    stage_timings_ms: dict = field(default_factory=dict)
    returned_chars: int = 0
    skipped: bool = False
    skip_reason: str = ""


class DialecticRequest(BaseModel):
    # S-05 修复：限制 query 长度，防止超长查询撑爆 LLM 提示词/向量输入造成 DoS。
    query: str = Field(max_length=2000)
    max_memories: int = Field(default=5, ge=1, le=200)
    include_context: bool = True
    scope_session_id: Optional[str] = None
    trace: bool = False
    task_type: Optional[str] = None  # AUDIT_FIX / FRONTEND_DEV / ...


class MemorySearch(BaseModel):
    # S-05 修复：限制 query 长度（与 DialecticRequest 一致）。
    query: str = Field(max_length=2000)
    top_k: int = Field(default=5, ge=1, le=200)
    scope_session_id: Optional[str] = None
    trace: bool = False
    task_type: Optional[str] = None  # AUDIT_FIX / FRONTEND_DEV / ...


class ExplainRequest(BaseModel):
    # S-05 修复：限制 query 长度（与 MemorySearch 一致）。
    query: str = Field(max_length=2000)
    scope_session_id: Optional[str] = None


# ── 保守门禁 ──
TRIVIAL_PATTERNS = ["你好", "hello", "hi", "hey"]
TRIVIAL_MAX_LEN = 2


def _should_skip(query: str) -> tuple[bool, str]:
    q = query.strip()
    if not q: return True, "empty"
    if len(q) <= TRIVIAL_MAX_LEN: return True, "too_short"
    for p in TRIVIAL_PATTERNS:
        if q.lower() == p.lower(): return True, "greeting"
    alpha_count = sum(1 for c in q if c.isalpha())
    if alpha_count == 0: return True, "noise"
    return False, ""


def _extract_keywords(query: str) -> list[str]:
    cleaned = re.sub(r'[？！!?，。、；：\s]+', ' ', query)
    return [w.strip() for w in cleaned.split() if len(w.strip()) > 1]


def _build_where_clause(
    user_id: str,
    scope_session_id: Optional[str],
    param_offset: int = 0,
    task_type: Optional[str] = None,
    fts_keywords: Optional[list] = None,
) -> tuple[str, list]:
    """构建 WHERE 子句和对应的参数（不包含 ORDER BY/LIMIT）。

    P2 修复：当 fts_keywords 提供（即嵌入不可用的纯文本回退路径）时，追加 GIN 全文索引
    硬过滤 ``to_tsvector @@ plainto_tsquery``，真正缩小候选集并利用 idx_memories_content_gin，
    而不是仅把 BM25 当作评分项。向量可用时不加此过滤（避免误伤语义相关但词面无关的结果）。
    """
    params = [user_id]
    parts = ["m.user_id=$1", "m.is_deleted=FALSE"]

    if scope_session_id:
        parts.append(
            f"(m.scope_target = 'durable' "
            f"OR (m.scope_target = 'general' AND m.scope_session_id = ${2 + param_offset}))"
        )
        params.append(scope_session_id)
    else:
        # 默认仅返回 durable，不暴露其他会话的 general 记忆
        parts.append("m.scope_target = 'durable'")

    # 按 task_type 过滤（metadata 中的 JSONB 字段）
    if task_type:
        idx_p = len(params) + 1 + param_offset
        parts.append(f"m.metadata->>'task_type' = ${{{idx_p}}}")
        params.append(task_type)

    # P2：纯文本回退路径的 GIN 全文硬过滤
    if fts_keywords:
        idx_kw = len(params) + 1 + param_offset
        kw_query = " ".join(fts_keywords[:5])
        parts.append(
            f"to_tsvector('simple', m.content) @@ plainto_tsquery('simple', ${idx_kw})"
        )
        params.append(kw_query)

    return "WHERE " + " AND ".join(parts), params


def _build_rerank_subquery_sql(
    where_clause: str, where_params: list, weights: dict,
    q_str: str, cap: int, limit: int,
) -> tuple[str, list]:
    """P3 修复：sql_rerank 开启且有向量时的安全重排 SQL。

    原单阶段实现把加权表达式直接作为全表 ``ORDER BY``，优化器只能顺序扫描
    百万级 ``durable`` 表并全量排序（灾难级退化）。

    改为：先用 HNSW 索引在子查询内 ``ORDER BY embedding <=> $q LIMIT cap`` 取
    出 top-cap 候选（cap = limit*8），再在候选集上做加权排序。加权排序仅作用于
    候选集，规模可控，且向量距离仍由索引加速。
    """
    q_param = len(where_params) + 1
    params = list(where_params) + [q_str]
    w_vec = float(weights.get("vector", DEFAULT_VECTOR_WEIGHT))
    w_bm25 = float(weights.get("bm25", 0.15))
    w_time = float(weights.get("time", 0.15))
    w_rel = float(weights.get("reliability", 0.15))
    w_heat = float(weights.get("heat", 0.10))
    temporal = (
        "CASE WHEN m.created_at > NOW() - INTERVAL '7 days' THEN 0.15 "
        "WHEN m.created_at > NOW() - INTERVAL '30 days' THEN 0.08 ELSE 0 END"
    )
    weighted = (
        f"({w_vec} * (1.0 - (m.embedding <=> ${q_param}::vector)) "
        f"+ {w_bm25} * (CASE WHEN to_tsvector('simple', m.content) "
        f"@@ plainto_tsquery('simple', ${q_param}) THEN 0.15 ELSE 0 END) "
        f"+ {w_time} * ({temporal}) "
        f"+ {w_rel} * m.reliability "
        f"+ {w_heat} * GREATEST(0.0, m.heat_score))"
    )
    sql = (
        "SELECT m.id, m.content, m.category, m.tier, "
        "m.heat_score, m.reliability, m.access_count, m.created_at, "
        "m.session_id, m.scope_target, "
        f"(m.embedding <=> ${q_param}::vector) AS distance "
        f"FROM (SELECT * FROM memories m {where_clause} "
        f"ORDER BY m.embedding <=> ${q_param}::vector LIMIT {cap}) m "
        f"ORDER BY {weighted} DESC LIMIT {limit}"
    )
    return sql, params


def _build_order_limit(
    keywords: list[str],
    q_str: str,
    limit: int,
    param_offset: int,
    weights: dict | None = None,
    two_phase: bool = True,
) -> tuple[str, list]:
    """构建 ORDER BY 和 LIMIT 子句，返回 (sql_fragment, params)。

    两阶段模式 (two_phase=True)：第一阶段用纯向量距离走 HNSW 索引取 limit*3 候选，
    第二阶段在 Python 层用加权公式重排。
    单阶段模式（原逻辑）：直接用加权公式排序（无法利用 HNSW 索引）。

    weights: 各维度权重，默认从 config.SEARCH_WEIGHTS 读取。
    """
    if weights is None:
        from config import SEARCH_WEIGHTS as default_weights
        weights = default_weights.copy()

    if two_phase and q_str:
        params = [q_str]
        param_idx = param_offset + 1
        cap = min(limit * 3, MAX_CANDIDATES)  # P3 修复：候选集硬上限，防止内存爆炸
        params.append(cap)
        param_idx += 1
        order = f"ORDER BY m.embedding <=> ${param_offset + 1}::vector LIMIT ${param_idx}"
        return order, params

    # 单阶段模式
    w_vec = float(weights.get("vector", DEFAULT_VECTOR_WEIGHT))
    w_bm25 = float(weights.get("bm25", 0.15))
    w_time = float(weights.get("time", 0.15))
    w_rel = float(weights.get("reliability", 0.15))
    w_heat = float(weights.get("heat", 0.10))

    params = []
    param_idx = param_offset

    temporal_sql = (
        "CASE WHEN m.created_at > NOW() - INTERVAL '7 days' THEN 0.15 "
        "WHEN m.created_at > NOW() - INTERVAL '30 days' THEN 0.08 ELSE 0 END"
    )

    bm25_parts = []
    for kw in keywords:
        param_idx += 1
        params.append(kw)
        bm25_parts.append(f"CASE WHEN to_tsvector('simple', m.content) @@ plainto_tsquery('simple', ${param_idx}) THEN 0.15 ELSE 0 END")
    bm25_sql = " + ".join(bm25_parts) if bm25_parts else "0"

    has_vector = bool(q_str)
    if has_vector:
        param_idx += 1
        params.append(q_str)
        order = (
            f"ORDER BY ({w_vec} * (1.0 - (m.embedding <=> ${param_idx}::vector)) "
            f"  + {w_bm25} * ({bm25_sql}) "
            f"  + {w_time} * ({temporal_sql}) "
            f"  + {w_rel} * m.reliability "
            f"  + {w_heat} * GREATEST(0.0, m.heat_score)) DESC"
        )
    else:
        # 无向量分支：各加权项用外层括号包裹，避免前导一元 + 运算符导致
        # PostgreSQL 语法错误（原实现生成 "ORDER BY (  + 0.30 * (...)"）。
        score_expr = (
            f"({w_bm25} * ({bm25_sql}) "
            f"+ {w_time} * ({temporal_sql}) "
            f"+ {w_rel} * m.reliability "
            f"+ {w_heat} * GREATEST(0.0, m.heat_score))"
        )
        order = f"ORDER BY {score_expr} DESC"

    params.append(limit)
    param_idx += 1
    return f"{order} LIMIT ${param_idx}", params


@router.post("/api/v1/dialectic")
async def dialectic_search(req: DialecticRequest, user_id: str = Depends(get_current_user),
                          pool: asyncpg.Pool = Depends(get_pool)) -> dict:
    """语义检索（支持作用域过滤 + 可选 Recall Funnel 追踪）"""
    trace = SearchTrace(query=req.query, scope_session_id=req.scope_session_id or "")
    t0 = time.time()
    
    skip, reason = _should_skip(req.query)
    if skip:
        trace.skipped = True
        trace.skip_reason = reason
        trace.stage_timings_ms = {"gate": int((time.time() - t0) * 1000)}
        result = {"query": req.query, "memories": [], "context": [],
                  "total_memories": 0, "skipped": True, "reason": reason}
        return {**result, "trace": asdict(trace)} if req.trace else result

    # 嵌入
    t1 = time.time()
    q_str = ""
    if shared.get_cached_embedding_fn():
        try:
            r_q = (await shared.get_cached_embedding_fn()([req.query]))[0]
            if r_q and len(r_q) > 0:
                q_str = vec_to_str(r_q)
                trace.has_vector = True
        except Exception:
            import logging
            logging.getLogger("amber").warning(
                "search: embedding 生成失败，降级为纯文本搜索"
            )
    trace.stage_timings_ms["embed"] = int((time.time() - t1) * 1000)
    
    keywords = _extract_keywords(req.query)
    where_clause, where_params = _build_where_clause(
        user_id, req.scope_session_id, req.task_type,
        fts_keywords=keywords if not q_str else None,
    )

    from config import SEARCH_WEIGHTS
    weights = SEARCH_WEIGHTS.copy()
    w_vec = float(weights.get("vector", DEFAULT_VECTOR_WEIGHT))
    w_bm25 = float(weights.get("bm25", 0.15))
    w_time = float(weights.get("time", 0.15))
    w_rel = float(weights.get("reliability", 0.15))
    w_heat = float(weights.get("heat", 0.10))

    # 缺陷 3.1 修复：SQL 重排可选项。
    # P3 修复：默认开启 sql_rerank=1，加权排序直接在数据库内完成（子查询预过滤），
    # 避免候选集全量载入应用层 Python 重排，降低 CPU/内存拷贝。设 MNEMOSYNE_SEARCH_SQL_RERANK=0 可回退两阶段。
    sql_rerank = os.getenv("MNEMOSYNE_SEARCH_SQL_RERANK", "1") == "1"
    ef_search = os.getenv("MNEMOSYNE_HNSW_EF_SEARCH")
    # P4 修复：dialectic 终裁条数对齐 max_memories（原两阶段路径误返回 2× 请求值，
    # 导致下游上下文超出 token 预算）。
    limit = req.max_memories
    if sql_rerank and q_str:
        cap = limit * 8  # 候选集上限：向量索引取 top-cap，再加权排序取 top-limit
        full_sql, all_params = _build_rerank_subquery_sql(
            where_clause, where_params, weights, q_str, cap, limit
        )
    else:
        order_sql, order_params = _build_order_limit(
            keywords, q_str, limit, len(where_params),
            two_phase=not sql_rerank,
        )
        # 添加实际向量距离列供重排使用
        vec_param_idx = len(where_params) + 1  # q_str 在 ORDER BY 中的参数位置
        full_sql = (
            "SELECT m.id, m.content, m.category, m.tier, "
            "m.heat_score, m.reliability, m.created_at, "
            "m.session_id, m.scope_target, "
            f"(m.embedding <=> ${vec_param_idx}::vector) AS distance "
            f"FROM memories m {where_clause} {order_sql}"
        )
        all_params = where_params + order_params
    trace.total_candidates = 0

    async with pool.acquire() as conn:
        # 缺陷 3.1 修复：暴露 HNSW ef_search（SET LOCAL 仅作用于本事务）
        async with conn.transaction():
            if ef_search:
                try:
                    ef_val = int(ef_search)
                    if not (1 <= ef_val <= 1000):
                        raise ValueError(f"ef_search 超出合法范围: {ef_val}")
                    await conn.execute(f"SET LOCAL hnsw.ef_search = {ef_val}")
                except Exception:
                    import logging
                    logging.getLogger("amber").warning("设置 hnsw.ef_search 失败（忽略）")
            t3 = time.time()
            rows = await conn.fetch(full_sql, *all_params)
            trace.stage_timings_ms["query"] = int((time.time() - t3) * 1000)

    # 第二阶段：Python 层加权重排（仅两阶段模式启用）
    if rows and q_str and not sql_rerank:
        def _rerank_dialectic(row: asyncpg.Record) -> float:
            content = row["content"] or ""
            kw_matches = sum(1 for kw in keywords if kw.lower() in content.lower()) if keywords else 0
            vec_sim = 1.0 - float(row["distance"]) if row.get("distance") is not None else 0.0
            score = (
                w_vec * vec_sim
                + w_bm25 * min(kw_matches * 0.15, 0.45)
                + w_time * (0.15 if row["created_at"] and (datetime.now(timezone.utc) - row["created_at"]).days < 7 else 0.08 if row["created_at"] and (datetime.now(timezone.utc) - row["created_at"]).days < 30 else 0)
                + w_rel * (row["reliability"] or 0.5)
                + w_heat * max(0.0, row["heat_score"] or 0.0)
            )
            return score
        rows.sort(key=_rerank_dialectic, reverse=True)
        rows = rows[:limit]
    
    # 统计关键词匹配数
    trace.keyword_match = sum(
        1 for r in rows
        if any(kw.lower() in (r["content"] or "").lower() for kw in keywords)
    ) if keywords else trace.total_candidates
    trace.vector_match = trace.total_candidates if trace.has_vector else 0
    
    if not rows:
        result = {"query": req.query, "memories": [], "context": [],
                  "total_memories": 0}
        trace.final_returned = 0
        trace.stage_timings_ms["total"] = int((time.time() - t0) * 1000)
        return ok({**result, "trace": asdict(trace)}) if req.trace else ok(result)
    
    memories = []
    session_ids = set()
    for r in rows:
        memories.append({
            "id": r["id"], "content": r["content"][:300],
            "category": r["category"], "tier": r["tier"],
            "heat": r["heat_score"], "reliability": r["reliability"],
            "created": str(r["created_at"])[:19],
            "scope": r["scope_target"] or "general",
        })
        if r["session_id"]:
            session_ids.add(str(r["session_id"]))
    
    context = []
    if session_ids and req.include_context:
        session_list = list(session_ids)
        phs = ",".join(f"${2 + i}" for i in range(len(session_list)))
        async with pool.acquire() as conn2:
            s_rows = await conn2.fetch(
                "SELECT s.id::text, s.session_label, s.summary, s.heat_score, "
                "s.fragment_ids, s.start_time, s.created_at "
                "FROM public.tmt_sessions s WHERE s.user_id=$1 "
                "AND s.id::text = ANY(ARRAY[" + phs + "])",
                user_id, *session_list
            )
        for s in s_rows:
            context.append({
                "session_id": s["id"], "label": s["session_label"],
                "summary": (s["summary"] or "")[:200],
                "heat": s["heat_score"], "fragments": s["fragment_ids"] or [],
                "start": str(s["start_time"])[:19] if s["start_time"] else "",
            })
    
    trace.final_returned = len(memories)
    trace.returned_chars = sum(len(m["content"]) for m in memories)
    trace.stage_timings_ms["total"] = int((time.time() - t0) * 1000)
    
    result = {
        "query": req.query, "memories": memories,
        "context": context, "total_memories": len(memories),
    }
    return ok({**result, "trace": asdict(trace)}) if req.trace else ok(result)


@router.post("/api/v1/memories/search")
async def search_memories(req: MemorySearch, user_id: str = Depends(get_current_user),
                          pool: asyncpg.Pool = Depends(get_pool)) -> dict:
    """全文搜索（支持作用域过滤 + 可选 Recall Funnel 追踪）"""
    trace = SearchTrace(query=req.query, scope_session_id=req.scope_session_id or "")
    t0 = time.time()
    
    skip, reason = _should_skip(req.query)
    if skip:
        trace.skipped = True
        trace.skip_reason = reason
        trace.stage_timings_ms = {"gate": int((time.time() - t0) * 1000)}
        result = {"memories": [], "skipped": True, "reason": reason}
        return {**result, "trace": asdict(trace)} if req.trace else result
    
    # 嵌入
    q_str = ""
    if shared.get_cached_embedding_fn():
        try:
            r_q = (await shared.get_cached_embedding_fn()([req.query]))[0]
            if r_q and len(r_q) > 0:
                q_str = vec_to_str(r_q)
                trace.has_vector = True
        except Exception:
            import logging
            logging.getLogger("amber").warning(
                "search: embedding 生成失败，降级为纯文本搜索"
            )
    
    keywords = _extract_keywords(req.query)
    where_clause, where_params = _build_where_clause(
        user_id, req.scope_session_id, req.task_type,
        fts_keywords=keywords if not q_str else None,
    )

    from config import SEARCH_WEIGHTS
    weights = SEARCH_WEIGHTS.copy()
    w_vec = float(weights.get("vector", DEFAULT_VECTOR_WEIGHT))
    w_bm25 = float(weights.get("bm25", 0.15))
    w_time = float(weights.get("time", 0.15))
    w_rel = float(weights.get("reliability", 0.15))
    w_heat = float(weights.get("heat", 0.10))

    # 缺陷 3.1 修复：SQL 重排可选项 + HNSW ef_search 暴露
    # P3 修复：默认开启 sql_rerank=1（见 dialectic_search 同款注释），加权排序在库内完成。
    sql_rerank = os.getenv("MNEMOSYNE_SEARCH_SQL_RERANK", "1") == "1"
    ef_search = os.getenv("MNEMOSYNE_HNSW_EF_SEARCH")
    async with pool.acquire() as conn:
        if sql_rerank and q_str:
            cap = req.top_k * 8
            full_sql, all_params = _build_rerank_subquery_sql(
                where_clause, where_params, weights, q_str, cap, req.top_k
            )
        else:
            order_sql, order_params = _build_order_limit(
                keywords, q_str, req.top_k, len(where_params),
                two_phase=not sql_rerank,
            )
            # 添加实际向量距离列供重排使用
            vec_param_idx = len(where_params) + 1
            full_sql = (
                "SELECT m.id, m.content, m.category, m.tier, "
                "m.heat_score, m.reliability, m.access_count, "
                "m.created_at, m.scope_target, "
                f"(m.embedding <=> ${vec_param_idx}::vector) AS distance "
                f"FROM memories m {where_clause} {order_sql}"
            )
            all_params = where_params + order_params
        # 缺陷 3.1 修复：暴露 HNSW ef_search（SET LOCAL 仅作用于本事务）
        async with conn.transaction():
            if ef_search:
                try:
                    ef_val = int(ef_search)
                    if not (1 <= ef_val <= 1000):
                        raise ValueError(f"ef_search 超出合法范围: {ef_val}")
                    await conn.execute(f"SET LOCAL hnsw.ef_search = {ef_val}")
                except Exception:
                    import logging
                    logging.getLogger("amber").warning("设置 hnsw.ef_search 失败（忽略）")
            rows = await conn.fetch(full_sql, *all_params)

    # 第二阶段：Python 层加权重排（仅两阶段模式启用）
    if rows and q_str and not sql_rerank:
        def _rerank(row: asyncpg.Record) -> float:
            content = row["content"] or ""
            kw_matches = sum(1 for kw in keywords if kw.lower() in content.lower()) if keywords else 0
            vec_sim = 1.0 - float(row["distance"]) if row.get("distance") is not None else 0.0
            score = (
                w_vec * vec_sim  # 使用实际向量距离
                + w_bm25 * min(kw_matches * 0.15, 0.45)
                + w_time * (0.15 if row["created_at"] and (datetime.now(timezone.utc) - row["created_at"]).days < 7 else 0.08 if row["created_at"] and (datetime.now(timezone.utc) - row["created_at"]).days < 30 else 0)
                + w_rel * (row["reliability"] or 0.5)
                + w_heat * max(0.0, row["heat_score"] or 0.0)
            )
            return score
        rows.sort(key=_rerank, reverse=True)
        rows = rows[:req.top_k]

    trace.total_candidates = len(rows)
    
    trace.keyword_match = sum(
        1 for r in rows
        if any(kw.lower() in (r["content"] or "").lower() for kw in keywords)
    ) if keywords else trace.total_candidates
    trace.vector_match = trace.total_candidates if trace.has_vector else 0
    trace.final_returned = len(rows)
    trace.returned_chars = sum(len(r["content"] or "") for r in rows)
    trace.stage_timings_ms["total"] = int((time.time() - t0) * 1000)
    
    memories = [
        {"id": r["id"], "content": r["content"][:300], "category": r["category"],
         "tier": r["tier"], "heat": r["heat_score"],
         "created": str(r["created_at"])[:19],
         "scope": r["scope_target"] or "general"}
        for r in rows
    ]
    data = {"memories": memories}
    return ok({**data, "trace": asdict(trace)}) if req.trace else ok(data)


@router.post("/api/v1/explain")
async def explain_search(req: ExplainRequest, user_id: str = Depends(get_current_user),
                         pool: asyncpg.Pool = Depends(get_pool)) -> dict:
    """召回说明：返回 trace + 每条结果的评分明细，帮助调试召回质量。"""
    trace = SearchTrace(query=req.query, scope_session_id=req.scope_session_id or "")
    t0 = time.time()

    q_str = ""
    if shared.get_cached_embedding_fn():
        try:
            r_q = (await shared.get_cached_embedding_fn()([req.query]))[0]
            if r_q and len(r_q) > 0:
                q_str = vec_to_str(r_q)
                trace.has_vector = True
        except Exception:
            import logging
            logging.getLogger("amber").warning(
                "search: embedding 生成失败，降级为纯文本搜索"
            )

    keywords = _extract_keywords(req.query)
    where_clause, where_params = _build_where_clause(
        user_id, req.scope_session_id, req.task_type
    )

    limit = 10
    order_sql, order_params = _build_order_limit(
        keywords, q_str, limit, len(where_params)
    )

    async with pool.acquire() as conn:
        full_sql = (
            "SELECT m.id, m.content, m.category, m.tier, "
            "m.heat_score, m.reliability, m.created_at, "
            "m.scope_target "
            f"FROM memories m {where_clause} {order_sql}"
        )
        all_params = where_params + order_params
        rows = await conn.fetch(full_sql, *all_params)

    trace.total_candidates = len(rows)
    trace.stage_timings_ms["total"] = int((time.time() - t0) * 1000)
    return ok({"memories": [dict(r) for r in rows], "trace": asdict(trace)})

