-- Basic WhisperForge Supabase Schema (No Permission Issues)
-- Copy and paste this entire content into Supabase SQL Editor

-- Users table
CREATE TABLE users (
    id BIGSERIAL PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    api_keys JSONB DEFAULT '{}',
    usage_quota INTEGER DEFAULT 60,
    usage_current REAL DEFAULT 0,
    is_admin BOOLEAN DEFAULT FALSE,
    subscription_tier TEXT DEFAULT 'free',
    last_login TIMESTAMPTZ,
    profile_data JSONB DEFAULT '{}'
);

-- Content storage table
CREATE TABLE content (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id) ON DELETE CASCADE,
    title TEXT NOT NULL DEFAULT 'Untitled',
    transcript TEXT DEFAULT '',
    wisdom TEXT DEFAULT '',
    outline TEXT DEFAULT '',
    social_content TEXT DEFAULT '',
    image_prompts TEXT DEFAULT '',
    article TEXT DEFAULT '',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    is_archived BOOLEAN DEFAULT FALSE,
    tags TEXT[] DEFAULT '{}',
    notion_page_id TEXT
);

-- Knowledge base files table
CREATE TABLE knowledge_base (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id) ON DELETE CASCADE,
    filename TEXT NOT NULL,
    content TEXT NOT NULL,
    file_type TEXT DEFAULT 'text',
    file_size INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE
);

-- Custom prompts table
CREATE TABLE custom_prompts (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id) ON DELETE CASCADE,
    prompt_type TEXT NOT NULL,
    content TEXT NOT NULL,
    version INTEGER DEFAULT 1,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE
);

-- Pipeline execution logs table
CREATE TABLE pipeline_logs (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id) ON DELETE CASCADE,
    content_id BIGINT REFERENCES content(id) ON DELETE SET NULL,
    pipeline_type TEXT NOT NULL DEFAULT 'full',
    duration_seconds REAL DEFAULT 0,
    ai_provider TEXT NOT NULL DEFAULT 'unknown',
    model TEXT NOT NULL DEFAULT 'unknown',
    success BOOLEAN DEFAULT FALSE,
    error_message TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    tokens_used INTEGER DEFAULT 0,
    cost_cents INTEGER DEFAULT 0
);

-- API usage tracking table
CREATE TABLE api_usage (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id) ON DELETE CASCADE,
    api_provider TEXT NOT NULL,
    endpoint TEXT NOT NULL,
    tokens_used INTEGER DEFAULT 0,
    cost_cents INTEGER DEFAULT 0,
    request_duration_ms INTEGER DEFAULT 0,
    success BOOLEAN DEFAULT TRUE,
    error_code TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'
);

-- User sessions table
CREATE TABLE user_sessions (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id) ON DELETE CASCADE,
    session_token TEXT UNIQUE NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_activity TIMESTAMPTZ DEFAULT NOW(),
    ip_address INET,
    user_agent TEXT,
    is_active BOOLEAN DEFAULT TRUE
);

-- Add a test admin user
INSERT INTO users (email, password, is_admin, subscription_tier, usage_quota)
VALUES (
    'admin@whisperforge.com',
    'temp-password-hash',
    true,
    'admin',
    999999
); 