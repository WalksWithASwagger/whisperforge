#!/usr/bin/env python3
"""
Create missing database tables for WhisperForge
"""

import os
import sys
from core.supabase_integration import get_supabase_client
from core.logging_config import logger

def create_prompts_table(client):
    """Create the prompts table"""
    sql = """
    CREATE TABLE IF NOT EXISTS prompts (
        id SERIAL PRIMARY KEY,
        user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
        prompt_type VARCHAR(100) NOT NULL,
        content TEXT NOT NULL,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        UNIQUE(user_id, prompt_type)
    );
    
    -- Add RLS policies
    ALTER TABLE prompts ENABLE ROW LEVEL SECURITY;
    
    CREATE POLICY "Users can manage their own prompts" ON prompts
        FOR ALL USING (auth.uid()::text = user_id::text);
    """
    
    try:
        result = client.client.rpc('exec_sql', {'sql': sql}).execute()
        logger.logger.info("✅ Prompts table created successfully")
        return True
    except Exception as e:
        logger.logger.error(f"❌ Failed to create prompts table: {e}")
        return False

def create_api_keys_table(client):
    """Create the api_keys table"""
    sql = """
    CREATE TABLE IF NOT EXISTS api_keys (
        id SERIAL PRIMARY KEY,
        user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
        key_name VARCHAR(100) NOT NULL,
        key_value TEXT NOT NULL,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        UNIQUE(user_id, key_name)
    );
    
    -- Add RLS policies
    ALTER TABLE api_keys ENABLE ROW LEVEL SECURITY;
    
    CREATE POLICY "Users can manage their own API keys" ON api_keys
        FOR ALL USING (auth.uid()::text = user_id::text);
    """
    
    try:
        result = client.client.rpc('exec_sql', {'sql': sql}).execute()
        logger.logger.info("✅ API keys table created successfully")
        return True
    except Exception as e:
        logger.logger.error(f"❌ Failed to create api_keys table: {e}")
        return False

def create_sessions_table(client):
    """Create the sessions table for persistent user sessions"""
    sql = """
    CREATE TABLE IF NOT EXISTS sessions (
        id SERIAL PRIMARY KEY,
        session_id VARCHAR(255) UNIQUE NOT NULL,
        user_id VARCHAR(255),
        session_data JSONB NOT NULL,
        expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
    );
    
    -- Indexes for performance
    CREATE INDEX IF NOT EXISTS idx_sessions_session_id ON sessions(session_id);
    CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id);
    CREATE INDEX IF NOT EXISTS idx_sessions_expires_at ON sessions(expires_at);
    
    -- Auto-cleanup expired sessions function
    CREATE OR REPLACE FUNCTION cleanup_expired_sessions()
    RETURNS void AS $$
    BEGIN
        DELETE FROM sessions WHERE expires_at < NOW();
    END;
    $$ LANGUAGE plpgsql;
    """
    
    try:
        result = client.client.rpc('exec_sql', {'sql': sql}).execute()
        logger.logger.info("✅ Sessions table created successfully")
        return True
    except Exception as e:
        logger.logger.error(f"❌ Failed to create sessions table: {e}")
        return False

def test_table_creation(client):
    """Test that tables were created and are accessible"""
    
    # Test prompts table
    try:
        result = client.client.table('prompts').select('*').limit(1).execute()
        logger.logger.info("✅ Prompts table accessible")
    except Exception as e:
        logger.logger.error(f"❌ Prompts table test failed: {e}")
    
    # Test api_keys table
    try:
        result = client.client.table('api_keys').select('*').limit(1).execute()
        logger.logger.info("✅ API keys table accessible")
    except Exception as e:
        logger.logger.error(f"❌ API keys table test failed: {e}")
    
    # Test sessions table
    try:
        result = client.client.table('sessions').select('*').limit(1).execute()
        logger.logger.info("✅ Sessions table accessible")
    except Exception as e:
        logger.logger.error(f"❌ Sessions table test failed: {e}")

def main():
    # Check for required environment variables
    required_vars = ['SUPABASE_URL', 'SUPABASE_ANON_KEY']
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        logger.logger.error(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        logger.logger.error("Please set them before running this script.")
        sys.exit(1)
    
    logger.logger.info("🔧 Creating Missing Database Tables")
    logger.logger.info("=" * 50)
    
    client = get_supabase_client()
    if not client:
        logger.logger.error("❌ Failed to initialize Supabase client")
        return
    
    logger.logger.info("✅ Supabase client initialized")
    
    # Create missing tables
    logger.logger.info("\n📋 Creating Tables:")
    create_prompts_table(client)
    create_api_keys_table(client)
    create_sessions_table(client)
    
    logger.logger.info("\n🧪 Testing Table Access:")
    test_table_creation(client)

if __name__ == "__main__":
    main() 