-- migrations/0002_health_log.sql
-- Phase 1: health_log table + memory_traces column fix

-- health_log table: service health check history
CREATE TABLE IF NOT EXISTS health_log (
    id BIGSERIAL PRIMARY KEY,
    service VARCHAR(64) NOT NULL,
    status VARCHAR(16) NOT NULL,
    latency_ms INTEGER,
    error TEXT,
    checked_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_health_log_time ON health_log (checked_at DESC);
CREATE INDEX IF NOT EXISTS idx_health_log_service ON health_log (service);

-- memory_traces: add columns used by code (user_id, op, details)
-- schema.sql defines action/metadata but code uses op/details/user_id
DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_schema = 'public' AND table_name = 'memory_traces' AND column_name = 'user_id') THEN
        ALTER TABLE memory_traces ADD COLUMN user_id VARCHAR(64) NOT NULL DEFAULT 'default';
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_schema = 'public' AND table_name = 'memory_traces' AND column_name = 'op') THEN
        ALTER TABLE memory_traces ADD COLUMN op VARCHAR(32);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_schema = 'public' AND table_name = 'memory_traces' AND column_name = 'details') THEN
        ALTER TABLE memory_traces ADD COLUMN details JSONB;
    END IF;
END$$;
