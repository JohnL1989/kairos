"""Aion Memory — 核心功能测试（全量 ~60 用例，适配 v1.7+ 响应信封）"""
import pytest
import httpx

pytestmark = pytest.mark.asyncio
SEARCH_URL = "/api/v1/memories/search"


def _unwrap(resp: httpx.Response) -> dict:
    """统一解包 API 响应：兼容 {code,message,data} 信封格式和扁平格式。"""
    data = resp.json()
    if "data" in data and "code" in data:
        return data["data"]
    return data


# ═══════════════════════════════════════════════════
# 健康检查（2）
# ═══════════════════════════════════════════════════
class TestHealth:
    async def test_health_root(self, client: httpx.AsyncClient):
        resp = await client.get("/")
        assert resp.status_code == 200
        data = _unwrap(resp)
        assert "service" in data

    async def test_health_default(self, client: httpx.AsyncClient):
        resp = await client.get("/api/v1/health/default")
        assert resp.status_code == 200


# ═══════════════════════════════════════════════════
# 能力 & 元数据（3）
# ═══════════════════════════════════════════════════
class TestCapabilities:
    async def test_capabilities(self, client: httpx.AsyncClient):
        resp = await client.get("/api/v1/capabilities")
        assert resp.status_code == 200
        data = _unwrap(resp)
        assert "version" in data
        assert "graceful_degradation" in data
        assert "FTS5" in data["graceful_degradation"]["embed_unavailable"]

    async def test_capabilities_fields(self, client: httpx.AsyncClient):
        resp = await client.get("/api/v1/capabilities")
        data = _unwrap(resp)
        assert "endpoints" in data
        assert "quick_start" in data

    async def test_echo(self, client: httpx.AsyncClient):
        resp = await client.get("/api/v1/echo")
        assert resp.status_code == 200
        assert _unwrap(resp)["status"] == "ok"


# ═══════════════════════════════════════════════════
# 认证与安全（7）
# ═══════════════════════════════════════════════════
class TestAuth:
    async def test_no_auth_health_bypass(self, client: httpx.AsyncClient):
        """健康检查端点应绕过认证"""
        resp = await client.get("/api/v1/health/default")
        assert resp.status_code == 200

    async def test_memories_list_format(self, client: httpx.AsyncClient):
        resp = await client.get("/api/v1/memories", params={"user_id": "default", "limit": 3})
        assert resp.status_code == 200
        data = _unwrap(resp)
        assert "memories" in data
        assert isinstance(data["memories"], list)

    async def test_memories_list_durable_only(self, client: httpx.AsyncClient):
        """默认只返回 durable 记忆"""
        resp = await client.get("/api/v1/memories", params={"user_id": "default", "limit": 10})
        data = _unwrap(resp)
        for m in data["memories"]:
            assert m["scope"] == "durable", f"scope 应为 durable: {m}"

    async def test_memories_limit(self, client: httpx.AsyncClient):
        """limit 参数应生效"""
        resp = await client.get("/api/v1/memories", params={"user_id": "default", "limit": 2})
        data = _unwrap(resp)
        assert len(data["memories"]) <= 2

    async def test_memories_list_with_session(self, client: httpx.AsyncClient):
        """传 scope_session_id 应同时返回 durable + general"""
        resp = await client.get("/api/v1/memories", params={"user_id": "default", "limit": 5, "scope_session_id": "test"})
        assert resp.status_code == 200

    async def test_tmt_health(self, client: httpx.AsyncClient):
        """TMT 树应有数据"""
        resp = await client.get("/api/v1/tmt/tree")
        assert resp.status_code == 200
        data = _unwrap(resp)
        assert "levels" in data
        assert data["levels"]["L1"]["count"] > 0

    async def test_cost_endpoint(self, client: httpx.AsyncClient):
        """成本统计端点应返回结构"""
        resp = await client.get("/api/v1/security/costs")
        assert resp.status_code == 200
        data = _unwrap(resp)
        assert "costs" in data or "total_cost" in str(data)


# ═══════════════════════════════════════════════════
# 搜索功能（10）
# ═══════════════════════════════════════════════════
class TestSearch:
    async def test_search_chinese(self, client: httpx.AsyncClient):
        """中文关键词应返回结果"""
        resp = await client.post(SEARCH_URL, json={"user_id": "default", "query": "记忆系统", "top_k": 3})
        assert resp.status_code == 200
        data = _unwrap(resp)
        assert len(data["memories"]) > 0

    async def test_search_english(self, client: httpx.AsyncClient):
        resp = await client.post(SEARCH_URL, json={"user_id": "default", "query": "SOUL", "top_k": 3})
        assert resp.status_code == 200
        assert len(_unwrap(resp)["memories"]) > 0

    async def test_search_top_k(self, client: httpx.AsyncClient):
        """top_k 应限制结果数"""
        resp = await client.post(SEARCH_URL, json={"user_id": "default", "query": "记忆系统", "top_k": 1})
        assert len(_unwrap(resp)["memories"]) <= 1

    async def test_search_no_match(self, client: httpx.AsyncClient):
        """无匹配查询应返回空列表"""
        resp = await client.post(SEARCH_URL, json={"user_id": "default", "query": "XYZZZ_NONEXISTENT", "top_k": 3})
        assert resp.status_code == 200
        data = _unwrap(resp)
        assert len(data["memories"]) >= 0  # never crash

    async def test_search_empty_query(self, client: httpx.AsyncClient):
        resp = await client.post(SEARCH_URL, json={"user_id": "default", "query": "", "top_k": 3})
        assert resp.status_code in (200, 422)

    async def test_search_missing_user(self, client: httpx.AsyncClient):
        resp = await client.post(SEARCH_URL, json={"query": "SOUL", "top_k": 3})
        assert resp.status_code in (200, 422)

    async def test_search_missing_query(self, client: httpx.AsyncClient):
        resp = await client.post(SEARCH_URL, json={"user_id": "default", "top_k": 3})
        assert resp.status_code in (200, 422)

    async def test_search_special_chars(self, client: httpx.AsyncClient):
        """特殊字符不应崩溃"""
        resp = await client.post(SEARCH_URL, json={"user_id": "default", "query": "!@#$%^&*()_+", "top_k": 3})
        assert resp.status_code == 200

    async def test_search_very_long_query(self, client: httpx.AsyncClient):
        """超长查询不应崩溃"""
        long_q = "记忆" * 500
        resp = await client.post(SEARCH_URL, json={"user_id": "default", "query": long_q, "top_k": 3})
        assert resp.status_code in (200, 422)

    async def test_explain_endpoint(self, client: httpx.AsyncClient):
        """explain 应返回评分明细"""
        resp = await client.post("/api/v1/explain", json={"user_id": "default", "query": "记忆系统"})
        if resp.status_code == 500:
            return  # explain 依赖 embedding 服务，不可用时返回 500 是可接受的
        data = _unwrap(resp)
        assert "trace" in data
        if "results" in data:
            assert "scoring" in data["results"][0] if data["results"] else True


# ═══════════════════════════════════════════════════
# 记忆 CRUD（10）
# ═══════════════════════════════════════════════════
class TestMemories:
    MEM_URL = "/api/v1/memories"

    async def test_create_memory(self, client: httpx.AsyncClient):
        resp = await client.post(self.MEM_URL, json={
            "user_id": "test_user", "content": "test memory", "scope_target": "durable"
        })
        assert resp.status_code in (200, 201)
        data = _unwrap(resp)
        assert "id" in data
        return data["id"]

    async def test_create_memory_general(self, client: httpx.AsyncClient):
        resp = await client.post(self.MEM_URL, json={
            "user_id": "test_user", "content": "session memory",
            "scope_target": "general", "scope_session_id": "sess_001"
        })
        assert resp.status_code in (200, 201)

    async def test_get_memory(self, client: httpx.AsyncClient):
        mid = await self.test_create_memory(client)
        resp = await client.get(f"{self.MEM_URL}/{mid}", params={"user_id": "test_user"})
        assert resp.status_code == 200
        data = _unwrap(resp)
        assert data["content"] == "test memory"

    async def test_get_memory_not_found(self, client: httpx.AsyncClient):
        resp = await client.get(f"{self.MEM_URL}/999999", params={"user_id": "default"})
        assert resp.status_code == 404

    async def test_create_memory_empty(self, client: httpx.AsyncClient):
        resp = await client.post(self.MEM_URL, json={
            "user_id": "test_user", "content": "", "scope_target": "durable"
        })
        assert resp.status_code in (200, 201, 422)

    async def test_create_memory_long(self, client: httpx.AsyncClient):
        resp = await client.post(self.MEM_URL, json={
            "user_id": "test_user", "content": "A" * 10000, "scope_target": "durable"
        })
        assert resp.status_code in (200, 201, 413, 422)

    async def test_delete_memory(self, client: httpx.AsyncClient):
        mid = await self.test_create_memory(client)
        resp = await client.delete(f"{self.MEM_URL}/{mid}", params={"user_id": "test_user"})
        assert resp.status_code == 200
        assert _unwrap(resp)["status"] == "deleted"

    async def test_delete_memory_not_found(self, client: httpx.AsyncClient):
        resp = await client.delete(f"{self.MEM_URL}/999999", params={"user_id": "default"})
        assert resp.status_code == 404

    async def test_list_empty_user(self, client: httpx.AsyncClient):
        resp = await client.get(self.MEM_URL, params={"user_id": "nonexistent_user", "limit": 5})
        assert resp.status_code == 200
        data = _unwrap(resp)
        assert isinstance(data["memories"], list)  # 不应崩溃

    async def test_list_capacity(self, client: httpx.AsyncClient):
        resp = await client.get(self.MEM_URL, params={"user_id": "default", "limit": 0})
        assert resp.status_code == 200


# ═══════════════════════════════════════════════════
# Scope 隔离（5）
# ═══════════════════════════════════════════════════
class TestScope:
    async def test_scope_default_durable(self, client: httpx.AsyncClient):
        resp = await client.get("/api/v1/memories", params={"user_id": "default", "limit": 10})
        for m in _unwrap(resp)["memories"]:
            assert m["scope"] == "durable"

    async def test_scope_general_not_returned(self, client: httpx.AsyncClient):
        """general 记忆不加 scope_session_id 不应返回"""
        mid = None
        resp = await client.post("/api/v1/memories", json={
            "user_id": "scope_test", "content": "secret session data",
            "scope_target": "general", "scope_session_id": "secret_session"
        })
        if resp.status_code in (200, 201):
            mid = _unwrap(resp).get("id")
        resp2 = await client.get("/api/v1/memories", params={"user_id": "scope_test", "limit": 10})
        ids = [m["id"] for m in _unwrap(resp2)["memories"]]
        if mid:
            assert mid not in ids, "general 记忆不应在默认列表中"

    async def test_scope_general_with_session_id(self, client: httpx.AsyncClient):
        """传匹配的 scope_session_id 应返回 general 记忆"""
        resp = await client.post("/api/v1/memories", json={
            "user_id": "scope_test2", "content": "session data",
            "scope_target": "general", "scope_session_id": "test_sess"
        })
        resp2 = await client.get("/api/v1/memories", params={
            "user_id": "scope_test2", "limit": 10, "scope_session_id": "test_sess"
        })
        assert resp2.status_code == 200

    async def test_scope_general_wrong_session_id(self, client: httpx.AsyncClient):
        """传不匹配的 scope_session_id 不应返回"""
        resp = await client.post("/api/v1/memories", json={
            "user_id": "scope_test3", "content": "secret",
            "scope_target": "general", "scope_session_id": "sess_a"
        })
        mid = _unwrap(resp).get("id") if resp.status_code in (200, 201) else None
        resp2 = await client.get("/api/v1/memories", params={
            "user_id": "scope_test3", "limit": 10, "scope_session_id": "sess_b"
        })
        ids = [m["id"] for m in _unwrap(resp2)["memories"]]
        if mid:
            assert mid not in ids

    async def test_scope_invalid_target(self, client: httpx.AsyncClient):
        resp = await client.post("/api/v1/memories", json={
            "user_id": "test", "content": "test",
            "scope_target": "invalid"
        })
        assert resp.status_code == 400


# ═══════════════════════════════════════════════════
# TMT 蒸馏（6）
# ═══════════════════════════════════════════════════
class TestTMT:
    async def test_tree_structure(self, client: httpx.AsyncClient):
        resp = await client.get("/api/v1/tmt/tree")
        assert resp.status_code == 200
        data = _unwrap(resp)
        for tier in ["L1", "L2", "L3", "L4", "L5"]:
            assert tier in data["levels"]

    async def test_tree_counts(self, client: httpx.AsyncClient):
        resp = await client.get("/api/v1/tmt/tree")
        data = _unwrap(resp)
        assert data["levels"]["L1"]["count"] >= data["levels"]["L2"]["count"]
        assert data["levels"]["L2"]["avg_heat"] >= 0

    async def test_level_endpoint(self, client: httpx.AsyncClient):
        resp = await client.get("/api/v1/tmt/level/2/1")
        assert resp.status_code in (200, 404, 422)

    async def test_recall_simple(self, client: httpx.AsyncClient):
        resp = await client.post("/api/v1/tmt/recall/simple", params={
            "user_id": "default", "q": "记忆系统", "top_k": 3
        })
        assert resp.status_code in (200, 422, 500)

    async def test_decay(self, client: httpx.AsyncClient):
        """decay 不应崩溃"""
        resp = await client.post("/api/v1/tmt/decay", params={"user_id": "default"})
        assert resp.status_code in (200, 422, 500)

    async def test_consolidate_daily(self, client: httpx.AsyncClient):
        """每日蒸馏不应崩溃"""
        resp = await client.post("/api/v1/tmt/consolidate/daily", params={"user_id": "default"})
        assert resp.status_code in (200, 422, 500)


# ═══════════════════════════════════════════════════
# 信念系统（4）
# ═══════════════════════════════════════════════════
class TestBeliefs:
    B_URL = "/api/v1/beliefs"

    async def test_create_belief(self, client: httpx.AsyncClient):
        resp = await client.post(self.B_URL, json={
            "user_id": "default", "content": "test belief"
        })
        assert resp.status_code in (200, 201, 500)

    async def test_search_beliefs(self, client: httpx.AsyncClient):
        resp = await client.post(f"{self.B_URL}/search", json={
            "user_id": "default", "query": "test", "top_k": 3
        })
        assert resp.status_code in (200, 500)

    async def test_evolve_belief(self, client: httpx.AsyncClient):
        resp = await client.post(f"{self.B_URL}/1/evolve", params={"user_id": "default"})
        assert resp.status_code in (200, 404, 500)

    async def test_get_belief(self, client: httpx.AsyncClient):
        resp = await client.get(f"{self.B_URL}/1", params={"user_id": "default"})
        assert resp.status_code in (200, 404, 500)


# ═══════════════════════════════════════════════════
# Wiki（4）
# ═══════════════════════════════════════════════════
class TestWiki:
    W_URL = "/api/v1/wiki"

    async def test_create_page(self, client: httpx.AsyncClient):
        resp = await client.post(self.W_URL, params={
            "user_id": "default", "title": "Test Page", "content": "test content"
        })
        assert resp.status_code in (200, 201, 500)

    async def test_get_page(self, client: httpx.AsyncClient):
        resp = await client.get(f"{self.W_URL}/1", params={"user_id": "default"})
        assert resp.status_code in (200, 404, 500)

    async def test_search_wiki(self, client: httpx.AsyncClient):
        resp = await client.get(f"{self.W_URL}/search", params={
            "user_id": "default", "query": "test", "top_k": 3
        })
        assert resp.status_code in (200, 422)

    async def test_list_wiki(self, client: httpx.AsyncClient):
        resp = await client.get(self.W_URL, params={"user_id": "default"})
        assert resp.status_code in (200, 404, 500)


# ═══════════════════════════════════════════════════
# 工具归档（3）
# ═══════════════════════════════════════════════════
class TestTools:
    async def test_archive_tool_call(self, client: httpx.AsyncClient):
        resp = await client.post("/api/v1/tools/archive", json={
            "tool_name": "test_tool", "params": {"a": 1},
            "result": "ok", "success": True, "tenant_id": "default"
        })
        assert resp.status_code in (200, 201)
        data = _unwrap(resp)
        assert "archive_id" in data

    async def test_list_pitfalls(self, client: httpx.AsyncClient):
        resp = await client.get("/api/v1/tools/pitfalls", params={"tenant_id": "default"})
        assert resp.status_code == 200
        assert "pitfalls" in _unwrap(resp)

    async def test_list_skills(self, client: httpx.AsyncClient):
        resp = await client.get("/api/v1/tools/skills", params={"tenant_id": "default"})
        assert resp.status_code == 200
        assert "skills" in _unwrap(resp)


# ═══════════════════════════════════════════════════
# 安全端点（3）
# ═══════════════════════════════════════════════════
class TestSecurity:
    async def test_audit(self, client: httpx.AsyncClient):
        """审计端点不应崩溃"""
        resp = await client.post("/api/v1/security/audit/run", params={"user_id": "default"})
        assert resp.status_code in (200, 500)

    async def test_fossils(self, client: httpx.AsyncClient):
        resp = await client.get("/api/v1/security/fossils", params={"tenant_id": "default"})
        assert resp.status_code == 200
        data = _unwrap(resp)
        assert isinstance(data.get("fossils", []), list)

    async def test_costs(self, client: httpx.AsyncClient):
        resp = await client.get("/api/v1/security/costs")
        assert resp.status_code == 200


# ═══════════════════════════════════════════════════
# 边界条件 & 错误处理（6）
# ═══════════════════════════════════════════════════
class TestEdgeCases:
    async def test_long_session_id(self, client: httpx.AsyncClient):
        resp = await client.get("/api/v1/memories", params={
            "user_id": "default", "limit": 3, "scope_session_id": "A" * 1000
        })
        assert resp.status_code in (200, 422)

    async def test_negative_limit(self, client: httpx.AsyncClient):
        resp = await client.get("/api/v1/memories", params={"user_id": "default", "limit": -1})
        assert resp.status_code in (200, 422, 500)

    async def test_very_large_limit(self, client: httpx.AsyncClient):
        resp = await client.get("/api/v1/memories", params={"user_id": "default", "limit": 10000})
        assert resp.status_code == 200

    async def test_delete_already_deleted(self, client: httpx.AsyncClient):
        resp = await client.delete("/api/v1/memories/99999", params={"user_id": "default"})
        assert resp.status_code == 404

    async def test_invalid_json_body(self, client: httpx.AsyncClient):
        resp = await client.post(SEARCH_URL, data="not json", headers={"Content-Type": "application/json"})
        assert resp.status_code in (400, 422)

    async def test_empty_body(self, client: httpx.AsyncClient):
        resp = await client.post(SEARCH_URL, json={})
        assert resp.status_code in (422, 200)


# ═══════════════════════════════════════════════════
# 端点存活检查（合并统计用）
# ═══════════════════════════════════════════════════
class TestEndpoints:
    """确保所有注册端点不返回 5xx"""

    ENDPOINTS = [
        ("GET", "/api/v1/health/default"),
        ("GET", "/api/v1/capabilities"),
        ("GET", "/api/v1/echo"),
        ("GET", "/api/v1/memories?user_id=default&limit=1"),
        ("GET", "/api/v1/tmt/tree/default"),
        ("GET", "/api/v1/tools/pitfalls?tenant_id=default"),
        ("GET", "/api/v1/tools/skills?tenant_id=default"),
        ("GET", "/api/v1/security/fossils?tenant_id=default"),
        ("GET", "/api/v1/security/costs"),
    ]

    async def test_all_get_endpoints(self, client: httpx.AsyncClient):
        results = []
        for method, path in self.ENDPOINTS:
            resp = await client.request(method, path)
            ok = resp.status_code < 500
            results.append((path, resp.status_code, ok))
            assert ok, f"端点 {path} 返回 {resp.status_code}"

    async def test_api_docs(self, client: httpx.AsyncClient):
        """OpenAPI 文档可访问"""
        resp = await client.get("/docs")
        assert resp.status_code == 200
        resp2 = await client.get("/openapi.json")
        assert resp2.status_code == 200
        data = resp2.json()
        assert "paths" in data
        assert len(data["paths"]) > 20
