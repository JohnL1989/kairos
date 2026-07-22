"""
Amber v5.0 — 统一配置中心 (Hermes integration version)
所有值通过环境变量读取，不硬编码任何模型或密钥。
"""
import os
import ipaddress
import logging

logger = logging.getLogger("amber.config")

# 唯一版本号源
__version__ = "2.3.5"


def _validate_outbound_url(name: str, url: str) -> None:
    """S6 修复：出站端点 SSRF 校验（与 hermes_provider 同源思路，覆盖 embedding/LLM 出站）。

    - 非 http/https 协议（file://、gopher:// 等）：硬性阻断（抛 RuntimeError）
    - 链路本地地址（169.254.169.254 等云元数据端点）：硬性阻断（抛 RuntimeError）
    - 内网/保留地址：保留告警，不阻断（自托管 embedding/LLM 常位于内网）
    - 经 MNEMOSYNE_ALLOW_OUTBOUND_HOSTS 显式列出的主机放行
    默认严格模式（MNEMOSYNE_STRICT_OUTBOUND=1）；设为 0 仅告警不阻断（CI/特殊自托管）。
    """
    if not url:
        return
    from urllib.parse import urlparse
    parsed = urlparse(url)
    # 无 scheme 且无网络位置（如未配置 BASE_URL 时退化的相对路径 "/embeddings"）
    # 不是可达出站端点，跳过校验，避免误报 CRITICAL。
    if not parsed.scheme and not parsed.netloc:
        return
    strict = os.getenv("MNEMOSYNE_STRICT_OUTBOUND", "1") == "1"
    allow = {h.strip() for h in os.getenv("MNEMOSYNE_ALLOW_OUTBOUND_HOSTS", "").split(",") if h.strip()}
    # 非 http/https：S6 修复硬性阻断（SSRF）
    if parsed.scheme not in ("http", "https"):
        msg = f"出站端点 {name} 协议非法: {parsed.scheme!r}（仅允许 http/https，疑似 SSRF）"
        if strict:
            raise RuntimeError(msg)
        logger.critical(msg)
        return
    host = parsed.hostname or ""
    if host in allow:
        return
    try:
        ip = ipaddress.ip_address(host)
    except ValueError:
        return  # 域名：运行时 DNS 解析，此处放行
    if ip.is_link_local:
        msg = f"出站端点 {name} 指向链路本地地址 {host}，SSRF 风险（疑似云元数据端点）"
        if strict:
            raise RuntimeError(msg)
        logger.critical(msg)
    elif ip.is_private or ip.is_reserved or ip.is_multicast:
        logger.warning("出站端点 %s 指向内网/保留地址 %s，请确认可信", name, host)

# Embedding — OpenAI 兼容 API
EMBEDDING_API_KEY = os.getenv("EMBEDDING_API_KEY", "")
EMBEDDING_BASE_URL = os.getenv("EMBEDDING_BASE_URL", "")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "")
RERANKER_URL = os.getenv("RERANKER_URL", "")
EMBEDDING_ENDPOINT = os.getenv("EMBEDDING_ENDPOINT", f"{EMBEDDING_BASE_URL}/embeddings")
EMBEDDING_DIM = int(os.getenv("EMBEDDING_DIM", "1024"))

# LLM — OpenAI 兼容 API
LLM_API_KEY = os.getenv("LLM_API_KEY", os.getenv("EMBEDDING_API_KEY", ""))
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://api.deepseek.com/v1")

LLM_MODEL_MINI = os.getenv("LLM_MODEL_MINI", "deepseek-chat")
LLM_MODEL_LITE = os.getenv("LLM_MODEL_LITE", "deepseek-chat")
LLM_MODEL_PRO = os.getenv("LLM_MODEL_PRO", "deepseek-chat")
LLM_BASE_URL_PRO = os.getenv("LLM_BASE_URL_PRO", "https://api.deepseek.com/v1")
LLM_API_KEY_PRO = os.getenv("LLM_API_KEY_PRO", os.getenv("LLM_API_KEY", ""))

TMT_LLM_TIER = os.getenv("TMT_LLM_TIER", "lite")
TMT_MAX_RETRIES = int(os.getenv("TMT_MAX_RETRIES", "3"))

# Reranker (可选)
RERANKER_URL = os.getenv("RERANKER_URL", "http://127.0.0.1:8080/v1/embeddings")

# S7 修复：对出站端点做 SSRF 配置校验（链路本地/非法协议告警）
_validate_outbound_url("EMBEDDING_ENDPOINT", EMBEDDING_ENDPOINT)
_validate_outbound_url("EMBEDDING_BASE_URL", EMBEDDING_BASE_URL)
_validate_outbound_url("LLM_BASE_URL", LLM_BASE_URL)
_validate_outbound_url("LLM_BASE_URL_PRO", LLM_BASE_URL_PRO)
_validate_outbound_url("RERANKER_URL", RERANKER_URL)

# 数据库 — PostgreSQL + pgvector + AGE
# 优先从 PG_DSN 解析（Docker 部署常用），回退到独立环境变量
PG_DSN = os.getenv("PG_DSN", "")
if PG_DSN:
    from urllib.parse import urlparse
    _p = urlparse(PG_DSN)
    PG_USER = _p.username or os.getenv("PGUSER", "postgres")
    PG_PASSWORD = _p.password or os.getenv("PGPASSWORD", "")
    PG_HOST = _p.hostname or os.getenv("PGHOST", "127.0.0.1")
    PG_PORT = _p.port or int(os.getenv("PGPORT", "5432"))
    PG_DB = (_p.path or "").lstrip("/") or os.getenv("PGDATABASE", "amber")
else:
    PG_USER = os.getenv("PGUSER", "postgres")
    PG_PASSWORD = os.getenv("PGPASSWORD", "")
    PG_DB = os.getenv("PGDATABASE", "amber")
    PG_HOST = os.getenv("PGHOST", "127.0.0.1")
    PG_PORT = int(os.getenv("PGPORT", "5432"))

# 服务
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("MNEMOSYNE_PORT", "8010"))

# 搜索权重
SEARCH_WEIGHTS = {"vector": 0.45, "bm25": 0.15, "time": 0.15, "reliability": 0.15, "heat": 0.10}
HEAT_DECAY_ALPHA = 0.95
HEAT_BOOST_ACCESS = 0.05


# A3 修复：统一配置模型，将 scattered os.getenv() 收敛到声明式配置。
# 收益：启动时一次性校验（如 embedding_dim>0、pool 范围合法），消除 silent misconfiguration。
# 负面影响：引入 pydantic 校验逻辑，但 pydantic 已是现有依赖，无新增依赖。
class AmberSettings:
    """集中式配置：从环境变量读取，启动时自动校验。"""

    def __init__(self) -> None:
        # Embedding
        self.embedding_dim: int = int(os.getenv("EMBEDDING_DIM", "1024"))
        self.embedding_base_url: str = os.getenv("EMBEDDING_BASE_URL", "")
        self.embedding_model: str = os.getenv("EMBEDDING_MODEL", "")
        # 连接池
        self.pool_min_size: int = int(os.getenv("MNEMOSYNE_POOL_MIN_SIZE", "2"))
        self.pool_max_size: int = int(os.getenv("MNEMOSYNE_POOL_MAX_SIZE", "10"))
        self.pool_retries: int = int(os.getenv("MNEMOSYNE_POOL_RETRIES", "3"))
        self.pool_retry_base_delay: float = float(os.getenv("MNEMOSYNE_POOL_RETRY_BASE_DELAY", "0.1"))
        self.pool_breaker_cooldown: float = float(os.getenv("MNEMOSYNE_POOL_BREAKER_COOLDOWN", "60"))
        # 限流
        self.write_limit_per_min: int = int(os.getenv("MNEMOSYNE_WRITE_LIMIT_PER_MIN", "30"))
        self.redis_url: str = os.getenv("MNEMOSYNE_REDIS_URL", "")
        # 调度器
        self.scheduler_interval_sec: int = int(os.getenv("MNEMOSYNE_SCHEDULER_INTERVAL_SEC", "300"))
        self.decay_factor: float = float(os.getenv("MNEMOSYNE_DECAY_FACTOR", "0.98"))
        self.disable_scheduler: bool = os.getenv("MNEMOSYNE_DISABLE_SCHEDULER", "0") == "1"
        # 搜索
        self.search_sql_rerank: bool = os.getenv("MNEMOSYNE_SEARCH_SQL_RERANK", "1") == "1"
        self.hnsw_ef_search: str | None = os.getenv("MNEMOSYNE_HNSW_EF_SEARCH")
        # 容量
        self.max_memories: int = int(os.getenv("MNEMOSYNE_MAX_MEMORIES", "0") or "0")
        # CORS
        self.cors_origins: list[str] = [
            o.strip()
            for o in os.getenv("MNEMOSYNE_CORS_ORIGINS", "http://localhost:5173,http://localhost:8000").split(",")
            if o.strip()
        ]
        # 启动校验
        self._validate()

    def _validate(self) -> None:
        if self.embedding_dim <= 0:
            raise ValueError(f"EMBEDDING_DIM must be positive, got {self.embedding_dim}")
        if self.pool_min_size < 1 or self.pool_max_size < self.pool_min_size:
            raise ValueError(f"pool size invalid: min={self.pool_min_size}, max={self.pool_max_size}")
        if not (0.0 < self.decay_factor <= 1.0):
            raise ValueError(f"DECAY_FACTOR must be in (0, 1], got {self.decay_factor}")
        if self.scheduler_interval_sec < 10:
            raise ValueError(f"SCHEDULER_INTERVAL_SEC too small: {self.scheduler_interval_sec}s (min 10s)")
        if self.write_limit_per_min < 1:
            raise ValueError(f"WRITE_LIMIT_PER_MIN must be >= 1, got {self.write_limit_per_min}")
        if not self.cors_origins:
            raise ValueError("MNEMOSYNE_CORS_ORIGINS 不能为空")

    def is_cors_origin_allowed(self, origin: str) -> bool:
        """支持精确匹配和后缀通配（如 .example.com）。"""
        for allowed in self.cors_origins:
            if origin == allowed:
                return True
            if allowed.startswith("*.") and origin.endswith(allowed[1:]):
                return True
        return False


settings = AmberSettings()
