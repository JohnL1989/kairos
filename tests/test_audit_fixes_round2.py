"""
Aion Memory — 审计报告（A/S/P/R 编号）12 项修复的回归测试（纯单元，无需运行中的服务/数据库）

覆盖：
- S5  请求体大小中间件：非数字 content-length → 400（原会 500）
- S6  CORS 方法白名单补齐 DELETE（与后端 DELETE 端点对齐）
- S7  出站端点 SSRF 校验（链路本地/非法协议 CRITICAL，内网 WARNING）
- A3  Provider 写入贯通结构化字段（memory_type/task_type/severity/…）
- R2  稳健解析 asyncpg 受影响行数（替换脆弱 str().split()[-1]）
- R3  LLM JSON 提取重写（修 or True 恒真死分支 + 规范化序列化）
- R4  断路器按 tier(2/3/4) 分实例隔离（PRO 抖动不误杀 MINI/LITE）
- P3  sql_rerank 向量路径改「子查询向量距离预过滤」避免全表排序
- P4  dialectic 终裁条数对齐 max_memories（原误返回 2×）
- P5  reflect 改按 id 分批更新（限制行锁范围）
- R5  PUT 更新增乐观锁 if_match_updated_at（版本冲突 → 409）
- 既有库迁移 0005（部分 HNSW + failed 索引，幂等）

约定：需要 amber.main 的用例在模块导入期设定 MNEMOSYNE_DEV_INSECURE=1，
使 main 可被安全 import。
"""
import os
import re
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

os.environ.setdefault("MNEMOSYNE_DEV_INSECURE", "1")

import pytest

ROOT = Path(__file__).resolve().parent.parent


# ── 轻量 Mock 连接/连接池（route 用 `async with pool.acquire() as conn`）──
class MockPool:
    def __init__(self):
        self.fetch = AsyncMock(return_value=[])
        self.fetchrow = AsyncMock(return_value=None)
        self.fetchval = AsyncMock(return_value=None)
        self.execute = AsyncMock(return_value="OK")

    def acquire(self, *a, **k):
        cm = AsyncMock()
        cm.__aenter__.return_value = self
        cm.__aexit__.return_value = False
        return cm


# ═══════════════════════════════════════════════════════════════════════════
# S5 — 请求体大小中间件：非数字 content-length → 400（原会因 int() 抛异常 500）
# ═══════════════════════════════════════════════════════════════════════════

class TestRequestSizeLimit:
    def _mw(self):
        from amber.main import RequestSizeLimitMiddleware
        return RequestSizeLimitMiddleware(app=MagicMock())

    @pytest.mark.asyncio
    async def test_non_numeric_content_length_returns_400(self):
        mw = self._mw()
        req = SimpleNamespace(headers={"content-length": "abc"})
        call_next = AsyncMock(return_value=MagicMock())
        resp = await mw.dispatch(req, call_next)
        assert resp.status_code == 400
        call_next.assert_not_called()

    @pytest.mark.asyncio
    async def test_oversized_returns_413(self):
        mw = self._mw()
        req = SimpleNamespace(headers={"content-length": "999999999999"})
        call_next = AsyncMock()
        resp = await mw.dispatch(req, call_next)
        assert resp.status_code == 413
        call_next.assert_not_called()

    @pytest.mark.asyncio
    async def test_valid_passes_through(self):
        mw = self._mw()
        req = SimpleNamespace(headers={"content-length": "100"})
        sentinel = MagicMock()
        call_next = AsyncMock(return_value=sentinel)
        resp = await mw.dispatch(req, call_next)
        call_next.assert_awaited_once()
        assert resp is sentinel

    @pytest.mark.asyncio
    async def test_missing_content_length_passes_through(self):
        mw = self._mw()
        req = SimpleNamespace(headers={})
        sentinel = MagicMock()
        call_next = AsyncMock(return_value=sentinel)
        resp = await mw.dispatch(req, call_next)
        call_next.assert_awaited_once()
        assert resp is sentinel


# ═══════════════════════════════════════════════════════════════════════════
# S6 — CORS 方法白名单补齐 DELETE
# ═══════════════════════════════════════════════════════════════════════════

class TestCorsAllowsDelete:
    def test_cors_allow_methods_includes_delete(self):
        from starlette.middleware.cors import CORSMiddleware
        from amber.main import app
        mw = next(m for m in app.user_middleware if m.cls is CORSMiddleware)
        assert "DELETE" in mw.kwargs["allow_methods"]


# ═══════════════════════════════════════════════════════════════════════════
# S7 — 出站端点 SSRF 校验
# ═══════════════════════════════════════════════════════════════════════════

class TestSsrfValidation:
    def test_empty_url_no_critical(self, caplog):
        import config
        with caplog.at_level(logging.CRITICAL):
            config._validate_outbound_url("EMBEDDING_ENDPOINT", "")
        assert not any(r.levelno >= logging.CRITICAL for r in caplog.records)

    def test_relative_path_skipped(self, caplog):
        import config
        with caplog.at_level(logging.CRITICAL):
            config._validate_outbound_url("EMBEDDING_ENDPOINT", "/embeddings")
        assert not any(r.levelno >= logging.CRITICAL for r in caplog.records)

    def test_link_local_critical(self, caplog):
        import config
        with caplog.at_level(logging.CRITICAL):
            config._validate_outbound_url("EMBEDDING_ENDPOINT", "http://169.254.169.254/latest")
        assert any("链路本地" in r.message for r in caplog.records)

    def test_file_scheme_critical(self, caplog):
        import config
        with caplog.at_level(logging.CRITICAL):
            config._validate_outbound_url("X", "file:///etc/passwd")
        assert any("协议非法" in r.message for r in caplog.records)

    def test_private_ip_warning(self, caplog):
        import config
        with caplog.at_level(logging.WARNING):
            config._validate_outbound_url("X", "http://10.0.0.5:8080")
        assert any("内网" in r.message for r in caplog.records)

    def test_public_ok(self, caplog):
        import config
        with caplog.at_level(logging.WARNING):
            config._validate_outbound_url("X", "https://api.openai.com/v1")
        assert len(caplog.records) == 0


# ═══════════════════════════════════════════════════════════════════════════
# A3 — Provider 写入贯通结构化字段
# ═══════════════════════════════════════════════════════════════════════════

class TestProviderStructuredFields:
    def _provider(self, monkeypatch):
        import adapters.hermes_provider as hp
        p = hp.AionMemoryProvider()
        calls = []

        def fake_api_call(url, payload, timeout=10):
            calls.append((url, json.loads(payload)))
            return True

        monkeypatch.setattr(p, "_api_call", fake_api_call)
        # 不再强制 no-op _write_trace：修复后它已实现并会在成功时双写，
        # 此处让其真实运行以验证「保存成功不再崩溃」这一修复点。
        return p, calls

    def test_on_memory_write_passes_structured_fields(self, monkeypatch):
        p, calls = self._provider(monkeypatch)
        p.on_memory_write(
            "add", "user", "do not delete tmp",
            metadata={"memory_type": "rule", "task_type": "AUDIT_FIX",
                      "severity": "high", "decay_months": 6, "linked_skills": ["pytest"]},
        )
        # 找到 memories 写入调用（成功路径还应触发一次 memory_traces 双写）
        mem_calls = [c for c in calls if c[0].endswith("/api/v1/memories")]
        trace_calls = [c for c in calls if c[0].endswith("/api/v1/memory-traces")]
        assert mem_calls, "应至少发起一次 /api/v1/memories 写入"
        assert trace_calls, "保存成功后应双写 memory_traces（_write_trace 已实现且不崩溃）"
        pl = mem_calls[0][1]
        assert pl["memory_type"] == "rule"
        assert pl["task_type"] == "AUDIT_FIX"
        assert pl["severity"] == "high"
        assert pl["decay_months"] == 6
        assert pl["linked_skills"] == ["pytest"]
        assert pl["scope_target"] == "durable"  # target='user' → durable

    def test_endpoint_is_memories_not_memory_save(self, monkeypatch):
        p, calls = self._provider(monkeypatch)
        p._api_save_memory(content="x", category="fact", scope_target="general")
        mem_calls = [c for c in calls if c[0].endswith("/api/v1/memories")]
        assert mem_calls, "应发起 /api/v1/memories 写入"
        assert mem_calls[0][0].endswith("/api/v1/memories")


# ═══════════════════════════════════════════════════════════════════════════
# R2 — 稳健解析 asyncpg 受影响行数
# ═══════════════════════════════════════════════════════════════════════════

class TestAffectedRows:
    @pytest.mark.parametrize("status,expected", [
        ("UPDATE 5", 5),
        ("DELETE 3", 3),
        ("INSERT 0 1", 1),
        (None, 0),
        ("garbage", 0),
        ("", 0),
    ])
    def test_parses(self, status, expected):
        from services.memory_service import _affected_rows
        assert _affected_rows(status) == expected


# ═══════════════════════════════════════════════════════════════════════════
# R3 — LLM JSON 提取重写（修 or True 恒真死分支 + 规范化序列化）
# ═══════════════════════════════════════════════════════════════════════════

class TestLlmJsonExtraction:
    @pytest.mark.asyncio
    async def test_valid_json_normalized(self, monkeypatch):
        import core.llm as llm_mod
        async def fake_api(*a, **k):
            return {"content": '{"summary":"ok"}', "tokens": 5, "cost": 0.0}
        monkeypatch.setattr(llm_mod, "_call_api_async", fake_api)
        monkeypatch.setattr(llm_mod, "TMT_MAX_RETRIES", 2)
        res = await llm_mod.call_llm("p", tier=3, json_mode=True, no_cache=True)
        assert json.loads(res["content"]) == {"summary": "ok"}

    @pytest.mark.asyncio
    async def test_non_json_falls_back_to_empty_object(self, monkeypatch):
        import core.llm as llm_mod
        async def fake_api(*a, **k):
            return {"content": "no json here", "tokens": 0, "cost": 0.0}
        monkeypatch.setattr(llm_mod, "_call_api_async", fake_api)
        monkeypatch.setattr(llm_mod, "TMT_MAX_RETRIES", 2)
        res = await llm_mod.call_llm("p", tier=3, json_mode=True, no_cache=True)
        # 非 JSON 文本不再被静默当作内容进入蒸馏，而是降级为空对象
        assert res["content"] == "{}"


# ═══════════════════════════════════════════════════════════════════════════
# R4 — 断路器按 tier(2/3/4) 分实例隔离
# ═══════════════════════════════════════════════════════════════════════════

class TestCircuitBreakerByTier:
    def test_distinct_per_tier_and_fallback(self):
        import core.llm as llm_mod
        assert llm_mod._breaker_for(2) is llm_mod.cb_by_tier[2]
        assert llm_mod._breaker_for(3) is llm_mod.cb_by_tier[3]
        assert llm_mod._breaker_for(4) is llm_mod.cb_by_tier[4]
        assert llm_mod._breaker_for(99) is llm_mod.cb  # 未知 tier 回退全局
        assert llm_mod.cb_by_tier[2] is not llm_mod.cb_by_tier[3]
        assert llm_mod.cb_by_tier[3] is not llm_mod.cb_by_tier[4]

    @pytest.mark.asyncio
    async def test_tier_failure_isolation(self):
        import core.llm as llm_mod
        await llm_mod.cb_by_tier[2].record_failure()
        await llm_mod.cb_by_tier[2].record_failure()
        await llm_mod.cb_by_tier[2].record_failure()
        assert llm_mod.cb_by_tier[2].state == "OPEN"   # MINI 跳闸
        assert llm_mod.cb_by_tier[4].state == "CLOSED"  # PRO 不受 MINI 故障影响


# ═══════════════════════════════════════════════════════════════════════════
# P3 — sql_rerank 向量路径改「子查询向量距离预过滤」
# ═══════════════════════════════════════════════════════════════════════════

class TestRerankSubquery:
    def test_subquery_pre_filter(self):
        from api.search import _build_rerank_subquery_sql
        where_clause = "WHERE m.user_id=$1 AND m.is_deleted=FALSE"
        where_params = ["default"]
        weights = {"vector": 0.45, "bm25": 0.15, "time": 0.15,
                   "reliability": 0.15, "heat": 0.10}
        q_str = "[0.1,0.2]"
        sql, params = _build_rerank_subquery_sql(
            where_clause, where_params, weights, q_str, cap=40, limit=5
        )
        # 子查询用向量距离取 top-cap（预过滤，避免全表加权排序）
        assert "ORDER BY m.embedding <=> $2::vector LIMIT 40" in sql
        # 加权排序仅作用于候选集，且向量参数位置正确
        assert "ORDER BY (0.45 * (1.0 - (m.embedding <=> $2::vector))" in sql
        assert "LIMIT 5" in sql
        assert params == ["default", q_str]


# ═══════════════════════════════════════════════════════════════════════════
# P4 — dialectic 终裁条数对齐 max_memories（原误返回 2×）
# ═══════════════════════════════════════════════════════════════════════════

class TestDialecticLimitAligned:
    @pytest.mark.asyncio
    async def test_limit_is_max_memories_and_final_slice(self, monkeypatch):
        from api.search import dialectic_search, DialecticRequest
        # 捕获 _build_order_limit 的 limit 参数（P4 修复点：应为 max_memories，而非 2×）
        captured = {}

        def fake_build(keywords, q_str, limit, param_offset, weights=None, two_phase=True):
            captured["limit"] = limit
            return "ORDER BY m.embedding <=> $1::vector LIMIT $2", ["x"]

        monkeypatch.setattr("api.search._build_order_limit", fake_build)

        # mock 嵌入函数（异步），使 q_str 非空（走向量路径）
        async def fake_emb(texts):
            return [[0.0] * 8 for _ in texts]

        monkeypatch.setattr("api.search.shared.get_cached_embedding_fn", lambda: fake_emb)
        # vec_to_str 在测试环境下对纯 list 输入可能抛错，直接 patch 为确定性向量串
        monkeypatch.setattr("api.search.vec_to_str", lambda v: "[0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0]")

        rows = [
            {"id": i, "content": "c", "category": "fact", "tier": "L1",
             "heat_score": 0.5, "reliability": 0.9,
             "created_at": datetime(2026, 1, 1, tzinfo=timezone.utc),
             "session_id": "", "scope_target": "durable", "distance": 0.1}
            for i in range(7)
        ]

        class MockConn:
            async def fetch(self, sql, *a):
                return rows

            def transaction(self):
                class Ctx:
                    async def __aenter__(self):
                        return self

                    async def __aexit__(self, *a):
                        return False
                return Ctx()

        class MockPool2:
            def acquire(self, *a, **k):
                cm = AsyncMock()
                cm.__aenter__.return_value = MockConn()
                cm.__aexit__.return_value = False
                return cm

        req = DialecticRequest(query="test query", max_memories=5, trace=False)
        res = await dialectic_search(req, user_id="default", pool=MockPool2())
        body = json.loads(res.body.decode())
        # P4：传递给 ORDER BY 的 limit 等于 max_memories，不是 2×
        assert captured["limit"] == 5
        # 终裁切片也对齐 max_memories
        assert len(body["data"]["memories"]) == 5


# ═══════════════════════════════════════════════════════════════════════════
# P5 — reflect 改按 id 分批更新（限制行锁范围）
# ═══════════════════════════════════════════════════════════════════════════

class TestBatchUpdate:
    @pytest.mark.asyncio
    async def test_batches_with_id_filter(self):
        from services.memory_service import _batch_update
        fetch_pages = [[{"id": 1}, {"id": 2}], [{"id": 3}], []]
        exec_sqls = []

        class C:
            async def fetch(self, q, *a):
                return fetch_pages.pop(0)

            async def execute(self, q, *a, **k):
                exec_sqls.append(q)
                return "UPDATE 2" if len(exec_sqls) == 1 else "UPDATE 1"

        total = await _batch_update(C(), "heat_score=0.1", "", "default", batch=2)
        assert total == 3
        # 每批都用 id=ANY 限定行锁范围，不扫全表
        for sql in exec_sqls:
            assert "WHERE user_id=$1 AND id=ANY($2::int[])" in sql

    @pytest.mark.asyncio
    async def test_reflect_light_completes(self):
        from services.memory_service import reflect

        class C:
            async def fetch(self, q, *a):
                return []

            async def execute(self, q, *a, **k):
                return "UPDATE 0"

        res = await reflect(C(), "default", "light")
        assert res["status"].startswith("Reflection")


# ═══════════════════════════════════════════════════════════════════════════
# R5 — PUT 更新增乐观锁 if_match_updated_at（版本冲突 → 409）
# ═══════════════════════════════════════════════════════════════════════════

class TestUpdateMemoryOptimisticLock:
    @pytest.mark.asyncio
    async def test_noop_when_no_fields(self):
        from api.memories import update_memory, MemoryUpdate
        res = await update_memory(1, MemoryUpdate(), "default", MockPool())
        body = json.loads(res.body.decode())
        assert body["data"]["status"] == "noop"

    @pytest.mark.asyncio
    async def test_404_when_not_found(self):
        from api.memories import update_memory, MemoryUpdate
        pool = MockPool()
        pool.fetchrow = AsyncMock(return_value=None)
        res = await update_memory(1, MemoryUpdate(content="x"), "default", pool)
        body = json.loads(res.body.decode())
        assert body.get("code") == 404

    @pytest.mark.asyncio
    async def test_409_on_version_conflict(self):
        from api.memories import update_memory, MemoryUpdate
        pool = MockPool()
        pool.fetchrow = AsyncMock(return_value=None)
        res = await update_memory(
            1, MemoryUpdate(content="x", if_match_updated_at="2026-01-01T00:00:00"),
            "default", pool,
        )
        body = json.loads(res.body.decode())
        assert body.get("code") == 409

    @pytest.mark.asyncio
    async def test_200_when_version_matches(self):
        from api.memories import update_memory, MemoryUpdate
        pool = MockPool()
        pool.fetchrow = AsyncMock(return_value={"id": 1})
        res = await update_memory(
            1, MemoryUpdate(content="x", if_match_updated_at="2026-01-01T00:00:00"),
            "default", pool,
        )
        body = json.loads(res.body.decode())
        assert body["data"]["status"] == "updated"


# ═══════════════════════════════════════════════════════════════════════════
# 迁移 0005 — 部分 HNSW + failed 索引（幂等）
# ═══════════════════════════════════════════════════════════════════════════

class TestMigration0005:
    def test_partial_hnsw_and_failed_index(self):
        m = (ROOT / "amber" / "migrations" / "0005_index_optimizations.sql").read_text(encoding="utf-8")
        assert "WHERE is_deleted=FALSE" in m          # 部分索引：已删除记忆退出 HNSW 图
        assert "idx_memories_embedding" in m
        assert "idx_memories_embed_fail" in m
        assert "embedding_status" in m                # failed backfill 扫描索引
        assert "idx_memories_user_deleted_id" in m    # 分批更新按 (user_id, is_deleted, id) 有序抓 id
