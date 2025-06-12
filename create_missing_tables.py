#!/usr/bin/env python3
"""
Create missing database tables for WhisperForge
"""

import os
from core.supabase_integration import get_supabase_client

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
        print("✅ Prompts table created successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to create prompts table: {e}")
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
        print("✅ API keys table created successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to create api_keys table: {e}")
        return False

def test_table_creation(client):
    """Test that tables were created and are accessible"""
    
    # Test prompts table
    try:
        result = client.client.table('prompts').select('*').limit(1).execute()
        print("✅ Prompts table accessible")
    except Exception as e:
        print(f"❌ Prompts table test failed: {e}")
    
    # Test api_keys table
    try:
        result = client.client.table('api_keys').select('*').limit(1).execute()
        print("✅ API keys table accessible")
    except Exception as e:
        print(f"❌ API keys table test failed: {e}")

def main():
    # Set environment variables
    os.environ['SUPABASE_URL'] = 'https://utyjhedtqaagihuogyuy.supabase.co'
    os.environ['SUPABASE_ANON_KEY'] = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InV0eWpoZWR0cWFhZ2lodW9neXV5Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDkzMjEyMDUsImV4cCI6MjA2NDg5NzIwNX0.vpRRn7anpmCokYcje5yJr3r2iC_8s11_LXQcCTgxtR8'
    
    print("🔧 Creating Missing Database Tables")
    print("=" * 50)
    
    client = get_supabase_client()
    if not client:
        print("❌ Failed to initialize Supabase client")
        return
    
    print("✅ Supabase client initialized")
    
    # Create missing tables
    print("\n📋 Creating Tables:")
    create_prompts_table(client)
    create_api_keys_table(client)
    
    print("\n🧪 Testing Table Access:")
    test_table_creation(client)

if __name__ == "__main__":
    main() 