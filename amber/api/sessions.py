"""
Aion Memory — 会话归档路由
"""
import json
import asyncpg
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from . import shared
from .response import ok, error as api_error
from .shared import get_current_user, get_pool, vec_to_str

router = APIRouter()


class SessionArchiveRequest(BaseModel):
    session_id: str = ""
    title: str = ""
    content: str  # 完整对话文本


@router.post("/api/v1/sessions/archive")
async def archive_session(req: SessionArchiveRequest, user_id: str = Depends(get_current_user),
                          pool: asyncpg.Pool = Depends(get_pool)) -> dict:
    """归档完整对话到记忆宫殿 — 自动向量化+入TMT蒸馏"""
    from services.memory_service import detect_conflict as svc_detect_conflict
    from core.embedding import get_embedding_async as get_embedding

    content = req.content.strip()
    if not content:
        return ok({"archived": False, "reason": "empty_content"})

    if not shared.get_cached_embedding_fn():
        return api_error(message="embedding not ready", code=503, status_code=503)

    import logging
    import hashlib
    vec_str = None
    try:
        raw = (await get_embedding([content[:2000]]))[0]
        if raw and len(raw) > 0:
            vec_str = vec_to_str(raw)
    except Exception:
        logging.getLogger("amber").warning(
            "sessions: embedding 生成失败，写入 NULL 向量（跳过向量冲突检测）"
        )
    content_hash = hashlib.sha256(content.encode()).hexdigest()[:64]

    async with pool.acquire() as conn:
        conflict = {"action": "fresh"}
        if vec_str:
            conflict = await svc_detect_conflict(conn, user_id, content, vec_str)
        if conflict["action"] == "merge":
            return ok({"archived": False, "reason": "duplicate", "merged_into": conflict["id"]})

        row = await conn.fetchrow(
            "INSERT INTO memories (user_id, content, content_hash, category, embedding, heat_score, "
            "metadata, tmt_level, scope_target, scope_session_id) VALUES ($1,$2,$3,$4,$5::vector,$6,$7,$8,'general',$9) RETURNING id",
            user_id, content, content_hash, "session", vec_str, 0.6,
            json.dumps({"session_id": req.session_id, "title": req.title}),
            1,
            req.session_id
        )
        memory_id = row["id"]

        # 实体提取 (异步，不阻塞)
        try:
            from core.llm import call_llm_json
            import secrets
            delim = secrets.token_hex(8)
            entities_prompt = (
                "从以下对话中提取关键实体(项目名/人名/技术名/概念)，输出JSON。\n"
                f"---CONTENT_DELIM_{delim}---\n"
                f"```\n{content[:1500]}\n```\n"
                f"---CONTENT_DELIM_{delim}---\n"
                '输出格式: {"entities": ["实体1", "实体2"]}'
            )
            entities_result = await call_llm_json(entities_prompt, tier=2)
            entities_data = json.loads(entities_result.get("content", "{}"))
            entities = entities_data.get("entities", [])
            if entities:
                for ent in entities:
                    try:
                        await conn.execute(
                            "INSERT INTO entities (user_id, name, memory_id) VALUES ($1, $2, $3) ON CONFLICT DO NOTHING",
                            user_id, ent, memory_id
                        )
                    except Exception:
                        pass
        except Exception:
            import logging
            logging.getLogger("amber").exception("会话实体提取后台任务失败")

        # 生成一句话摘要
        summary = ""
        try:
            from core.llm import call_llm_fast
            summary_result = await call_llm_fast(
                "用一句话概括这段对话(不超过30字)。\n"
                f"对话内容:\n```\n{content[:1000]}\n```"
            )
            summary = summary_result.get("content", "")[:100]
        except Exception:
            summary = content[:100]

        return ok({
            "archived": True,
            "memory_id": memory_id,
            "summary": summary,
            "content_length": len(content)
        })
