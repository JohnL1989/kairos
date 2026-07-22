"""
Amber v5.0 — 哈希净化与化石节点
白皮书 L3 第三纵深 + 合规保真

原理: 
- 删除 = SHA-256 哈希替代原始内容 (不可逆)
- 保留元数据 + 拓扑关系 (链路完整)
- DAG 中显示为灰色化石节点

对应 白皮书 §5.6 合规与保真平衡
"""
import os
import secrets
import logging
import asyncpg
import hashlib
import json
from typing import Optional
from datetime import datetime, timezone

logger = logging.getLogger("amber.purifier")

# S-04 修复：净化哈希加盐，杜绝「确定性 SHA-256 可链接性攻击」。
# 原实现对相同明文恒定产出同一哈希，攻击者可借已知明文确认某内容是否被存储
# （确认攻击），或将跨记录的相同内容关联起来。现引入部署级 pepper + 租户 user_id
# 作为盐，使相同明文在不同部署/不同租户下哈希不同，破坏可链接性。
# pepper 未配置时生成一次性临时值并告警（进程重启即变更，仅作开发兜底）。
_PURIFY_PEPPER = os.getenv("MNEMOSYNE_PURIFY_PEPPER", "")
if not _PURIFY_PEPPER:
    _PURIFY_PEPPER = secrets.token_hex(16)
    logger.warning(
        "MNEMOSYNE_PURIFY_PEPPER 未配置，已生成临时 pepper（进程重启即失效）。"
        "生产应在环境变量固化该值，以保证净化哈希稳定且不可被离线彩虹表覆盖。"
    )


def purify_content(content: str, salt: str = "") -> str:
    """
    哈希净化: 将原始内容替换为【加盐】SHA-256 哈希（不可逆、不可链接）。

    Args:
        content: 原始内容
        salt: 通常为「部署 pepper + 租户 user_id」，确保跨部署/跨租户哈希不同。

    Returns:
        sha256:hash (不可逆、不可链接)
    """
    h = hashlib.sha256((salt + "|" + content).encode()).hexdigest()
    return f"sha256:{h}"


async def soft_delete_memory(conn: asyncpg.Connection, memory_id: int, reason: str = "user_request") -> dict:
    """
    软删除 + 哈希净化
    
    流程:
    1. 读取原始内容 + 原始 content_hash
    2. 原始内容 → SHA-256 哈希
    3. content 替换为净化值 (不可读)
    4. is_deleted = TRUE
    5. metadata 记录删除原因
    6. 保留所有关联关系 (拓扑完整)
    
    Returns:
        {"memory_id": int, "status": "purified", "fossil": bool}
    """
    row = await conn.fetchrow(
        "SELECT content, content_hash, user_id FROM memories WHERE id=$1 AND is_deleted=FALSE",
        memory_id
    )
    if not row:
        return {"error": "Memory not found or already deleted"}
    
    original_hash = row["content_hash"] or ""
    # S-04：以「部署 pepper + 租户 user_id」作为盐，使净化哈希不可跨租户链接。
    salt = f"{_PURIFY_PEPPER}:{row['user_id'] or 'default'}"
    purified = purify_content(row["content"] or "", salt)
    purified_hash = hashlib.sha256(purified.encode()).hexdigest()[:64]

    # A11 修复：统一时间源为数据库 NOW()，消除「Python datetime.now()」与
    # 「SQL NOW()」时钟偏差导致 purified_at 与 updated_at 不一致、审计时间不可信。
    now = await conn.fetchval("SELECT NOW()")
    meta = {"purified_at": str(now), "reason": reason}

    # S5 修复：净化时保留 original_content_hash，防止未来审计/恢复功能无法匹配原始内容。
    async with conn.transaction():
        await conn.execute(
            """UPDATE memories SET 
               content=$1, content_hash=$2, original_content_hash=$3,
               is_deleted=TRUE, embedding=NULL,
               metadata = COALESCE(metadata,'{}')::jsonb || $4::jsonb,
               updated_at=NOW()
               WHERE id=$5""",
            purified, purified_hash, original_hash,
            json.dumps(meta), memory_id
        )

        # S3/S8 修复：净化时同步脱敏 memory_traces——不仅替换 content 明文，
        # 而是将整个 metadata 收敛为 {action, redacted:true}，彻底清除任何可能含
        # 敏感信息的字段，确保被遗忘权在审计表也完整生效（GDPR）。仅保留 action。
        await conn.execute(
            "UPDATE memory_traces "
            "SET metadata = jsonb_build_object("
            "  'action', COALESCE(metadata->>'action','unknown'),"
            "  'redacted', TRUE)"
            "WHERE memory_id=$1",
            memory_id
        )

        # S2 修复：级联净化——遗忘权在旁路表同样生效。
        # 1) 哈希化分块明文（memory_chunks.content 经 search-chunks 返回原始片段）
        await conn.execute(
            "UPDATE memory_chunks SET content='[redacted]' WHERE memory_id=$1",
            memory_id,
        )
        # 2) 解除记忆-实体关联，清理 entities 表对该记忆的引用
        await conn.execute(
            "DELETE FROM memory_entities WHERE memory_id=$1", memory_id
        )
        await conn.execute(
            "UPDATE entities SET memory_id=NULL WHERE memory_id=$1", memory_id
        )
        # 3) 从信念证据引用中移除本记忆 id
        await conn.execute(
            "UPDATE beliefs SET evidence_memories = array_remove(evidence_memories, $1) "
            "WHERE $1 = ANY(evidence_memories)",
            memory_id,
        )

    return {
        "memory_id": memory_id,
        "status": "purified",
        "fossil": True,
        "purified_hash": purified[:20] + "...",
        "reason": reason,
        "note": "内容已哈希净化，拓扑关系完整保留",
    }


def verify_purified(content: str) -> bool:
    """检查内容是否已被净化"""
    return content.startswith("sha256:")


async def get_fossil_nodes(conn: asyncpg.Connection, tenant_id: str = "default", limit: int = 20) -> list:
    """
    查询化石节点列表 (已净化但拓扑保留的记忆)
    
    白皮书: "净化后的节点在 DAG 中显示为灰色化石状"
    """
    rows = await conn.fetch(
        """SELECT id, content, category, metadata, 
           created_at, updated_at, reliability, heat_score
           FROM memories
           WHERE user_id=$1 AND is_deleted=TRUE AND content LIKE 'sha256:%'
           ORDER BY updated_at DESC LIMIT $2""",
        tenant_id, limit
    )
    
    import json as _json
    fossils = []
    for r in rows:
        meta = r["metadata"] or {}
        if isinstance(meta, str):
            try:
                meta = _json.loads(meta)
            except _json.JSONDecodeError:
                meta = {}
        
        fossils.append({
            "id": r["id"],
            "status": "fossilized",
            "hash_snippet": (r["content"] or "")[:30] + "...",
            "category": r["category"],
            
            "purified_at": meta.get("purified_at", ""),
            "reason": meta.get("reason", "unknown"),
            "created": str(r["created_at"])[:19],
            "reliability": r["reliability"],
            "heat": r["heat_score"],
        })
    
    return fossils
