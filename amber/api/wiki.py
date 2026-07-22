"""
Aion Memory — Wiki 与媒体路由
"""
import asyncpg
from fastapi import APIRouter, Depends

from . import shared
from .shared import get_current_user, get_pool
from .response import ok, error as api_error

router = APIRouter()


@router.get("/api/v1/wiki")
async def list_wiki_pages(limit: int = 20, user_id: str = Depends(get_current_user),
                          pool: asyncpg.Pool = Depends(get_pool)) -> dict:
    if not shared.get_cached_embedding_fn():
        return ok({"pages": []})
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT id, title, slug, tags, is_published, created_at, updated_at "
            "FROM wiki_pages WHERE user_id=$1 ORDER BY updated_at DESC LIMIT $2",
            user_id, limit
        )
        return ok({"pages": [
            {"id": r["id"], "title": r["title"], "slug": r["slug"],
             "tags": r["tags"], "published": r["is_published"],
             "created": str(r["created_at"])[:19], "updated": str(r["updated_at"])[:19]}
            for r in rows
        ]})


@router.get("/api/v1/wiki/{page_id}")
async def get_wiki_page(page_id: int, user_id: str = Depends(get_current_user),
                        pool: asyncpg.Pool = Depends(get_pool)) -> dict:
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT id, title, slug, content, tags, created_at, updated_at "
            "FROM wiki_pages WHERE id=$1 AND user_id=$2", page_id, user_id
        )
        if not row:
            return api_error(message="page not found", code=404, status_code=404)
        return ok({
            "id": row["id"], "title": row["title"], "slug": row["slug"],
            "content": row["content"], "tags": row["tags"],
            "created": str(row["created_at"])[:19], "updated": str(row["updated_at"])[:19],
        })


@router.post("/api/v1/wiki")
async def create_wiki_page(title: str, content: str = "", user_id: str = Depends(get_current_user),
                           pool: asyncpg.Pool = Depends(get_pool)) -> dict:
    import re
    slug = re.sub(r'[^a-zA-Z0-9\u4e00-\u9fff_-]+', '-', title).strip('-').lower()[:64]
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "INSERT INTO wiki_pages (user_id, title, slug, content) VALUES ($1,$2,$3,$4) "
            "ON CONFLICT (slug) DO UPDATE SET content=EXCLUDED.content, updated_at=NOW() RETURNING id",
            user_id, title, slug, content
        )
        return ok({"id": row["id"], "slug": slug})
