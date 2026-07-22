"""
Aion Memory — 服务层单元测试（Mock DB，可在无 PostgreSQL 环境运行）
"""
import pytest
from unittest.mock import AsyncMock, MagicMock

# ── 辅助工具 ──

@pytest.fixture
def mock_conn():
    """创建模拟的 asyncpg 连接对象"""
    conn = AsyncMock()
    conn.fetch = AsyncMock()
    conn.fetchrow = AsyncMock()
    conn.fetchval = AsyncMock()
    conn.execute = AsyncMock()
    return conn


# ═══════════════════════════════════════════════════
# services.memory_service 测试
# ═══════════════════════════════════════════════════

class TestMemoryService:

    @pytest.mark.asyncio
    async def test_detect_conflict_fresh(self, mock_conn):
        """无冲突时返回 fresh"""
        from services.memory_service import detect_conflict
        mock_conn.fetch.return_value = []
        result = await detect_conflict(mock_conn, "default", "new content", "[0.1,0.2]")
        assert result == {"action": "fresh"}

    @pytest.mark.asyncio
    async def test_detect_conflict_merge(self, mock_conn):
        """高文本相似度返回 merge"""
        from services.memory_service import detect_conflict
        mock_conn.fetch.return_value = [
            {"id": 1, "content": "这是一条测试记忆内容", "dist": 0.05, "heat_score": 0.8}
        ]
        result = await detect_conflict(
            mock_conn, "default",
            "这是一条测试记忆内容",  # 完全相同 → ratio=1.0 → merge
            "[0.1,0.2,0.3]"
        )
        assert result["action"] == "merge"
        assert result["id"] == 1

    @pytest.mark.asyncio
    async def test_cleanup(self, mock_conn):
        """cleanup 返回正确结构"""
        from services.memory_service import cleanup
        mock_conn.execute.return_value = "UPDATE 5"
        result = await cleanup(mock_conn, "default", 0.1)
        assert result["status"] == "cleanup done"
        assert result["threshold"] == 0.1

    @pytest.mark.asyncio
    async def test_reflect_light(self, mock_conn):
        """light 模式返回正确状态"""
        from services.memory_service import reflect
        mock_conn.execute.return_value = "UPDATE 10"
        result = await reflect(mock_conn, "default", "light")
        assert "completed" in result["status"]

    @pytest.mark.asyncio
    async def test_reflect_deep(self, mock_conn):
        """deep 模式执行实体提取"""
        from services.memory_service import reflect
        mock_conn.execute.return_value = "UPDATE 0"
        mock_conn.fetch.return_value = [
            {"id": 1, "content": "项目中提到「智能合约」和「共识算法」"}
        ]
        mock_conn.fetchrow.return_value = None  # 实体不存在
        result = await reflect(mock_conn, "default", "deep")
        assert "completed" in result["status"]

    @pytest.mark.asyncio
    async def test_evolve_consolidate(self, mock_conn):
        """合并策略返回 merged 计数（适配 GROUP BY 格式）"""
        from services.memory_service import evolve_memories
        mock_conn.fetch.return_value = [
            {"content": "重复内容", "ids": [1, 2], "cnt": 2},
            {"content": "独有内容", "ids": [3], "cnt": 1},
        ]
        result = await evolve_memories(mock_conn, "default", "consolidate")
        assert result["strategy"] == "consolidate"
        assert result["merged"] == 1  # 只有 1 组有重复（id=2 被删除）

    @pytest.mark.asyncio
    async def test_evolve_boost(self, mock_conn):
        """提频策略返回 affected 计数"""
        from services.memory_service import evolve_memories
        mock_conn.execute.return_value = "UPDATE 5"
        result = await evolve_memories(mock_conn, "default", "boost")
        assert result["strategy"] == "boost"

    @pytest.mark.asyncio
    async def test_text_diff_ratio(self):
        """文本相似度计算"""
        from services.memory_service import text_diff_ratio
        r = text_diff_ratio("hello world", "hello world")
        assert r == 1.0
        r = text_diff_ratio("hello world", "goodbye world")
        assert 0.3 < r < 0.9


# ═══════════════════════════════════════════════════
# 认证中间件测试（模拟 Request）
# ═══════════════════════════════════════════════════

class TestAuthMiddleware:

    @pytest.mark.asyncio
    async def test_no_key_dev_mode(self, monkeypatch):
        """DEV_INSECURE 模式下跳过认证"""
        # 模拟 MNEMOSYNE_DEV_INSECURE=1 环境（使用 monkeypatch 仅作用于单键，
        # 避免 patch.dict 在超大环境变量的沙箱中还原失败）
        monkeypatch.setenv("MNEMOSYNE_DEV_INSECURE", "1")
        # 只是验证不抛出 RuntimeError
        from amber.main import EXPECTED_API_KEY, TENANT_ID
        assert EXPECTED_API_KEY == ""
        assert TENANT_ID == "default"
