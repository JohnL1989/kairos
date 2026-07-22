-- Aion Memory — 迁移 0002：索引卫生 + 约束补齐 + 记忆计数（v1.6.0）
-- 适用：从旧版升级、已跑过 schema.sql 的用户。全新部署直接用 schema.sql。
-- 注意：本文件刻意不包裹 BEGIN/COMMIT，因 CREATE INDEX CONCURRENTLY 不能在事务块内执行。

-- ── R12：HNSW 索引排除 NULL embedding（软删除记忆不再占用图空间）──
-- 重建需先 DROP 再 CREATE；用 CONCURRENTLY 避免长时间 ACCESS EXCLUSIVE 锁与全表重建。
DROP INDEX IF EXISTS idx_memories_embedding;
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_memories_embedding
    ON memories USING hnsw (embedding vector_cosine_ops) WITH (m=16, ef_construction=200)
    WHERE is_deleted=FALSE AND embedding IS NOT NULL;

DROP INDEX IF EXISTS idx_memories_embedding_durable;
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_memories_embedding_durable
    ON memories USING hnsw (embedding vector_cosine_ops) WITH (m=16, ef_construction=200)
    WHERE is_deleted=FALSE AND scope_target='durable' AND embedding IS NOT NULL;

-- ── R14：tmt_tree_edges 子节点唯一父约束 ──
-- 保证「同一子节点在同一层级仅有一个父节点」（树结构不变量）；
-- 5 列全唯一仅防重复边，不防一个子节点被多个父节点引用。
ALTER TABLE public.tmt_tree_edges ADD CONSTRAINT IF NOT EXISTS uq_tmt_tree_edge_child
    UNIQUE (user_id, child_level, child_id);

-- ── P10：记忆计数表 + 触发器（替代写入时 COUNT(*) 全表/索引扫描）──
CREATE TABLE IF NOT EXISTS public.user_memory_counts (
    user_id VARCHAR(64) PRIMARY KEY,
    cnt BIGINT NOT NULL DEFAULT 0
);

CREATE OR REPLACE FUNCTION trg_update_memory_count() RETURNS trigger AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        IF NEW.is_deleted = FALSE THEN
            INSERT INTO user_memory_counts(user_id, cnt) VALUES (NEW.user_id, 1)
            ON CONFLICT (user_id) DO UPDATE SET cnt = user_memory_counts.cnt + 1;
        END IF;
        RETURN NEW;
    ELSIF TG_OP = 'DELETE' THEN
        IF OLD.is_deleted = FALSE THEN
            UPDATE user_memory_counts SET cnt = GREATEST(0, cnt - 1) WHERE user_id = OLD.user_id;
        END IF;
        RETURN OLD;
    ELSIF TG_OP = 'UPDATE' THEN
        IF OLD.is_deleted = FALSE AND NEW.is_deleted = TRUE THEN
            UPDATE user_memory_counts SET cnt = GREATEST(0, cnt - 1) WHERE user_id = OLD.user_id;
        ELSIF OLD.is_deleted = TRUE AND NEW.is_deleted = FALSE THEN
            INSERT INTO user_memory_counts(user_id, cnt) VALUES (NEW.user_id, 1)
            ON CONFLICT (user_id) DO UPDATE SET cnt = user_memory_counts.cnt + 1;
        END IF;
        RETURN NEW;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_memories_count ON memories;
CREATE TRIGGER trg_memories_count AFTER INSERT OR UPDATE OR DELETE ON memories
    FOR EACH ROW EXECUTE FUNCTION trg_update_memory_count();

-- P10 回填：为已有数据初始化计数。存量库若仅靠触发器从 0 累加，
-- 容量门禁会严重失真（误判仅 1 条记忆）；此处一次性 seed 正确计数。
INSERT INTO user_memory_counts(user_id, cnt)
SELECT user_id, COUNT(*) FROM memories WHERE is_deleted=FALSE
GROUP BY user_id
ON CONFLICT (user_id) DO NOTHING;
