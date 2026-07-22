"""
Aion Memory — 多模态记忆路由
"""
import ipaddress
import logging
from typing import List
import asyncpg
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from . import shared
from .response import ok, error as api_error
from .shared import get_current_user, vec_to_str, get_pool

router = APIRouter()
logger = logging.getLogger("amber.media")


def _validate_media_url(url: str) -> None:
    """S3 修复：media_url SSRF 校验，与 config._validate_outbound_url 同源。

    拒绝非 http/https 协议与链路本地地址（云元数据端点）；内网/保留地址告警放行
    （自托管媒体服务常位于内网）。校验失败抛 ValueError，由端点返回 400。
    """
    from urllib.parse import urlparse
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise ValueError(f"非法 media_url 协议: {parsed.scheme!r}")
    host = parsed.hostname or ""
    try:
        ip = ipaddress.ip_address(host)
    except ValueError:
        return  # 域名放行
    if ip.is_link_local:
        raise ValueError(f"media_url 指向链路本地地址 {host}，SSRF 阻断")
    if ip.is_private or ip.is_reserved or ip.is_multicast:
        logger.warning("media_url 指向内网/保留地址 %s，请确认可信", host)


class MultiModalCreate(BaseModel):
    content: str
    media_urls: List[str] = []
    media_type: str = "image"


@router.post("/api/v1/media-memories")
async def create_multimodal(mem: MultiModalCreate, user_id: str = Depends(get_current_user),
                            pool: asyncpg.Pool = Depends(get_pool)) -> dict:
    """存储多模态记忆（仅描述文本，不调用视觉API）"""
    # S3 修复：写入前校验 media_url，阻断链路本地/非法协议（SSRF）
    media_url = mem.media_urls[0] if mem.media_urls else ""
    if media_url:
        try:
            _validate_media_url(media_url)
        except ValueError as e:
            return api_error(message=str(e), code=400, status_code=400)
    if not shared.get_cached_embedding_fn():
        return api_error(message="embedding not ready", code=503, status_code=503)
    v_str = None
    try:
        raw_v = (await shared.get_cached_embedding_fn()([mem.content]))[0]
        if raw_v and len(raw_v) > 0:
            v_str = vec_to_str(raw_v)
    except Exception:
        logger.warning("media: embedding 生成失败，写入 NULL 向量")
    async with pool.acquire() as conn:
        await conn.execute(
            "INSERT INTO media_memories (user_id, content, media_type, media_url, embedding) VALUES ($1,$2,$3,$4,$5::vector)",
            user_id, mem.content, mem.media_type, media_url, v_str
        )
    return ok({"status": "stored"})


@router.delete("/api/v1/media-memories/{media_id}")
async def delete_multimodal(media_id: int, user_id: str = Depends(get_current_user),
                            pool: asyncpg.Pool = Depends(get_pool)) -> dict:
    """S3 修复：删除多模态记忆（此前媒体模块仅能写入/检索，无生命周期管理）。
    仅删除属于当前用户（单租户常量）的记录，返回 404 若不存在。"""
    async with pool.acquire() as conn:
        exist = await conn.fetchval(
            "SELECT id FROM media_memories WHERE id=$1 AND user_id=$2", media_id, user_id
        )
        if not exist:
            return api_error(message="media not found", code=404, status_code=404)
        await conn.execute(
            "DELETE FROM media_memories WHERE id=$1 AND user_id=$2", media_id, user_id
        )
    return ok({"status": "deleted", "id": media_id})


@router.get("/api/v1/media-memories")
async def search_media(query: str, top_k: int = 5, user_id: str = Depends(get_current_user),
                       pool: asyncpg.Pool = Depends(get_pool)) -> dict:
    """搜索多模态记忆"""
    if not shared.get_cached_embedding_fn():
        return ok({"data": []})
    v_str = None
    try:
        v = (await shared.get_cached_embedding_fn()([query]))[0]
        if v and len(v) > 0:
            v_str = vec_to_str(v)
    except Exception:
        logger.warning("media search: embedding 生成失败，返回空结果")
    if not v_str:
        return ok({"data": []})
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT id, content, media_type, media_url, metadata, created_at, "
            "1 - (embedding <=> $2::vector) AS score "
            "FROM media_memories WHERE user_id=$1 ORDER BY score DESC LIMIT $3",
            user_id, v_str, top_k
        )
    return ok({"data": [dict(r) for r in rows]})
