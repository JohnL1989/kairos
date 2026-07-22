-- Aion Memory — Mnemosyne 数据库 Schema
-- 所有表位于 public schema，自动创建
-- 注意：本文件是首次部署的完整 schema。迁移管理见 migrations/ 目录。

-- 启用 pgvector 扩展
CREATE EXTENSION IF NOT EXISTS vector;

-- ── 迁移版本表（R10 修复）──
-- 记录已应用的迁移文件名，entrypoint 仅对未应用迁移执行，避免与 schema.sql 双轨漂移。
CREATE TABLE IF NOT EXISTS public.schema_migrations (
    id SERIAL PRIMARY KEY,
    migration_name VARCHAR(255) NOT NULL UNIQUE,
    applied_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ── 记忆主表 ──
CREATE TABLE IF NOT EXISTS public.memories (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(64) NOT NULL DEFAULT 'default',
    content TEXT NOT NULL,
    content_hash VARCHAR(64),
    category VARCHAR(32) DEFAULT 'general',
    tier VARCHAR(4) DEFAULT 'L1',
    embedding vector(1024),
    heat_score FLOAT DEFAULT 0.5,
    reliability FLOAT DEFAULT 0.5,
    access_count INTEGER DEFAULT 0,
    session_id VARCHAR(64),
    entities TEXT[] DEFAULT '{}',
    is_deleted BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- TMT 蒸馏层级 (v1.1+)
    tmt_level INTEGER DEFAULT 1,

    -- 访问与遗忘追踪 (v1.0+)
    last_accessed TIMESTAMP WITH TIME ZONE,
    forgotten_at TIMESTAMP WITH TIME ZONE,
    invalid_at TIMESTAMP WITH TIME ZONE,

    -- 重要性评分 (v1.0+)
    importance FLOAT DEFAULT 0.0,

    -- 元数据 (v1.0+)
    metadata JSONB DEFAULT '{}',

    -- 项目关联 (v1.1+)
    project_id VARCHAR(64),

    -- 作用域支持 (v1.2+)
    scope_target VARCHAR(16) DEFAULT 'general'
        CHECK (scope_target IN ('durable', 'general')),
    scope_session_id VARCHAR(64),

    -- 溯源支持 (v1.3+)
    source_ids INTEGER[] DEFAULT '{}'
);

-- ── 记忆主表索引 ──
-- P1 修复：改为部分索引（WHERE is_deleted=FALSE），减少 HNSW 图规模与写入放大
-- 已删除的记忆不参与向量检索，无需进入 HNSW 索引
-- R5 修复：移除 DROP INDEX，仅保留 CREATE INDEX IF NOT EXISTS（pgvector 的 IF NOT EXISTS
-- 不会重建已存在索引），避免每次启动 R5 所述 ACCESS EXCLUSIVE 锁与全表扫描重建。
CREATE INDEX IF NOT EXISTS idx_memories_embedding
    ON memories USING hnsw (embedding vector_cosine_ops) WITH (m=16, ef_construction=200)
    WHERE is_deleted=FALSE AND embedding IS NOT NULL;  -- R12 修复：排除 NULL embedding，避免软删除记忆占用 HNSW 图空间
-- P1 修复（增强）：durable 作用域部分 HNSW 索引。主检索路径恒为
-- `scope_target='durable' AND is_deleted=FALSE AND user_id=$1`，新增仅覆盖该子集的
-- 部分索引，使 durable 检索无需遍历全表 HNSW 图（已删除/working 记忆不计入图规模），
-- 延迟随 durable 记忆总量增长而非全表增长；配合 P4 硬上限防止 durable 无界膨胀。
-- 查询规划器会据 WHERE 自动选择该更小子集索引。
CREATE INDEX IF NOT EXISTS idx_memories_embedding_durable
    ON memories USING hnsw (embedding vector_cosine_ops) WITH (m=16, ef_construction=200)
    WHERE is_deleted=FALSE AND scope_target='durable' AND embedding IS NOT NULL;  -- R12 修复
CREATE INDEX IF NOT EXISTS idx_memories_user_deleted
    ON memories(user_id, is_deleted);
CREATE INDEX IF NOT EXISTS idx_memories_user_deleted_created
    ON memories(user_id, is_deleted, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_memories_user_deleted_heat
    ON memories(user_id, is_deleted, heat_score DESC);
CREATE INDEX IF NOT EXISTS idx_memories_user_tier
    ON memories(user_id, tier);
CREATE INDEX IF NOT EXISTS idx_memories_scope
    ON memories(scope_target, scope_session_id);
CREATE INDEX IF NOT EXISTS idx_memories_source_ids
    ON memories USING gin(source_ids);
CREATE INDEX IF NOT EXISTS idx_memories_content_gin
    ON memories USING gin(to_tsvector('simple', coalesce(content, '')));
CREATE INDEX IF NOT EXISTS idx_memories_content_hash
    ON memories(content_hash) WHERE content_hash IS NOT NULL;
-- R3 修复：去重原子性——在 (user_id, content_hash) WHERE is_deleted=FALSE 上建立
-- 部分唯一约束，消除「读-判-写」CHECK-THEN-ACT 的 TOCTOU 竞态（并发相同内容只插一条）。
-- 若历史数据已存在重复（未删除）记忆，约束创建会失败；此处用 DO 块兜住，
-- 跳过约束但告警，避免启动中断（请先经 evolve/consolidate 去重）。
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'uq_memories_user_content_active'
    ) THEN
        BEGIN
            ALTER TABLE public.memories ADD CONSTRAINT uq_memories_user_content_active
                UNIQUE (user_id, content_hash) WHERE is_deleted = FALSE;
        EXCEPTION WHEN others THEN
            RAISE NOTICE '跳过唯一约束 uq_memories_user_content_active（存在重复未删除记忆，请先去重）';
        END;
    END IF;
END $$;
-- P2 修复：failed embedding 快速扫描索引，避免全表扫描
CREATE INDEX IF NOT EXISTS idx_memories_embed_fail
    ON memories(user_id) WHERE metadata->>'embedding_status' = 'failed' AND is_deleted=FALSE;

-- ── TMT 会话层 ──
CREATE TABLE IF NOT EXISTS public.tmt_sessions (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(64) NOT NULL DEFAULT 'default',
    session_label VARCHAR(128),
    summary TEXT,
    embedding vector(1024),
    heat_score FLOAT DEFAULT 0.5,
    themes TEXT[] DEFAULT '{}',
    fragment_ids TEXT[] DEFAULT '{}',
    start_time TIMESTAMP WITH TIME ZONE,
    end_time TIMESTAMP WITH TIME ZONE,
    token_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_tmt_sessions_embedding
    ON tmt_sessions USING hnsw (embedding vector_cosine_ops) WITH (m=16, ef_construction=200);
CREATE INDEX IF NOT EXISTS idx_tmt_sessions_user
    ON tmt_sessions(user_id);

-- ── TMT 日报层 ──
CREATE TABLE IF NOT EXISTS public.tmt_daily (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(64) NOT NULL DEFAULT 'default',
    date DATE NOT NULL,
    summary TEXT,
    embedding vector(1024),
    heat_score FLOAT DEFAULT 0.5,
    themes TEXT[] DEFAULT '{}',
    session_ids TEXT[] DEFAULT '{}',
    token_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, date)
);

-- ── TMT 周报层 ──
CREATE TABLE IF NOT EXISTS public.tmt_weekly (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(64) NOT NULL DEFAULT 'default',
    week_start DATE NOT NULL,
    week_end DATE NOT NULL,
    summary TEXT,
    embedding vector(1024),
    heat_score FLOAT DEFAULT 0.5,
    patterns TEXT[] DEFAULT '{}',
    daily_ids TEXT[] DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, week_start)
);

-- ── TMT 画像层 ──
CREATE TABLE IF NOT EXISTS public.tmt_profiles (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(64) NOT NULL DEFAULT 'default',
    period_start DATE,
    period_end DATE,
    profile_json JSONB DEFAULT '{}',
    summary TEXT,
    embedding vector(1024),
    heat_score FLOAT DEFAULT 0.5,
    weekly_ids TEXT[] DEFAULT '{}',
    is_active BOOLEAN DEFAULT TRUE,
    previous_id INTEGER REFERENCES tmt_profiles(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- R4 修复：tmt_profiles 按月唯一，防止重复画像（同月重跑产生重复行）。
-- 部分唯一约束 (user_id, period_start) WHERE is_active=TRUE；历史重复数据用 DO 块兜住。
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'uq_tmt_profiles_active_period'
    ) THEN
        BEGIN
            ALTER TABLE public.tmt_profiles ADD CONSTRAINT uq_tmt_profiles_active_period
                UNIQUE (user_id, period_start) WHERE is_active = TRUE;
        EXCEPTION WHEN others THEN
            RAISE NOTICE '跳过唯一约束 uq_tmt_profiles_active_period（存在重复画像，请先清理）';
        END;
    END IF;
END $$;

-- ── TMT 画像迁移兼容 ──
ALTER TABLE public.tmt_profiles ADD COLUMN IF NOT EXISTS summary TEXT;
ALTER TABLE public.tmt_profiles ADD COLUMN IF NOT EXISTS embedding vector(1024);
ALTER TABLE public.tmt_profiles ADD COLUMN IF NOT EXISTS heat_score FLOAT DEFAULT 0.5;
ALTER TABLE public.tmt_profiles ADD COLUMN IF NOT EXISTS weekly_ids TEXT[] DEFAULT '{}';

-- ── TMT 树结构边 ──
CREATE TABLE IF NOT EXISTS public.tmt_tree_edges (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(64) NOT NULL DEFAULT 'default',
    parent_level INTEGER NOT NULL,
    parent_id INTEGER NOT NULL,
    child_level INTEGER NOT NULL,
    child_id INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, parent_level, parent_id, child_level, child_id)
);

-- R14 修复：保证「同一子节点在同一层级仅有一个父节点」（树结构不变量）。
-- 上方 5 列全唯一仅防重复边，不防一个子节点被多个父节点引用；此约束补齐。
ALTER TABLE public.tmt_tree_edges ADD CONSTRAINT IF NOT EXISTS uq_tmt_tree_edge_child
    UNIQUE (user_id, child_level, child_id);

-- ── 信念表 ──
CREATE TABLE IF NOT EXISTS public.beliefs (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(64) NOT NULL DEFAULT 'default',
    content TEXT NOT NULL,
    category VARCHAR(32) DEFAULT 'general',
    confidence FLOAT DEFAULT 0.5,
    source TEXT DEFAULT 'reflection',
    tags TEXT[] DEFAULT '{}',
    status VARCHAR(16) DEFAULT 'active',
    trajectory JSONB DEFAULT '[]',
    evidence_memories INTEGER[] DEFAULT '{}',
    embedding vector(1024),
    valid_from TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CHECK (status IN ('active', 'tentative', 'established', 'contradicted'))
);

-- ── 信念迁移兼容 ──
ALTER TABLE public.beliefs ADD COLUMN IF NOT EXISTS embedding vector(1024);
ALTER TABLE public.beliefs DROP CONSTRAINT IF EXISTS beliefs_status_check;
ALTER TABLE public.beliefs ADD CONSTRAINT beliefs_status_check CHECK (status IN ('active', 'tentative', 'established', 'contradicted'));
CREATE INDEX IF NOT EXISTS idx_beliefs_user_id ON beliefs(user_id);

-- ── 记忆块（分块检索用） ──
CREATE TABLE IF NOT EXISTS public.memory_chunks (
    id SERIAL PRIMARY KEY,
    memory_id INTEGER REFERENCES memories(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    embedding vector(1024),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(memory_id, chunk_index)
);

-- ── 记忆块迁移兼容 ──
ALTER TABLE public.memory_chunks DROP CONSTRAINT IF EXISTS memory_chunks_memory_id_chunk_index_key;
ALTER TABLE public.memory_chunks ADD CONSTRAINT memory_chunks_memory_id_chunk_index_key UNIQUE (memory_id, chunk_index);

-- ── 记忆-实体关联 ──
CREATE TABLE IF NOT EXISTS public.memory_entities (
    entity_id VARCHAR(128) NOT NULL,
    memory_id INTEGER NOT NULL REFERENCES memories(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    PRIMARY KEY (entity_id, memory_id)
);

-- ── 实体表 ──
CREATE TABLE IF NOT EXISTS public.entities (
    id SERIAL PRIMARY KEY,
    entity_id VARCHAR(128) UNIQUE NOT NULL,
    name VARCHAR(256),
    user_id VARCHAR(64) NOT NULL DEFAULT 'default',
    type VARCHAR(32) DEFAULT 'general',
    metadata JSONB DEFAULT '{}',
    memory_id INTEGER REFERENCES memories(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ── 实体 embedding 与全文搜索 ──
ALTER TABLE public.entities ADD COLUMN IF NOT EXISTS embedding vector(1024);

-- ── 项目沙箱 ──
CREATE TABLE IF NOT EXISTS public.projects (
    id SERIAL PRIMARY KEY,
    project_id VARCHAR(64) UNIQUE NOT NULL,
    tenant_id VARCHAR(64) NOT NULL DEFAULT 'default',
    name VARCHAR(128) NOT NULL,
    description TEXT,
    status VARCHAR(16) DEFAULT 'active',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_projects_tenant ON projects(tenant_id);
CREATE INDEX IF NOT EXISTS idx_projects_status ON projects(status);

-- ── 工具归档 ──
CREATE TABLE IF NOT EXISTS public.tool_archives (
    id SERIAL PRIMARY KEY,
    archive_id VARCHAR(64) UNIQUE NOT NULL,
    tool_name VARCHAR(64) NOT NULL,
    params JSONB DEFAULT '{}',
    result TEXT,
    success BOOLEAN NOT NULL,
    error_type VARCHAR(32),
    knowledge_type VARCHAR(16),
    session_id VARCHAR(64),
    project_id VARCHAR(64),
    duration_ms INTEGER,
    tenant_id VARCHAR(64) NOT NULL DEFAULT 'default',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_tool_archives_tenant_tool
    ON tool_archives(tenant_id, tool_name);
CREATE INDEX IF NOT EXISTS idx_tool_archives_success
    ON tool_archives(success);

-- ── 媒体记忆 ──
CREATE TABLE IF NOT EXISTS public.media_memories (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(64) NOT NULL DEFAULT 'default',
    media_type VARCHAR(16) NOT NULL,
    media_url TEXT,
    content TEXT,
    description TEXT,
    embedding vector(1024),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ── 记忆追踪 ──
CREATE TABLE IF NOT EXISTS public.memory_traces (
    id SERIAL PRIMARY KEY,
    memory_id INTEGER NOT NULL REFERENCES memories(id) ON DELETE CASCADE,
    action VARCHAR(32) NOT NULL,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_memory_traces_memory
    ON memory_traces(memory_id);

-- ── 记忆计数表（P10 修复）──
-- 维护每个租户未删除记忆数，避免 create_memory 每次写入 COUNT(*) 全表/索引扫描。
-- 由 trg_memories_count 触发器在 INSERT/UPDATE(is_deleted 变更)/DELETE 时实时维护。
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

-- P10 回填：为已有数据初始化计数。否则全新库为空（无副作用），
-- 存量库若仅靠触发器从 0 累加，容量门禁会严重失真（误判仅 1 条记忆）。
-- 此处一次性 seed 正确计数，之后由触发器增量维护，计数器即刻权威。
INSERT INTO user_memory_counts(user_id, cnt)
SELECT user_id, COUNT(*) FROM memories WHERE is_deleted=FALSE
GROUP BY user_id
ON CONFLICT (user_id) DO NOTHING;

-- ── Wiki 页面 ──
CREATE TABLE IF NOT EXISTS public.wiki_pages (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(64) NOT NULL DEFAULT 'default',
    title VARCHAR(256) NOT NULL,
    slug VARCHAR(256) NOT NULL,
    content TEXT DEFAULT '',
    tags TEXT[] DEFAULT '{}',
    is_published BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, slug)
);

-- ── Wiki 迁移兼容 ──
ALTER TABLE public.wiki_pages DROP CONSTRAINT IF EXISTS wiki_pages_slug_key;
ALTER TABLE public.wiki_pages ADD CONSTRAINT wiki_pages_user_id_slug_key UNIQUE (user_id, slug);

-- ── Wiki 版本历史 ──
CREATE TABLE IF NOT EXISTS public.wiki_versions (
    id SERIAL PRIMARY KEY,
    page_id INTEGER NOT NULL REFERENCES wiki_pages(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    summary VARCHAR(256),
    editor VARCHAR(64) DEFAULT 'system',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ── Gate 记录 ──
CREATE TABLE IF NOT EXISTS public.gates (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(64) NOT NULL DEFAULT 'default',
    gate_name VARCHAR(64) NOT NULL,
    passed BOOLEAN NOT NULL,
    detail TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ── HNSW 向量索引（v1.6.0 补齐：所有含 embedding 列的表）──
-- 缺陷 3.3：按表的写入/查询热度分级索引参数，降低写入放大。
--   热表（高频写入+检索）：memories / beliefs / entities / memory_chunks / tmt_sessions
--     → 保持 m=16, ef_construction=200（高精度）
--   冷表（批量蒸馏写入）：tmt_daily / tmt_weekly / tmt_profiles
--     → m=12, ef_construction=128（降低 ~25% 构建时间与内存）
--   低频表（偶发检索）：media_memories / wiki_versions
--     → m=8, ef_construction=64（最低维护成本）
CREATE INDEX IF NOT EXISTS idx_beliefs_embedding
    ON beliefs USING hnsw (embedding vector_cosine_ops) WITH (m=16, ef_construction=200);
CREATE INDEX IF NOT EXISTS idx_entities_embedding
    ON entities USING hnsw (embedding vector_cosine_ops) WITH (m=16, ef_construction=200);
CREATE INDEX IF NOT EXISTS idx_media_memories_embedding
    ON media_memories USING hnsw (embedding vector_cosine_ops) WITH (m=8, ef_construction=64);
CREATE INDEX IF NOT EXISTS idx_memory_chunks_embedding
    ON memory_chunks USING hnsw (embedding vector_cosine_ops) WITH (m=16, ef_construction=200);
CREATE INDEX IF NOT EXISTS idx_tmt_daily_embedding
    ON tmt_daily USING hnsw (embedding vector_cosine_ops) WITH (m=12, ef_construction=128);
CREATE INDEX IF NOT EXISTS idx_tmt_weekly_embedding
    ON tmt_weekly USING hnsw (embedding vector_cosine_ops) WITH (m=12, ef_construction=128);
CREATE INDEX IF NOT EXISTS idx_tmt_profiles_embedding
    ON tmt_profiles USING hnsw (embedding vector_cosine_ops) WITH (m=12, ef_construction=128);
CREATE INDEX IF NOT EXISTS idx_wiki_versions_embedding
    ON wiki_versions USING hnsw (embedding vector_cosine_ops) WITH (m=8, ef_construction=64);

