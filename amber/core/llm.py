"""
Amber v5.0 — LLM 路由引擎（异步版）
支持任何 OpenAI 兼容 API 的分级调度 + 自动升降级
"""
import json
import os
import re
import time
import hashlib
import asyncio
from collections import OrderedDict
from typing import Dict, Optional, List, Tuple
import httpx

from config import (LLM_API_KEY, LLM_BASE_URL, LLM_MODEL_MINI, LLM_MODEL_LITE, LLM_MODEL_PRO)
from config import LLM_BASE_URL_PRO, LLM_API_KEY_PRO, TMT_MAX_RETRIES

TIERS = {
    1: {"model": "embedding", "type": "embedding"},
    2: {"model": LLM_MODEL_MINI, "type": "chat", "max_tokens": 500},
    3: {"model": LLM_MODEL_LITE, "type": "chat", "max_tokens": 800},
    4: {"model": LLM_MODEL_PRO, "type": "chat", "max_tokens": 1024,
        "base_url": LLM_BASE_URL_PRO, "api_key": LLM_API_KEY_PRO},
}

_cost_stats: "OrderedDict[str, dict]" = OrderedDict()
# P-04 修复：成本统计原为无界 dict。实践中它按 model_name 聚合、键集有限（≈TIERS 数量），
# 增长其实可控；但为防御「未来动态 model / base_url 组合」导致键无限增长，改为有界
# OrderedDict + LRU 淘汰，超过 MAX_COST_ENTRIES 时移除最早写入的模型统计。
MAX_COST_ENTRIES = int(os.getenv("MNEMOSYNE_MAX_COST_ENTRIES", "50"))
# 缺陷 3.4 修复：带 TTL 的 LRU 缓存，避免长期运行下的内存泄漏与命中率下降。
# 原实现为纯 dict（仅 FIFO 淘汰），过期条目无法自动失效，长期运行后缓存持续膨胀。
class TTLLRUCache:
    """带 TTL 的 LRU 缓存：写入按访问时间淘汰，过期条目在读取时自动失效（不依赖后台清理）。"""

    def __init__(self, maxsize: int = 500, ttl: float = 3600.0):
        self._cache: "OrderedDict[str, Tuple[float, object]]" = OrderedDict()
        self._maxsize = maxsize
        self._ttl = ttl

    def get(self, key: str):
        if key in self._cache:
            ts, val = self._cache[key]
            if time.time() - ts < self._ttl:
                self._cache.move_to_end(key)
                return val
            del self._cache[key]
        return None

    def set(self, key: str, value) -> None:
        if key in self._cache:
            del self._cache[key]
        self._cache[key] = (time.time(), value)
        while len(self._cache) > self._maxsize:
            self._cache.popitem(last=False)

    def __len__(self) -> int:
        return len(self._cache)


MAX_CACHE = 500
_cache = TTLLRUCache(maxsize=MAX_CACHE, ttl=3600.0)
_embed_cache = TTLLRUCache(maxsize=MAX_CACHE, ttl=7200.0)
_SHARED_CLIENT: Optional[httpx.AsyncClient] = None

# ── 断路器（Circuit Breaker）──
CB_THRESHOLD = 3          # 连续失败 N 次后断开
CB_RECOVERY_SEC = 30      # 断开后等待秒数再半开测试


class CircuitBreaker:
    """协程安全的断路器：用 asyncio.Lock 保护状态转换，避免并发竞态。

    原实现使用模块级全局变量 + global 读写，在并发请求下多个协程可能同时
    读取 CLOSED→同时发起请求→同时记录失败→计数器错乱。本实现对每次状态
    转换加锁，保证原子性。
    """

    def __init__(self, failure_threshold: int = CB_THRESHOLD,
                 recovery_timeout: float = CB_RECOVERY_SEC):
        self._state = "CLOSED"
        self._failures = 0
        self._opened_at = 0.0
        self._lock = asyncio.Lock()
        self._half_open_inflight = False
        self._failure_threshold = failure_threshold
        self._recovery_timeout = recovery_timeout

    @property
    def state(self) -> str:
        return self._state

    @property
    def failures(self) -> int:
        return self._failures

    async def allow_request(self) -> bool:
        async with self._lock:
            if self._state == "CLOSED":
                return True
            if self._state == "OPEN":
                if time.time() - self._opened_at > self._recovery_timeout:
                    if not self._half_open_inflight:
                        self._state = "HALF_OPEN"
                        self._half_open_inflight = True
                        return True  # 仅放行一个探测请求
                return False
            # HALF_OPEN：探测进行中，其余请求拒绝，避免恢复中的服务被再次压垮导致震荡
            if not self._half_open_inflight:
                self._half_open_inflight = True
                return True
            return False

    async def record_success(self) -> None:
        async with self._lock:
            self._failures = 0
            self._state = "CLOSED"
            self._half_open_inflight = False

    async def record_failure(self) -> None:
        async with self._lock:
            self._failures += 1
            self._half_open_inflight = False
            if self._state == "HALF_OPEN" or self._failures >= self._failure_threshold:
                self._state = "OPEN"
                self._opened_at = time.time()

    def state_snapshot(self) -> dict:
        remaining = (max(0, self._recovery_timeout - (time.time() - self._opened_at))
                     if self._state == "OPEN" else 0)
        return {
            "state": self._state,
            "consecutive_failures": self._failures,
            "threshold": self._failure_threshold,
            "recovery_remaining_sec": round(remaining, 1),
        }


# 全局断路器实例（协程安全）
cb = CircuitBreaker()
# R4 修复：按模型 tier 分实例的断路器映射。
# 全局单断路器会导致 PRO tier 失败连带阻断 MINI/LITE 的调用（误杀）。
# 拆分后各 tier 独立熔断/恢复，PRO 抖动不再影响低 tier 的可用性。
cb_by_tier: Dict[int, CircuitBreaker] = {
    2: CircuitBreaker(),  # MINI
    3: CircuitBreaker(),  # LITE
    4: CircuitBreaker(),  # PRO
}


def _breaker_for(tier: int) -> "CircuitBreaker":
    return cb_by_tier.get(tier, cb)

# 模型单价（每 1K token，单位：元）
MODEL_PRICES = {
    "deepseek-chat": {"input": 0.001, "output": 0.002},
    "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
}


def get_client() -> httpx.AsyncClient:
    global _SHARED_CLIENT
    if _SHARED_CLIENT is None or _SHARED_CLIENT.is_closed:
        _SHARED_CLIENT = httpx.AsyncClient(timeout=60.0)
    return _SHARED_CLIENT


async def _call_api_async(messages: list, model: str, max_tokens: int = 500,
                          response_format: Optional[dict] = None, temperature: float = 0.3,
                          base_url: str = None, api_key: str = None) -> dict:
    url = f"{base_url or LLM_BASE_URL}/chat/completions"
    key = api_key or LLM_API_KEY
    payload = {"model": model, "messages": messages, "max_tokens": max_tokens, "temperature": temperature}
    if response_format:
        payload["response_format"] = response_format
    client = get_client()
    resp = await client.post(url, json=payload,
        headers={'Content-Type': 'application/json', 'Authorization': f'Bearer {key}'})
    resp.raise_for_status()
    data = resp.json()
    tokens = data.get('usage', {}).get('total_tokens', 0)
    prices = MODEL_PRICES.get(model, {"input": 0.001, "output": 0.002})
    cost = (tokens / 1000) * prices["output"]
    return {"content": data['choices'][0]['message']['content'], "tokens": tokens, "model": model, "cost": cost}


async def call_llm(prompt: str, tier: int = 3, json_mode: bool = False,
                   temperature: float = 0.3, no_cache: bool = False,
                   system: str | None = None) -> dict:
    # A-02 修复：支持独立的 system 指令消息。将「任务指令/安全护栏」放入 system 角色，
    # 将「不可信的用户记忆数据」放入 user 角色，实现结构性隔离——模型对 system 与 user
    # 的信任级别不同，可显著降低记忆原文里的注入语句劫持蒸馏行为的风险。
    # ── 断路器检查（协程安全，R4：按 tier 隔离）──
    breaker = _breaker_for(tier)
    if not await breaker.allow_request():
        return {"content": "", "tokens": 0, "model": "", "tier": 0,
                "cache_hit": False, "latency_ms": 0, "upgraded": False,
                "error": "circuit_breaker_open", "cost": 0}
    if breaker.state == "HALF_OPEN":
        import logging
        logging.getLogger("amber.llm").warning("断路器半开 — 允许测试请求")
    
    _sys_key = hashlib.sha256((system or "").encode()).hexdigest()[:8]
    cache_key = f"t{tier}:j{json_mode}:t{temperature}:s{_sys_key}:{hashlib.sha256(prompt.encode()).hexdigest()[:16]}"
    if not no_cache:
        cached = _cache.get(cache_key)
        if cached is not None:
            result = cached.copy()
            result["cache_hit"] = True
            return result
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    fmt = {"type": "json_object"} if json_mode else None
    current_tier, last_error = tier, None
    for _ in range(TMT_MAX_RETRIES):
        tinfo = TIERS.get(current_tier, TIERS[3])
        # R4：使用当前尝试 tier 对应的断路器
        breaker = _breaker_for(current_tier)
        try:
            t0 = time.time()
            result = await _call_api_async(messages, tinfo["model"], tinfo.get("max_tokens", 800),
                                           response_format=fmt, temperature=temperature,
                                           base_url=tinfo.get("base_url"), api_key=tinfo.get("api_key"))
            elapsed = time.time() - t0
            if json_mode:
                try:
                    content = result["content"]
                    # R3 修复：用贪心正则抽取 JSON 对象并显式校验。
                    # 原写法 ``m.group() if m and json.loads(m.group()) or True else content``
                    # 中 ``or True`` 使条件恒真、且 ``else content`` 分支永不可达，
                    # 一旦模型返回非 JSON 文本会被静默当作内容进入蒸馏。
                    # 现改为：未匹配或非合法 JSON → 抛异常触发 tier 升级/降级兜底。
                    m = re.search(r'\{.*\}', content, re.DOTALL)
                    if not m:
                        raise json.JSONDecodeError("no json object found", content, 0)
                    parsed = json.loads(m.group())  # 校验合法性
                    # 规范化：统一序列化为合法 JSON 字符串，下游无需再次容错
                    result["content"] = json.dumps(parsed, ensure_ascii=False)
                except json.JSONDecodeError:
                    if current_tier < 4:
                        current_tier += 1
                        continue
                    result["content"] = "{}"
            cost = result.get("cost", 0)
            final = {"content": result["content"], "tokens": result["tokens"], "model": tinfo["model"],
                     "tier": current_tier, "cache_hit": False, "latency_ms": round(elapsed*1000), "upgraded": current_tier>tier,
                     "cost": cost}
            # 累计成本统计（P-04：有界 LRU）
            model_name = tinfo["model"]
            if model_name not in _cost_stats:
                _cost_stats[model_name] = {"calls": 0, "tokens": 0, "cost": 0.0}
                # 超出上限时淘汰最早写入的模型统计（FIFO/LRU）
                while len(_cost_stats) > MAX_COST_ENTRIES:
                    _cost_stats.popitem(last=False)
            else:
                _cost_stats.move_to_end(model_name)  # 命中即刷新为最近使用
            _cost_stats[model_name]["calls"] += 1
            _cost_stats[model_name]["tokens"] += result["tokens"]
            _cost_stats[model_name]["cost"] += cost
            _cache.set(cache_key, final)
            # 成功 → 重置断路器
            await breaker.record_success()
            return final
        except Exception as e:
            last_error = e
            await breaker.record_failure()
            if breaker.state == "OPEN":
                import logging
                logging.getLogger("amber.llm").error(
                    f"断路器跳闸：连续 {breaker.failures} 次失败，断开 {CB_RECOVERY_SEC}s")
            if current_tier < 4:
                current_tier += 1
            else:
                break
    # 错误信息脱敏：仅返回类型，不暴露架构细节
    err_type = type(last_error).__name__ if last_error else "unknown"
    return {"content": "", "tokens": 0, "model": "", "tier": 0,
            "cache_hit": False, "latency_ms": 0, "upgraded": False,
            "error": err_type, "cost": 0}


async def call_llm_json(prompt: str, tier: int = 3, system: str | None = None,
                        temperature: float = 0.3) -> dict:
    return await call_llm(prompt, tier=tier, json_mode=True, system=system,
                          temperature=temperature)


async def call_llm_fast(prompt: str) -> dict:
    return await call_llm(prompt, tier=2)


def get_cost_stats() -> dict:
    total = sum(s["cost"] for s in _cost_stats.values())
    return {"by_tier": _cost_stats, "total_cost": round(total, 4)}


def get_cache_stats() -> dict:
    return {"llm_cache_size": len(_cache), "llm_cache_max": MAX_CACHE}


def get_embed_cached(text: str) -> Optional[List[float]]:
    return _embed_cache.get(text)


def set_embed_cached(text: str, embedding: List[float]) -> None:
    _embed_cache.set(text, embedding)


def get_circuit_breaker_state() -> dict:
    """返回断路器当前状态（R4：含各 tier 独立实例 + 默认实例快照）"""
    return {
        "default": cb.state_snapshot(),
        "by_tier": {t: b.state_snapshot() for t, b in sorted(cb_by_tier.items())},
    }
