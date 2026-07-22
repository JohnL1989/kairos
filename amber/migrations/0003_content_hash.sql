-- migrations/0003_content_hash.sql
-- 缺陷 4.2 修复：为 memories 增加 content_hash 列，避免 evolve_memories 的
-- consolidate 策略对 TEXT 字段 GROUP BY 造成全表排序 / 聚合 OOM。
-- 改为对定长 content_hash (VARCHAR(64)) 分组，索引友好、聚合成本可控。

DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_schema = 'public' AND table_name = 'memories'
                     AND column_name = 'content_hash') THEN
        ALTER TABLE memories ADD COLUMN content_hash VARCHAR(64);
    END IF;
END$$;

-- 回填：为已有记忆计算 content_hash（幂等，可重复执行）
UPDATE memories
SET content_hash = LEFT(SHA256(content::bytea)::text, 64)
WHERE content_hash IS NULL AND content IS NOT NULL;

-- 部分索引：仅对非空哈希建索引，加速 GROUP BY content_hash
CREATE INDEX IF NOT EXISTS idx_memories_content_hash
    ON memories(content_hash) WHERE content_hash IS NOT NULL;
