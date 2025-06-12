#!/usr/bin/env python3
"""
WhisperForge Deployment Verification Script
Final check before production deployment
"""

import os
import sys
from datetime import datetime

def setup_environment():
    """Setup environment variables"""
    os.environ['SUPABASE_URL'] = 'https://utyjhedtqaagihuogyuy.supabase.co'
    os.environ['SUPABASE_ANON_KEY'] = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InV0eWpoZWR0cWFhZ2lodW9neXV5Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDkzMjEyMDUsImV4cCI6MjA2NDg5NzIwNX0.vpRRn7anpmCokYcje5yJr3r2iC_8s11_LXQcCTgxtR8'

def verify_database_tables():
    """Verify all required tables exist"""
    print("🔍 Verifying Database Tables")
    print("=" * 40)
    
    from core.supabase_integration import get_supabase_client
    client = get_supabase_client()
    
    required_tables = ['users', 'content', 'knowledge_base', 'pipeline_logs', 'prompts', 'api_keys']
    missing_tables = []
    
    for table in required_tables:
        try:
            client.client.table(table).select('*').limit(1).execute()
            print(f"✅ {table}")
        except Exception:
            print(f"❌ {table} - MISSING")
            missing_tables.append(table)
    
    if missing_tables:
        print(f"\n🚨 Missing tables: {', '.join(missing_tables)}")
        print("Execute the SQL commands from SYSTEM_ANALYSIS_REPORT.md")
        return False
    
    print("✅ All required tables exist!")
    return True

def test_core_functionality():
    """Test core app functionality"""
    print("\n🧪 Testing Core Functionality")
    print("=" * 40)
    
    try:
        # Test imports
        from core.supabase_integration import get_supabase_client
        from core.utils import DEFAULT_PROMPTS, load_prompt_from_file
        from core.content_generation import transcribe_audio
        print("✅ Core imports successful")
        
        # Test prompt system
        prompts = DEFAULT_PROMPTS
        wisdom_prompt = load_prompt_from_file('wisdom_extraction')
        print(f"✅ Prompt system: {len(prompts)} default + file-based prompts")
        
        # Test database connection
        client = get_supabase_client()
        if client and client.test_connection():
            print("✅ Database connection working")
        else:
            print("❌ Database connection failed")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Core functionality test failed: {e}")
        return False

def main():
    """Run deployment verification"""
    print("🚀 WHISPERFORGE DEPLOYMENT VERIFICATION")
    print("=" * 60)
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    setup_environment()
    
    # Run verification checks
    database_ok = verify_database_tables()
    functionality_ok = test_core_functionality()
    
    print(f"\n📊 DEPLOYMENT READINESS")
    print("=" * 60)
    
    if database_ok and functionality_ok:
        print("🎉 ✅ READY FOR DEPLOYMENT!")
        print("\n🚀 Start your app with:")
        print("source venv/bin/activate")
        print("export SUPABASE_URL='https://utyjhedtqaagihuogyuy.supabase.co'")
        print("export SUPABASE_ANON_KEY='eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InV0eWpoZWR0cWFhZ2lodW9neXV5Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDkzMjEyMDUsImV4cCI6MjA2NDg5NzIwNX0.vpRRn7anpmCokYcje5yJr3r2iC_8s11_LXQcCTgxtR8'")
        print("streamlit run app.py --server.headless true --server.port 8502")
    else:
        print("❌ NOT READY - Fix issues above first")
        print("\n📝 Next steps:")
        if not database_ok:
            print("1. Create missing database tables (see SYSTEM_ANALYSIS_REPORT.md)")
        print("2. Re-run this verification script")
        print("3. Deploy when all checks pass")

if __name__ == "__main__":
    main() 