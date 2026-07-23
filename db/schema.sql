-- ============================================================================
-- Kairos Database Schema
-- Generated from docs/specification/data-model.md v1.0.0
-- Target: PostgreSQL + pgvector
-- 29 tables total
-- ============================================================================

-- Extensions
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- ============================================================================
-- Idempotency: Drop all tables in reverse-dependency order
-- ============================================================================
DROP TABLE IF EXISTS memory_tags CASCADE;
DROP TABLE IF EXISTS memory_relations CASCADE;
DROP TABLE IF EXISTS witness_anchor CASCADE;
DROP TABLE IF EXISTS usage_weight CASCADE;
DROP TABLE IF EXISTS usage_events CASCADE;
DROP TABLE IF EXISTS sublimation_queue CASCADE;
DROP TABLE IF EXISTS forgetting_queue CASCADE;
DROP TABLE IF EXISTS sublimation_outputs CASCADE;
DROP TABLE IF EXISTS memory_chunks CASCADE;
DROP TABLE IF EXISTS memory_entities CASCADE;
DROP TABLE IF EXISTS sync_queue CASCADE;
DROP TABLE IF EXISTS fact_freshness CASCADE;
DROP TABLE IF EXISTS knowledge_evolution CASCADE;
DROP TABLE IF EXISTS playbook_versions CASCADE;
DROP TABLE IF EXISTS procedural_playbooks_fts CASCADE;
DROP TABLE IF EXISTS procedural_playbooks CASCADE;
DROP TABLE IF EXISTS entities CASCADE;
DROP TABLE IF EXISTS memories CASCADE;
DROP TABLE IF EXISTS memory_states CASCADE;
DROP TABLE IF EXISTS audit_log CASCADE;
DROP TABLE IF EXISTS config CASCADE;
DROP TABLE IF EXISTS seeds CASCADE;
DROP TABLE IF EXISTS journal_entries CASCADE;
DROP TABLE IF EXISTS session_summaries CASCADE;
DROP TABLE IF EXISTS daily_reports CASCADE;
DROP TABLE IF EXISTS weekly_packs CASCADE;
DROP TABLE IF EXISTS user_profiles CASCADE;
DROP TABLE IF EXISTS conversation_messages CASCADE;
DROP TABLE IF EXISTS entity_communities CASCADE;


-- ============================================================================
-- 一、核心记忆表
-- ============================================================================

-- memories（主记忆表）
CREATE TABLE IF NOT EXISTS memories (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    path TEXT NOT NULL,
    version INTEGER NOT NULL DEFAULT 1,
    content TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    embedding vector(1536),
    memory_types JSONB NOT NULL,
    contract TEXT NOT NULL DEFAULT 'ondemand',
    hall TEXT DEFAULT 'processing',
    sync_version INTEGER DEFAULT 0,
    provenance TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'active',
    is_identity BOOLEAN DEFAULT FALSE,
    is_structure BOOLEAN DEFAULT FALSE,
    is_deleted BOOLEAN DEFAULT FALSE,
    calibration_confidence FLOAT DEFAULT 0.5 CHECK (calibration_confidence >= 0 AND calibration_confidence <= 1),
    vad_v FLOAT DEFAULT 0 CHECK (vad_v >= -1 AND vad_v <= 1),
    vad_a FLOAT DEFAULT 0 CHECK (vad_a >= -1 AND vad_a <= 1),
    vad_d FLOAT DEFAULT 0 CHECK (vad_d >= -1 AND vad_d <= 1),
    decontextualization_level FLOAT DEFAULT 0 CHECK (decontextualization_level >= 0 AND decontextualization_level <= 1),
    heat_score FLOAT DEFAULT 1.0 CHECK (heat_score >= 0 AND heat_score <= 1),
    expires_at TIMESTAMPTZ,
    encoding_context JSONB,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL,
    superseded_by UUID REFERENCES memories(id),
    last_access_at TIMESTAMPTZ,
    domain TEXT DEFAULT 'general',
    UNIQUE (path, version)
);

CREATE INDEX idx_memories_path ON memories (path);
CREATE INDEX idx_memories_contract ON memories (contract);
CREATE INDEX idx_memories_types ON memories USING GIN (memory_types);
CREATE INDEX idx_memories_created ON memories (created_at);
CREATE INDEX idx_memories_identity ON memories (is_identity) WHERE is_identity = TRUE;
CREATE INDEX idx_memories_status ON memories (status);
CREATE INDEX idx_memories_last_access ON memories (last_access_at);
CREATE INDEX idx_memories_hall_status ON memories (hall, status);
-- Vector index: choose IVFFlat or HNSW based on deployment needs
-- CREATE INDEX idx_memories_embedding ON memories USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
-- CREATE INDEX idx_memories_embedding ON memories USING hnsw (embedding vector_cosine_ops);


-- memory_relations（关系索引表）
CREATE TABLE IF NOT EXISTS memory_relations (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    source_id UUID NOT NULL REFERENCES memories(id),
    target_id UUID NOT NULL REFERENCES memories(id),
    relation_type TEXT NOT NULL,
    strength FLOAT DEFAULT 1.0 CHECK (strength >= 0 AND strength <= 1),
    created_at TIMESTAMPTZ NOT NULL,
    UNIQUE (source_id, target_id, relation_type)
);


-- memory_tags（记忆标签表）
CREATE TABLE IF NOT EXISTS memory_tags (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    memory_id UUID NOT NULL REFERENCES memories(id) ON DELETE CASCADE,
    key TEXT NOT NULL,
    value TEXT
);


-- ============================================================================
-- 二、双副本存储
-- ============================================================================

-- witness_anchor（见证锚定主副本）
CREATE TABLE IF NOT EXISTS witness_anchor (
    memory_id UUID PRIMARY KEY REFERENCES memories(id),
    narrative_coherence_score FLOAT DEFAULT 0 CHECK (narrative_coherence_score >= 0 AND narrative_coherence_score <= 1),
    last_calibrated_at TIMESTAMPTZ,
    calibration_count INTEGER DEFAULT 0,
    anchor_version INTEGER DEFAULT 1,
    overridden_by_external BOOLEAN DEFAULT FALSE
);


-- usage_weight（使用权重影子副本）
CREATE TABLE IF NOT EXISTS usage_weight (
    memory_id UUID PRIMARY KEY REFERENCES memories(id),
    usage_count INTEGER DEFAULT 0,
    last_used_at TIMESTAMPTZ,
    activation_weight FLOAT DEFAULT 0 CHECK (activation_weight >= 0 AND activation_weight <= 1),
    use_load_retrieval FLOAT DEFAULT 0,
    use_load_verification FLOAT DEFAULT 0,
    use_load_contribution FLOAT DEFAULT 0,
    use_load_simulation FLOAT DEFAULT 0,
    use_load_implicit FLOAT DEFAULT 0,
    exploration_confidence FLOAT DEFAULT 0 CHECK (exploration_confidence >= 0 AND exploration_confidence <= 1),
    suspect_flag BOOLEAN DEFAULT FALSE
);


-- ============================================================================
-- 三、使用事件表
-- ============================================================================

-- usage_events（使用事件总线持久化）
CREATE TABLE IF NOT EXISTS usage_events (
    id BIGSERIAL PRIMARY KEY,
    event_type TEXT NOT NULL,
    source_layer TEXT NOT NULL,
    memory_id UUID REFERENCES memories(id),
    context JSONB,
    severity INTEGER DEFAULT 0 CHECK (severity >= 0 AND severity <= 9),
    created_at TIMESTAMPTZ NOT NULL,
    ttl INTERVAL
);


-- ============================================================================
-- 四、调度与状态表
-- ============================================================================

-- sublimation_queue（升华队列）
CREATE TABLE IF NOT EXISTS sublimation_queue (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    memory_id UUID NOT NULL REFERENCES memories(id),
    stage TEXT NOT NULL,
    status TEXT NOT NULL,
    output TEXT,
    created_at TIMESTAMPTZ NOT NULL,
    completed_at TIMESTAMPTZ
);


-- forgetting_queue（遗忘队列）
CREATE TABLE IF NOT EXISTS forgetting_queue (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    memory_id UUID NOT NULL REFERENCES memories(id),
    forgetting_score FLOAT NOT NULL CHECK (forgetting_score >= 0 AND forgetting_score <= 1),
    reason TEXT,
    status TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL
);


-- ============================================================================
-- 五、审计表
-- ============================================================================

-- audit_log（审计日志）
CREATE TABLE IF NOT EXISTS audit_log (
    id BIGSERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL,
    operator TEXT NOT NULL,
    action TEXT NOT NULL,
    target_type TEXT,
    target_id TEXT,
    content_hash TEXT,
    previous_hash TEXT,
    hmac TEXT NOT NULL,
    details JSONB,
    redline_id TEXT
);


-- ============================================================================
-- 六、配置表
-- ============================================================================

-- config（运行时配置）
CREATE TABLE IF NOT EXISTS config (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    scope TEXT DEFAULT 'static',
    updated_at TIMESTAMPTZ NOT NULL,
    updated_by TEXT
);


-- seeds（种子锚点）
CREATE TABLE IF NOT EXISTS seeds (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    path TEXT NOT NULL UNIQUE,
    seed_type TEXT NOT NULL,
    initial_confidence FLOAT NOT NULL CHECK (initial_confidence >= 0 AND initial_confidence <= 1),
    current_confidence FLOAT NOT NULL CHECK (current_confidence >= 0 AND current_confidence <= 1),
    degradation_level FLOAT DEFAULT 0 CHECK (degradation_level >= 0 AND degradation_level <= 1),
    status TEXT NOT NULL DEFAULT 'active',
    created_at TIMESTAMPTZ NOT NULL,
    last_reviewed_at TIMESTAMPTZ,
    review_count INTEGER DEFAULT 0,
    bias_reset_count INTEGER DEFAULT 0,
    content_snapshot JSONB
);


-- sublimation_outputs（升华输出表，v1.0 新增）
CREATE TABLE IF NOT EXISTS sublimation_outputs (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    memory_id UUID NOT NULL REFERENCES memories(id),
    stage TEXT NOT NULL,
    output_type TEXT NOT NULL,
    content TEXT NOT NULL,
    confidence FLOAT NOT NULL CHECK (confidence >= 0 AND confidence <= 1),
    status TEXT NOT NULL DEFAULT 'pending_review',
    created_at TIMESTAMPTZ NOT NULL
);


-- memory_states（记忆状态转换跟踪表）
CREATE TABLE IF NOT EXISTS memory_states (
    id BIGSERIAL PRIMARY KEY,
    memory_id UUID NOT NULL,
    memory_type TEXT NOT NULL,
    state TEXT NOT NULL,
    previous_state TEXT DEFAULT '',
    state_changed_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    reason TEXT DEFAULT '',
    source TEXT DEFAULT 'system'
);

CREATE INDEX idx_memory_states_lookup ON memory_states (memory_id, state_changed_at);


-- knowledge_evolution（知识演化追踪表）
CREATE TABLE IF NOT EXISTS knowledge_evolution (
    id BIGSERIAL PRIMARY KEY,
    source_id UUID NOT NULL,
    target_id UUID NOT NULL,
    relation_type TEXT NOT NULL,
    confidence FLOAT DEFAULT 0.5,
    detection_method TEXT DEFAULT 'jaccard',
    reason TEXT DEFAULT '',
    created_at TIMESTAMPTZ DEFAULT now()
);


-- journal_entries（升华原始轮次表，v1.0 新增）
CREATE TABLE IF NOT EXISTS journal_entries (
    id BIGSERIAL PRIMARY KEY,
    session_id TEXT NOT NULL,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    source TEXT,
    platform TEXT,
    filtered BOOLEAN DEFAULT FALSE,
    captured_at TIMESTAMPTZ NOT NULL
);


-- session_summaries（L1 会话摘要表，v1.0 新增）
CREATE TABLE IF NOT EXISTS session_summaries (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    session_id TEXT NOT NULL UNIQUE,
    user_id TEXT NOT NULL,
    summary TEXT,
    key_decisions JSONB,
    entities JSONB,
    heat_score FLOAT DEFAULT 1.0,
    token_count INTEGER DEFAULT 0,
    start_time TIMESTAMPTZ,
    end_time TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL,
    ttl_days INTEGER DEFAULT 30
);


-- daily_reports（L2 日报告表，v1.0 新增）
CREATE TABLE IF NOT EXISTS daily_reports (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id TEXT NOT NULL,
    report_date DATE NOT NULL,
    summary TEXT,
    insights JSONB,
    session_count INTEGER DEFAULT 0,
    decision_count INTEGER DEFAULT 0,
    heat_score FLOAT DEFAULT 1.0,
    created_at TIMESTAMPTZ NOT NULL,
    UNIQUE (user_id, report_date)
);


-- weekly_packs（L3 周知识包表，v1.0 新增）
CREATE TABLE IF NOT EXISTS weekly_packs (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id TEXT NOT NULL,
    week_start DATE NOT NULL,
    patterns JSONB,
    trends JSONB,
    key_decisions JSONB,
    session_ids UUID[],
    heat_score FLOAT DEFAULT 1.0,
    created_at TIMESTAMPTZ NOT NULL,
    UNIQUE (user_id, week_start)
);


-- user_profiles（L4 用户画像表，v1.0 新增）
CREATE TABLE IF NOT EXISTS user_profiles (
    user_id TEXT NOT NULL,
    trait_type TEXT NOT NULL DEFAULT 'dynamic',
    preferences JSONB DEFAULT '{}',
    traits JSONB DEFAULT '{}',
    skill_summaries JSONB DEFAULT '{}',
    confidence FLOAT DEFAULT 0.5,
    version INTEGER DEFAULT 1,
    updated_at TIMESTAMPTZ NOT NULL,
    PRIMARY KEY (user_id, trait_type)
);


-- ============================================================================
-- 七、扩展表
-- ============================================================================

-- conversation_messages（对话消息持久化）
CREATE TABLE IF NOT EXISTS conversation_messages (
    id BIGSERIAL PRIMARY KEY,
    session_id TEXT NOT NULL,
    role TEXT NOT NULL,
    content TEXT,
    tool_call_id TEXT,
    tool_calls JSONB,
    tool_name TEXT,
    timestamp FLOAT NOT NULL,
    token_count INTEGER,
    finish_reason TEXT,
    reasoning TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_conv_session ON conversation_messages (session_id);
CREATE INDEX idx_conv_timestamp ON conversation_messages (timestamp);


-- entities（实体知识图谱）
CREATE TABLE IF NOT EXISTS entities (
    id BIGSERIAL PRIMARY KEY,
    user_id TEXT NOT NULL,
    name TEXT NOT NULL,
    type TEXT DEFAULT 'concept',
    description TEXT,
    embedding vector(1536),
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE (user_id, name)
);


-- memory_entities（记忆-实体关联）
CREATE TABLE IF NOT EXISTS memory_entities (
    id BIGSERIAL PRIMARY KEY,
    memory_id UUID NOT NULL REFERENCES memories(id),
    entity_id BIGINT NOT NULL REFERENCES entities(id),
    relation TEXT DEFAULT 'mentions',
    valid_from TIMESTAMPTZ,
    valid_to TIMESTAMPTZ,
    superseded_by BIGINT,
    UNIQUE (memory_id, entity_id, valid_from)
);


-- memory_chunks（长文本分块索引）
CREATE TABLE IF NOT EXISTS memory_chunks (
    id BIGSERIAL PRIMARY KEY,
    memory_id UUID NOT NULL REFERENCES memories(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    text_hash TEXT,
    embedding vector(1536),
    created_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE (memory_id, chunk_index)
);


-- sync_queue（端云同步队列）
CREATE TABLE IF NOT EXISTS sync_queue (
    id BIGSERIAL PRIMARY KEY,
    memory_id UUID NOT NULL REFERENCES memories(id),
    operation TEXT NOT NULL,
    sync_direction TEXT NOT NULL,
    sync_state TEXT NOT NULL,
    local_version INTEGER NOT NULL,
    remote_version INTEGER,
    created_at TIMESTAMPTZ NOT NULL,
    synced_at TIMESTAMPTZ
);


-- fact_freshness（事实新鲜度元数据）
CREATE TABLE IF NOT EXISTS fact_freshness (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    subject_type TEXT NOT NULL,
    subject_id UUID NOT NULL,
    fact_key TEXT NOT NULL,
    truth_type TEXT NOT NULL,
    validator_kind TEXT DEFAULT 'none',
    validator_spec JSONB,
    ttl_days INTEGER DEFAULT 0,
    last_checked_at TIMESTAMPTZ,
    valid_until TIMESTAMPTZ,
    status TEXT DEFAULT 'needs_live_check',
    stale_reason TEXT DEFAULT '',
    superseded_by TEXT DEFAULT '',
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);


-- procedural_playbooks（过程知识 Playbook）
CREATE TABLE IF NOT EXISTS procedural_playbooks (
    id TEXT PRIMARY KEY,
    scope_id TEXT NOT NULL,
    shared_scope_id TEXT,
    task_class TEXT NOT NULL,
    title TEXT NOT NULL,
    trigger TEXT,
    goal TEXT,
    preconditions JSONB DEFAULT '[]',
    steps JSONB NOT NULL,
    pitfalls JSONB DEFAULT '[]',
    verification JSONB DEFAULT '[]',
    cleanup JSONB DEFAULT '[]',
    evidence_anchors JSONB DEFAULT '[]',
    related_skills JSONB DEFAULT '[]',
    environment_constraints JSONB DEFAULT '{}',
    reuse_policy JSONB DEFAULT '{}',
    status TEXT DEFAULT 'candidate',
    confidence FLOAT DEFAULT 0.5,
    success_count INTEGER DEFAULT 0,
    failure_count INTEGER DEFAULT 0,
    stale_count INTEGER DEFAULT 0,
    created_from_episode_id TEXT,
    superseded_by TEXT,
    last_used_at TIMESTAMPTZ,
    last_verified_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    metadata JSONB DEFAULT '{}'
);


-- procedural_playbooks_fts（Playbook 全文索引）
CREATE TABLE IF NOT EXISTS procedural_playbooks_fts (
    playbook_id TEXT PRIMARY KEY REFERENCES procedural_playbooks(id),
    title TEXT,
    trigger TEXT,
    goal TEXT,
    preconditions TEXT,
    steps TEXT,
    pitfalls TEXT,
    verification TEXT
);


-- playbook_versions（Playbook 版本历史）
CREATE TABLE IF NOT EXISTS playbook_versions (
    id TEXT PRIMARY KEY,
    playbook_id TEXT NOT NULL REFERENCES procedural_playbooks(id),
    version INTEGER NOT NULL,
    change_type TEXT NOT NULL,
    change_reason TEXT,
    snapshot JSONB,
    created_at TIMESTAMPTZ DEFAULT now()
);


-- entity_communities（实体社区）
CREATE TABLE IF NOT EXISTS entity_communities (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    community_label TEXT NOT NULL,
    member_entity_ids UUID[] NOT NULL,
    summary TEXT,
    detection_algorithm TEXT DEFAULT 'label_propagation',
    confidence FLOAT DEFAULT 0.5,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);
