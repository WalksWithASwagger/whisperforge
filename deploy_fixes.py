#!/usr/bin/env python3
"""
WhisperForge Deployment Verification Script
Verifies all systems are ready for production deployment
"""

import os
import sys
from datetime import datetime


def verify_database_tables():
    """Verify all required database tables exist"""
    print("🔍 Verifying Database Tables")
    print("=" * 40)

    required_tables = [
        "users", "content", "api_keys", "prompts",
        "knowledge_base", "pipeline_logs"
    ]

    try:
        from core.supabase_integration import get_supabase_client
        client = get_supabase_client()

        if not client:
            print("❌ Failed to connect to Supabase")
            return False

        missing_tables = []
        for table in required_tables:
            try:
                # Test table access
                result = client.client.table(table).select("*").limit(1).execute()
                print(f"✅ {table}")
            except Exception:
                print(f"❌ {table} - MISSING")
                missing_tables.append(table)

        if missing_tables:
            print(f"\n🚨 Missing tables: {', '.join(missing_tables)}")
            print("Execute the SQL commands from SYSTEM_ANALYSIS_REPORT.md")
            return False
        else:
            print("✅ All required tables exist!")
            return True

    except Exception as e:
        print(f"❌ Database verification failed: {e}")
        return False


def test_core_functionality():
    """Test core application functionality"""
    print("\n🧪 Testing Core Functionality")
    print("=" * 40)

    try:
        # Test imports
        from core.content_generation import transcribe_audio, generate_wisdom
        from core.file_upload import FileUploadManager, EnhancedLargeFileProcessor
        from core.utils import DEFAULT_PROMPTS, load_prompt_from_file
        from core.supabase_integration import get_supabase_client

        print("✅ Core imports successful")

        # Test prompt system
        prompts = DEFAULT_PROMPTS
        print(f"✅ Prompt system: {len(prompts)} default + file-based prompts")

        # Test database connection
        client = get_supabase_client()
        if client:
            print("✅ Database connection working")
        else:
            print("❌ Database connection failed")
            return False

        return True

    except Exception as e:
        print(f"❌ Core functionality test failed: {e}")
        return False


def main():
    """Main deployment verification"""
    print("🚀 WHISPERFORGE DEPLOYMENT VERIFICATION")
    print("=" * 60)
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Run verification tests
    db_ok = verify_database_tables()
    core_ok = test_core_functionality()

    # Final assessment
    print(f"\n📊 DEPLOYMENT READINESS")
    print("=" * 60)

    if db_ok and core_ok:
        print("READY FOR DEPLOYMENT!")
        print("\nStart your app with:")
        print("source venv/bin/activate")
        print("# Ensure SUPABASE_URL and SUPABASE_ANON_KEY are set in your .env file")
        print("streamlit run app_simple.py --server.headless true --server.port 8502")
    else:
        print("❌ NOT READY - Fix issues above first")
        print("\n📝 Next steps:")
        if not db_ok:
            print("1. Create missing database tables (see SYSTEM_ANALYSIS_REPORT.md)")
        print("2. Re-run this verification script")
        print("3. Deploy when all checks pass")


if __name__ == "__main__":
    main()
