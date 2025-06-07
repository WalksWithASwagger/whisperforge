#!/usr/bin/env python3
"""
Test Google OAuth Configuration with Supabase
"""

import os
import sys
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables
load_dotenv()

def test_supabase_google_oauth():
    """Test if Google OAuth is configured in Supabase"""
    
    # Get credentials
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_ANON_KEY")
    google_client_id = os.getenv("GOOGLE_CLIENT_ID")
    google_client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
    
    print("🔍 Checking Supabase Google OAuth Configuration...")
    print(f"Supabase URL: {url}")
    print(f"Google Client ID: {google_client_id[:20]}..." if google_client_id and len(google_client_id) > 20 else f"Google Client ID: {google_client_id}")
    print(f"Google Client Secret: {'✅ Set' if google_client_secret else '❌ Not Set'}")
    
    if not url or not key:
        print("❌ Supabase credentials missing")
        return False
    
    if not google_client_id or not google_client_secret:
        print("❌ Google OAuth credentials missing")
        return False
    
    if google_client_id == "your-client-id" or google_client_secret == "your-client-secret":
        print("❌ Google OAuth credentials are still placeholder values")
        return False
    
    try:
        # Initialize Supabase client
        supabase: Client = create_client(url, key)
        
        # Test basic connection
        print("\n🧪 Testing Supabase connection...")
        result = supabase.table("users").select("id").limit(1).execute()
        print("✅ Supabase connection successful")
        
        # Test if we can attempt a Google OAuth URL generation
        print("\n🔗 Testing Google OAuth URL generation...")
        
        # The auth flow would normally be:
        # 1. Generate OAuth URL with Supabase
        # 2. Redirect user to Google 
        # 3. Handle callback
        
        # For now, let's check if the auth methods are available
        auth_methods = dir(supabase.auth)
        google_methods = [method for method in auth_methods if 'google' in method.lower() or 'oauth' in method.lower()]
        
        print(f"Available auth methods: {google_methods}")
        
        # Try to generate a sign-in URL (this will help us verify if Google is configured)
        try:
            # This would normally redirect to Google OAuth
            oauth_url = supabase.auth.sign_in_with_oauth({
                "provider": "google",
                "options": {
                    "redirect_to": "http://localhost:8507"
                }
            })
            print(f"✅ Google OAuth URL generation successful")
            print(f"OAuth Response: {oauth_url}")
            return True
            
        except Exception as oauth_error:
            print(f"❌ Google OAuth not configured in Supabase: {oauth_error}")
            print("\n📋 Next Steps:")
            print("1. Go to your Supabase Dashboard: https://utyjhedtqaagihuogyuy.supabase.co")
            print("2. Navigate to: Authentication → Providers")
            print("3. Enable Google provider")
            print("4. Add your Google Client ID and Secret")
            print("5. Set redirect URL to: http://localhost:8507")
            return False
    
    except Exception as e:
        print(f"❌ Error testing Supabase: {e}")
        return False

def main():
    """Main test function"""
    print("=" * 60)
    print("🔐 SUPABASE GOOGLE OAUTH CONFIGURATION TEST")
    print("=" * 60)
    
    success = test_supabase_google_oauth()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ GOOGLE OAUTH CONFIGURATION VERIFIED")
        print("Ready to implement OAuth login buttons!")
    else:
        print("❌ GOOGLE OAUTH CONFIGURATION NEEDED")
        print("Please configure Google OAuth in Supabase Dashboard")
    print("=" * 60)
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 