#!/usr/bin/env python3
"""
Supabase Connection Test Script
==============================

Test the Supabase connection and MCP integration for WhisperForge.
Run this after setting up your Supabase database and environment variables.
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the current directory to Python path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from core.supabase_integration import SupabaseClient, MCPSupabaseIntegration, get_supabase_client, get_mcp_integration
    print("✅ Successfully imported Supabase integration modules")
except ImportError as e:
    print(f"❌ Failed to import modules: {e}")
    sys.exit(1)

def test_environment_variables():
    """Test that required environment variables are set"""
    print("\n🔍 Testing environment variables...")
    
    required_vars = [
        "SUPABASE_URL",
        "SUPABASE_ANON_KEY"
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        print("Please set these in your .env file")
        return False
    
    print("✅ All required environment variables are set")
    return True

def test_supabase_connection():
    """Test basic Supabase connectivity"""
    print("\n🔗 Testing Supabase connection...")
    
    try:
        client = SupabaseClient()
        print("✅ Supabase client created successfully")
        
        # Test connection
        if client.test_connection():
            print("✅ Supabase connection test passed")
            return client
        else:
            print("❌ Supabase connection test failed")
            return None
            
    except Exception as e:
        print(f"❌ Failed to create Supabase client: {e}")
        return None

def test_user_operations(client):
    """Test user-related database operations"""
    print("\n👤 Testing user operations...")
    
    try:
        # Test creating a user
        test_email = "test@whisperforge.com"
        test_password = "test123"
        
        print(f"Creating test user: {test_email}")
        user = client.create_user(test_email, test_password)
        
        if user:
            user_id = user.get("id")
            print(f"✅ Test user created with ID: {user_id}")
            
            # Test retrieving the user
            retrieved_user = client.get_user(user_id)
            if retrieved_user:
                print("✅ User retrieval test passed")
            else:
                print("❌ User retrieval test failed")
            
            return user_id
        else:
            print("❌ Failed to create test user")
            return None
            
    except Exception as e:
        print(f"❌ User operations test failed: {e}")
        return None

def test_content_operations(client, user_id):
    """Test content storage operations"""
    print("\n📄 Testing content operations...")
    
    try:
        # Test saving content
        test_content = {
            "title": "Test Content",
            "transcript": "This is a test transcript",
            "wisdom": "Test wisdom insights",
            "outline": "1. Introduction\n2. Main points\n3. Conclusion",
            "social_content": "Test social media posts",
            "image_prompts": "Test image generation prompts",
            "article": "Test article content",
            "metadata": {"test": True}
        }
        
        content_id = client.save_content(user_id, test_content)
        if content_id:
            print(f"✅ Content saved with ID: {content_id}")
            
            # Test retrieving content
            user_content = client.get_user_content(user_id)
            if user_content and len(user_content) > 0:
                print(f"✅ Retrieved {len(user_content)} content items for user")
                return True
            else:
                print("❌ Failed to retrieve user content")
                return False
        else:
            print("❌ Failed to save content")
            return False
            
    except Exception as e:
        print(f"❌ Content operations test failed: {e}")
        return False

def test_knowledge_base_operations(client, user_id):
    """Test knowledge base operations"""
    print("\n📚 Testing knowledge base operations...")
    
    try:
        # Test saving knowledge base file
        filename = "test_knowledge.md"
        content = "# Test Knowledge Base\n\nThis is test knowledge base content."
        
        if client.save_knowledge_base_file(user_id, filename, content):
            print("✅ Knowledge base file saved")
            
            # Test retrieving knowledge base
            kb = client.get_user_knowledge_base(user_id)
            if kb and len(kb) > 0:
                print(f"✅ Retrieved {len(kb)} knowledge base files")
                return True
            else:
                print("❌ Failed to retrieve knowledge base")
                return False
        else:
            print("❌ Failed to save knowledge base file")
            return False
            
    except Exception as e:
        print(f"❌ Knowledge base operations test failed: {e}")
        return False

def test_custom_prompts_operations(client, user_id):
    """Test custom prompts operations"""
    print("\n🎯 Testing custom prompts operations...")
    
    try:
        # Test saving custom prompt
        prompt_type = "test_prompt"
        prompt_content = "This is a test custom prompt for testing purposes."
        
        if client.save_custom_prompt(user_id, prompt_type, prompt_content):
            print("✅ Custom prompt saved")
            
            # Test retrieving custom prompts
            prompts = client.get_user_prompts(user_id)
            if prompts and prompt_type in prompts:
                print(f"✅ Retrieved {len(prompts)} custom prompts")
                return True
            else:
                print("❌ Failed to retrieve custom prompts")
                return False
        else:
            print("❌ Failed to save custom prompt")
            return False
            
    except Exception as e:
        print(f"❌ Custom prompts operations test failed: {e}")
        return False

def test_pipeline_logging(client, user_id):
    """Test pipeline execution logging"""
    print("\n📊 Testing pipeline logging...")
    
    try:
        # Test logging pipeline execution
        pipeline_data = {
            "type": "test",
            "duration": 30.5,
            "ai_provider": "openai",
            "model": "gpt-3.5-turbo",
            "success": True,
            "metadata": {"test": True}
        }
        
        if client.log_pipeline_execution(user_id, pipeline_data):
            print("✅ Pipeline execution logged")
            
            # Test retrieving analytics
            analytics = client.get_user_analytics(user_id)
            if analytics and analytics.get("total_executions", 0) > 0:
                print(f"✅ Retrieved analytics: {analytics['total_executions']} executions")
                return True
            else:
                print("❌ Failed to retrieve analytics")
                return False
        else:
            print("❌ Failed to log pipeline execution")
            return False
            
    except Exception as e:
        print(f"❌ Pipeline logging test failed: {e}")
        return False

def test_mcp_integration(user_id):
    """Test MCP integration functionality"""
    print("\n🤖 Testing MCP integration...")
    
    try:
        mcp = get_mcp_integration()
        print("✅ MCP integration instance created")
        
        # Test getting user context
        context = mcp.get_user_context(user_id)
        if context and "user_profile" in context:
            print("✅ User context retrieved successfully")
            print(f"   - User profile: {bool(context.get('user_profile'))}")
            print(f"   - Knowledge base: {len(context.get('knowledge_base', {}))}")
            print(f"   - Custom prompts: {len(context.get('custom_prompts', {}))}")
            print(f"   - Content history: {len(context.get('content_history', []))}")
            
            # Test updating context from interaction
            interaction_data = {
                "type": "test_interaction",
                "duration_seconds": 15,
                "ai_provider": "test",
                "model": "test-model",
                "success": True
            }
            
            if mcp.update_context_from_interaction(user_id, interaction_data):
                print("✅ Context update from interaction successful")
                return True
            else:
                print("❌ Failed to update context from interaction")
                return False
        else:
            print("❌ Failed to retrieve user context")
            return False
            
    except Exception as e:
        print(f"❌ MCP integration test failed: {e}")
        return False

def cleanup_test_data(client, user_id):
    """Clean up test data (optional)"""
    print("\n🧹 Cleaning up test data...")
    
    try:
        # Note: In a real scenario, you might want to delete test data
        # For now, we'll just note that cleanup should be implemented
        print("ℹ️  Test data cleanup not implemented (leaving data for inspection)")
        print(f"   Test user ID: {user_id}")
        return True
        
    except Exception as e:
        print(f"❌ Cleanup failed: {e}")
        return False

def main():
    """Main test runner"""
    print("🚀 WhisperForge Supabase & MCP Integration Test Suite")
    print("=" * 60)
    
    # Step 1: Test environment variables
    if not test_environment_variables():
        sys.exit(1)
    
    # Step 2: Test Supabase connection
    client = test_supabase_connection()
    if not client:
        sys.exit(1)
    
    # Step 3: Test user operations
    user_id = test_user_operations(client)
    if not user_id:
        sys.exit(1)
    
    # Step 4: Test content operations
    if not test_content_operations(client, user_id):
        sys.exit(1)
    
    # Step 5: Test knowledge base operations
    if not test_knowledge_base_operations(client, user_id):
        sys.exit(1)
    
    # Step 6: Test custom prompts operations
    if not test_custom_prompts_operations(client, user_id):
        sys.exit(1)
    
    # Step 7: Test pipeline logging
    if not test_pipeline_logging(client, user_id):
        sys.exit(1)
    
    # Step 8: Test MCP integration
    if not test_mcp_integration(user_id):
        sys.exit(1)
    
    # Step 9: Cleanup (optional)
    cleanup_test_data(client, user_id)
    
    print("\n🎉 All tests passed! Supabase and MCP integration is working correctly.")
    print("\nNext steps:")
    print("1. Update your .env file with actual Supabase credentials")
    print("2. Run the SQL schema in your Supabase SQL editor")
    print("3. Update your main app to use Supabase instead of SQLite")
    print("4. Test the full pipeline with real data")

if __name__ == "__main__":
    main() 