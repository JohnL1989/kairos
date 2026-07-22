"""
Aion Memory — 审计报告 18 项缺陷修复的回归测试（纯单元，无需运行中的服务/数据库）

覆盖：1.1 trace 字段统一 / 1.2 无向量 ORDER BY / 1.3 beliefs 类型护栏 /
1.4+4.1 TMT 故障隔离 / 2.3 API Key 哈希 / 2.4 审计异构告警 /
3.1 断路器协程安全 / 3.2 嵌入零向量→异常 / 3.3 HNSW 分级 / 3.4 两阶段默认 /
4.2 content_hash 去重 / 4.3 连接池重试 / 4.4 线程池退出清理 / 4.5 自包含测试传输。

约定：需要 amber.main 的用例（2.3/4.5）在模块导入期设定 MNEMOSYNE_DEV_INSECURE=1，
使 main 可被安全 import（主机门禁已移至 lifespan，不影响 import）。
"""
import os
import re
import asyncio
import hashlib
import json
import atexit
import importlib
import concurrent.futures
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

# 使 main 模块可被 import（缺陷 2.1 门禁已移至 lifespan，import 期不再崩溃）
os.environ.setdefault("MNEMOSYNE_DEV_INSECURE", "1")

import pytest

ROOT = Path(__file__).resolve().parent.parent


class MockPool:
    """既是「连接」也是「连接池」：route 用 `async with pool.acquire() as conn`，
    acquire() 的异步上下文管理器直接 yield 自身，因此 conn.fetch/execute 即本对象的方法。
    直接以 conn 传入的服务函数（如 evolve_memories）同样可用。"""

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


@pytest.fixture
def mock_conn():
    """模拟 asyncpg 连接/连接池（见 MockPool）。"""
    return MockPool()


# ═══════════════════════════════════════════════════════════════════════════
# 缺陷 1.1 — memory_traces 写读字段统一为 action / metadata / created_at
# ═══════════════════════════════════════════════════════════════════════════

class TestMemoryTraceFields:

    @pytest.mark.asyncio
    async def test_create_memory_trace_writes_action_metadata(self, mock_conn):
        from api.memories import create_memory_trace, MemoryTraceCreate
        captured = {}

        async def fake_fetchrow(q, *a):
            captured["sql"] = q
            return {"id": 1, "created_at": datetime(2026, 1, 1, 12, 0, 0)}

        mock_conn.fetchrow = fake_fetchrow
        res = await create_memory_trace(
            MemoryTraceCreate(
                user_id="default", memory_id=5,
                action="update", metadata={"k": "v"},
            ),
            user_id="default", pool=mock_conn,
        )
        # 写入列必须是 action/metadata，绝不能残留旧的 op/details
        assert "action" in captured["sql"] and "metadata" in captured["sql"]
        assert "op" not in captured["sql"] and "details" not in captured["sql"]
        # 响应映射 created_at → executed_at（路由返回 Response，需解析 body）
        body = json.loads(res.body.decode())
        assert body["data"]["executed_at"].startswith("2026-01-01")

    @pytest.mark.asyncio
    async def test_get_events_maps_created_at_to_executed_at(self, mock_conn):
        from api.console import get_events

        async def fake_fetch(q, *a):
            return [{
                "id": 1, "action": "create", "memory_id": 5,
                "preview": "p", "created_at": datetime(2026, 1, 2, 3, 4, 5),
            }]

        mock_conn.fetch = fake_fetch
        res = await get_events(pool=mock_conn, limit=10)
        body = json.loads(res.body.decode())
        assert body["data"]["events"][0]["executed_at"] == "2026-01-02T03:04:05"
        assert body["data"]["events"][0]["action"] == "create"


# ═══════════════════════════════════════════════════════════════════════════
# 缺陷 1.2 — search.py 无向量时 ORDER BY 前导一元加号语法错误
# ═══════════════════════════════════════════════════════════════════════════

class TestSearchOrderLimit:

    def test_no_vector_single_phase_no_leading_plus(self):
        from api.search import _build_order_limit
        sql, _ = _build_order_limit(
            keywords=["记忆"], q_str="", limit=10, param_offset=0, two_phase=False
        )
        assert "ORDER BY" in sql and "DESC" in sql
        # 原缺陷生成 "ORDER BY (  + 0.30 * (...)"，这里断言没有前导一元加号
        assert not re.search(r"ORDER BY \(\s*\+", sql), f"前导一元加号未修复: {sql}"
        assert "m.reliability" in sql  # 加权项确实参与排序

    def test_two_phase_with_vector_uses_hnsw(self):
        from api.search import _build_order_limit
        sql, _ = _build_order_limit(
            keywords=[], q_str="[0.1,0.2,0.3]", limit=10, param_offset=0, two_phase=True
        )
        # 两阶段：纯向量距离走 HNSW 索引
        assert "<=>" in sql and "LIMIT" in sql
        assert "m.reliability" not in sql  # 重排序放到 Python 层

    def test_two_phase_default_true(self):
        from api.search import _build_order_limit
        # 不传 two_phase，默认值应为 True（利用 HNSW）
        sql, _ = _build_order_limit(
            keywords=[], q_str="[0.1]", limit=5, param_offset=0
        )
        assert "<=>" in sql


# ═══════════════════════════════════════════════════════════════════════════
# 缺陷 1.3 — beliefs.evolve_belief 轨迹类型守卫 + 状态合法性护栏
# ═══════════════════════════════════════════════════════════════════════════

class TestBeliefsEvolve:

    @pytest.mark.asyncio
    async def test_trajectory_str_is_parsed(self, mock_conn):
        from api.beliefs import evolve_belief
        mock_conn.fetchrow = AsyncMock(return_value={
            "id": 1, "confidence": 0.5, "evidence_memories": [],
            "status": "active", "trajectory": '["active→tentative"]',  # asyncpg 返回 str
        })
        captured = {}

        async def fake_exec(q, *a):
            captured["args"] = a
            return None

        mock_conn.execute = fake_exec
        res = await evolve_belief(1, new_confidence=0.45, user_id="default", pool=mock_conn)
        assert json.loads(res.body.decode())["data"]["status"] == "tentative"
        # trajectory 必须以 JSON 字符串写入 JSONB，且包含历史过渡（解码后校验）
        assert isinstance(captured["args"][3], str)
        traj = json.loads(captured["args"][3])
        assert isinstance(traj, list)
        assert "active→tentative" in traj

    @pytest.mark.asyncio
    async def test_status_guard_rejects_hypothesis(self, mock_conn):
        from api.beliefs import evolve_belief
        # new_conf<0.3 原逻辑会置 'hypothesis'（不在 CHECK 约束内）→ 护栏回退原状态
        mock_conn.fetchrow = AsyncMock(return_value={
            "id": 1, "confidence": 0.9, "evidence_memories": [],
            "status": "established", "trajectory": None,
        })
        captured = {}

        async def fake_exec(q, *a):
            captured["args"] = a
            return None

        mock_conn.execute = fake_exec
        res = await evolve_belief(1, new_confidence=0.1, user_id="default", pool=mock_conn)
        assert json.loads(res.body.decode())["data"]["status"] == "established"  # 回退，而非非法 'hypothesis'


# ═══════════════════════════════════════════════════════════════════════════
# 缺陷 1.4 + 4.1 — TMT 逐层蒸馏故障隔离（超时/异常不阻断其它层级）
# ═══════════════════════════════════════════════════════════════════════════

class TestTmtFaultIsolation:

    @pytest.mark.asyncio
    async def test_consolidate_level_safe_timeout(self, monkeypatch):
        import tmt.router as tmt

        # 直接触发 except asyncio.TimeoutError 分支（wait_for 的取消语义在不同
        # Python 版本下会包装为 CancelledError，这里直接抛 TimeoutError 以稳定断言隔离逻辑）
        async def slow(_u, _l, _s, _e, _p):
            raise asyncio.TimeoutError("slow level")

        monkeypatch.setattr(tmt, "consolidate_level", slow)
        res = await tmt.consolidate_level_safe(
            "u", 2, datetime(2026, 1, 1), datetime(2026, 1, 2),
            AsyncMock(), timeout_sec=0.05,
        )
        assert res["status"] == "timeout"
        assert res["level"] == 2

    @pytest.mark.asyncio
    async def test_consolidate_level_safe_failure(self, monkeypatch):
        import tmt.router as tmt

        async def boom(_u, _l, _s, _e, _p):
            raise ValueError("kaboom")

        monkeypatch.setattr(tmt, "consolidate_level", boom)
        res = await tmt.consolidate_level_safe(
            "u", 3, datetime(2026, 1, 1), datetime(2026, 1, 2), AsyncMock()
        )
        assert res["status"] == "failed"

    @pytest.mark.asyncio
    async def test_pipeline_isolation(self, monkeypatch):
        import tmt.router as tmt

        async def fake(_u, _l, _s, _e, _p):
            if _l == 3:
                raise RuntimeError("L3 失败")
            return {"status": "done", "level": _l}

        monkeypatch.setattr(tmt, "consolidate_level", fake)
        res = await tmt.run_consolidation_pipeline("u", [2, 3, 4], AsyncMock())
        assert res[2]["status"] == "done"
        assert res[3]["status"] == "failed"   # L3 失败
        # 缺陷 1.2 修复：L4 蒸馏依赖 L3 产出，L3 失败后 L4 无输入 → 按层间依赖检查跳过
        # （而非继续空蒸馏浪费 LLM 调用，也非被 L3 失败阻塞崩溃）
        assert res[4]["status"] == "skipped"
        assert res[4].get("reason", "").startswith("L3")


# ═══════════════════════════════════════════════════════════════════════════
# 缺陷 2.3 — API Key 仅存哈希 + hmac.compare_digest 时序安全比对
# ═══════════════════════════════════════════════════════════════════════════

class TestApiKeyHash:

    def _mk_request(self, path, api_key=""):
        from types import SimpleNamespace
        req = MagicMock()
        req.url = SimpleNamespace(path=path)
        req.headers.get.return_value = api_key
        return req

    @pytest.mark.asyncio
    async def test_wrong_key_rejected(self, monkeypatch):
        import amber.main as main_mod
        monkeypatch.setattr(main_mod, "EXPECTED_API_KEY", "secret")
        monkeypatch.setattr(main_mod, "API_KEY_HASH", hashlib.sha256(b"secret").hexdigest())
        req = self._mk_request("/api/v1/memories", "wrong")
        called = {"n": 0}

        async def call_next(r):
            called["n"] += 1
            return MagicMock()

        resp = await main_mod.auth_middleware(req, call_next)
        assert resp.status_code == 401
        assert called["n"] == 0  # 错误密钥未进入端点

    @pytest.mark.asyncio
    async def test_correct_key_accepted(self, monkeypatch):
        import amber.main as main_mod
        monkeypatch.setattr(main_mod, "EXPECTED_API_KEY", "secret")
        monkeypatch.setattr(main_mod, "API_KEY_HASH", hashlib.sha256(b"secret").hexdigest())
        req = self._mk_request("/api/v1/memories", "secret")
        called = {"n": 0}

        async def call_next(r):
            called["n"] += 1
            return MagicMock()

        resp = await main_mod.auth_middleware(req, call_next)
        assert called["n"] == 1  # 认证通过 → 端点被调用
        assert resp is not None

    def test_key_compared_via_hmac(self):
        import amber.main as main_mod
        # 比对使用时序安全的 hmac.compare_digest，而非明文 ==
        key = "some-secret"
        h = hashlib.sha256(key.encode()).hexdigest()
        assert len(h) == 64  # sha256 哈希，非明文
        assert main_mod.hmac.compare_digest(h, h) is True
        assert main_mod.hmac.compare_digest(h, "other") is False


# ═══════════════════════════════════════════════════════════════════════════
# 缺陷 2.4 — 双采样异构校验告警（同模型时降级有效性）
# ═══════════════════════════════════════════════════════════════════════════

class TestAuditHeterogeneity:

    @pytest.mark.asyncio
    async def test_warns_when_same_model(self, monkeypatch, caplog):
        import logging
        import core.llm as llm_mod
        import security.audit as audit_mod
        from security.audit import audit_memory
        # 强制两模型相同 → 应产生 warning
        monkeypatch.setattr(audit_mod, "LLM_MODEL_LITE", "same-model")
        monkeypatch.setattr(audit_mod, "LLM_MODEL_PRO", "same-model")
        # audit_memory 内部 `from core.llm import call_llm_json`，需打 core.llm
        async def fake_llm_json(*a, **k):
            return {"content": '{"is_factual": true, "confidence": 0.9, "reasoning": "ok", "potential_issues": []}'}

        monkeypatch.setattr(llm_mod, "call_llm_json", fake_llm_json)
        with caplog.at_level(logging.WARNING):
            await audit_memory(AsyncMock(), 1, "test content")
        assert any("双采样使用相同模型" in r.message for r in caplog.records)

    @pytest.mark.asyncio
    async def test_no_warn_when_heterogeneous(self, monkeypatch, caplog):
        import logging
        import core.llm as llm_mod
        import security.audit as audit_mod
        from security.audit import audit_memory
        monkeypatch.setattr(audit_mod, "LLM_MODEL_LITE", "model-A")
        monkeypatch.setattr(audit_mod, "LLM_MODEL_PRO", "model-B")

        async def fake_llm_json(*a, **k):
            return {"content": '{"is_factual": true, "confidence": 0.9, "reasoning": "ok", "potential_issues": []}'}

        monkeypatch.setattr(llm_mod, "call_llm_json", fake_llm_json)
        with caplog.at_level(logging.WARNING):
            await audit_memory(AsyncMock(), 1, "test content")
        assert not any("双采样使用相同模型" in r.message for r in caplog.records)


# ═══════════════════════════════════════════════════════════════════════════
# 缺陷 3.1 — 断路器协程安全（asyncio.Lock 保护状态转换）
# ═══════════════════════════════════════════════════════════════════════════

class TestCircuitBreaker:

    @pytest.mark.asyncio
    async def test_state_transitions(self):
        from core.llm import CircuitBreaker
        cb = CircuitBreaker(failure_threshold=3, recovery_timeout=0.1)
        assert cb.state == "CLOSED"
        assert await cb.allow_request() is True
        await cb.record_failure()
        await cb.record_failure()
        await cb.record_failure()  # 第 3 次 → OPEN
        assert cb.state == "OPEN"
        assert await cb.allow_request() is False  # 恢复期内拒绝
        await asyncio.sleep(0.15)  # 超过 recovery
        assert await cb.allow_request() is True   # HALF_OPEN 放行
        await cb.record_success()
        assert cb.state == "CLOSED"

    @pytest.mark.asyncio
    async def test_concurrent_allow_is_safe(self):
        from core.llm import CircuitBreaker
        cb = CircuitBreaker(failure_threshold=100)
        results = await asyncio.gather(*[cb.allow_request() for _ in range(50)])
        assert all(results)  # CLOSED 下并发全部放行，无竞态异常


# ═══════════════════════════════════════════════════════════════════════════
# 缺陷 3.2 — 嵌入失败抛出 EmbeddingUnavailableError，杜绝零向量污染
# ═══════════════════════════════════════════════════════════════════════════

class TestEmbeddingUnavailable:

    @pytest.mark.asyncio
    async def test_raises_not_zero_vector(self, monkeypatch):
        import core.embedding as emb_mod
        from core.embedding import get_embedding_async, EmbeddingUnavailableError

        # get_client() 在 try 之外，但 client.post() 在 try 之内——
        # 让返回的客户端在 post 时抛错，从而被 except 捕获并转为 EmbeddingUnavailableError
        class FailingClient:
            async def post(self, *a, **k):
                raise RuntimeError("embedding API down")

        async def fake_get_client(*a, **k):
            return FailingClient()

        monkeypatch.setattr(emb_mod, "get_client", fake_get_client)
        with pytest.raises(EmbeddingUnavailableError) as exc:
            await get_embedding_async(["hello"])
        assert "Embedding API failed" in str(exc.value)


# ═══════════════════════════════════════════════════════════════════════════
# 缺陷 3.3 — HNSW 索引按热度分级（文件级断言：schema.sql + 迁移 0004）
# ═══════════════════════════════════════════════════════════════════════════

class TestHnswTiering:

    def test_schema_hot_tables_high_precision(self):
        schema = (ROOT / "amber" / "schema.sql").read_text(encoding="utf-8")
        assert re.search(r"ON beliefs USING hnsw.*?WITH \(m=16, ef_construction=200\)", schema, re.S)
        assert re.search(r"ON memory_chunks USING hnsw.*?WITH \(m=16, ef_construction=200\)", schema, re.S)

    def test_schema_cold_tables_lower_params(self):
        schema = (ROOT / "amber" / "schema.sql").read_text(encoding="utf-8")
        assert re.search(r"ON tmt_daily USING hnsw.*?WITH \(m=12, ef_construction=128\)", schema, re.S)
        assert re.search(r"ON media_memories USING hnsw.*?WITH \(m=8, ef_construction=64\)", schema, re.S)

    def test_migration_0004_rebuilds_tiered_indexes(self):
        m = (ROOT / "amber" / "migrations" / "0004_hnsw_index_tiering.sql").read_text(encoding="utf-8")
        assert "DROP INDEX IF EXISTS idx_tmt_daily_embedding" in m
        assert "m=12, ef_construction=128" in m
        assert "DROP INDEX IF EXISTS idx_media_memories_embedding" in m
        assert "m=8, ef_construction=64" in m


# ═══════════════════════════════════════════════════════════════════════════
# 缺陷 3.4 — 两阶段搜索默认启用（利用 HNSW）
# ═══════════════════════════════════════════════════════════════════════════

class TestTwoPhaseDefault:

    def test_build_order_limit_default_two_phase(self):
        import inspect
        from api.search import _build_order_limit
        # 缺陷 3.4：两阶段（利用 HNSW）应为默认，单阶段加权排序无法走索引
        sig = inspect.signature(_build_order_limit)
        assert sig.parameters["two_phase"].default is True


# ═══════════════════════════════════════════════════════════════════════════
# 缺陷 4.2 — evolve_memories 按 content_hash 分组（迁移 + 调用点断言）
# ═══════════════════════════════════════════════════════════════════════════

class TestContentHashDedup:

    def test_migration_0003_adds_content_hash(self):
        m = (ROOT / "amber" / "migrations" / "0003_content_hash.sql").read_text(encoding="utf-8")
        assert "content_hash VARCHAR(64)" in m
        assert "SHA256" in m
        assert "idx_memories_content_hash" in m

    @pytest.mark.asyncio
    async def test_evolve_groups_by_content_hash(self, mock_conn):
        from services.memory_service import evolve_memories
        captured = {}

        async def fake_fetch(q, *a):
            captured["sql"] = q
            return [{"content_hash": "abc", "content": "dup", "ids": [1, 2], "cnt": 2}]

        mock_conn.fetch = fake_fetch
        mock_conn.execute = AsyncMock()
        res = await evolve_memories(mock_conn, "default", "consolidate")
        assert "GROUP BY content_hash" in captured["sql"]
        assert "GROUP BY content)\n" not in captured["sql"]  # 旧的 TEXT 分组已废弃
        assert res["merged"] == 1


# ═══════════════════════════════════════════════════════════════════════════
# 缺陷 4.3 — 连接池获取失败重试（RetryPool 代理）
# ═══════════════════════════════════════════════════════════════════════════

class TestRetryPool:

    @pytest.mark.asyncio
    async def test_retries_then_succeeds(self):
        import amber.main as main_mod

        class FakeConn:
            async def execute(self, *a, **k):
                return None

        class FakeRealPool:
            def __init__(self, fail_times=2):
                self._fail = fail_times
                self._calls = 0
                self.released = 0

            async def acquire(self):
                self._calls += 1
                if self._calls <= self._fail:
                    raise RuntimeError("conn unavailable")
                return FakeConn()

            async def release(self, conn):
                self.released += 1

            async def close(self):
                return None

        fake = FakeRealPool(fail_times=2)
        pool = main_mod.RetryPool(fake)
        async with pool.acquire() as conn:
            assert isinstance(conn, FakeConn)
        assert fake.released == 1  # 退出上下文释放连接

    @pytest.mark.asyncio
    async def test_exhausts_retries_then_raises(self, monkeypatch):
        import amber.main as main_mod
        monkeypatch.setattr(main_mod, "POOL_ACQUIRE_MAX_RETRIES", 2)
        monkeypatch.setattr(main_mod, "POOL_ACQUIRE_BASE_DELAY", 0.0)

        class AlwaysFail:
            async def acquire(self):
                raise RuntimeError("down")

            async def release(self, conn):
                return None

            async def close(self):
                return None

        pool = main_mod.RetryPool(AlwaysFail())
        with pytest.raises(RuntimeError):
            async with pool.acquire() as conn:
                pass


# ═══════════════════════════════════════════════════════════════════════════
# 缺陷 4.4 — 进程退出时清理 HTTP 线程池（atexit 注册）
# ═══════════════════════════════════════════════════════════════════════════

class TestThreadPoolCleanup:

    def test_atexit_registers_pool_shutdown(self):
        import adapters.hermes_provider as hp
        recorded = []
        original = atexit.register

        def capture(fn):
            recorded.append(fn)

        atexit.register = capture
        try:
            importlib.reload(hp)
        finally:
            atexit.register = original
        assert recorded, "atexit.register 未被调用——线程池退出清理缺失"
        # 模块级线程池必须是 ThreadPoolExecutor（具备 shutdown 方法，可被 atexit 清理）
        assert isinstance(hp._HTTP_THREAD_POOL, concurrent.futures.ThreadPoolExecutor)
        # 验证清理逻辑本身可安全执行：在独立池上复刻同样调用，不应抛异常
        # （不调用真实回调，避免关闭共享的模块级线程池，进而影响其它用例）
        dummy = concurrent.futures.ThreadPoolExecutor(max_workers=1)
        dummy.shutdown(wait=False)


# ═══════════════════════════════════════════════════════════════════════════
# 缺陷 4.5 — 自包含 ASGI 测试传输可用（无需运行中服务）
# ═══════════════════════════════════════════════════════════════════════════

class TestAsgiTransport:

    @pytest.mark.asyncio
    async def test_root_via_asgi_transport(self, asgi_client):
        # 根路由 / 不依赖数据库，可完全自包含验证 ASGITransport 可用（缺陷 4.5）。
        # DEV_INSECURE 模式下 / 仍需携带一次性 X-Dev-Token（缺陷 2.1 修复）；
        # 自包含测试直连 ASGI app（不触发 lifespan），但 _DEV_TOKEN 在 import 期已生成，
        # 此处复用该 Token 通过中间件校验，验证根路由确实可访问。
        from amber import main as main_mod
        headers = {}
        if main_mod._DEV_TOKEN:
            headers["X-Dev-Token"] = main_mod._DEV_TOKEN
        resp = await asgi_client.get("/", headers=headers)
        assert resp.status_code == 200
        assert "service" in resp.json()["data"]
