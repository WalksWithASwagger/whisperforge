#!/usr/bin/env python3
"""
Test script to verify Google OAuth redirect URI configuration
"""

import os
import requests
from dotenv import load_dotenv
from supabase import create_client
from core.oauth_handler import GoogleOAuthHandler

def test_oauth_url():
    """Test if the OAuth URL is properly configured"""
    
    load_dotenv()
    
    print("🔍 Testing Google OAuth Configuration")
    print("=" * 50)
    
    # Initialize Supabase
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_ANON_KEY')
    
    if not supabase_url or not supabase_key:
        print("❌ Missing Supabase credentials")
        return False
    
    try:
        supabase = create_client(supabase_url, supabase_key)
        oauth_handler = GoogleOAuthHandler(supabase)
        
        # Generate OAuth URL
        oauth_url = oauth_handler.generate_oauth_url()
        print(f"✅ OAuth URL Generated: {oauth_url[:80]}...")
        
        # Check if the redirect URI is in the URL
        expected_redirect = "https://utyjhedtqaagihuogyuy.supabase.co/auth/v1/callback"
        if "utyjhedtqaagihuogyuy.supabase.co/auth/v1" in oauth_url:
            print("✅ Correct Supabase redirect URI detected in OAuth URL")
        else:
            print("❌ Unexpected redirect URI in OAuth URL")
            return False
        
        print("\n🎯 READY TO TEST:")
        print("1. Go to: http://localhost:8507")
        print("2. Click 'Sign in with Google'")
        print("3. Complete the OAuth flow")
        print("\n📍 If you get redirect_uri_mismatch:")
        print("   → Wait 5-10 more minutes for Google to propagate")
        print("   → Clear browser cache and try again")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    test_oauth_url() 