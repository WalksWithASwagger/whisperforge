-- WhisperForge Supabase Database Schema
-- Run this in your Supabase SQL editor to create all necessary tables

-- Enable Row Level Security
ALTER DATABASE postgres SET "app.jwt_secret" TO 'your-jwt-secret-here';

-- Users table (enhanced from SQLite version)
CREATE TABLE IF NOT EXISTS users (
    id BIGSERIAL PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    password TEXT, -- Nullable to support OAuth users
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    api_keys JSONB DEFAULT '{}',
    usage_quota INTEGER DEFAULT 60, -- Minutes per month
    usage_current REAL DEFAULT 0,
    is_admin BOOLEAN DEFAULT FALSE,
    subscription_tier TEXT DEFAULT 'free',
    last_login TIMESTAMPTZ,
    profile_data JSONB DEFAULT '{}'
);

-- Content storage table
CREATE TABLE IF NOT EXISTS content (
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
CREATE TABLE IF NOT EXISTS knowledge_base (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id) ON DELETE CASCADE,
    filename TEXT NOT NULL,
    content TEXT NOT NULL,
    file_type TEXT DEFAULT 'text',
    file_size INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE,
    UNIQUE(user_id, filename)
);

-- Custom prompts table
CREATE TABLE IF NOT EXISTS custom_prompts (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id) ON DELETE CASCADE,
    prompt_type TEXT NOT NULL, -- wisdom_extraction, outline_creation, etc.
    content TEXT NOT NULL,
    version INTEGER DEFAULT 1,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE,
    UNIQUE(user_id, prompt_type)
);

-- Pipeline execution logs table
CREATE TABLE IF NOT EXISTS pipeline_logs (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id) ON DELETE CASCADE,
    content_id BIGINT REFERENCES content(id) ON DELETE SET NULL,
    pipeline_type TEXT NOT NULL DEFAULT 'full', -- full, wisdom_only, etc.
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
CREATE TABLE IF NOT EXISTS api_usage (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id) ON DELETE CASCADE,
    api_provider TEXT NOT NULL, -- openai, anthropic, grok
    endpoint TEXT NOT NULL, -- transcription, completion, etc.
    tokens_used INTEGER DEFAULT 0,
    cost_cents INTEGER DEFAULT 0,
    request_duration_ms INTEGER DEFAULT 0,
    success BOOLEAN DEFAULT TRUE,
    error_code TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'
);

-- User sessions table
CREATE TABLE IF NOT EXISTS user_sessions (
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

-- Webhook logs table (for integrations)
CREATE TABLE IF NOT EXISTS webhook_logs (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id) ON DELETE CASCADE,
    webhook_type TEXT NOT NULL, -- notion, zapier, etc.
    payload JSONB NOT NULL,
    response JSONB,
    status_code INTEGER,
    success BOOLEAN DEFAULT FALSE,
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    processed_at TIMESTAMPTZ
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_content_user_id ON content(user_id);
CREATE INDEX IF NOT EXISTS idx_content_created_at ON content(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_knowledge_base_user_id ON knowledge_base(user_id);
CREATE INDEX IF NOT EXISTS idx_custom_prompts_user_id ON custom_prompts(user_id);
CREATE INDEX IF NOT EXISTS idx_pipeline_logs_user_id ON pipeline_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_pipeline_logs_created_at ON pipeline_logs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_api_usage_user_id ON api_usage(user_id);
CREATE INDEX IF NOT EXISTS idx_api_usage_created_at ON api_usage(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_user_sessions_token ON user_sessions(session_token);
CREATE INDEX IF NOT EXISTS idx_user_sessions_user_id ON user_sessions(user_id);

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Add updated_at triggers
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_content_updated_at BEFORE UPDATE ON content
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_knowledge_base_updated_at BEFORE UPDATE ON knowledge_base
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_custom_prompts_updated_at BEFORE UPDATE ON custom_prompts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Row Level Security (RLS) Policies
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE content ENABLE ROW LEVEL SECURITY;
ALTER TABLE knowledge_base ENABLE ROW LEVEL SECURITY;
ALTER TABLE custom_prompts ENABLE ROW LEVEL SECURITY;
ALTER TABLE pipeline_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE api_usage ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_sessions ENABLE ROW LEVEL SECURITY;

-- Users can only see/edit their own data
CREATE POLICY "Users can view own profile" ON users
    FOR ALL USING (auth.uid()::text = id::text);

CREATE POLICY "Users can view own content" ON content
    FOR ALL USING (auth.uid()::text = user_id::text);

CREATE POLICY "Users can manage own knowledge base" ON knowledge_base
    FOR ALL USING (auth.uid()::text = user_id::text);

CREATE POLICY "Users can manage own prompts" ON custom_prompts
    FOR ALL USING (auth.uid()::text = user_id::text);

CREATE POLICY "Users can view own logs" ON pipeline_logs
    FOR SELECT USING (auth.uid()::text = user_id::text);

CREATE POLICY "Users can view own API usage" ON api_usage
    FOR SELECT USING (auth.uid()::text = user_id::text);

CREATE POLICY "Users can manage own sessions" ON user_sessions
    FOR ALL USING (auth.uid()::text = user_id::text);

-- Admin policies (admins can see everything)
CREATE POLICY "Admins can see all data" ON users
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM users 
            WHERE id::text = auth.uid()::text 
            AND is_admin = true
        )
    );

CREATE POLICY "Admins can see all content" ON content
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM users 
            WHERE id::text = auth.uid()::text 
            AND is_admin = true
        )
    );

-- Create some useful views
CREATE OR REPLACE VIEW user_stats AS
SELECT 
    u.id,
    u.email,
    u.subscription_tier,
    u.usage_quota,
    u.usage_current,
    COUNT(c.id) as total_content_pieces,
    COUNT(pl.id) as total_pipeline_runs,
    SUM(pl.duration_seconds) as total_processing_time,
    MAX(pl.created_at) as last_pipeline_run,
    COUNT(CASE WHEN pl.success = true THEN 1 END) as successful_runs,
    COUNT(CASE WHEN pl.success = false THEN 1 END) as failed_runs
FROM users u
LEFT JOIN content c ON u.id = c.user_id
LEFT JOIN pipeline_logs pl ON u.id = pl.user_id
GROUP BY u.id, u.email, u.subscription_tier, u.usage_quota, u.usage_current;

CREATE OR REPLACE VIEW recent_activity AS
SELECT 
    'content' as activity_type,
    c.user_id,
    c.title as description,
    c.created_at,
    c.id as reference_id
FROM content c
UNION ALL
SELECT 
    'pipeline' as activity_type,
    pl.user_id,
    CONCAT(pl.pipeline_type, ' pipeline with ', pl.ai_provider) as description,
    pl.created_at,
    pl.id as reference_id
FROM pipeline_logs pl
ORDER BY created_at DESC;

-- Insert default admin user (update with your details)
INSERT INTO users (email, password, is_admin, subscription_tier, usage_quota)
VALUES (
    'admin@whisperforge.com',
    'change-this-password-hash',
    true,
    'admin',
    999999
) ON CONFLICT (email) DO NOTHING;

-- Insert default prompts (these will be system-wide defaults)
INSERT INTO custom_prompts (user_id, prompt_type, content) VALUES
(1, 'wisdom_extraction', 'Extract the key insights and wisdom from this content. Focus on actionable advice and important concepts.'),
(1, 'outline_creation', 'Create a structured outline for this content that could be used for an article or presentation.'),
(1, 'social_media', 'Create social media posts for different platforms based on this content. Include relevant hashtags.'),
(1, 'image_prompts', 'Generate detailed image prompts that could be used with AI image generators to create visuals for this content.'),
(1, 'article_writing', 'Write a comprehensive article based on the provided outline and content. Make it engaging and well-structured.')
ON CONFLICT (user_id, prompt_type) DO NOTHING; 