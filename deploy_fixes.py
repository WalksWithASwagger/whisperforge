#!/usr/bin/env python3
"""
WhisperForge Deployment Verification Script
Final check before production deployment
"""

import os
import sys
from datetime import datetime
from core.logging_config import logger

def setup_environment():
    """Setup environment variables"""
    # Ensure required environment variables are set
    required_vars = ['SUPABASE_URL', 'SUPABASE_ANON_KEY']
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        logger.logger.error(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        logger.logger.error("Please set them before running this script.")
        sys.exit(1)

def verify_database_tables():
    """Verify all required tables exist"""
    logger.logger.info("🔍 Verifying Database Tables")
    logger.logger.info("=" * 40)
    
    from core.supabase_integration import get_supabase_client
    client = get_supabase_client()
    
    required_tables = ['users', 'content', 'knowledge_base', 'pipeline_logs', 'prompts', 'api_keys']
    missing_tables = []
    
    for table in required_tables:
        try:
            client.client.table(table).select('*').limit(1).execute()
            logger.logger.info(f"✅ {table}")
        except Exception:
            logger.logger.error(f"❌ {table} - MISSING")
            missing_tables.append(table)
    
    if missing_tables:
        logger.logger.error(f"\n🚨 Missing tables: {', '.join(missing_tables)}")
        logger.logger.error("Execute the SQL commands from SYSTEM_ANALYSIS_REPORT.md")
        return False
    
    logger.logger.info("✅ All required tables exist!")
    return True

def test_core_functionality():
    """Test core app functionality"""
    logger.logger.info("\n🧪 Testing Core Functionality")
    logger.logger.info("=" * 40)
    
    try:
        # Test imports
        from core.supabase_integration import get_supabase_client
        from core.utils import DEFAULT_PROMPTS, load_prompt_from_file
        from core.content_generation import transcribe_audio
        logger.logger.info("✅ Core imports successful")
        
        # Test prompt system
        prompts = DEFAULT_PROMPTS
        wisdom_prompt = load_prompt_from_file('wisdom_extraction')
        logger.logger.info(f"✅ Prompt system: {len(prompts)} default + file-based prompts")
        
        # Test database connection
        client = get_supabase_client()
        if client and client.test_connection():
            logger.logger.info("✅ Database connection working")
        else:
            logger.logger.error("❌ Database connection failed")
            return False
        
        return True
        
    except Exception as e:
        logger.logger.error(f"❌ Core functionality test failed: {e}")
        return False

def main():
    """Run deployment verification"""
    logger.logger.info("🚀 WHISPERFORGE DEPLOYMENT VERIFICATION")
    logger.logger.info("=" * 60)
    logger.logger.info(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.logger.info("")
    
    setup_environment()
    
    # Run verification checks
    database_ok = verify_database_tables()
    functionality_ok = test_core_functionality()
    
    logger.logger.info(f"\n📊 DEPLOYMENT READINESS")
    logger.logger.info("=" * 60)
    
    if database_ok and functionality_ok:
        logger.logger.info("🎉 ✅ READY FOR DEPLOYMENT!")
        logger.logger.info("\n🚀 Start your app with:")
        logger.logger.info("source venv/bin/activate")
        logger.logger.info("export SUPABASE_URL='<your-supabase-url>'")
        logger.logger.info("export SUPABASE_ANON_KEY='<your-supabase-anon-key>'")
        logger.logger.info("streamlit run app.py --server.headless true --server.port 8502")
    else:
        logger.logger.error("❌ NOT READY - Fix issues above first")
        logger.logger.info("\n📝 Next steps:")
        if not database_ok:
            logger.logger.info("1. Create missing database tables (see SYSTEM_ANALYSIS_REPORT.md)")
        logger.logger.info("2. Re-run this verification script")
        logger.logger.info("3. Deploy when all checks pass")

if __name__ == "__main__":
    main() 