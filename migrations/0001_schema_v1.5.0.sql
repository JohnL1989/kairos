-- Aion Memory — 数据库迁移 0001：补齐缺失列（v1.5.0）
-- 适用场景：从旧版 schema（2026-07 之前）升级的用户
-- 注意：本迁移假定 old schema 已有记忆主表。全新部署的用户直接用 schema.sql。

-- ── 1. memories 表补齐 ──

-- 新增列（仅当不存在时添加）
ALTER TABLE public.memories ADD COLUMN IF NOT EXISTS tmt_level INTEGER DEFAULT 1;
ALTER TABLE public.memories ADD COLUMN IF NOT EXISTS last_accessed TIMESTAMP WITH TIME ZONE;
ALTER TABLE public.memories ADD COLUMN IF NOT EXISTS forgotten_at TIMESTAMP WITH TIME ZONE;
ALTER TABLE public.memories ADD COLUMN IF NOT EXISTS invalid_at TIMESTAMP WITH TIME ZONE;
ALTER TABLE public.memories ADD COLUMN IF NOT EXISTS importance FLOAT DEFAULT 0.0;
ALTER TABLE public.memories ADD COLUMN IF NOT EXISTS metadata JSONB DEFAULT '{}';
ALTER TABLE public.memories ADD COLUMN IF NOT EXISTS project_id VARCHAR(64);

-- tier 列迁移：如果原有 tier 是 INTEGER，转为 VARCHAR
-- PostgreSQL 自动处理隐式转换，但如果原表用 INTEGER，需先改类型
-- 本脚本假设 tier 已为 VARCHAR（v1.4+）。如是 INTEGER 请手动执行：
-- ALTER TABLE public.memories ALTER COLUMN tier TYPE VARCHAR(4) USING tier::VARCHAR;

-- 补齐索引
CREATE INDEX IF NOT EXISTS idx_memories_user_deleted
    ON memories(user_id, is_deleted);
CREATE INDEX IF NOT EXISTS idx_memories_user_deleted_created
    ON memories(user_id, is_deleted, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_memories_user_deleted_heat
    ON memories(user_id, is_deleted, heat_score DESC);


-- ── 2. beliefs 表补齐 ──

ALTER TABLE public.beliefs ADD COLUMN IF NOT EXISTS status VARCHAR(16) DEFAULT 'active';
ALTER TABLE public.beliefs ADD COLUMN IF NOT EXISTS trajectory JSONB DEFAULT '[]';
ALTER TABLE public.beliefs ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();


-- ── 3. media_memories 表重建 ──
-- 旧 schema: id, user_id, media_type, file_path, content, description, created_at
-- 新 schema: id, user_id, media_type, media_url, content, description, embedding, metadata, created_at

ALTER TABLE public.media_memories ADD COLUMN IF NOT EXISTS media_url TEXT;
ALTER TABLE public.media_memories ADD COLUMN IF NOT EXISTS embedding vector(1024);
ALTER TABLE public.media_memories ADD COLUMN IF NOT EXISTS metadata JSONB DEFAULT '{}';

-- 保留 file_path 列（如有旧数据），后续版本可移除
-- 迁移数据：如果 file_path 有值而 media_url 为空，复制过去
UPDATE public.media_memories
    SET media_url = file_path
    WHERE media_url IS NULL AND file_path IS NOT NULL;


-- ── 4. projects 表重建 ──
-- 旧 schema: id, user_id, project_name, description, status, created_at, updated_at
-- 新 schema: id, project_id, tenant_id, name, description, status, created_at, updated_at
-- 注意：由于表结构变更较大（user_id→tenant_id, project_name→name, 新增 project_id），
-- 建议旧数据迁移以下步骤：
--   (a) 创建临时新表
--   (b) 迁移数据
--   (c) 重命名旧表、新表

-- 步骤 A：建临时表
CREATE TABLE IF NOT EXISTS public.projects_new (
    id SERIAL PRIMARY KEY,
    project_id VARCHAR(64) UNIQUE NOT NULL,
    tenant_id VARCHAR(64) NOT NULL DEFAULT 'default',
    name VARCHAR(128) NOT NULL,
    description TEXT,
    status VARCHAR(16) DEFAULT 'active',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 步骤 B：迁移旧数据（如果旧表存在且有数据）
DO $$
BEGIN
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'projects' AND table_schema = 'public') THEN
        -- 检测旧表是哪个版本的（通过列名）
        IF EXISTS (SELECT FROM information_schema.columns
                   WHERE table_name = 'projects' AND column_name = 'project_name') THEN
            -- 旧版（user_id, project_name）
            INSERT INTO public.projects_new (project_id, tenant_id, name, description, status, created_at, updated_at)
            SELECT
                'proj_migrated_' || id,  -- 从旧 id 生成 project_id
                COALESCE(user_id, 'default'),
                project_name,
                description,
                COALESCE(status, 'active'),
                created_at,
                updated_at
            FROM public.projects
            ON CONFLICT (project_id) DO NOTHING;
        ELSE
            -- 可能已是新版或空表
            INSERT INTO public.projects_new (project_id, tenant_id, name, description, status, created_at, updated_at)
            SELECT
                project_id, tenant_id, name, description, status, created_at, updated_at
            FROM public.projects
            ON CONFLICT (project_id) DO NOTHING;
        END IF;
    END IF;
END $$;

-- 步骤 C：如果新旧表都有数据，替换
DO $$
BEGIN
    IF EXISTS (SELECT FROM public.projects_new LIMIT 1) AND
       EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'projects') THEN
        DROP TABLE IF EXISTS public.projects_old;
        ALTER TABLE public.projects RENAME TO projects_old;
        ALTER TABLE public.projects_new RENAME TO projects;
    ELSE
        -- 新表无数据 → 用原有表或留在新表
        IF NOT EXISTS (SELECT FROM public.projects_new LIMIT 1) THEN
            DROP TABLE IF EXISTS public.projects_new;
        END IF;
    END IF;
END $$;

-- projects 索引
CREATE INDEX IF NOT EXISTS idx_projects_tenant ON projects(tenant_id);
CREATE INDEX IF NOT EXISTS idx_projects_status ON projects(status);


-- ── 5. tool_archives 表重建 ──
-- 旧 schema: id, user_id, tool_name, pattern, pitfalls, metadata, created_at
-- 新 schema: id, archive_id, tool_name, params, result, success, error_type, knowledge_type, session_id, project_id, duration_ms, tenant_id, created_at

CREATE TABLE IF NOT EXISTS public.tool_archives_new (
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

DO $$
BEGIN
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'tool_archives') THEN
        INSERT INTO public.tool_archives_new (
            archive_id, tool_name, params, result, success,
            error_type, knowledge_type, session_id, project_id, duration_ms, tenant_id, created_at
        )
        SELECT
            'ta_migrated_' || id,
            tool_name,
            '{}'::jsonb,
            COALESCE(pattern, ''),
            TRUE,  -- 旧表 pattern 可视为成功的沉淀
            NULL,
            CASE WHEN pitfalls IS NOT NULL AND array_length(pitfalls, 1) > 0
                 THEN 'pitfall' ELSE 'skill' END,
            NULL, NULL, NULL,
            COALESCE(user_id, 'default'),
            created_at
        FROM public.tool_archives
        ON CONFLICT (archive_id) DO NOTHING;

        DROP TABLE IF EXISTS public.tool_archives_old;
        ALTER TABLE public.tool_archives RENAME TO tool_archives_old;
        ALTER TABLE public.tool_archives_new RENAME TO tool_archives;
    ELSE
        IF NOT EXISTS (SELECT FROM public.tool_archives_new LIMIT 1) THEN
            DROP TABLE IF EXISTS public.tool_archives_new;
        END IF;
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_tool_archives_tenant_tool
    ON tool_archives(tenant_id, tool_name);
CREATE INDEX IF NOT EXISTS idx_tool_archives_success
    ON tool_archives(success);


-- ── 6. entities 表补齐 ──

ALTER TABLE public.entities ADD COLUMN IF NOT EXISTS memory_id INTEGER REFERENCES memories(id) ON DELETE SET NULL;


-- ── 7. memory_traces 索引 ──

CREATE INDEX IF NOT EXISTS idx_memory_traces_memory
    ON memory_traces(memory_id);


-- ── 8. beliefs 表补齐证据和有效期 ──

ALTER TABLE public.beliefs ADD COLUMN IF NOT EXISTS evidence_memories INTEGER[] DEFAULT '{}';
ALTER TABLE public.beliefs ADD COLUMN IF NOT EXISTS valid_from TIMESTAMP WITH TIME ZONE DEFAULT NOW();


-- ── 9. 补齐 8 张表 HNSW 向量索引 ──

CREATE INDEX IF NOT EXISTS idx_beliefs_embedding
    ON beliefs USING hnsw (embedding vector_cosine_ops) WITH (m=16, ef_construction=200);
CREATE INDEX IF NOT EXISTS idx_entities_embedding
    ON entities USING hnsw (embedding vector_cosine_ops) WITH (m=16, ef_construction=200);
CREATE INDEX IF NOT EXISTS idx_media_memories_embedding
    ON media_memories USING hnsw (embedding vector_cosine_ops) WITH (m=16, ef_construction=200);
CREATE INDEX IF NOT EXISTS idx_memory_chunks_embedding
    ON memory_chunks USING hnsw (embedding vector_cosine_ops) WITH (m=16, ef_construction=200);
CREATE INDEX IF NOT EXISTS idx_tmt_daily_embedding
    ON tmt_daily USING hnsw (embedding vector_cosine_ops) WITH (m=16, ef_construction=200);
CREATE INDEX IF NOT EXISTS idx_tmt_weekly_embedding
    ON tmt_weekly USING hnsw (embedding vector_cosine_ops) WITH (m=16, ef_construction=200);
CREATE INDEX IF NOT EXISTS idx_tmt_profiles_embedding
    ON tmt_profiles USING hnsw (embedding vector_cosine_ops) WITH (m=16, ef_construction=200);
CREATE INDEX IF NOT EXISTS idx_wiki_versions_embedding
    ON wiki_versions USING hnsw (embedding vector_cosine_ops) WITH (m=16, ef_construction=200);
