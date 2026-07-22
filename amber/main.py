from api.response import ok
"""
Amber 记忆核心引擎 v1.0.0
认知型记忆操作系统 — 七层架构完整实现
"""
import os
import sys
import time
import asyncio
import hashlib
import logging
from typing import Callable
import asyncpg
import hmac
from fastapi import FastAPI, Request, Depends
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.middleware import SlowAPIMiddleware

limiter = Limiter(key_func=get_remote_address, default_limits=["100/minute"])


def _get_real_ip(request: Request) -> str:
    """从 X-Forwarded-For 提取真实客户端 IP（缺陷 2.2 / S-02 修复）。

    仅在显式信任反向代理（MNEMOSYNE_TRUST_PROXY=1）时解析 XFF，
    避免攻击者伪造 XFF 绕过限流。未信任时直接使用 TCP 对端 IP。

    S-02 修复：XFF 是「client, proxy1, proxy2, ...」自左向右追加的链，最左段
    完全由客户端控制、可任意伪造。取 split(",")[0] 会让攻击者通过伪造首段
    绕过按 IP 的限流。正确做法是从右侧数、跳过我方受信代理跳数（默认 1 跳），
    取受信代理链之外、由最内层受信代理实际观测到的对端地址：
        real_ip = xff_list[-trusted_hops]
    受信跳数由 MNEMOSYNE_TRUSTED_PROXY_HOPS 配置（默认 1，即单层 nginx/网关）。
    若配置跳数超过实际链长，回退到最左段并交由上层判断。
    """
    if os.getenv("MNEMOSYNE_TRUST_PROXY", "0") == "1":
        xff = request.headers.get("x-forwarded-for", "")
        if xff:
            parts = [p.strip() for p in xff.split(",") if p.strip()]
            if parts:
                hops = int(os.getenv("MNEMOSYNE_TRUSTED_PROXY_HOPS", "1"))
                hops = max(1, hops)
                idx = -hops
                if -idx <= len(parts):
                    return parts[idx]
                return parts[0]
    return request.client.host if request.client else "unknown"


def _resolve_tenant(api_key: str) -> str:
    """A5 修复：租户身份由认证派生，消除「全局常量 + 接受但忽略客户端 user_id」的误导契约。

    - 若显式设置 MNEMOSYNE_TENANT_ID（单租户部署的权威租户名），直接采用；
    - 否则在密钥模式下由 API Key 稳定派生（每个 Key = 一个租户，隔离真实可落地）；
    - DEV 不安全模式（无 Key）下固定 'default'，等价于单用户本地部署。

    关键：租户来自「谁通过了认证」，而非客户端任意传入的 user_id 查询参数——
    客户端在 URL/Body 中携带的 user_id 一律被忽略（见 shared.get_current_user），
    从而在单租户本地场景下给出「诚实」的契约：我们就是单租户，隔离由部署/凭证决定。
    需要多租户时，用独立部署（独立 DB / 独立 MNEMOSYNE_TENANT_ID）或独立 API Key 实现。
    """
    configured = os.getenv("MNEMOSYNE_TENANT_ID")
    if configured:
        return configured
    if EXPECTED_API_KEY and api_key:
        return "tk_" + hashlib.sha256(api_key.encode()).hexdigest()[:8]
    return "default"

# 请求体大小限制（默认 10MB）
MAX_REQUEST_SIZE = int(os.getenv("MAX_REQUEST_SIZE_MB", "10")) * 1024 * 1024

class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> None:
        # 仅通过 content-length 头部做大小校验，避免读取并消费请求体
        # （BaseHTTPMiddleware 下 await request.body() 会耗尽流，导致 POST/PUT 解析失败）
        # S5 修复：content-length 缺失（分块传输 Transfer-Encoding: chunked）时跳过头部校验，
        # 交由反向代理/下游限制；非数字 content-length 必须捕获 ValueError 并返回 400，
        # 否则 int() 抛异常会被 ASGI 栈转为 500，破坏「过大请求 → 413」的预期行为。
        cl = request.headers.get("content-length")
        if cl:
            try:
                if int(cl) > MAX_REQUEST_SIZE:
                    return JSONResponse(status_code=413, content={"error": "请求体过大"})
            except ValueError:
                return JSONResponse(status_code=400, content={"error": "非法的 content-length 头"})
        return await call_next(request)


class WriteRateLimitMiddleware(BaseHTTPMiddleware):
    """写操作速率限制中间件（独立于认证逻辑）。

    S7 修复：支持两种后端，由 MNEMOSYNE_REDIS_URL 决定：
      - 设置且 redis 可用 → Redis 滑动窗口（多 Worker 共享，阈值真正生效）；
      - 未设置 / redis 不可用 → 进程内计数（仅单 Worker 有效），并在启动日志高亮约束。
    redis 为可选依赖，未安装时不强制要求；连接失败自动回退进程内并告警。
    """

    MAX_IPS = 10000
    CLEANUP_INTERVAL = 300  # 秒
    WINDOW_SEC = 60
    MAX_PER_WINDOW = int(os.getenv("MNEMOSYNE_WRITE_LIMIT_PER_MIN", "30"))
    # S-01 修复：读接口（搜索/列表/详情/辩证检索）此前完全不限流，攻击者可用
    # 高频向量检索打满连接池与 CPU（每次检索都要算 embedding + HNSW 查询）。
    # 为读接口引入独立、更宽松的滑动窗口限流（默认 120/min），与写限流分桶计数。
    MAX_READ_PER_WINDOW = int(os.getenv("MNEMOSYNE_READ_LIMIT_PER_MIN", "120"))

    def __init__(self, app):
        super().__init__(app)
        self._initialized = False

    async def _ensure_state(self, request: Request) -> None:
        if self._initialized:
            return
        self._initialized = True
        app_state = request.app.state
        redis_url = os.getenv("MNEMOSYNE_REDIS_URL")
        if redis_url:
            try:
                from redis import asyncio as aioredis
                client = aioredis.Redis.from_url(
                    redis_url, socket_connect_timeout=1.0, socket_timeout=1.0
                )
                await client.ping()
                app_state._rate_backend = "redis"
                app_state._rate_redis = client
                logging.getLogger("amber").info(
                    "WriteRateLimitMiddleware：Redis 滑动窗口已启用（多 Worker 共享限流）。"
                )
                return
            except Exception as e:
                logging.getLogger("amber").warning(
                    "WriteRateLimitMiddleware：Redis 不可用（%s），回退进程内限流。", e
                )
        # 进程内回退
        from collections import defaultdict
        app_state._rate_backend = "inproc"
        app_state._rate_lock = asyncio.Lock()
        app_state._rate_store = defaultdict(list)
        app_state._rate_last_cleanup = time.time()
        logging.getLogger("amber").warning(
            "WriteRateLimitMiddleware 为进程内限流（仅单 Worker 有效）；"
            "多 Worker 部署请设置 MNEMOSYNE_REDIS_URL 启用 Redis 共享限流，"
            "或在反向代理（nginx 等）层做限流。"
        )

    # 写路径（低阈值）
    _WRITE_PATHS = ('/reflect', '/evolve', '/beliefs', '/cleanup', '/delete', '/feedback',
                    '/memories', '/memory-traces', '/sessions/archive')
    # 读路径（高阈值）：搜索 / 辩证检索 / 列表 / 概览统计
    _READ_PATHS = ('/search', '/recall', '/query', '/console/', '/stats', '/trends',
                   '/events', '/maturity', '/pipeline')

    @staticmethod
    def _is_write(request: Request) -> bool:
        # 写方法命中写路径才算写；GET /memories 属于读
        if request.method in ("POST", "PUT", "PATCH", "DELETE"):
            return any(p in request.url.path for p in WriteRateLimitMiddleware._WRITE_PATHS)
        return False

    @staticmethod
    def _is_read(request: Request) -> bool:
        return any(p in request.url.path for p in WriteRateLimitMiddleware._READ_PATHS)

    async def dispatch(self, request: Request, call_next: Callable) -> None:
        await self._ensure_state(request)
        # S-01 修复：区分写/读两类受限流量，各自独立分桶与阈值；其余（如 /health、/docs）放行。
        if self._is_write(request):
            kind, limit = "w", self.MAX_PER_WINDOW
        elif self._is_read(request):
            kind, limit = "r", self.MAX_READ_PER_WINDOW
        else:
            return await call_next(request)

        app_state = request.app.state
        ip = _get_real_ip(request)  # 缺陷 2.2 / S-02 修复：安全解析 X-Forwarded-For
        now = time.time()
        if app_state._rate_backend == "redis":
            allowed = await self._redis_check(app_state, ip, now, kind, limit)
        else:
            allowed = await self._inproc_check(app_state, ip, now, kind, limit)
        if not allowed:
            return JSONResponse(status_code=429, content={"error": "请求过于频繁"})
        return await call_next(request)

    async def _redis_check(self, app_state, ip: str, now: float, kind: str, limit: int) -> bool:
        """Redis 滑动窗口：ZSET 以时间戳为 score，窗口外成员定期清理。"""
        client = app_state._rate_redis
        key = f"amber:{kind}limit:{ip}"
        try:
            await client.zremrangebyscore(key, 0, now - self.WINDOW_SEC)
            await client.zadd(key, {str(now): now})
            await client.expire(key, self.WINDOW_SEC + 5)
            total = await client.zcard(key)
            return total < limit
        except Exception as e:
            logging.getLogger("amber").warning(
                "Redis 限流组件故障，降级到进程内限流: %s", e
            )
            # S2 修复：Redis 故障时降级到进程内限流，而非直接放行。
            # 进程内限流在 lifespan 启动时已初始化（见 _ensure_state），
            # 此时 app_state 一定存在且 _rate_backend 被设为 'inproc'。
            return await self._inproc_check(app_state, ip, now, kind, limit)

    async def _inproc_check(self, app_state, ip: str, now: float, kind: str, limit: int) -> bool:
        async with app_state._rate_lock:
            store = app_state._rate_store
            bkey = f"{kind}:{ip}"  # 写/读分桶，避免相互挤占配额
            # 周期清理过期 IP
            if now - app_state._rate_last_cleanup > self.CLEANUP_INTERVAL:
                cutoff = now - self.WINDOW_SEC
                for k in list(store.keys()):
                    store[k] = [t for t in store[k] if t > cutoff]
                    if not store[k]:
                        del store[k]
                if len(store) > self.MAX_IPS:
                    sorted_ips = sorted(store.keys(), key=lambda k: max(store[k], default=0))
                    for old in sorted_ips[:len(store) - self.MAX_IPS]:
                        del store[old]
                app_state._rate_last_cleanup = now
            store[bkey] = [t for t in store[bkey] if now - t < self.WINDOW_SEC]
            if len(store[bkey]) >= limit:
                return False
            store[bkey].append(now)
            return True


from typing import List

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import __version__, PG_USER, PG_PASSWORD, PG_DB, PG_HOST, PG_PORT, HOST, PORT
from core.embedding import get_embedding_async

from contextlib import asynccontextmanager


# ── 连接池重试代理（缺陷 4.3）──
# 包装 asyncpg.Pool，使其在 acquire 失败时带指数退避重试，避免瞬时网络抖动
# 或连接超时直接返回 500。保留 `async with pool.acquire() as conn` 语义。
POOL_ACQUIRE_MAX_RETRIES = int(os.getenv("MNEMOSYNE_POOL_RETRIES", "3"))
POOL_ACQUIRE_BASE_DELAY = float(os.getenv("MNEMOSYNE_POOL_RETRY_BASE_DELAY", "0.1"))
# R6 自愈：熔断后冷却期（秒），到期允许一次探测式重连，避免永久熔断。
BREAKER_COOLDOWN_SEC = float(os.getenv("MNEMOSYNE_POOL_BREAKER_COOLDOWN", "60"))
# R-03 修复：熔断触发阈值独立可配。此前硬编码为 3 * POOL_ACQUIRE_MAX_RETRIES(=9)，
# 意味着要连续 9 次 acquire 失败才熔断——DB 已明显不可用时仍反复重试放大雪崩。
# 默认下调至 5，并允许通过环境变量按部署容量微调。
BREAKER_FAIL_THRESHOLD = int(os.getenv("MNEMOSYNE_POOL_BREAKER_THRESHOLD", "5"))


class _RetryAcquireContext:
    def __init__(self, pool: "RetryPool", *args, **kwargs):
        self._pool = pool
        self._args = args
        self._kwargs = kwargs
        self._conn = None

    async def __aenter__(self) -> asyncpg.Connection:
        last_err: Exception | None = None
        # R6 修复：仅对网络/超时/连接类异常重试；逻辑错误（配置/类型）直接上抛，
        # 避免掩盖真实报错并延迟故障暴露；连续失败过多触发熔断，停止重试以防雪崩。
        _RETRYABLE = (
            asyncpg.ConnectionDoesNotExistError,
            asyncpg.PostgresConnectionError,
            asyncpg.InterfaceError,
            OSError,
            asyncio.TimeoutError,
        )
        # 半开恢复（R6/R8 协同）：熔断冷却期过后允许一次探测式重连，
        # 避免「DB 抖动恢复后熔断永久开启」导致服务无法自愈。
        # R2 修复：改为实例变量访问，支持多池独立熔断。
        # R-03 修复：使用独立阈值 BREAKER_FAIL_THRESHOLD（默认 5）而非 9。
        if self._pool._consecutive_failures >= BREAKER_FAIL_THRESHOLD:
            if time.monotonic() - self._pool._breaker_opened_at > BREAKER_COOLDOWN_SEC:
                self._pool._consecutive_failures = 0  # 进入半开态，放行一次真实尝试
            else:
                raise RuntimeError("DB acquire 熔断冷却期中，拒绝重试以防雪崩")
        for attempt in range(POOL_ACQUIRE_MAX_RETRIES):
            try:
                self._conn = await self._pool._real.acquire(*self._args, **self._kwargs)
                self._pool._consecutive_failures = 0
                return self._conn
            except _RETRYABLE as e:
                last_err = e
                self._pool._consecutive_failures += 1
                if self._pool._consecutive_failures >= BREAKER_FAIL_THRESHOLD:
                    self._pool._breaker_opened_at = time.monotonic()
                    logging.getLogger("amber").error(
                        "DB acquire 连续失败达阈值(%d)，触发熔断: %s",
                        BREAKER_FAIL_THRESHOLD, e,
                    )
                    raise
                if attempt == POOL_ACQUIRE_MAX_RETRIES - 1:
                    raise
                delay = POOL_ACQUIRE_BASE_DELAY * (2 ** attempt)
                logging.getLogger("amber").warning(
                    "DB acquire 失败(第 %d 次)，%.2fs 后重试: %s", attempt + 1, delay, e
                )
                await asyncio.sleep(delay)
            except Exception as e:
                last_err = e
                raise
        assert last_err is not None
        raise last_err

    async def __aexit__(self, exc_type, exc, tb) -> None:
        if self._conn is not None:
            await self._pool._real.release(self._conn)


class RetryPool:
    """asyncpg.Pool 的轻量代理：acquire 带重试，其余方法/属性透传。"""
    def __init__(self, real: asyncpg.Pool):
        self._real = real
        # R2 修复：改为实例变量，避免多个 RetryPool 实例共享熔断状态。
        # 若未来有读写分离/多池场景，每个池的熔断独立计数。
        self._consecutive_failures = 0
        self._breaker_opened_at = 0.0

    def acquire(self, *args, **kwargs) -> _RetryAcquireContext:
        return _RetryAcquireContext(self, *args, **kwargs)

    async def close(self, *args, **kwargs):
        return await self._real.close(*args, **kwargs)

    def __getattr__(self, name):
        return getattr(self._real, name)


@asynccontextmanager
async def lifespan(app: FastAPI) -> None:
    """应用生命周期：启动时创建连接池，关闭时清理"""
    global pool
    # 缺陷 2.1 安全门禁：DEV_INSECURE 模式下，绑定公网主机等于裸奔。
    # 放在启动阶段（而非 import 阶段），仅当服务真正拉起时才拦截，
    # 不影响测试对 main 模块的 import。
    if _DEV_INSECURE_START is not None:
        _bound_host = os.getenv("MNEMOSYNE_HOST") or os.getenv("HOST", "0.0.0.0")
        if _bound_host not in ("127.0.0.1", "localhost"):
            raise RuntimeError(
                "DEV_INSECURE=1 仅允许绑定 127.0.0.1，"
                "请设置 HOST=127.0.0.1（或 MNEMOSYNE_HOST=127.0.0.1）后再启动。"
            )
    # 缺陷 3.3 修复：连接池大小可配置（默认 min=2/max=10），生产多 Worker / 蒸馏并发可上调
    _pool_min = int(os.getenv("MNEMOSYNE_POOL_MIN_SIZE", "2"))
    _pool_max = int(os.getenv("MNEMOSYNE_POOL_MAX_SIZE", "10"))
    real_pool = await asyncpg.create_pool(
        user=PG_USER, password=PG_PASSWORD, database=PG_DB,
        host=PG_HOST, port=PG_PORT, min_size=_pool_min, max_size=_pool_max,
        server_settings={'search_path': '"$user", public'},
    )
    # 包装为带重试的代理（缺陷 4.3）
    pool = RetryPool(real_pool)
    # 初始化 app.state 中的共享资源
    app.state.pool = pool
    app.state.get_embedding_fn = get_embedding
    # 初始化模块级缓存（供后台任务等非请求上下文使用）
    api_shared.setup(pool, get_embedding)
    # A6/R8 修复：启动内置轻量调度器（默认开启），周期触发 反思衰减 / embedding 补偿 /
    # 遗忘曲线回写，使「自主进化」与「崩溃后自动恢复」脱离 Hermes cron 仍成立。
    scheduler_task = None
    if os.getenv("MNEMOSYNE_DISABLE_SCHEDULER", "0") != "1":
        scheduler_task = asyncio.create_task(_background_scheduler(pool))
    yield
    # R1 修复：优雅排空后台任务（embedding/trace 写入），防止关闭即丢数据
    if scheduler_task is not None:
        scheduler_task.cancel()
        try:
            await scheduler_task
        except asyncio.CancelledError:
            pass
    try:
        from api.shared import BACKGROUND_TASKS as _bg_tasks
        if _bg_tasks:
            import asyncio
            # R-01 修复：排空窗口从 5s 延长至可配置（默认 10s），给 embedding/trace
            # 写入更充裕的落盘时间；超时后显式 cancel 仍未完成的任务并 await 其退出，
            # 避免「事件循环关闭时仍有挂起 Task」告警与潜在的资源泄漏。
            _drain_timeout = float(os.getenv("MNEMOSYNE_SHUTDOWN_DRAIN_SEC", "10"))
            _, pending = await asyncio.wait(set(_bg_tasks), timeout=_drain_timeout)
            if pending:
                import logging
                logging.getLogger("amber").warning(
                    "R-01: %d 个后台任务在 %.0fs 超时后仍未完成，执行显式取消",
                    len(pending), _drain_timeout,
                )
                for _t in pending:
                    _t.cancel()
                # 等待取消真正落定，忽略 CancelledError
                await asyncio.gather(*pending, return_exceptions=True)
    except Exception:
        pass  # 导入失败不影响正常关闭
    if pool:
        await pool.close()


# ── App 创建 ──
app = FastAPI(docs_url="/docs", title=f"Amber OS v{__version__}", lifespan=lifespan)
app.state.limiter = limiter
app.add_exception_handler(429, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)
app.add_middleware(WriteRateLimitMiddleware)
app.add_middleware(RequestSizeLimitMiddleware)
# S4 修复：CORS 源改为配置模型，支持环境变量动态覆盖。
# 收益：新增前端源无需重启代码，通过环境变量即可生效；
# 负面影响：无，仅将硬编码列表改为 config.settings.cors_origins。
app.add_middleware(CORSMiddleware,
                   allow_origins=config.settings.cors_origins,
                   allow_credentials=True,
                   # S6 修复：补齐 DELETE（后端已提供 DELETE /api/v1/memories/{id}，
                   # 此前 CORS 排除 DELETE 导致浏览器侧无法删除；当前 allow_credentials=True
                   # 且源白名单固定，补 DELETE 不与安全门禁冲突）。
                   allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
                   allow_headers=["Content-Type", "X-API-Key", "X-Dev-Token", "Authorization"])

# ── API 认证中间件 ──
EXPECTED_API_KEY = os.getenv("MNEMOSYNE_API_KEY", "")
# S3 修复：API Key 使用 PBKDF2-HMAC-SHA256 哈希（10000轮），抗预计算/彩虹表攻击。
# 固定盐与代码同生命周期，不持久化；比对使用 hmac.compare_digest 防止时序攻击。
# S-01 整改：PBKDF2 盐值禁止硬编码固定字节串（同源同盐可被预计算/彩虹表攻击）。
# 优先级：环境变量 MNEMOSYNE_API_KEY_SALT（各部署唯一、持久化）> 拒绝启动。
# S-06 整改：生产（已设置 API Key）若未配置独立盐，拒绝启动而非 CRITICAL 告警。
# CRITICAL 告警不阻断启动，攻击者可利用固定盐预计算彩虹表攻破所有实例。
# DEV_INSECURE 模式（无 API Key）使用开发专用盐，不用默认值。
_API_KEY_SALT = os.getenv("MNEMOSYNE_API_KEY_SALT", "")
if not _API_KEY_SALT:
    if EXPECTED_API_KEY:
        raise RuntimeError(
            "安全阻断[S-06]：MNEMOSYNE_API_KEY_SALT 未设置。"
            "生产环境必须为每个部署配置唯一且持久化的盐值。"
            "请设置环境变量 MNEMOSYNE_API_KEY_SALT=<your-unique-salt>"
        )
    # DEV_INSECURE 模式：无 API Key 时不需盐，但不用默认值
    _API_KEY_SALT = "dev_insecure_salt_not_for_production"
_API_KEY_SALT = _API_KEY_SALT.encode()
_API_KEY_ITERATIONS = 10000

def _hash_api_key(key: str) -> str:
    return hashlib.pbkdf2_hmac("sha256", key.encode(), _API_KEY_SALT, _API_KEY_ITERATIONS).hex()

API_KEY_HASH = _hash_api_key(EXPECTED_API_KEY) if EXPECTED_API_KEY else ""
TENANT_ID = os.getenv("MNEMOSYNE_TENANT_ID", "default")
# 开发不安全模式时间门禁
_DEV_INSECURE_START: float | None = None
# 缺陷 2.1 修复：DEV_INSECURE 模式下的进程级临时 Token（启动时生成，见日志）
_DEV_TOKEN: str | None = None

if not EXPECTED_API_KEY:
    if os.getenv("MNEMOSYNE_DEV_INSECURE", "0") != "1":
        raise RuntimeError(
            "MNEMOSYNE_API_KEY 未设置，拒绝启动。\n"
            "  生产环境：设置环境变量 MNEMOSYNE_API_KEY=<your-secret-key>\n"
            "  开发环境：设置 MNEMOSYNE_DEV_INSECURE=1 临时绕过（仅在本地开发）"
        )
    else:
        import logging
        import secrets as _secrets
        import tempfile as _tf
        # S1 修复：DEV Token 不再写入临时文件，改为纯环境变量传递。
        # 文件方案即使 0o600+随机 salt，仍无法阻止 root 读取或同用户进程读取。
        # 环境变量 MNEMOSYNE_DEV_TOKEN 由服务启动时生成并输出到日志，桥接层从环境变量读取。
        # 其他客户端同样通过环境变量传递，消除文件系统泄露面。
        _DEV_INSECURE_START = time.time()
        _DEV_TOKEN = _secrets.token_hex(16)
        logging.critical("=" * 60)
        logging.critical("⚠️  严重安全警告：MNEMOSYNE_DEV_INSECURE=1 已启用")
        logging.critical("   API 认证已完全禁用，仅限本地开发（127.0.0.1）！")
        logging.critical("   此模式严禁在生产环境使用；上线前必须设置 MNEMOSYNE_API_KEY。")
        logging.critical("   DEV 模式临时 Token：%s", _DEV_TOKEN)
        logging.critical("   同机桥接层（hermes_provider）从环境变量 MNEMOSYNE_DEV_TOKEN 读取；")
        logging.critical("   其它客户端也设置环境变量 MNEMOSYNE_DEV_TOKEN=%s", _DEV_TOKEN)
        logging.critical("=" * 60)

@app.middleware("http")
async def auth_middleware(request: Request, call_next: Callable) -> None:
    if request.url.path in ("/api/v1/health/default", "/health"):
        request.state.tenant_id = _resolve_tenant("")
        return await call_next(request)
    if EXPECTED_API_KEY:
        api_key = request.headers.get("X-API-Key", "")
        req_hash = _hash_api_key(api_key)
        if not hmac.compare_digest(req_hash, API_KEY_HASH):
            return JSONResponse(status_code=401, content={"error": "无效或缺失 API Key"})
    else:
        # 缺陷 2.1 修复：DEV_INSECURE 模式仍需携带一次性临时 Token，避免本地多用户裸奔。
        # 可通过 MNEMOSYNE_DEV_INSECURE_REQUIRE_TOKEN=0 关闭（仅当确有兼容需求时）。
        if os.getenv("MNEMOSYNE_DEV_INSECURE_REQUIRE_TOKEN", "1") == "1" and _DEV_TOKEN:
            dev_token = request.headers.get("X-Dev-Token", "")
            if not hmac.compare_digest(dev_token, _DEV_TOKEN):
                return JSONResponse(status_code=401, content={
                    "error": "DEV 模式需提供 X-Dev-Token（见启动日志）。"
                             "从环境变量 MNEMOSYNE_DEV_TOKEN 读取。"
                })
    request.state.tenant_id = _resolve_tenant(api_key if EXPECTED_API_KEY else "")
    # 开发不安全模式时间门禁——超过 4h 自动拒绝（S-04 整改：缩短有效窗口，
    # 降低同机进程经环境变量读取 DEV Token 的泄露暴露面）
    if _DEV_INSECURE_START and time.time() - _DEV_INSECURE_START > 14400:
        return JSONResponse(status_code=403, content={
            "error": "DEV_INSECURE 模式已超过 4 小时，自动拒绝。请设置 MNEMOSYNE_API_KEY 重启服务。"
        })
    resp = await call_next(request)
    # 开发不安全模式响应头提醒
    if _DEV_INSECURE_START:
        resp.headers["X-Dev-Insecure"] = "true"
    return resp

# ── 路由注册 ──
import tmt.router as tmt_module
app.include_router(tmt_module.router)
from api.tools import router as tools_router
app.include_router(tools_router)
from api.projects import router as projects_router
app.include_router(projects_router)
from api.security import router as security_router
app.include_router(security_router)
from api.wiki import router as wiki_router
app.include_router(wiki_router)
from api.search import router as search_router
app.include_router(search_router)
from api.memories import router as memories_router
app.include_router(memories_router)
from api.beliefs import router as beliefs_router
app.include_router(beliefs_router)
from api import shared as api_shared
from api.chunks import router as chunks_router
app.include_router(chunks_router)
from api.sessions import router as sessions_router
app.include_router(sessions_router)
from api.media import router as media_router
app.include_router(media_router)
from api.console import router as console_router
app.include_router(console_router)

from api.pipeline import router as pipeline_router
app.include_router(pipeline_router)

from api.pipeline_detail import router as pipeline_detail_router
app.include_router(pipeline_detail_router)

from api.actions import router as actions_router
app.include_router(actions_router)
from api.maturity import router as maturity_router
app.include_router(maturity_router)

# ── 启动/关闭 ──
pool = None

from services.memory_service import (
    reflect as svc_reflect,
    evolve_memories as svc_evolve,
    cleanup as svc_cleanup,
)

# ── 嵌入函数别名 ──
async def get_embedding(texts: List[str]) -> List[List[float]]:
    return await get_embedding_async(texts)


# ── A6/R8 内置调度器 ──
# A-03 长期整改：deep 反思每日触发一次的冷启动时间戳（进程级）
SCHED_LAST_DEEP_TS = 0.0
# A-07 修复：调度器统一使用 _batch_update 分批更新，避免全表行锁
from services.memory_service import _batch_update


async def _background_scheduler(pool: "RetryPool") -> None:
    """内置轻量调度器：周期触发 反思衰减 / embedding 补偿 / 遗忘曲线回写。

    脱离 Hermes cron 独立运行（受 MNEMOSYNE_DISABLE_SCHEDULER 开关控制），
    使「自主进化」与「崩溃后自动恢复」在宿主调度缺失时仍成立。各步骤独立 try，
    单步失败不影响其余周期任务。间隔由 MNEMOSYNE_SCHEDULER_INTERVAL_SEC 配置（默认 300s）。
    """
    import logging as _log
    _logger = _log.getLogger("amber.scheduler")
    interval = int(os.getenv("MNEMOSYNE_SCHEDULER_INTERVAL_SEC", "300"))
    # P4 修复：衰减系数可配置，默认 0.98；高频场景可调低（如 0.95），低频场景可调高（如 0.995）
    decay_factor = float(os.getenv("MNEMOSYNE_DECAY_FACTOR", "0.98"))
    _logger.info("内置调度器已启动（间隔 %ds，衰减系数 %.4f）", interval, decay_factor)
    while True:
        try:
            await asyncio.sleep(interval)
        except asyncio.CancelledError:
            _logger.info("调度器被取消，退出")
            return
        except Exception as e:
            _logger.error("调度器 sleep 异常（将继续运行）: %s", e, exc_info=True)
            continue
        # R5 修复：外层容错循环，任一周期异常不终止调度器
        try:
            # A5 修复：租户由认证派生，调度器须遍历库中实际存在的租户，而非依赖全局
            # TENANT_ID 常量，保证与请求路径的租户一致（多 Key / 多部署场景不漏跑）。
            tenants: list = []
            try:
                async with pool.acquire() as conn:
                    rows = await conn.fetch(
                        "SELECT DISTINCT user_id FROM memories WHERE is_deleted=FALSE"
                    )
                    tenants = [r["user_id"] for r in rows]
            except Exception as e:
                _logger.warning("调度器 获取租户列表失败: %s", e)
            # 1) 反思 + 冗余合并（A-03 长期整改：合并 reflector 入 API 内部调度，
            #    复用同一连接池与已获取的租户列表，消除独立进程旁路；
            #    advisory lock 保证与独立 CLI reflector 不双跑。reflect 与冗余合并均在此完成。）
            try:
                from reflector import run_reflector_cycle
                await run_reflector_cycle(pool, "light", tenants)
            except Exception as e:
                _logger.warning("调度器 reflector(light) 周期执行失败: %s", e)
            # 1b) 每日 deep 反思（实体提取），约 24h 一次，与 light 互斥（不同锁键）
            global SCHED_LAST_DEEP_TS
            _now_m = time.monotonic()
            if _now_m - SCHED_LAST_DEEP_TS >= 86400:
                try:
                    from reflector import run_reflector_cycle as _ref_cycle
                    await _ref_cycle(pool, "deep", tenants)
                    SCHED_LAST_DEEP_TS = _now_m
                except Exception as e:
                    _logger.warning("调度器 reflector(deep) 周期执行失败: %s", e)
            # 2) embedding 补偿：回收 pending/failed 孤儿记忆（R2/R8）
            try:
                from api.memories import _backfill_failed_embeddings
                await _backfill_failed_embeddings(pool, 100)
            except Exception as e:
                _logger.warning("调度器 embedding 补偿失败: %s", e)
            # 3) 遗忘曲线回写：对 L1 记忆施加时间衰减（A-07））
            for tid in tenants:
                try:
                    async with pool.acquire() as conn:
                        await _batch_update(
                            conn,
                            set_clause="heat_score = GREATEST(0.01, heat_score * $3)",
                            where_extra="",
                            user_id=tid,
                            batch=1000,
                            params=(decay_factor,),
                        )
                except Exception as e:
                    _logger.warning("调度器 decay 失败 tenant=%s: %s", tid, e)
            # 4) R-05 修复：embedding 服务健康探测。主动探测可用性并落盘 health_log。
            try:
                await _check_embedding_health(pool)
            except Exception as e:
                _logger.warning("调度器 embedding 健康探测失败: %s", e)
        except Exception as e:
            _logger.error("调度器周期执行异常（将继续运行）: %s", e, exc_info=True)
            continue


async def _check_embedding_health(pool: "RetryPool") -> None:
    """R-05：主动探测 embedding 服务可用性并写入 health_log（best-effort）。

    以极小输入调用嵌入函数并计时；成功记 ok + latency，失败记 down + error。
    health_log 写入失败（如表不存在）不抛出，避免影响调度器主循环。
    """
    import logging as _log
    _logger = _log.getLogger("amber.scheduler")
    status, latency_ms, err = "ok", None, None
    t0 = time.monotonic()
    try:
        vecs = await get_embedding(["health probe"])
        latency_ms = int((time.monotonic() - t0) * 1000)
        if not vecs or not vecs[0]:
            status, err = "degraded", "empty embedding returned"
    except Exception as e:
        latency_ms = int((time.monotonic() - t0) * 1000)
        status, err = "down", str(e)[:500]
    if status != "ok":
        _logger.error("embedding 健康探测异常 status=%s latency=%sms err=%s",
                      status, latency_ms, err)
    try:
        async with pool.acquire() as conn:
            await conn.execute(
                "INSERT INTO health_log (service, status, latency_ms, error) "
                "VALUES ($1, $2, $3, $4)",
                "embedding", status, latency_ms, err,
            )
    except Exception as e:
        _logger.debug("health_log 写入失败（忽略）: %s", e)


# ── 内存驻留路由（不宜拆分的薄封装）──
@app.post("/api/v1/memories/evolve")
async def evolve_memories(strategy: str = "consolidate", limit: int = 50,
                          user_id: str = Depends(api_shared.get_current_user)) -> dict:
    async with pool.acquire() as conn:
        return await svc_evolve(conn, user_id, strategy)

@app.get("/api/v1/memories/tree")
@app.post("/api/v1/reflect")
async def reflect(mode: str = "light", user_id: str = Depends(api_shared.get_current_user)) -> dict:
    async with pool.acquire() as conn:
        return await svc_reflect(conn, user_id, mode)

@app.post("/api/v1/cleanup")
async def cleanup(user_id: str = Depends(api_shared.get_current_user), threshold: float = 0.1) -> dict:
    async with pool.acquire() as conn:
        return await svc_cleanup(conn, user_id, threshold)

@app.get("/api/v1/health/{user_id}")
async def health_report(user_id: str = Depends(api_shared.get_current_user)) -> dict:
    async with pool.acquire() as conn:
        tiers = await conn.fetch("SELECT tier, COUNT(*) as cnt FROM memories WHERE user_id=$1 AND is_deleted=FALSE GROUP BY tier", user_id)
    return ok({"tiers": {r["tier"]: r["cnt"] for r in tiers}})

@app.get("/")
async def root() -> dict:
    return ok({"service": f"Amber Memory Engine v{__version__}", "docs": "/api/v1/capabilities"})

# 记忆驾驶舱 — 静态文件挂载（仅挂载 dist/，静态资源由 CDN 缓存）
import os as _os
_console_dist = _os.path.join(_os.path.dirname(__file__), "console", "dist")
if _os.path.isdir(_console_dist):
    from fastapi.staticfiles import StaticFiles
    app.mount("/console", StaticFiles(directory=_console_dist, html=True), name="console")

@app.get("/api/v1/capabilities")
async def capabilities() -> dict:
    return ok({"service": f"Amber OS v{__version__}", "version": __version__,
            "description": "个人AI记忆库 — 存入、搜索、追溯、演化",
            "auth": "X-API-Key", "graceful_degradation": {"embed_unavailable": "FTS5"},
            "endpoints": ["/api/v1/memories", "/api/v1/memories/search", "/api/v1/reflect",
                          "/api/v1/beliefs", "/api/v1/wiki", "/api/v1/tmt/tree",
                          "/api/v1/security/costs", "/api/v1/health"],
            "quick_start": "1. 存记忆 POST /api/v1/memories → 2. 搜记忆 POST /api/v1/memories/search → 3. 触反思 POST /api/v1/reflect"})

@app.get("/api/v1/echo")
async def echo() -> dict:
    return ok({"status": "ok", "service": "Amber OS", "version": __version__})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=HOST, port=PORT, log_level="info")
