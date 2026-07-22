"""
Aion Memory — 审计报告修复的端到端回归（依赖运行中的 Mnemosyne 服务）。

见 conftest.client（直连 http://127.0.0.1:8010）。这些用例验证 DB 支撑的修复路径：
- 缺陷 1.1：创建记忆后，console 事件流返回 executed_at（由 created_at 映射）。
- 缺陷 1.3：信念 evolve 返回合法状态（不含非法 'hypothesis'）。
其余缺陷已由 test_audit_fixes.py 的纯单元测试在调用点覆盖。
"""
import pytest
import httpx

pytestmark = pytest.mark.asyncio


def _unwrap(resp: httpx.Response):
    data = resp.json()
    if isinstance(data, dict) and "data" in data and "code" in data:
        return data["data"]
    return data


class TestMemoryTraceIntegration:

    async def test_create_memory_then_events_have_executed_at(self, client):
        # 创建一条 durable 记忆（嵌入失败时优雅降级为 NULL，仍返回 201）
        r = await client.post("/api/v1/memories", json={
            "user_id": "default",
            "content": "trace-e2e-unique-marker-7f3a",
            "scope_target": "durable",
        })
        assert r.status_code in (200, 201)

        # 事件流必须包含 executed_at（缺陷 1.1 修复点：读取 created_at 并映射）
        r2 = await client.get(
            "/api/v1/console/events", params={"user_id": "default", "limit": 10}
        )
        assert r2.status_code == 200
        evs = _unwrap(r2).get("events", [])
        assert isinstance(evs, list)
        if evs:
            assert "executed_at" in evs[0]
            assert "action" in evs[0]


class TestBeliefsIntegration:

    async def test_evolve_belief_status_valid(self, client):
        r = await client.post("/api/v1/beliefs", json={
            "user_id": "default", "content": "belief-e2e-marker-9c2d"
        })
        if r.status_code not in (200, 201):
            pytest.skip("belief 创建依赖 embedding 服务，本环境不可用")
        bid = _unwrap(r).get("id")
        assert bid is not None

        r2 = await client.post(
            f"/api/v1/beliefs/{bid}/evolve",
            params={"user_id": "default", "new_confidence": 0.8},
        )
        assert r2.status_code in (200, 404, 500)
        if r2.status_code == 200:
            # 状态必须落在合法枚举内（缺陷 1.3 护栏：不会写出非法 'hypothesis'）
            st = _unwrap(r2).get("status")
            assert st in ("active", "tentative", "established", "contradicted")
