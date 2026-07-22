"""
Amber v1.0.0 — Embedding 抽象层

支持任何 OpenAI 兼容 Embedding API。
默认 FTS5 降级，嵌入服务不可达时静默返回空向量。
"""
import sys
import os
import httpx
from typing import List

try:
    from .config import EMBEDDING_API_KEY, EMBEDDING_MODEL, EMBEDDING_DIM, EMBEDDING_ENDPOINT
except ImportError:
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from config import EMBEDDING_API_KEY, EMBEDDING_MODEL, EMBEDDING_DIM, EMBEDDING_ENDPOINT


class EmbeddingUnavailableError(Exception):
    """嵌入服务不可达时抛出，由调用方决定降级策略（NULL 写入 / 纯文本检索）。

    不再静默返回零向量——零向量会污染向量空间几何结构，导致排序退化和
    搜索质量静默劣化，且用户无感知、难以排查。
    """
    pass


SHARED_CLIENT: httpx.AsyncClient | None = None

# A-05 修复：为共享 httpx 客户端设置连接池上限，避免高并发嵌入请求无界占用连接
# （原 httpx.AsyncClient() 默认 max_connections=100 但 keepalive 无界、且未显式声明）。
# 这里显式限定并发连接与空闲保活连接数，并允许通过环境变量调优。
_SHARED_LIMITS = httpx.Limits(
    max_connections=int(os.getenv("MNEMOSYNE_EMBED_MAX_CONN", "100")),
    max_keepalive_connections=int(os.getenv("MNEMOSYNE_EMBED_MAX_KEEPALIVE", "20")),
    keep_alive_expiry=30.0,
)


async def get_client() -> httpx.AsyncClient:
    """获取共享 httpx 客户端（连接复用，带连接池上限）。"""
    global SHARED_CLIENT
    if SHARED_CLIENT is None or SHARED_CLIENT.is_closed:
        SHARED_CLIENT = httpx.AsyncClient(timeout=15, limits=_SHARED_LIMITS)
    return SHARED_CLIENT


async def close_client() -> None:
    """关闭共享 httpx 客户端（由 lifespan 回调调用）。"""
    global SHARED_CLIENT
    if SHARED_CLIENT and not SHARED_CLIENT.is_closed:
        await SHARED_CLIENT.aclose()
        SHARED_CLIENT = None


async def get_embedding_async(texts: List[str]) -> List[List[float]]:
    """
    异步嵌入调用。嵌入服务不可达时返回空列表 + 日志警告。
    使用共享 httpx 客户端，避免每次请求新建连接。
    内置缓存：相同文本的嵌入结果按文本内容缓存。
    """
    # ── 缓存优先 ──
    from .llm import get_embed_cached, set_embed_cached

    embeddings = []
    uncached: List[int] = []  # indices of texts not in cache
    for i, t in enumerate(texts):
        cached = get_embed_cached(t)
        if cached is not None:
            embeddings.append(cached)
        else:
            embeddings.append(None)  # placeholder
            uncached.append(i)

    if not uncached:
        # 全部命中缓存
        return embeddings

    # ── 仅对未缓存的文本请求 API ──
    uncached_texts = [texts[i] for i in uncached]
    client = await get_client()
    payload = {
        "model": EMBEDDING_MODEL,
        "input": uncached_texts,
        "dimensions": EMBEDDING_DIM,
    }
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {EMBEDDING_API_KEY}'
    }
    try:
        resp = await client.post(EMBEDDING_ENDPOINT, json=payload, headers=headers)
        resp.raise_for_status()
        data = resp.json()
        for idx, item in zip(uncached, data['data']):
            emb = item['embedding']
            embeddings[idx] = emb
            set_embed_cached(texts[idx], emb)
    except Exception as e:
        import logging
        logger = logging.getLogger("amber.embedding")
        logger.error(f"嵌入服务不可达 ({type(e).__name__}): 抛出 EmbeddingUnavailableError，"
                     f"由调用方降级（NULL 写入 / 纯文本检索），不再写入零向量")
        raise EmbeddingUnavailableError(
            f"Embedding API failed: {type(e).__name__}: {e}"
        ) from e
    return embeddings


# 向后兼容
get_embedding = get_embedding_async
