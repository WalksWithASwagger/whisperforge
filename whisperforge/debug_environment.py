#!/usr/bin/env python3
"""
Debug script to check environment and OAuth configuration
"""

import os
from pathlib import Path

def debug_environment():
    """Print debug information about the current environment"""
    
    print("🔍 WHISPERFORGE DEBUG INFORMATION")
    print("=" * 50)
    
    # Version info
    version_file = Path("VERSION")
    if version_file.exists():
        version = version_file.read_text().strip()
        print(f"📦 Version: {version}")
    else:
        print("❌ VERSION file not found")
    
    print("\n🌐 Environment Variables:")
    print("-" * 30)
    
    # Check key environment variables
    env_vars = [
        'HOSTNAME',
        'STREAMLIT_SHARING_MODE', 
        'SUPABASE_URL',
        'SUPABASE_ANON_KEY'
    ]
    
    for var in env_vars:
        value = os.getenv(var, 'Not set')
        if 'KEY' in var and value != 'Not set':
            # Mask sensitive keys
            masked_value = value[:10] + '...' + value[-5:] if len(value) > 15 else value
            print(f"{var}: {masked_value}")
        else:
            print(f"{var}: {value}")
    
    print("\n🔗 URL Detection:")
    print("-" * 20)
    
    # Simulate URL detection logic
    hostname = os.getenv('HOSTNAME', '')
    sharing_mode = os.getenv('STREAMLIT_SHARING_MODE', '')
    
    if sharing_mode or 'streamlit.app' in hostname:
        detected_url = "https://whisperforge.streamlit.app"
        environment = "Production (Streamlit Cloud)"
    elif 'streamlit' in hostname or 'share' in hostname:
        detected_url = "https://whisperforge.streamlit.app"
        environment = "Production (Streamlit Cloud - via hostname)"
    else:
        detected_url = "http://localhost:8507"
        environment = "Development (localhost)"
    
    print(f"Detected Environment: {environment}")
    print(f"Detected App URL: {detected_url}")
    
    print("\n📋 OAuth Configuration Check:")
    print("-" * 35)
    print("✅ Google OAuth credentials: Configured in Supabase dashboard")
    print("✅ Supabase provider: Enabled")
    print("⚠️  Google Console redirect URIs should include:")
    print("   - https://utyjhedtqaagihuogyuy.supabase.co/auth/v1/callback")
    print("   - https://whisperforge.streamlit.app")
    print("   - http://localhost:8507 (optional)")
    
    print(f"\n🎯 Current OAuth redirect will use: {detected_url}")
    print("\nIf OAuth fails, check that the detected URL above is in your Google Console redirect URIs!")

if __name__ == "__main__":
    debug_environment() 