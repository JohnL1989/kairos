-- 0006: durable 作用域部分 HNSW 索引（P1 修复增强）
-- 对应 schema.sql 中 idx_memories_embedding_durable 的增量等价物：
-- 已 bootstrap 的存量库不再重跑 schema.sql，由此迁移补齐该索引。
-- 幂等：CREATE INDEX IF NOT EXISTS，重复执行安全。
CREATE INDEX IF NOT EXISTS idx_memories_embedding_durable
    ON memories USING hnsw (embedding vector_cosine_ops) WITH (m=16, ef_construction=200)
    WHERE is_deleted=FALSE AND scope_target='durable';
