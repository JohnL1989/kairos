#!/usr/bin/env python3
"""
Honcho -> Amber 数据迁移脚本（已修复 asyncpg cursor 问题）
用法：
  python migrate_honcho_to_amber.py --dry-run
  python migrate_honcho_to_amber.py --force-dimension
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
import time
from datetime import datetime, timezone

import asyncpg

HONCHO_DSN = os.getenv("HONCHO_DSN", "postgresql://postgres:honcho@127.0.0.1:5432/honcho")
MNEMOSYNE_DSN = os.getenv("MNEMOSYNE_DSN", "postgresql://postgres:amber@127.0.0.1:5433/amber")
EMBEDDING_API_URL = os.getenv("EMBEDDING_API_URL", "http://localhost:8010/api/v1/embed")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "qwen3-embedding")
EMBEDDING_DIM = int(os.getenv("EMBEDDING_DIM", "1024"))
BATCH_SIZE = 500


class Message:
    def __init__(self, row):
        self.public_id = row["public_id"]
        self.content = row["content"]
        self.metadata = json.loads(row["metadata"]) if row["metadata"] else {}
        self.created_at = row["created_at"]
        self.peer_name = row["peer_name"]
        self.session_name = row["session_name"]
        self.workspace_name = row["workspace_name"]
        self.token_count = row["token_count"]
        self.embedding = str(row["embedding"]) if row["embedding"] else None
        self.role = self.metadata.get("role", "user")


class Peer:
    def __init__(self, row):
        self.id = row["id"]
        self.name = row["name"]
        self.metadata = json.loads(row["metadata"]) if row["metadata"] else {}
        self.created_at = row["created_at"]
        self.configuration = json.loads(row["configuration"]) if row["configuration"] else {}
        self.workspace_name = row["workspace_name"]


async def migrate_peers(dst: asyncpg.Connection, peers: list[Peer]) -> int:
    count = 0
    for p in peers:
        content = json.dumps({
            "peer_id": p.id,
            "name": p.name,
            "metadata": p.metadata,
            "configuration": p.configuration,
            "workspace": p.workspace_name,
            "source": "honcho_peer_migration",
        })
        meta = json.dumps({"honcho_peer_id": p.id})
        await dst.execute(
            "INSERT INTO memories (user_id, content, category, scope_target, scope_session_id, "
            "created_at, is_deleted, metadata, tmt_level, tier) "
            "VALUES ('default', $1, 'peer_profile', 'durable', NULL, $2, FALSE, $3::jsonb, 5, 'verified') "
            "ON CONFLICT DO NOTHING",
            content, p.created_at, meta,
        )
        count += 1
    return count


async def migrate_messages(dst: asyncpg.Connection, messages: list[Message], dim: int, force_dim: bool) -> tuple[int, int]:
    success = skip = 0
    for msg in messages:
        category = "user_message" if msg.role == "user" else "assistant_reply"
        emb = msg.embedding

        if emb is not None:
            try:
                emb_list = json.loads(emb) if isinstance(emb, str) else emb
                actual_dim = len(emb_list)
            except Exception:
                actual_dim = 0

            if actual_dim != dim:
                if force_dim:
                    new_emb = await recompute_embedding(msg.content)
                    if new_emb is None:
                        skip += 1
                        continue
                    emb = new_emb
                else:
                    skip += 1
                    continue

        meta = json.dumps({
            "honcho_public_id": msg.public_id,
            "honcho_peer": msg.peer_name,
            "honcho_session": msg.session_name,
            "honcho_workspace": msg.workspace_name,
            "source": "honcho_message_migration",
        })

        try:
            if emb:
                await dst.execute(
                    "INSERT INTO memories (user_id, content, category, embedding, scope_target, "
                    "scope_session_id, created_at, is_deleted, metadata) "
                    "VALUES ('default', $1, $2, $3::vector, 'general', NULL, $4, FALSE, $5::jsonb)",
                    msg.content[:3000], category, emb, msg.created_at, meta,
                )
            else:
                await dst.execute(
                    await dst.execute(
                        "INSERT INTO memories "
                        "(user_id, content, category, scope_target, scope_session_id, "
                        "created_at, is_deleted, metadata, tier, tmt_level, importance, reliability, heat_score) "
                        "VALUES ($1, $2, $3, 'general', NULL, $4, FALSE, '{}', 'L2', 1, 0.5, 0.5, 0.5)",
                        'default', msg.content[:3000], 'fact', msg.created_at)
                )
            success += 1
        except Exception as e:
            skip += 1
            if skip <= 5:
                print(f"  x {msg.public_id}: {e}")

    return success, skip


async def recompute_embedding(content: str) -> str | None:
    try:
        import urllib.request
        data = json.dumps({"input": content[:4096], "model": EMBEDDING_MODEL}).encode()
        req = urllib.request.Request(
            EMBEDDING_API_URL,
            data=data,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read())
            vec = result["data"][0]["embedding"]
            return json.dumps(vec)
    except Exception as e:
        print(f"  x 重算 embedding 失败: {e}")
        return None


async def verify(conn: asyncpg.Connection) -> dict[str, int]:
    return {
        "total": await conn.fetchval("SELECT COUNT(*) FROM memories WHERE is_deleted = FALSE"),
        "durable": await conn.fetchval("SELECT COUNT(*) FROM memories WHERE is_deleted = FALSE AND scope_target = 'durable'"),
        "general": await conn.fetchval("SELECT COUNT(*) FROM memories WHERE is_deleted = FALSE AND scope_target = 'general'"),
    }


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--force-dimension", action="store_true")
    parser.add_argument("--skip-peers", action="store_true")
    args = parser.parse_args()

    print("=" * 60)
    print("Honcho -> Amber 数据迁移")
    print(f"模式: {'DRY RUN' if args.dry_run else '正式迁移'}")
    print(f"force-dimension: {args.force_dimension}")
    print("=" * 60)

    print("\n[1/6] 连接数据库...")
    honcho = await asyncpg.connect(HONCHO_DSN)
    amber = await asyncpg.connect(MNEMOSYNE_DSN)
    print("  OK")

    try:
        print("\n[2/6] 验证 embedding 维度...")
        honcho_dim = await honcho.fetchval(
            "SELECT array_length(embedding::real[], 1) FROM message_embeddings WHERE embedding IS NOT NULL LIMIT 1"
        )
        print(f"  Honcho: {honcho_dim}D  |  Amber 配置: {EMBEDDING_DIM}D")
        if honcho_dim != EMBEDDING_DIM:
            if args.force_dimension:
                print("  -> --force-dimension: 将通过 API 重算")
            else:
                print("  -> 请使用 --force-dimension")
                return
        else:
            print("  OK")

        print("\n[3/6] 快照统计...")
        msg_count = await honcho.fetchval("SELECT COUNT(*) FROM messages")
        peer_count = await honcho.fetchval("SELECT COUNT(*) FROM peers")
        old_count = await amber.fetchval("SELECT COUNT(*) FROM memories WHERE is_deleted = FALSE")
        print(f"  Honcho messages: {msg_count}")
        print(f"  Honcho peers: {peer_count}")
        print(f"  Amber 旧数据: {old_count}")

        if args.dry_run:
            print("\n[DRY RUN] 退出")
            return

        print("\n[4/6] 硬替换: 软删 Amber 旧数据...")
        deleted = await amber.execute("UPDATE memories SET is_deleted = TRUE WHERE user_id = 'default' AND is_deleted = FALSE")
        print(f"  OK: {deleted.split()[-1]} 条")

        print("\n[5/6] 开始迁移...")
        t0 = time.time()

        if not args.skip_peers:
            peer_rows = await honcho.fetch("SELECT * FROM peers ORDER BY created_at")
            peers = [Peer(r) for r in peer_rows]
            pc = await migrate_peers(amber, peers)
            print(f"  OK Peers -> durable: {pc} 条")
        else:
            print("  跳过 peers")

        rows = await honcho.fetch("""
            SELECT m.public_id, m.content, m.metadata, m.created_at,
                   m.peer_name, m.workspace_name, m.session_name, m.token_count,
                   me.embedding
            FROM messages m
            LEFT JOIN message_embeddings me ON me.message_id = m.public_id
            ORDER BY m.created_at ASC
        """)
        messages = [Message(r) for r in rows]
        print(f"  拉取 {len(messages)} 条消息...")

        success = skip = 0
        for i in range(0, len(messages), BATCH_SIZE):
            batch = messages[i:i + BATCH_SIZE]
            s, k = await migrate_messages(amber, batch, EMBEDDING_DIM, args.force_dimension)
            success += s
            skip += k
            print(f"    进度 {min(i + BATCH_SIZE, len(messages))}/{len(messages)}", end="\r")

        elapsed = time.time() - t0
        print(f"\n  OK {success} 成功 / {skip} 跳过 / {elapsed:.1f}s")

        print("\n[6/6] 迁移后验证...")
        stats = await verify(amber)
        print(f"  Total: {stats['total']}  |  Durable: {stats['durable']}  |  General: {stats['general']}")
        ok = stats["total"] >= msg_count * 0.95
        print(f"  验收: {'OK' if ok else 'FAIL'} (预期 >= {int(msg_count * 0.95)})")

    finally:
        await honcho.close()
        await amber.close()


if __name__ == "__main__":
    asyncio.run(main())
