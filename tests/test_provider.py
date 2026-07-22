"""Aion Memory — Hermes Provider 单元测试（Mock HTTP，无需运行 Amber）"""

import pytest
from unittest.mock import patch, MagicMock
from adapters.hermes_provider import (
    should_skip_retrieval,
    AionMemoryProvider,
)


# ═══════════════════════════════════════════════════
# should_skip_retrieval — 保守门禁
# ═══════════════════════════════════════════════════

class TestShouldSkipRetrieval:
    """测试召回门禁的各种边界条件"""

    def test_empty_query(self):
        skip, reason = should_skip_retrieval("")
        assert skip is True
        assert reason == "empty"

    def test_blank_query(self):
        skip, reason = should_skip_retrieval("   ")
        assert skip is True
        assert reason == "empty"

    def test_too_short(self):
        skip, reason = should_skip_retrieval("a")
        assert skip is True
        assert reason == "too_short"

    def test_two_chars(self):
        skip, reason = should_skip_retrieval("ab")
        assert skip is True
        assert reason == "too_short"

    def test_greeting_cn(self):
        """2字符中文问候因长度限制走 too_short 分支（问候检查前已被长度门禁拦截）"""
        skip, reason = should_skip_retrieval("你好")
        assert skip is True
        assert reason == "too_short"

    def test_greeting_en(self):
        skip, reason = should_skip_retrieval("hello")
        assert skip is True
        assert reason == "greeting"

    def test_greeting_case_insensitive(self):
        skip, reason = should_skip_retrieval("HELLO")
        assert skip is True
        assert reason == "greeting"

    def test_noise_only(self):
        """纯符号应跳过"""
        skip, reason = should_skip_retrieval("!@#$%")
        assert skip is True
        assert reason == "noise"

    def test_valid_query(self):
        skip, reason = should_skip_retrieval("记忆系统架构")
        assert skip is False
        assert reason == ""

    def test_valid_english(self):
        skip, reason = should_skip_retrieval("architecture design")
        assert skip is False
        assert reason == ""

    def test_mixed_noise_and_text(self):
        """含文本的混合输入不应跳过"""
        skip, reason = should_skip_retrieval("你好，请问记忆系统")
        assert skip is False
        assert reason == ""


# ═══════════════════════════════════════════════════
# _api_call — 重试与错误处理
# ═══════════════════════════════════════════════════

class TestApiCall:
    """测试 HTTP 调用重试逻辑"""

    def test_success_first_attempt(self):
        """首次成功应返回 True"""
        provider = AionMemoryProvider()
        provider._amber_url = "http://localhost:8010"

        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_urlopen.return_value.__enter__.return_value.status = 200
            result = provider._api_call(
                "http://localhost:8010/api/v1/test",
                b"{}",
                timeout=10,
            )
            assert result is True
            assert mock_urlopen.call_count == 1

    def test_retry_on_timeout(self):
        """超时应触发重试（最多 2 次）"""
        provider = AionMemoryProvider()
        provider._amber_url = "http://localhost:8010"

        with patch("urllib.request.urlopen") as mock_urlopen:
            from urllib.error import URLError
            mock_urlopen.side_effect = [
                URLError(TimeoutError("timeout")),
                MagicMock(),
            ]
            mock_urlopen.return_value.__enter__.return_value.status = 200

            result = provider._api_call(
                "http://localhost:8010/api/v1/test",
                b"{}",
                timeout=10,
            )
            assert result is True
            assert mock_urlopen.call_count == 2

    def test_retry_exhausted(self):
        """重试耗尽后返回 False"""
        provider = AionMemoryProvider()
        provider._amber_url = "http://localhost:8010"

        with patch("urllib.request.urlopen") as mock_urlopen:
            from urllib.error import URLError
            mock_urlopen.side_effect = URLError(TimeoutError("timeout"))

            result = provider._api_call(
                "http://localhost:8010/api/v1/test",
                b"{}",
                timeout=10,
            )
            assert result is False
            assert mock_urlopen.call_count == 2

    def test_non_retryable_error(self):
        """非重试类错误（如 4xx）不应重试"""
        provider = AionMemoryProvider()
        provider._amber_url = "http://localhost:8010"

        with patch("urllib.request.urlopen") as mock_urlopen:
            from urllib.error import HTTPError
            mock_urlopen.side_effect = HTTPError(
                "http://localhost", 401, "Unauthorized",
                {}, None,
            )

            result = provider._api_call(
                "http://localhost:8010/api/v1/test",
                b"{}",
                timeout=10,
            )
            assert result is False
            assert mock_urlopen.call_count == 1


# ═══════════════════════════════════════════════════
# _flush_turns — 失败保护
# ═══════════════════════════════════════════════════

class TestFlushTurns:
    """测试 _flush_turns 的失败保护逻辑"""

    def test_flush_clear_on_success(self):
        """成功时应清空待处理队列"""
        provider = AionMemoryProvider()
        provider._session_id = "test_session"
        provider._amber_url = "http://localhost:8010"
        provider._pending_turns = [
            {"user": "hi", "assistant": "hello"},
            {"user": "how are you", "assistant": "fine"},
        ]

        with patch.object(provider, "_api_save_memory", return_value=True):
            provider._flush_turns()
            assert len(provider._pending_turns) == 0

    def test_flush_keep_on_failure(self):
        """失败时应保留队列"""
        provider = AionMemoryProvider()
        provider._session_id = "test_session"
        provider._amber_url = "http://localhost:8010"
        provider._pending_turns = [
            {"user": "hi", "assistant": "hello"},
        ]

        with patch.object(provider, "_api_save_memory", return_value=False):
            provider._flush_turns()
            assert len(provider._pending_turns) == 1

    def test_flush_empty_noop(self):
        """空队列不应报错"""
        provider = AionMemoryProvider()
        provider._session_id = "test_session"
        provider._amber_url = "http://localhost:8010"
        provider._pending_turns = []

        with patch.object(provider, "_api_save_memory") as mock_save:
            provider._flush_turns()
            mock_save.assert_not_called()

    def test_flush_discard_old_when_overflow(self):
        """队列超 50 条后丢弃最旧批次"""
        provider = AionMemoryProvider()
        provider._session_id = "test_session"
        provider._amber_url = "http://localhost:8010"
        provider._pending_turns = [
            {"user": f"turn_{i}", "assistant": f"resp_{i}"}
            for i in range(60)
        ]

        with patch.object(provider, "_api_save_memory", return_value=False):
            provider._flush_turns()
            # 应保留最近 30 轮
            assert len(provider._pending_turns) == 30
            # 最旧的应被丢弃（turn_0 不在了）
            assert provider._pending_turns[0]["user"] == "turn_30"

    def test_shutdown_flushes_pending(self):
        """shutdown 应尝试刷写待处理队列"""
        provider = AionMemoryProvider()
        provider.initialize("test_session")
        provider._amber_url = "http://localhost:8010"
        provider._pending_turns = [
            {"user": "hi", "assistant": "hello"},
        ]

        with patch.object(provider, "_api_save_memory", return_value=True):
            provider.shutdown()
            assert len(provider._pending_turns) == 0

    def test_shutdown_keeps_on_failure(self):
        """shutdown 失败时保留队列"""
        provider = AionMemoryProvider()
        provider.initialize("test_session")
        provider._amber_url = "http://localhost:8010"
        provider._pending_turns = [
            {"user": "hi", "assistant": "hello"},
        ]

        with patch.object(provider, "_api_save_memory", return_value=False):
            provider.shutdown()
            assert len(provider._pending_turns) == 1


# ═══════════════════════════════════════════════════
# 生命周期
# ═══════════════════════════════════════════════════

class TestProviderLifecycle:
    """测试 Provider 初始化与基础功能"""

    def test_name(self):
        provider = AionMemoryProvider()
        assert provider.name == "aion-memory"

    def test_is_available(self):
        provider = AionMemoryProvider()
        assert provider.is_available() is True

    def test_initialize_with_session(self):
        provider = AionMemoryProvider()
        provider.initialize("test-sess-123")
        assert provider._session_id == "test-sess-123"
        assert provider._turn_count == 0

    def test_system_prompt_block_contains_core_concepts(self):
        provider = AionMemoryProvider()
        prompt = provider.system_prompt_block()
        assert "作用域" in prompt
        assert "durable" in prompt
        assert "general" in prompt

    def test_sync_turn_counts(self):
        provider = AionMemoryProvider()
        provider.initialize("test-sess-456")
        provider.sync_turn("user msg", "assistant reply")
        assert provider._turn_count == 1
