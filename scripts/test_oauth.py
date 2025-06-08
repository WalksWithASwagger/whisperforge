#!/usr/bin/env python3
"""
Test OAuth URL generation to ensure it works correctly
"""

import sys
import os
from pathlib import Path

# Add the project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_oauth_url_generation():
    """Test that OAuth URL generation works"""
    try:
        from core.supabase_integration import get_supabase_client
        
        print("🔍 Testing OAuth URL generation...")
        
        db, _ = get_supabase_client()
        
        if not db:
            print("❌ Failed to get Supabase client")
            return False
        
        # Test OAuth URL generation
        redirect_url = "http://localhost:8501"
        auth_response = db.client.auth.sign_in_with_oauth({
            "provider": "google",
            "options": {"redirect_to": redirect_url}
        })
        
        if hasattr(auth_response, 'url') and auth_response.url:
            print(f"✅ OAuth URL generated successfully")
            print(f"   URL: {auth_response.url[:50]}...")
            return True
        else:
            print(f"❌ OAuth URL not generated properly")
            print(f"   Response: {auth_response}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing OAuth: {e}")
        import traceback
        print(f"   Full error: {traceback.format_exc()}")
        return False

def main():
    print("🚀 WhisperForge OAuth Test")
    print("=" * 30)
    
    success = test_oauth_url_generation()
    
    if success:
        print("\n🎉 OAuth URL generation is working!")
        print("You should be able to sign in with Google now.")
    else:
        print("\n💥 OAuth URL generation failed!")
        print("Check your Supabase configuration.")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 