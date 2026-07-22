-- migrations/0004_hnsw_index_tiering.sql
-- 缺陷 3.3 修复：按表的写入/查询热度分级 HNSW 索引参数，降低写入放大。
--   schema.sql 已对「全新部署」生效；本迁移对「已存在数据库」补齐新参数
--   （CREATE INDEX IF NOT EXISTS 不会改写已存在索引的参数，必须先 DROP 再 CREATE）。
--
-- ⚠️ 运维提示：DROP INDEX 对目标表取 ACCESS EXCLUSIVE 锁，会在重建期间阻塞该表的
--    写入。请在低流量维护窗口执行本迁移；冷表（tmt_daily/weekly/profiles）与低频表
--    （media_memories/wiki_versions）写入压力通常较低，风险可控。

-- 冷表：tmt_daily / tmt_weekly / tmt_profiles → m=12, ef_construction=128
DROP INDEX IF EXISTS idx_tmt_daily_embedding;
CREATE INDEX idx_tmt_daily_embedding
    ON tmt_daily USING hnsw (embedding vector_cosine_ops) WITH (m=12, ef_construction=128);

DROP INDEX IF EXISTS idx_tmt_weekly_embedding;
CREATE INDEX idx_tmt_weekly_embedding
    ON tmt_weekly USING hnsw (embedding vector_cosine_ops) WITH (m=12, ef_construction=128);

DROP INDEX IF EXISTS idx_tmt_profiles_embedding;
CREATE INDEX idx_tmt_profiles_embedding
    ON tmt_profiles USING hnsw (embedding vector_cosine_ops) WITH (m=12, ef_construction=128);

-- 低频表：media_memories / wiki_versions → m=8, ef_construction=64
DROP INDEX IF EXISTS idx_media_memories_embedding;
CREATE INDEX idx_media_memories_embedding
    ON media_memories USING hnsw (embedding vector_cosine_ops) WITH (m=8, ef_construction=64);

DROP INDEX IF EXISTS idx_wiki_versions_embedding;
CREATE INDEX idx_wiki_versions_embedding
    ON wiki_versions USING hnsw (embedding vector_cosine_ops) WITH (m=8, ef_construction=64);
