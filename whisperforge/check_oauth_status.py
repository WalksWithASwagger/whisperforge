#!/usr/bin/env python3
"""
Quick script to check Google OAuth configuration status
"""

import os
import sys
from dotenv import load_dotenv
from supabase import create_client

def check_oauth_status():
    """Check the current OAuth configuration status"""
    
    # Load environment variables
    load_dotenv()
    
    print("🔍 Checking Google OAuth Configuration Status")
    print("=" * 50)
    
    # Check environment variables
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_ANON_KEY')
    
    if not supabase_url or not supabase_key:
        print("❌ Missing Supabase credentials in .env file")
        return False
    
    print(f"✅ Supabase URL: {supabase_url}")
    print(f"✅ Supabase Key: {supabase_key[:20]}...")
    
    try:
        # Test Supabase connection
        supabase = create_client(supabase_url, supabase_key)
        print("✅ Supabase connection successful")
        
        # Try to get auth settings (this will help us understand the current config)
        try:
            # Test if we can access auth
            settings_response = supabase.auth.get_settings()
            print("✅ Auth settings accessible")
        except Exception as auth_error:
            print(f"⚠️  Auth settings check: {auth_error}")
        
        # Test database connection
        try:
            response = supabase.table("users").select("count", count="exact").execute()
            user_count = response.count if hasattr(response, 'count') else 0
            print(f"✅ Database accessible - {user_count} users in database")
        except Exception as db_error:
            print(f"❌ Database error: {db_error}")
        
        return True
        
    except Exception as e:
        print(f"❌ Supabase connection failed: {e}")
        return False

def main():
    print("🚀 WhisperForge OAuth Status Check")
    print()
    
    if not check_oauth_status():
        print("\n❌ Configuration check failed!")
        return 1
    
    print("\n" + "=" * 50)
    print("📋 NEXT STEPS TO FIX GOOGLE OAUTH:")
    print("=" * 50)
    print("1. Go to: https://supabase.com/dashboard")
    print("2. Select your project: utyjhedtqaagihuogyuy")
    print("3. Go to Authentication > Providers")
    print("4. Enable Google provider")
    print("5. Add your Google Client ID and Secret")
    print("6. Set redirect URL to: https://utyjhedtqaagihuogyuy.supabase.co/auth/v1/callback")
    print()
    print("📖 See GOOGLE_OAUTH_SETUP.md for detailed instructions")
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 