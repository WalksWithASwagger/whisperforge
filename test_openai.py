#!/usr/bin/env python3
"""
Test script for OpenAI API connection.
Run this script directly to test API connection outside of Streamlit.
"""

import os
import sys
from dotenv import load_dotenv
from openai import OpenAI
import traceback

# Load environment variables
load_dotenv()

def print_environment_info():
    """Print information about the environment"""
    print("\n--- Environment Information ---")
    
    # Check Python version
    print(f"Python version: {sys.version}")
    
    # Check OpenAI version
    try:
        from openai import __version__ as openai_version
        print(f"OpenAI Python package version: {openai_version}")
    except (ImportError, AttributeError):
        print("OpenAI Python package version: Unknown")
    
    # Check environment variables
    api_key = os.environ.get("OPENAI_API_KEY")
    print(f"OPENAI_API_KEY: {'Set' if api_key else 'Not Set'}")
    
    # Check proxy settings
    proxy_vars = {}
    for env_var in os.environ:
        if 'PROXY' in env_var.upper() or 'HTTP_PROXY' in env_var.upper() or 'HTTPS_PROXY' in env_var.upper():
            proxy_vars[env_var] = os.environ[env_var]
    
    if proxy_vars:
        print("\nProxy Environment Variables:")
        for var_name, value in proxy_vars.items():
            print(f"  {var_name}: {value}")
    else:
        print("\nNo proxy environment variables found")
    
    print("\n--- End of Environment Information ---\n")

def test_openai_connection():
    """Test connection to OpenAI API"""
    print("Testing OpenAI API connection...")
    api_key = os.environ.get("OPENAI_API_KEY")
    
    if not api_key:
        print("Error: OPENAI_API_KEY is not set in environment variables or .env file")
        return False
    
    try:
        # Print all environment variables for debugging
        print("\nFull Environment Variables:")
        for env_var, value in os.environ.items():
            if 'API_KEY' in env_var or 'PROXY' in env_var.upper():
                masked_value = value[:4] + '*' * (len(value) - 8) + value[-4:] if len(value) > 8 else '****'
                print(f"  {env_var}: {masked_value}")
        
        # Try without proxy settings
        print("\nTrying to initialize OpenAI client without proxy settings...")
        
        # Save original proxy settings
        proxy_vars = {}
        for env_var in list(os.environ.keys()):
            if 'PROXY' in env_var.upper() or 'HTTP_PROXY' in env_var.upper() or 'HTTPS_PROXY' in env_var.upper():
                proxy_vars[env_var] = os.environ[env_var]
                del os.environ[env_var]
        
        try:
            client = OpenAI(
                api_key=api_key,
            )
            
            # Test with a simple completion
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": "Hello, can you hear me?"}
                ],
                max_tokens=50
            )
            
            print(f"\nSuccess! OpenAI API response: {response.choices[0].message.content}")
            return True
            
        finally:
            # Restore proxy settings
            for env_var, value in proxy_vars.items():
                os.environ[env_var] = value
    
    except Exception as e:
        print(f"\nError testing OpenAI API: {str(e)}")
        print("\nTraceback:")
        traceback.print_exc()
        
        print("\nPlease check:")
        print("1. Your API key is correct")
        print("2. You have removed or correctly configured any proxy settings")
        print("3. Your OpenAI account has sufficient credits")
        print("4. Your network can connect to OpenAI API servers")
        
        return False

if __name__ == "__main__":
    print_environment_info()
    success = test_openai_connection()
    
    if success:
        print("\nOpenAI API test completed successfully!")
        sys.exit(0)
    else:
        print("\nOpenAI API test failed. See error messages above.")
        sys.exit(1) 