#!/usr/bin/env python3
"""
Simple test script to debug Notion connection issues
"""

import os
import sys
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up logging to see debug messages
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Import the functions we need to test
try:
    from app import test_notion_connection, get_api_key_for_service, get_notion_database_id
    print("✅ Successfully imported functions from app.py")
except ImportError as e:
    print(f"❌ Failed to import from app.py: {e}")
    sys.exit(1)

def main():
    print("🔍 Testing Notion Connection...")
    print("=" * 50)
    
    # Test 1: Check if API key is available
    print("\n1. Checking API Key...")
    api_key = get_api_key_for_service("notion")
    if api_key:
        print(f"✅ API Key found (length: {len(api_key)})")
        print(f"   Starts with: {api_key[:10]}...")
    else:
        print("❌ No API Key found")
        print("   Checked sources:")
        print(f"   - Environment NOTION_API_KEY: {'✅' if os.getenv('NOTION_API_KEY') else '❌'}")
        print("   - User stored keys: ❌ (requires session state)")
    
    # Test 2: Check if Database ID is available
    print("\n2. Checking Database ID...")
    try:
        db_id = get_notion_database_id()
        if db_id:
            print(f"✅ Database ID found: {db_id}")
        else:
            print("❌ No Database ID found")
            print("   Checked sources:")
            print(f"   - Environment NOTION_DATABASE_ID: {'✅' if os.getenv('NOTION_DATABASE_ID') else '❌'}")
            print("   - User stored keys: ❌ (requires session state)")
    except Exception as e:
        print(f"❌ Error getting database ID: {e}")
    
    # Test 3: Test the full connection
    print("\n3. Testing Full Connection...")
    try:
        result = test_notion_connection()
        print(f"Result: {result}")
        
        if result["success"]:
            print("✅ Connection successful!")
            print(f"   Database: {result.get('database_title', 'Unknown')}")
            print(f"   Database ID: {result.get('database_id', 'Unknown')}")
        else:
            print(f"❌ Connection failed: {result['error']}")
            
            # Provide specific troubleshooting
            error = result['error']
            if "No Notion API key" in error:
                print("\n💡 Troubleshooting:")
                print("   - Set NOTION_API_KEY environment variable")
                print("   - Or configure it in the app's API Keys page")
            elif "No Notion database ID" in error:
                print("\n💡 Troubleshooting:")
                print("   - Set NOTION_DATABASE_ID environment variable")
                print("   - Or configure it in the app's API Keys page")
            elif "Failed to create Notion client" in error:
                print("\n💡 Troubleshooting:")
                print("   - Check that your API key is valid")
                print("   - Ensure it starts with 'secret_'")
            elif "Failed to access database" in error:
                print("\n💡 Troubleshooting:")
                print("   - Verify the database ID is correct")
                print("   - Ensure your integration has access to the database")
                print("   - Check that the database exists")
    except Exception as e:
        print(f"❌ Unexpected error during connection test: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 50)
    print("🏁 Test completed!")

if __name__ == "__main__":
    main() 