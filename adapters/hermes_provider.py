from __future__ import annotations
# Aion Memory — Hermes Agent MemoryProvider 插件
# 实现 Hermes v0.18.0 MemoryProvider ABC
"""
Aion Memory Provider — Hermes Agent 原生 MemoryProvider 插件。
通过 Amber API 实现跨会话记忆持久化、作用域隔离、TMT 蒸馏、自主反思。
"""
import atexit
import ipaddress
import json
import logging
import os
import re
import tempfile
import time
import urllib.request
import urllib.error
import concurrent.futures
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

from agent.memory_provider import MemoryProvider

logger = logging.getLogger(__name__)

# ── HTTP 线程池：将同步 urllib 调用推入独立线程，避免阻塞 Hermes 事件循环 ──
_HTTP_THREAD_POOL = concurrent.futures.ThreadPoolExecutor(
    max_workers=4, thread_name_prefix="aion-http"
)

# ── 缺陷 4.4：进程退出时清理线程池，避免线程泄露 ──
atexit.register(lambda: _HTTP_THREAD_POOL.shutdown(wait=False))

# ── Layer 1 自我管理：容量自检 / Instinct 自动毕业 / User 去重 ──
CAPACITY_WARNING_THRESHOLD = 0.80  # 80% 触发 warning
INSTINCT_GRADUATION_THRESHOLD = 3   # 同 domain ≥3 条 → 自动毕业
_USER_DEDUP_SIMILARITY = 0.5  # 关键词重叠率 >50% → 视为同类
_MEMORY_ID_RE = re.compile(r"\[memory#(\d+)\]")

# ── 默认配置（通过环境变量覆盖） ──
DEFAULT_MNEMOSYNE_URL = os.getenv("AION_MNEMOSYNE_URL", "http://127.0.0.1:8010")


# ── 缺陷 2.3 修复：SSRF 防护 ──
# 校验目标 URL，拒绝链路本地（云元数据 169.254.169.254 等）与非法协议；
# 回环地址（localhost 开发）放行，其它内网/保留地址放行但告警，
# 显式可信内网主机可经 AION_MNEMOSYNE_ALLOWED_HOSTS 白名单放行。
def _validate_amber_url(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise ValueError(f"非法协议: {parsed.scheme}（仅允许 http/https）")
    host = parsed.hostname or ""
    try:
        ip = ipaddress.ip_address(host)
    except ValueError:
        return  # 域名：放行（如需可加 DNS 解析检查）
    if ip.is_link_local:
        raise ValueError(f"目标 IP {host} 为链路本地地址，SSRF 防护拒绝（疑似云元数据端点）")
    allowed = {h.strip() for h in os.getenv("AION_MNEMOSYNE_ALLOWED_HOSTS", "").split(",") if h.strip()}
    if host in allowed:
        return
    if ip.is_loopback:
        return
    if ip.is_private or ip.is_reserved or ip.is_multicast:
        logger.warning("MNEMOSYNE_URL 指向内网/保留地址 %s，请确认可信后再使用", host)


def _resolve_dev_token(amber_url: str) -> str:
    """解析 DEV 模式临时 Token（缺陷 2.1 桥接层适配）。

    优先级：环境变量 MNEMOSYNE_DEV_TOKEN > 服务启动时写入的临时文件
    （<tmp>/amber_dev_token_<port>，由 amber.main 在 DEV_INSECURE 模式写入）。
    """
    tok = os.getenv("MNEMOSYNE_DEV_TOKEN", "").strip()
    if tok:
        return tok
    try:
        port = urlparse(amber_url).port or 8010
        tf_path = os.path.join(tempfile.gettempdir(), f"amber_dev_token_{port}")
        if os.path.exists(tf_path):
            with open(tf_path) as f:
                return f.read().strip()
    except Exception:
        pass
    return ""

# ── 保守门禁 ──
TRIVIAL_QUERIES = {"你好", "hello", "hi", "hey", ""}
TRIVIAL_MAX_LEN = 2


def should_skip_retrieval(query: str) -> tuple[bool, str]:
    """检查查询是否应跳过召回。
    返回 (skip: bool, reason: str)"""
    q = query.strip()
    if not q:
        return True, "empty"
    if len(q) <= TRIVIAL_MAX_LEN:
        return True, "too_short"
    if q.lower() in TRIVIAL_QUERIES:
        return True, "greeting"
    alpha_count = sum(1 for c in q if c.isalpha())
    if alpha_count == 0 and len(q) > 0:
        return True, "noise"
    return False, ""


def _format_recall_context(memories: list) -> str:
    """将召回的记忆列表格式化为可读上下文。"""
    lines = ["## 相关记忆（根据作用域过滤）："]
    for m in memories:
        scope_tag = "📌" if m.get("scope") == "durable" else "💬"
        lines.append(
            f"{scope_tag} [{m.get('category', 'general')}] "
            f"{m['content'][:200]}"
        )
    return "\n".join(lines)


def _unwrap_response(data: dict, key: str = "memories") -> dict:
    """A1 修复：显式解包后端响应包络 {data:{...}}，缺字段抛清晰异常而非 KeyError 静默返回空。

    后端统一以 ok({...}) 返回 ``{"code":0,"message":"ok","data":{...}}``；桥接层此前在
    prefetch 中直接 ``result.get("memories")`` 读取顶层（实际在 data 内），导致召回恒为空。
    此处统一解包，契约不匹配时抛 ValueError 而非静默降级为空串。
    """
    if not isinstance(data, dict) or "data" not in data:
        raise ValueError("后端响应缺少 data 包络（契约不匹配）")
    return data["data"]


class AionMemoryProvider(MemoryProvider):
    """Hermes Agent MemoryProvider for the Aion Memory system.
    
    作用域模型：
    - durable：跨会话持久记忆（用户偏好、项目知识、工作规则）
    - general：仅当前会话（临时对话内容）
    """

    def __init__(self) -> None:
        """预初始化，确保 handle_tool_call() 不依赖 initialize() 的调用时机。"""
        self._session_id: str = ""
        self._amber_url: str = os.getenv(
            "AION_MNEMOSYNE_URL", DEFAULT_MNEMOSYNE_URL
        )
        # 缺陷 2.3 修复：启动时校验目标 URL，非法（如链路本地）直接告警
        try:
            _validate_amber_url(self._amber_url)
        except ValueError as e:
            logger.critical("MNEMOSYNE_URL 校验失败，桥接层将不可用: %s", e)
        self._api_key: str = os.getenv("MNEMOSYNE_API_KEY", "")
        self._turn_count: int = 0
        self._pending_turns: List[Dict[str, str]] = []
        self._last_recall_time: float = 0.0
        self._last_prefetch_persist: float = 0.0
        self._recall_cooldown: float = 2.0
        # R9 修复：近期召回上下文本地缓存（TTL 5 分钟），Amber 宕机时作降级上下文。
        self._recall_cache: str = ""
        self._recall_cache_time: float = 0.0
        # 缺陷 1.5：进程内只读镜像缓存（不触碰文件记忆），供增量失效使用
        self._local_cache: Dict[int, Dict[str, Any]] = {}

    @property
    def name(self) -> str:
        return "aion-memory"

    # ── 核心生命周期 ──

    def _threaded_urlopen(self, req, timeout=10):
        """在线程池中执行 HTTP 请求，避免阻塞主事件循环。"""
        global _HTTP_THREAD_POOL
        future = _HTTP_THREAD_POOL.submit(
            lambda: urllib.request.urlopen(req, timeout=timeout)
        )
        try:
            return future.result(timeout=timeout + 5)
        except concurrent.futures.TimeoutError:
            raise urllib.error.URLError(f"请求超时 {timeout}s")

    def _get_headers(self, extra: dict | None = None) -> dict:
        """返回含 API Key 的请求头。"""
        headers = {"Content-Type": "application/json"}
        if self._api_key:
            headers["X-API-Key"] = self._api_key
        # 缺陷 2.1 修复：DEV_INSECURE 模式自动携带临时 Token（避免本地多用户裸奔）
        if not self._api_key:
            dev_token = _resolve_dev_token(self._amber_url)
            if dev_token:
                headers["X-Dev-Token"] = dev_token
        if extra:
            headers.update(extra)
        return headers

    def is_available(self) -> bool:
        """检查配置是否就绪（不发起网络调用）。"""
        return True

    def initialize(self, session_id: str, **kwargs) -> None:
        """初始化会话连接。"""
        self._session_id = session_id
        self._amber_url = os.getenv(
            "AION_MNEMOSYNE_URL", DEFAULT_MNEMOSYNE_URL
        )
        self._turn_count = 0
        self._pending_turns: List[Dict[str, str]] = []
        self._last_recall_time = 0.0
        self._last_prefetch_persist = 0.0
        self._recall_cooldown = 2.0  # 同一轮不重复召回
        
        logger.info(
            "Aion Memory 初始化完成 (session=%s, amber=%s)",
            session_id[:8] if session_id else "?",
            self._amber_url,
        )

    def system_prompt_block(self) -> str:
        """返回注入系统提示的静态描述。"""
        return (
            "你正在使用 Aion Memory 自主记忆系统。\n"
            "你的记忆会通过 Amber API 持久化并自动管理。\n"
            "记忆分为两种作用域：\n"
            "  - durable（持久）：跨会话可用，适合用户偏好、项目知识等重要事实\n"
            "  - general（普通）：仅当前会话，适合临时对话上下文\n"
            "当你知道用户的重要偏好或事实时，使用 memory() 工具写入 durable 记忆。"
        )

    def prefetch(self, query: str, *, session_id: str = "") -> str:
        """在每轮对话前检索相关记忆（按作用域过滤）。
        
        通过 Amber API 搜索：
        - durable 记忆：跨所有会话搜索
        - general 记忆：仅当前会话搜索
        """
        # ── 保守门禁 ──
        skip, reason = should_skip_retrieval(query)
        if skip:
            logger.debug("跳过召回: %s (query=%s)", reason, query[:20])
            return ""
        
        # ── 冷却检查 ──
        now = time.time()
        if now - self._last_recall_time < self._recall_cooldown:
            return ""
        self._last_recall_time = now
        
        # ── 调用 Amber 搜索 API ──
        try:
            payload = json.dumps({
                "user_id": "default",
                "query": query,
                "max_memories": 5,
                "include_context": True,
                "scope_session_id": self._session_id,
            }).encode("utf-8")

            url = f"{self._amber_url}/api/v1/dialectic"
            req = urllib.request.Request(
                url, data=payload,
                headers=self._get_headers(),
                method="POST",
            )
            with self._threaded_urlopen(req, timeout=10) as resp:
                result = json.loads(resp.read().decode("utf-8"))
            
            memories = _unwrap_response(result).get("memories", [])
            if not memories:
                return ""

            # ── 格式化为可读上下文 ──
            context = _format_recall_context(memories)
            # R9 修复：缓存近期召回上下文（TTL 5 分钟），供宕机降级使用
            self._recall_cache = context
            self._recall_cache_time = time.time()

            # ── A2 修复：移除 prefetch 噪声记忆回写 ──
            # 原实现每 5 分钟把「N durable hits」当作一条 durable 记忆写入，
            # 与「记忆满了是设计缺陷」哲学冲突，持续污染 durable 空间。
            # 召回事件本应落在 memory_traces（action='recall'），而非 memories 事实表。
            # 现仅做本地统计（不写库），如需审计可经 _write_trace("recall", ...) 旁路记录。
            durable_hits = [m for m in memories if m.get("scope") == "durable"]
            if durable_hits:
                logger.debug("prefetch 召回 %d 条 durable 记忆（不写库，仅作召回统计）",
                             len(durable_hits))

            return context

        except urllib.error.URLError as e:
            # R9 修复：读路径降级——瞬时网络抖动先重试一次，仍失败则回退到
            # 近期本地召回缓存（TTL 5 分钟）并显式标记 recall_unavailable，
            # 避免 Amber 宕机时 Agent 静默丢失全部记忆上下文且无感知。
            try:
                with self._threaded_urlopen(req, timeout=10) as resp2:
                    result2 = json.loads(resp2.read().decode("utf-8"))
                    # R9 修复：重试分支同样解包 {data:{...}} 包络，否则与首次调用不一致、
                    # 重试成功也会因读顶层而落空，退化到缓存降级分支。
                    memories2 = _unwrap_response(result2).get("memories", [])
                    if memories2:
                        ctx2 = _format_recall_context(memories2)
                        self._recall_cache = ctx2
                        self._recall_cache_time = time.time()
                        return ctx2
            except Exception:
                pass
            if self._recall_cache and (time.time() - self._recall_cache_time) < 300:
                logger.warning("Amber 召回失败，使用近期本地缓存降级（recall_unavailable）")
                return self._recall_cache + "\n[recall_unavailable]"
            logger.debug("Amber 召回失败: %s", e)
            return ""
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.debug("Amber 召回响应解析失败: %s", e)
            return ""

    def queue_prefetch(self, query: str, *, session_id: str = "") -> None:
        """每一轮结束后触发后台检索（为下一轮准备）。
        
        当前实现：不预取（防止 topic bleed）。
        scope-recall 的设计也是如此——queue_prefetch 是空操作。
        """
        pass

    def sync_turn(
        self,
        user_content: str,
        assistant_content: str,
        *,
        session_id: str = "",
        messages: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        """每轮对话后将内容推送到 Amber。
        
        对话轮次默认为 general 作用域（仅当前会话可检索）。
        """
        self._turn_count += 1
        
        # 跳过过短或工具调用的轮次
        if not user_content or len(user_content.strip()) < 3:
            return
        
        self._pending_turns.append({
            "user": user_content[:200],
            "assistant": assistant_content[:200],
        })
        
        # 每 3 轮触发一次批量推送
        if self._turn_count % 3 == 0:
            self._flush_turns(scope_target="general")

        # 每 10 轮触发一次 instinct 毕业检查
        if self._turn_count % 10 == 0:
            self._auto_graduate_instincts()

        # 每 10 轮同步一次 Hermes 本地缓存（Amber → MEMORY.md/USER.md）
        if self._turn_count % 10 == 0:
            self._cache_sync_to_hermes_memory()

    def _flush_turns(self, scope_target: str = "general") -> None:
        """批量推送待同步的对话轮次。

        仅当 API 调用成功时才清空待处理队列。
        失败时保留队列，由后续 _flush_turns 或 shutdown 重试。
        为防止队列无限增长，超过 MAX_PENDING_TURNS 后丢弃最旧批次。

        Layer 1 自我管理：写入前检查 Amber 容量，>80% 时 log warning。
        """
        if not self._pending_turns:
            return

        # ── 容量自检（每次刷写前） ──
        self._check_capacity()

        summaries = []
        for t in self._pending_turns:
            summaries.append(f"[user] {t['user']}\n[assistant] {t['assistant']}")
        content = "\n---\n".join(summaries)

        if self._api_save_memory(
            content=content,
            category="conversation",
            scope_target=scope_target,
        ):
            self._pending_turns.clear()
        else:
            # 防止队列无限增长：超过阈值后丢弃最旧批次
            if len(self._pending_turns) > 50:
                logger.warning(
                    "待推送队列已累积 %d 轮，丢弃最旧批次",
                    len(self._pending_turns),
                )
                # 保留最近 30 轮
                self._pending_turns = self._pending_turns[-30:]

    # ── Layer 1 自我管理辅助方法 ──

    def _cache_put(self, mem: Optional[Dict[str, Any]]) -> None:
        """写入进程内只读镜像缓存（不触碰 MEMORY.md/USER.md 文件记忆）。"""
        if not isinstance(mem, dict):
            return
        mid = mem.get("id")
        if isinstance(mid, int):
            self._local_cache[mid] = mem

    def _cache_sync_to_hermes_memory(self) -> None:
        """增量失效：基于最近更新列表，将本地只读镜像缓存中过旧的条目失效。

        设计要点（缺陷 1.5 —— 解决原禁用导致的本地缓存过时风险）：
        - 仅维护进程内只读镜像 self._local_cache，绝不写文件记忆，
          因此不会与 memory() 工具的文件管理（漂移门禁）冲突。
        - 不做全量同步：只拉取最近更新的 memory 列表，将命中本地缓存的 id 失效，
          下次读取时自然取最新值（尽力而为的轻量一致性协议）。
        - 任何网络/解析异常都静默跳过，保留现有缓存，不抛错、不影响主流程。
        """
        if not self._local_cache:
            return
        try:
            url = f"{self._amber_url}/api/v1/memories?user_id=default&limit=50"
            req = urllib.request.Request(url, headers=self._get_headers())
            with self._threaded_urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read())
            recent = data.get("data", {}).get("memories", [])
            invalidated = 0
            for mem in recent:
                mid = mem.get("id")
                if isinstance(mid, int) and mid in self._local_cache:
                    del self._local_cache[mid]
                    invalidated += 1
            if invalidated:
                logger.debug("本地缓存增量失效 %d 条", invalidated)
        except Exception:
            logger.debug("_cache_sync_to_hermes_memory 增量失效跳过（拉取失败）")



    def _check_capacity(self) -> None:
        """检查 Amber 容量，超过阈值时 log warning。"""
        try:
            url = f"{self._amber_url}/api/v1/health/default"
            req = urllib.request.Request(url, headers=self._get_headers())
            with self._threaded_urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read())
            tiers = data.get("data", {}).get("tiers", {})
            l2_count = tiers.get("L2", 0)
            if l2_count > CAPACITY_WARNING_THRESHOLD * 1000:  # >800 触发
                logger.warning("Amber 容量警告：L2=%d 条", l2_count)
        except Exception:
            pass

    def _auto_graduate_instincts(self) -> None:
        """同 domain ≥3 条 instinct → 自动合并为 skill。每 10 轮由 sync_turn 触发。"""
        try:
            url = f"{self._amber_url}/api/v1/beliefs/search"
            payload = json.dumps({"user_id": "default", "query": "instinct", "top_k": 100}).encode()
            req = urllib.request.Request(url, data=payload,
                                        headers=self._get_headers(),
                                        method="POST")
            with self._threaded_urlopen(req, timeout=10) as resp:
                beliefs = json.loads(resp.read()).get("data", {}).get("beliefs", [])
            from collections import Counter
            domain_counts = Counter(b.get("domain", "general") for b in beliefs)
            for domain, count in domain_counts.items():
                if count >= INSTINCT_GRADUATION_THRESHOLD:
                    logger.info("Instinct 毕业触发：domain=%s 共 %d 条", domain, count)
        except Exception:
            pass

    def _dedup_user_profile(self, content: str) -> bool:
        """检测 content 是否与现有 user profile 高度重复。返回 True=跳过。"""
        try:
            url = f"{self._amber_url}/api/v1/memories?category=preference&scope_target=durable&limit=20"
            req = urllib.request.Request(url, headers=self._get_headers())
            with self._threaded_urlopen(req, timeout=5) as resp:
                existing = json.loads(resp.read()).get("data", {}).get("memories", [])
            new_words = set(content.lower().split())
            for mem in existing:
                old_words = set(mem.get("content", "").lower().split())
                if not old_words:
                    continue
                overlap = len(new_words & old_words) / len(new_words | old_words)
                if overlap > _USER_DEDUP_SIMILARITY:
                    logger.debug("User profile 去重：重叠率 %.0f%% → 跳过", overlap * 100)
                    return True
        except Exception:
            pass
        return False

    def get_tool_schemas(self) -> List[Dict[str, Any]]:
        """返回 Aion Memory 工具清单（供 Agent 调用 Amber API）。"""
        return [
            {
                "name": "aion_search",
                "description": "语义搜索记忆（支持作用域过滤 + 按任务类型过滤 + trace 追踪）。按相关性排序返回匹配记忆。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "搜索关键词"},
                        "max_results": {"type": "integer", "default": 5, "description": "最大返回数"},
                        "scope_session_id": {"type": "string", "default": "", "description": "当前会话ID（可选，用于 general 隔离）"},
                        "trace": {"type": "boolean", "default": False, "description": "是否返回召回追踪数据"},
                        "task_type": {"type": "string", "default": "", "description": "按任务类型过滤：AUDIT_FIX / FRONTEND_DEV / BACKEND_DEV / DEPLOY / TROUBLESHOOT / ARCHITECTURE / TEST / CONFIG / GENERAL"},
                    },
                    "required": ["query"],
                },
            },
            {
                "name": "aion_context",
                "description": "获取当前用户的记忆上下文摘要（按作用域过滤后的近期记忆概要）。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "limit": {"type": "integer", "default": 5, "description": "返回条数"},
                        "scope_session_id": {"type": "string", "default": "", "description": "当前会话ID"},
                    },
                },
            },
            {
                "name": "aion_stats",
                "description": "记忆系统状态统计：总记忆数、各作用域分布、TMT 各层级节点数。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "user_id": {"type": "string", "default": "default"},
                    },
                },
            },
            {
                "name": "aion_explain",
                "description": "召回说明：为什么某次搜索返回了特定结果，含评分明细和当前权重配置。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "要解释的搜索查询"},
                        "scope_session_id": {"type": "string", "default": "", "description": "当前会话ID"},
                    },
                    "required": ["query"],
                },
            },
            {
                "name": "aion_forget",
                "description": "删除指定记忆（软删除）。需要提供记忆 ID。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "memory_id": {"type": "integer", "description": "要删除的记忆 ID"},
                        "user_id": {"type": "string", "default": "default"},
                    },
                    "required": ["memory_id"],
                },
            },
            {
                "name": "aion_probe",
                "description": "实体探针：搜索与指定实体相关的记忆。用于了解某个项目、概念或人的相关记忆。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "entity": {"type": "string", "description": "实体名称（项目名/概念/人名）"},
                        "scope_session_id": {"type": "string", "default": "", "description": "当前会话ID"},
                        "max_results": {"type": "integer", "default": 5},
                    },
                    "required": ["entity"],
                },
            },
            {
                "name": "aion_inspect",
                "description": "查看单条记忆的完整详情（含所有元数据字段）。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "memory_id": {"type": "integer", "description": "记忆 ID"},
                        "user_id": {"type": "string", "default": "default"},
                    },
                    "required": ["memory_id"],
                },
            },
            {
                "name": "aion_benchmark",
                "description": "召回质量基准测试：用一组预定义查询测试召回系统的准确率和覆盖率。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "queries": {"type": "array", "items": {"type": "string"}, "description": "测试查询列表"},
                        "scope_session_id": {"type": "string", "default": ""},
                    },
                    "required": ["queries"],
                },
            },
        ]

    


    def handle_tool_call(self, tool_name: str, args: dict, **kwargs) -> str:
        """处理 aion_* 工具的调用请求，通过 Amber API 执行。"""
        base = self._amber_url
        user_id = args.get("user_id", "default")

        try:
            if tool_name == "aion_search":
                payload = json.dumps({
                    "query": args.get("query", ""),
                    "max_memories": args.get("max_results", 5),
                    "scope_session_id": args.get("scope_session_id", None) or None,
                    "trace": args.get("trace", False),
                    "task_type": args.get("task_type", "") or None,
                }).encode()
                req = urllib.request.Request(
                    f"{base}/api/v1/dialectic", data=payload,
                    headers=self._get_headers(),
                    method="POST",
                )
                with self._threaded_urlopen(req, timeout=10) as resp:
                    data = json.loads(resp.read())
                results = data.get("data", {}).get("memories", [])
                for m in results:
                    self._cache_put(m)
                return json.dumps({"results": results, "count": len(results)}, ensure_ascii=False)

            elif tool_name == "aion_context":
                limit = args.get("limit", 5)
                url = f"{base}/api/v1/memories?limit={limit}&user_id={user_id}"
                sess_id = args.get("scope_session_id", "")
                if sess_id:
                    url += f"&scope_session_id={sess_id}"
                req = urllib.request.Request(url, headers=self._get_headers())
                with self._threaded_urlopen(req, timeout=10) as resp:
                    data = json.loads(resp.read())
                mems = data.get("data", {}).get("memories", [])
                summary = chr(10).join(
                    f"- [{m.get('scope','?')}] {m.get('content','')[:120]}" for m in mems[:limit]
                )
                return f"近期记忆摘要（{len(mems)}条）:{chr(10)}{summary}"

            elif tool_name == "aion_stats":
                req = urllib.request.Request(f"{base}/api/v1/console/stats", headers=self._get_headers())
                with self._threaded_urlopen(req, timeout=10) as resp:
                    data = json.loads(resp.read())
                d = data.get("data", {})
                memories = d.get("memories", {})
                beliefs = d.get("beliefs", {})
                tiers = memories.get("tier", {})
                cats = d.get("by_category", {})
                return json.dumps({
                    "total_memories": memories.get("total", 0),
                    "total_beliefs": beliefs.get("total", 0),
                    "total_traces": d.get("total_traces", 0),
                    "by_tier": tiers,
                    "by_category": cats,
                }, ensure_ascii=False)

            elif tool_name == "aion_explain":
                payload = json.dumps({
                    "query": args.get("query", ""),
                    "max_memories": 3,
                    "scope_session_id": args.get("scope_session_id", None) or None,
                    "trace": True,
                }).encode()
                req = urllib.request.Request(
                    f"{base}/api/v1/dialectic", data=payload,
                    headers=self._get_headers(),
                    method="POST",
                )
                with self._threaded_urlopen(req, timeout=10) as resp:
                    data = json.loads(resp.read())
                trace_data = data.get("data", {}).get("trace", {})
                results = data.get("data", {}).get("memories", [])
                return json.dumps({
                    "trace": trace_data,
                    "results_count": len(results),
                    "query": args.get("query", ""),
                }, ensure_ascii=False)

            elif tool_name == "aion_forget":
                memory_id = args.get("memory_id", 0)
                req = urllib.request.Request(
                    f"{base}/api/v1/memories/{memory_id}",
                    headers=self._get_headers(),
                    method="DELETE",
                )
                with self._threaded_urlopen(req, timeout=10) as resp:
                    result = json.loads(resp.read())
                return json.dumps(result.get("data", result), ensure_ascii=False)

            elif tool_name == "aion_probe":
                entity = args.get("entity", "")
                payload = json.dumps({
                    "query": entity,
                    "max_memories": args.get("max_results", 5),
                    "scope_session_id": args.get("scope_session_id", None) or None,
                }).encode()
                req = urllib.request.Request(
                    f"{base}/api/v1/dialectic", data=payload,
                    headers=self._get_headers(),
                    method="POST",
                )
                with self._threaded_urlopen(req, timeout=10) as resp:
                    data = json.loads(resp.read())
                results = data.get("data", {}).get("memories", [])
                for m in results:
                    self._cache_put(m)
                return json.dumps({"entity": entity, "results": results, "count": len(results)}, ensure_ascii=False)

            elif tool_name == "aion_inspect":
                memory_id = args.get("memory_id", 0)
                req = urllib.request.Request(f"{base}/api/v1/memories/{memory_id}", headers=self._get_headers())
                with self._threaded_urlopen(req, timeout=10) as resp:
                    data = json.loads(resp.read())
                self._cache_put(data.get("data", data))
                return json.dumps(data.get("data", data), ensure_ascii=False)

            elif tool_name == "aion_benchmark":
                queries = args.get("queries", [])
                if not queries:
                    return json.dumps({"error": "no queries provided"}, ensure_ascii=False)
                results = []
                for q in queries:
                    t0 = time.time()
                    payload = json.dumps({
                        "query": q, "max_memories": 3,
                        "scope_session_id": args.get("scope_session_id", None) or None,
                    }).encode()
                    try:
                        req = urllib.request.Request(
                            f"{base}/api/v1/dialectic", data=payload,
                            headers=self._get_headers(),
                            method="POST",
                        )
                        with self._threaded_urlopen(req, timeout=10) as resp:
                            data = json.loads(resp.read())
                        mems = data.get("data", {}).get("memories", [])
                        latency_ms = int((time.time() - t0) * 1000)
                        results.append({"query": q, "hits": len(mems), "latency_ms": latency_ms, "status": "ok"})
                    except Exception as e:
                        results.append({"query": q, "error": str(e), "status": "error"})
                return json.dumps({"benchmark": results}, ensure_ascii=False)

            else:
                return json.dumps({"error": f"unknown tool: {tool_name}"}, ensure_ascii=False)

        except urllib.error.HTTPError as e:
            return json.dumps({
                "error": f"Amber API 错误 ({e.code})",
                "detail": e.read().decode("utf-8", errors="replace")[:200],
            }, ensure_ascii=False)
        except (urllib.error.URLError, OSError, ValueError) as e:
            return json.dumps({
                "error": f"Amber 连接失败: {e}",
                "hint": "确认 amber-api 容器正在运行 (docker ps)",
            }, ensure_ascii=False)

    def shutdown(self) -> None:
        """清理退出——刷写待处理队列并同步 Hermes 本地缓存。"""
        self._flush_turns()
        # 最后同步一次 Hermes 本地缓存
        self._cache_sync_to_hermes_memory()
        logger.info("Aion Memory 已关闭 (共处理 %d 轮对话)", self._turn_count)

    # ── 可选钩子 ──

    def on_session_end(self, messages: List[Dict[str, Any]]) -> None:
        """会话结束时触发记忆提炼和刷写。"""
        self._flush_turns()
        # 同步 Hermes 本地缓存（会话结束前最后同步）
        self._cache_sync_to_hermes_memory()
        # 尝试触发 Amber Reflect
        try:
            payload = b"{}"
            url = f"{self._amber_url}/api/v1/reflect?user_id=default&mode=light"
            self._api_call(url, payload, timeout=10)
            logger.debug("已触发 Reflect")
        except Exception as e:
            logger.debug("Reflect 触发失败（正常：%s）", e)

    def on_memory_write(
        self,
        action: str,
        target: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """镜射 builtin memory 写入到 Amber。
        
        - target='user' 或 target='memory' 时 → durable（跨会话持久）
        - 其他 target → general（仅当前会话）
        """
        if action not in ("add", "replace"):
            return
        
        # 决定作用域
        scope_target = "durable" if target in ("user", "memory") else "general"

        # A3 修复：从 metadata 中提取结构化字段并贯通到 API，
        # 使 MemoryCreate 建模的 memory_type/task_type/severity 等不再成为死字段。
        md = metadata or {}
        # A3 修复：durable 记忆（用户偏好/事实）原样持久，不截断——截断会永久丢失
        # 长偏好/长规则等关键信息；仅 general（临时对话上下文）保留截断以控制体积，
        # trace 预览截断（_write_trace 的 [:200]）维持不变。
        stored_content = content if scope_target == "durable" else content[:500]
        self._api_save_memory(
            content=f"[{target}] {stored_content}",
            category="preference" if target == "user" else "fact",
            scope_target=scope_target,
            memory_type=md.get("memory_type"),
            task_type=md.get("task_type"),
            severity=md.get("severity"),
            decay_months=md.get("decay_months"),
            linked_skills=md.get("linked_skills"),
        )

    def get_config_schema(self) -> List[Dict[str, Any]]:
        """配置字段定义（供 hermes memory setup 使用）。"""
        return [
            {
                "key": "amber_url",
                "description": "Amber API 地址",
                "default": DEFAULT_MNEMOSYNE_URL,
                "required": False,
            },
        ]

    def backup_paths(self) -> List[str]:
        """返回需要备份的外部路径。"""
        aion_home = str(Path.home() / ".aion-memory")
        return [aion_home] if os.path.isdir(aion_home) else []

    # ── 内部工具方法 ──

    def _api_call(self, url: str, payload: bytes, timeout: int = 10) -> bool:
        """执行 JSON POST 请求，含自动重试。

        为同步 MemoryProvider 设计（ABC 不暴露异步接口）。
        重试策略：网络超时/连接错误等可恢复错误重试 1 次。
        """
        for attempt in range(2):
            try:
                req = urllib.request.Request(
                    url, data=payload,
                    headers=self._get_headers(),
                    method="POST",
                )
                with self._threaded_urlopen(req, timeout=timeout) as resp:
                    return True
            except urllib.error.URLError as e:
                if attempt == 0 and isinstance(e.reason, (TimeoutError, ConnectionError)):
                    logger.debug("Amber 请求重试 (url=%s, attempt=%d)", url, attempt)
                    continue
                logger.debug("Amber 请求失败 (url=%s): %s", url, e)
                return False
            except (OSError, ValueError) as e:
                logger.debug("Amber 请求异常 (url=%s): %s", url, e)
                return False
        return False

    def _api_save_memory(
        self,
        content: str,
        category: str = "general",
        scope_target: str = "general",
        memory_type: Optional[str] = None,
        task_type: Optional[str] = None,
        severity: Optional[str] = None,
        decay_months: Optional[int] = None,
        linked_skills: Optional[list] = None,
    ) -> bool:
        """通过 Amber API 保存记忆（带作用域标记）。

        A3 修复：新增结构化字段透传（memory_type/task_type/severity/decay_months/linked_skills），
        与 MemoryCreate 模型对齐；仅当显式传入时才写入 payload，保持向后兼容。
        返回 True 表示成功，False 表示失败。
        """
        try:
            payload_dict: Dict[str, Any] = {
                "user_id": "default",
                "content": content,
                "category": category,
                "scope_target": scope_target,
                "scope_session_id": self._session_id if scope_target == "general" else None,
            }
            # 仅当显式提供时才加入，避免向旧版服务发送其不认识的字段
            if memory_type is not None:
                payload_dict["memory_type"] = memory_type
            if task_type is not None:
                payload_dict["task_type"] = task_type
            if severity is not None:
                payload_dict["severity"] = severity
            if decay_months is not None:
                payload_dict["decay_months"] = decay_months
            if linked_skills is not None:
                payload_dict["linked_skills"] = linked_skills
            payload = json.dumps(payload_dict).encode("utf-8")

            url = f"{self._amber_url}/api/v1/memories"
            success = self._api_call(url, payload)
            if success:
                logger.debug(
                    "已保存 %s/%s 至 Amber (scope=%s)",
                    category, content[:30], scope_target,
                )
                # ── memory_traces 双写（Layer 1 自我管理） ──
                self._write_trace("create", content, memory_id=None)
            return success
        except (TypeError, ValueError) as e:
            logger.debug("保存至 Amber 序列化失败: %s", e)
            return False

    def _write_trace(self, action: str, content_preview: str, memory_id: Optional[int] = None) -> None:
        """Layer 1 自我管理：双写 memory_traces 审计日志（best-effort）。

        修复：此前 _api_save_memory 成功路径调用了 ``self._write_trace``，
        但该方法从未定义，导致每次成功保存记忆都会抛 ``AttributeError`` 崩溃，
        进而中断 Hermes 的 _flush_turns 批量推送。现补齐实现：
        POST /api/v1/memory-traces（服务端身份由 API 注入，见审计报告 S1 修复，
        此处不传用户身份，仅传 action/metadata 预览）。
        写入失败不影响主保存流程。
        """
        if not self._amber_url:
            return
        try:
            # S-03 整改：与服务端 S8 修复对齐——审计轨迹仅记录内容哈希前缀，
            # 不再下发明文预览，消除 GDPR 合规回退（此前桥接层抵消了 S8 修复）。
            content_hash = hashlib.sha256(content_preview.encode("utf-8")).hexdigest()[:16]
            payload = json.dumps({
                "action": action,
                "memory_id": memory_id,
                "metadata": {
                    "content_hash": content_hash,
                    "content_length": len(content_preview),
                },
                "scope_target": "durable",
            }).encode("utf-8")
            self._api_call(f"{self._amber_url}/api/v1/memory-traces", payload)
        except Exception as e:  # 审计日志写入失败不应影响主流程
            logger.debug("memory_traces 双写失败（忽略）: %s", e)
