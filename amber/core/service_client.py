"""
共享服务探测层 — ServiceRegistry

统一管理对外部服务的健康探测，确保：
1. 统一的超时/降级策略
2. 共享 httpx.AsyncClient 连接池
3. health_log 异步写入（不阻塞响应返回）
"""
from __future__ import annotations

import asyncio
import logging
import os
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

import asyncpg
import httpx

logger = logging.getLogger("amber.service_client")


@dataclass
class HealthStatus:
    """单个服务的健康检查结果"""
    name: str
    kind: str  # database, cache, embedding, http, self
    status: str  # healthy, degraded, unreachable
    latency_ms: Optional[float] = None
    error: Optional[str] = None
    last_check: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class ServiceConfig:
    """服务探测配置"""
    kind: str  # pg, redis, http, self
    url: Optional[str] = None
    timeout: float = 5.0


class ServiceRegistry:
    """
    服务注册表：统一管理对外部服务的健康探测。

    所有对外部服务的调用通过此类进行，确保：
    1. 统一的超时/重试/降级策略
    2. 统一的连接池管理（共享 httpx.AsyncClient）
    3. 统一的 health_log 写入
    """

    def __init__(self) -> None:
        self._services: dict[str, ServiceConfig] = {}
        self._http_client: Optional[httpx.AsyncClient] = None
        self._register_defaults()

    def _register_defaults(self) -> None:
        """注册默认服务探测配置（从环境变量读取）"""
        # PostgreSQL — 通过连接池 SELECT 1
        self._services["amber-db"] = ServiceConfig(kind="pg")

        # Redis — 通过 redis 库 ping
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self._services["redis"] = ServiceConfig(kind="redis", url=redis_url)

        # Embedding — HTTP /models 探测
        embed_url = os.getenv("EMBEDDING_BASE_URL", "")
        if embed_url:
            name = self._service_name(embed_url)
            self._services[name] = ServiceConfig(
                kind="http",
                url=f"{embed_url.rstrip('/')}/models",
                timeout=3.0,
            )

    @staticmethod
    def _service_name(url: str) -> str:
        try:
            from urllib.parse import urlparse
            return urlparse(url).hostname or url
        except Exception:
            return url

    async def _get_http_client(self) -> httpx.AsyncClient:
        if self._http_client is None or self._http_client.is_closed:
            self._http_client = httpx.AsyncClient(timeout=10.0)
        return self._http_client

    async def close(self) -> None:
        if self._http_client and not self._http_client.is_closed:
            await self._http_client.aclose()

    async def check_all(self, pool: asyncpg.Pool) -> dict[str, Any]:
        """
        并发检测所有注册服务，返回健康状态 dict。
        使用 asyncio.gather(return_exceptions=True) 并发执行，
        单个服务超时不阻塞其他服务检测。
        """
        results = await asyncio.gather(
            *[self._check_one(name, cfg, pool) for name, cfg in self._services.items()],
            return_exceptions=True,
        )

        services: dict[str, Any] = {}
        overall = "healthy"
        for result in results:
            if isinstance(result, Exception):
                logger.warning(f"service check exception: {result}")
                continue
            hs: HealthStatus = result
            services[hs.name] = {
                "status": hs.status,
                "kind": hs.kind,
                "latency_ms": hs.latency_ms,
                "last_checked": hs.last_check,
            }
            if hs.error:
                services[hs.name]["error"] = hs.error
            if hs.status != "healthy" and overall == "healthy":
                overall = "degraded" if hs.status == "degraded" else "unreachable"

        # 异步写入 health_log（不阻塞响应返回）
        asyncio.create_task(self._write_health_log(pool, results))

        return {"services": services, "overall": overall}

    async def _check_one(
        self, name: str, cfg: ServiceConfig, pool: asyncpg.Pool
    ) -> HealthStatus:
        """检测单个服务"""
        now = datetime.now(timezone.utc)

        if cfg.kind == "pg":
            return await self._check_pg(name, pool, now)
        elif cfg.kind == "redis":
            return await self._check_redis(name, cfg, now)
        elif cfg.kind == "http":
            return await self._check_http(name, cfg, now)
        else:
            return HealthStatus(
                name=name, kind=cfg.kind, status="healthy", last_check=now.isoformat()
            )

    async def _check_pg(
        self, name: str, pool: asyncpg.Pool, now: datetime
    ) -> HealthStatus:
        try:
            t0 = time.monotonic()
            async with pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
            ms = (time.monotonic() - t0) * 1000
            return HealthStatus(
                name=name, kind="database", status="healthy",
                latency_ms=round(ms, 1), last_check=now.isoformat(),
            )
        except Exception as exc:
            return HealthStatus(
                name=name, kind="database", status="unreachable",
                error=str(exc)[:120], last_check=now.isoformat(),
            )

    async def _check_redis(
        self, name: str, cfg: ServiceConfig, now: datetime
    ) -> HealthStatus:
        try:
            import redis as redis_sync
            t0 = time.monotonic()
            # 在独立线程中执行同步 redis 调用，避免阻塞事件循环
            import asyncio
            r = await asyncio.to_thread(redis_sync.from_url, cfg.url, socket_timeout=2)
            await asyncio.to_thread(r.ping)
            ms = (time.monotonic() - t0) * 1000
            await asyncio.to_thread(r.close)
            return HealthStatus(
                name=name, kind="cache", status="healthy",
                latency_ms=round(ms, 1), last_check=now.isoformat(),
            )
        except Exception as exc:
            return HealthStatus(
                name=name, kind="cache", status="unreachable",
                error=str(exc)[:120], last_check=now.isoformat(),
            )

    async def _check_http(
        self, name: str, cfg: ServiceConfig, now: datetime
    ) -> HealthStatus:
        try:
            client = await self._get_http_client()
            t0 = time.monotonic()
            resp = await client.get(cfg.url, timeout=cfg.timeout)
            ms = (time.monotonic() - t0) * 1000
            if resp.status_code < 500:
                return HealthStatus(
                    name=name, kind="embedding", status="healthy",
                    latency_ms=round(ms, 1), last_check=now.isoformat(),
                )
            else:
                return HealthStatus(
                    name=name, kind="embedding", status="degraded",
                    latency_ms=round(ms, 1),
                    error=f"HTTP {resp.status_code}", last_check=now.isoformat(),
                )
        except Exception as exc:
            return HealthStatus(
                name=name, kind="embedding", status="unreachable",
                error=str(exc)[:120], last_check=now.isoformat(),
            )

    async def _write_health_log(
        self, pool: asyncpg.Pool, results: list
    ) -> None:
        """
        异步写入 health_log 表。
        写入失败时通过 try/except + logging 双重兜底。
        每次写入前自动清理 7 天前过期数据。
        """
        try:
            async with pool.acquire() as conn:
                # 清理 7 天前数据
                await conn.execute(
                    "DELETE FROM health_log WHERE checked_at < NOW() - INTERVAL '7 days'"
                )
                # 写入本次检查结果
                for result in results:
                    if isinstance(result, Exception):
                        continue
                    hs: HealthStatus = result
                    await conn.execute(
                        "INSERT INTO health_log (service, status, latency_ms, error, checked_at) "
                        "VALUES ($1, $2, $3, $4, $5)",
                        hs.name, hs.status,
                        hs.latency_ms, hs.error,
                        datetime.now(timezone.utc),
                    )
        except Exception as exc:
            logger.warning(f"health_log write failed: {exc}")


# 全局单例
registry = ServiceRegistry()
