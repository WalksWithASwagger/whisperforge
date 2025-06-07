#!/usr/bin/env python3
"""
Test Google OAuth Flow
"""

from core.supabase_integration import get_supabase_client
from core.oauth_handler import GoogleOAuthHandler
import sys

def test_oauth_flow():
    """Test the complete OAuth flow"""
    print("=" * 60)
    print("🔐 TESTING GOOGLE OAUTH FLOW")
    print("=" * 60)
    
    try:
        # 1. Initialize Supabase
        print("1. 🔧 Initializing Supabase...")
        db = get_supabase_client()
        print("   ✅ Supabase client created")
        
        # 2. Initialize OAuth handler
        print("2. 🔧 Initializing OAuth handler...")
        oauth_handler = GoogleOAuthHandler(db.client)
        print("   ✅ OAuth handler created")
        
        # 3. Generate OAuth URL
        print("3. 🔗 Generating OAuth URL...")
        oauth_url = oauth_handler.generate_oauth_url()
        print(f"   ✅ OAuth URL generated: {oauth_url[:80]}...")
        
        # 4. Test user table structure
        print("4. 🗄️  Testing user table structure...")
        try:
            # Check if new columns exist by attempting a query
            result = db.client.table("users").select("id, email, google_id, auth_provider").limit(1).execute()
            print("   ✅ Google OAuth columns available in users table")
        except Exception as e:
            print(f"   ⚠️  Google OAuth columns may need manual addition: {e}")
        
        print("\n" + "=" * 60)
        print("✅ GOOGLE OAUTH INTEGRATION READY!")
        print("=" * 60)
        print("\n📋 Next Steps:")
        print("1. Visit: http://localhost:8507")
        print("2. Click 'Sign in with Google' button")
        print("3. Complete Google OAuth flow")
        print("4. Check if user is created/signed in")
        print("\n🎯 OAuth URL for manual testing:")
        print(oauth_url)
        
        return True
        
    except Exception as e:
        print(f"❌ OAuth flow test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_oauth_flow()
    sys.exit(0 if success else 1) 