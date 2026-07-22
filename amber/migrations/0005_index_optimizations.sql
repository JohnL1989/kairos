-- migrations/0005_index_optimizations.sql
-- P1 修复：记忆主表 HNSW 索引改为「部分索引」（WHERE is_deleted=FALSE）。
--   软删除从不物理回收，原全量 HNSW 索引将持续包含死行，写入放大 + 检索退化。
--   部分索引使已删除记忆退出 HNSW 图，缩小维护面、提升检索质量。
-- P2 修复：新增 failed embedding 快速扫描索引，避免 backfill 全表扫描。
--
-- ⚠️ 运维提示：DROP INDEX 对 memories 表取 ACCESS EXCLUSIVE 锁，重建期间阻塞写入。
--    请在低流量维护窗口执行（建议与清理窗口错峰）。

-- P1：重建记忆主表 HNSW 为部分索引
DROP INDEX IF EXISTS idx_memories_embedding;
CREATE INDEX IF NOT EXISTS idx_memories_embedding
    ON memories USING hnsw (embedding vector_cosine_ops) WITH (m=16, ef_construction=200)
    WHERE is_deleted=FALSE;

-- P2：failed embedding 扫描索引（供 /api/v1/memories/embeddings/backfill 使用）
CREATE INDEX IF NOT EXISTS idx_memories_embed_fail
    ON memories(user_id) WHERE metadata->>'embedding_status' = 'failed' AND is_deleted=FALSE;

-- 辅助：reflect 分批更新（P5）按 (user_id, is_deleted, id) 有序抓 id 的索引支撑
-- （idx_memories_user_deleted 已存在，此处仅确保组合覆盖 id 排序，无则补充）
CREATE INDEX IF NOT EXISTS idx_memories_user_deleted_id
    ON memories(user_id, is_deleted, id);
