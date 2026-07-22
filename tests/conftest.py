"""Aion Memory — 测试基础设施

缺陷 4.5：测试不再「只能」依赖运行中的外部服务。提供两种 client fixture：
- `client`：保留对运行中的真实服务的直连（http://127.0.0.1:8010），
  用于需要完整 DB / embedding 服务的端到端回归（与既有 test_core.py 等兼容）。
- `asgi_client`：基于 httpx.ASGITransport 直连 ASGI app，自包含、CI 可复现，
  不需要外部监听端口。DB 相关端点需在 CI 中提供 Postgres 容器
  （+ MNEMOSYNE_DEV_INSECURE=1）。新增测试应优先使用 asgi_client。
"""
import sys
import os
from pathlib import Path

# 添加 amber/ 到 Python 路径（使 services/api/core 等包可导入）
_amber_path = str(Path(__file__).resolve().parent.parent / "amber")
if _amber_path not in sys.path:
    sys.path.insert(0, _amber_path)

import pytest
import httpx
from typing import AsyncGenerator

BASE_URL = "http://127.0.0.1:8010"


@pytest.fixture
def api_key() -> str:
    return ""


@pytest.fixture
def headers(api_key: str) -> dict:
    h = {"Content-Type": "application/json"}
    if api_key:
        h["X-API-Key"] = api_key
    return h


@pytest.fixture
async def client() -> AsyncGenerator[httpx.AsyncClient, None]:
    """直连运行中的真实服务（端到端回归，兼容既有用例）。"""
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as c:
        yield c


@pytest.fixture
async def asgi_client() -> AsyncGenerator[httpx.AsyncClient, None]:
    """缺陷 4.5：自包含 ASGI 传输客户端，不依赖运行中的外部服务。

    直连 FastAPI app；纯路由/能力类用例无需 DB，DB 相关端点需 CI 提供 Postgres。
    审计修复 A2：每个测试自动重置 app.state / api.shared 缓存，防止状态泄漏。
    """
    from amber.main import app
    import api.shared as _api_shared

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        # 保存原始状态
        orig_pool = getattr(app.state, "pool", None)
        orig_embed = getattr(app.state, "get_embedding_fn", None)
        orig_cached_embed = getattr(_api_shared, "_cached_embedding_fn", None)
        try:
            yield c
        finally:
            app.state.pool = orig_pool
            app.state.get_embedding_fn = orig_embed
            _api_shared._cached_embedding_fn = orig_cached_embed
            # 同时重置 shared 模块级缓存，防止测试间泄漏
            _api_shared._pool = None
