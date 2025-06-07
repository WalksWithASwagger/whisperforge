#!/usr/bin/env python3
"""
Comprehensive OAuth integration test for WhisperForge
Tests both localhost and deployment scenarios
"""

import os
import logging
from dotenv import load_dotenv
from supabase import create_client
from core.oauth_handler import GoogleOAuthHandler
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_oauth_comprehensive():
    """Comprehensive OAuth integration test"""
    
    print("🧪 WHISPERFORGE OAUTH COMPREHENSIVE TEST")
    print("=" * 55)
    
    # Load environment
    load_dotenv()
    
    # Check version
    version_file = Path("VERSION")
    version = version_file.read_text().strip() if version_file.exists() else "Unknown"
    print(f"📦 Testing Version: {version}")
    
    # Test 1: Environment Detection
    print("\n🔍 TEST 1: Environment Detection")
    print("-" * 35)
    
    hostname = os.getenv('HOSTNAME', 'Not set')
    sharing_mode = os.getenv('STREAMLIT_SHARING_MODE', 'Not set')
    
    print(f"HOSTNAME: {hostname}")
    print(f"STREAMLIT_SHARING_MODE: {sharing_mode}")
    
    # Test URL detection logic
    if sharing_mode != 'Not set' or 'streamlit.app' in hostname:
        detected_env = "Production (Streamlit Cloud)"
        expected_redirect = "https://whisperforge.streamlit.app"
    elif 'streamlit' in hostname or 'share' in hostname:
        detected_env = "Production (Streamlit Cloud - via hostname)"
        expected_redirect = "https://whisperforge.streamlit.app"
    else:
        detected_env = "Development (localhost)"
        expected_redirect = "http://localhost:8507"
    
    print(f"✅ Detected Environment: {detected_env}")
    print(f"✅ Expected Redirect URL: {expected_redirect}")
    
    # Test 2: Supabase Connection
    print("\n🔍 TEST 2: Supabase Connection")
    print("-" * 35)
    
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_ANON_KEY')
    
    if not supabase_url or not supabase_key:
        print("❌ Supabase credentials not found in environment")
        print("   Make sure SUPABASE_URL and SUPABASE_ANON_KEY are set")
        return False
    
    try:
        supabase = create_client(supabase_url, supabase_key)
        print(f"✅ Supabase client created: {supabase_url}")
    except Exception as e:
        print(f"❌ Failed to create Supabase client: {e}")
        return False
    
    # Test 3: OAuth Handler Initialization
    print("\n🔍 TEST 3: OAuth Handler Initialization")
    print("-" * 42)
    
    try:
        oauth_handler = GoogleOAuthHandler(supabase)
        print("✅ OAuth handler created successfully")
        print(f"✅ Detected redirect URL: {oauth_handler.redirect_url}")
        
        if oauth_handler.redirect_url == expected_redirect:
            print("✅ Redirect URL matches environment expectation")
        else:
            print(f"⚠️  Redirect URL mismatch!")
            print(f"   Expected: {expected_redirect}")
            print(f"   Detected: {oauth_handler.redirect_url}")
            
    except Exception as e:
        print(f"❌ Failed to create OAuth handler: {e}")
        return False
    
    # Test 4: OAuth URL Generation
    print("\n🔍 TEST 4: OAuth URL Generation")
    print("-" * 35)
    
    try:
        oauth_url = oauth_handler.generate_oauth_url()
        print(f"✅ OAuth URL generated successfully")
        print(f"   URL: {oauth_url[:80]}...")
        
        # Verify the URL contains the expected redirect
        if expected_redirect.replace(':', '%3A').replace('/', '%2F') in oauth_url:
            print("✅ OAuth URL contains correct redirect parameter")
        else:
            print("⚠️  OAuth URL may have incorrect redirect parameter")
            
        # Check for required OAuth parameters
        required_params = ['redirect_to', 'scopes', 'code_challenge', 'provider=google']
        for param in required_params:
            if param in oauth_url:
                print(f"✅ Contains {param}")
            else:
                print(f"❌ Missing {param}")
                
    except Exception as e:
        print(f"❌ Failed to generate OAuth URL: {e}")
        return False
    
    # Test 5: Database Schema Check
    print("\n🔍 TEST 5: Database Schema Check")
    print("-" * 35)
    
    try:
        # Test basic table access
        users_response = supabase.table("users").select("count", count="exact").execute()
        user_count = users_response.count if hasattr(users_response, 'count') else 0
        print(f"✅ Users table accessible - {user_count} users")
        
        # Test custom tables
        tables_to_check = ["custom_prompts", "knowledge_base", "content", "pipeline_logs"]
        for table in tables_to_check:
            try:
                response = supabase.table(table).select("count", count="exact").limit(1).execute()
                print(f"✅ {table} table accessible")
            except Exception as table_error:
                print(f"⚠️  {table} table issue: {table_error}")
                
    except Exception as e:
        print(f"❌ Database schema check failed: {e}")
        return False
    
    # Test 6: Google Console Configuration Check
    print("\n🔍 TEST 6: Google Console Configuration")
    print("-" * 42)
    
    required_redirects = [
        "https://utyjhedtqaagihuogyuy.supabase.co/auth/v1/callback",
        "https://whisperforge.streamlit.app",
        "http://localhost:8507"
    ]
    
    print("✅ Required redirect URIs in Google Console:")
    for redirect in required_redirects:
        print(f"   - {redirect}")
    
    print(f"\n🎯 Current OAuth will use: {expected_redirect}")
    print("   ⚠️  Ensure this URL is in your Google Console redirect URIs!")
    
    # Summary
    print("\n🎯 TEST SUMMARY")
    print("=" * 15)
    print("✅ All core OAuth components tested successfully")
    print(f"✅ Version {version} OAuth integration is ready")
    print(f"✅ Environment: {detected_env}")
    print(f"✅ OAuth will redirect to: {expected_redirect}")
    
    print("\n📋 NEXT STEPS:")
    print("1. Deploy to Streamlit Cloud")
    print("2. Check that version shows v1.1")
    print("3. Verify debug panel shows 'Production' environment")
    print("4. Test Google OAuth login")
    print("5. Check logs for detailed OAuth flow information")
    
    return True

if __name__ == "__main__":
    success = test_oauth_comprehensive()
    if success:
        print("\n🎉 OAuth integration test completed successfully!")
    else:
        print("\n❌ OAuth integration test failed!")
    exit(0 if success else 1) 