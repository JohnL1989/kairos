"""Aion Memory — 搜索 API 基础测试"""
import pytest
import httpx

BASE_URL = "http://127.0.0.1:8010"

@pytest.mark.asyncio
async def test_health():
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{BASE_URL}/api/v1/health/default")
        assert resp.status_code == 200

@pytest.mark.asyncio
async def test_search_no_auth():
    """未配置 API Key 时应正常返回"""
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{BASE_URL}/api/v1/memories/search",
            json={"user_id": "default", "query": "test", "top_k": 3}
        )
        assert resp.status_code in (200, 401)  # 取决于是否有 API key
