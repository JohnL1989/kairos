-- migrations/0001_initial.sql
-- schema.sql 创建后的初始化迁移，补齐缺失列

-- beliefs 表补列
ALTER TABLE public.beliefs
  ADD COLUMN IF NOT EXISTS embedding vector(1024),
  ADD COLUMN IF NOT EXISTS status VARCHAR(16) DEFAULT 'tentative',
  ADD COLUMN IF NOT EXISTS trajectory JSONB DEFAULT '[]',
  ADD COLUMN IF NOT EXISTS valid_from DATE,
  ADD COLUMN IF NOT EXISTS evidence_memories JSONB DEFAULT '[]';

-- media_memories 表补列
ALTER TABLE public.media_memories ADD COLUMN IF NOT EXISTS media_url TEXT;

-- 移除 hall 相关残留
ALTER TABLE memories DROP CONSTRAINT IF EXISTS chk_hall;
ALTER TABLE memories RENAME COLUMN hall TO hall_deprecated;
