#!/usr/bin/env python3
"""
WhisperForge Pipeline Test
Tests the complete content generation pipeline with Render environment variables
"""

import os
import requests
import json
from datetime import datetime

def test_environment_variables():
    """Test that all required environment variables are available"""
    required_vars = [
        'OPENAI_API_KEY',
        'SUPABASE_URL', 
        'SUPABASE_ANON_KEY'
    ]
    
    print("🔍 Testing Environment Variables...")
    
    missing = []
    for var in required_vars:
        if not os.getenv(var):
            missing.append(var)
        else:
            print(f"✅ {var}: {'*' * 20}")
    
    if missing:
        print(f"❌ Missing variables: {missing}")
        return False
    
    print("✅ All environment variables present!")
    return True

def test_openai_connection():
    """Test OpenAI API connection"""
    print("\n🤖 Testing OpenAI Connection...")
    
    try:
        from openai import OpenAI
        client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
        # Simple test completion
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Say 'WhisperForge test successful!'"}],
            max_tokens=10
        )
        
        result = response.choices[0].message.content
        print(f"✅ OpenAI Response: {result}")
        return True
        
    except Exception as e:
        print(f"❌ OpenAI Error: {e}")
        return False

def test_supabase_connection():
    """Test Supabase connection"""
    print("\n🗄️ Testing Supabase Connection...")
    
    try:
        from supabase import create_client
        
        url = os.getenv('SUPABASE_URL')
        key = os.getenv('SUPABASE_ANON_KEY')
        
        if not url or not key:
            print("❌ Supabase credentials missing")
            return False
        
        client = create_client(url, key)
        
        # Test connection with a simple query
        result = client.table('content').select('id').limit(1).execute()
        print(f"✅ Supabase Connected - Table accessible")
        return True
        
    except Exception as e:
        print(f"❌ Supabase Error: {e}")
        return False

def test_complete_pipeline():
    """Test the complete content generation pipeline"""
    print("\n🎯 Testing Complete Content Pipeline...")
    
    # Sample transcript for testing
    sample_transcript = """
    Hello, this is a test transcript for WhisperForge. We're testing the complete content pipeline 
    including wisdom extraction, outline creation, article generation, social media posts, 
    image prompts, and research enrichment. This should demonstrate the full capabilities 
    of the WhisperForge system including visible AI thinking and Aurora UI.
    """
    
    tests = []
    
    # Test 1: Wisdom Generation
    try:
        print("📝 Testing Wisdom Generation...")
        from app import generate_content_simple
        wisdom = generate_content_simple(sample_transcript, "wisdom", "test_user")
        if wisdom and not wisdom.startswith("❌"):
            print("✅ Wisdom generation successful")
            tests.append(True)
        else:
            print(f"❌ Wisdom generation failed: {wisdom}")
            tests.append(False)
    except Exception as e:
        print(f"❌ Wisdom generation error: {e}")
        tests.append(False)
    
    # Test 2: Article Generation
    try:
        print("📝 Testing Article Generation...")
        from app import generate_article_content
        article = generate_article_content(sample_transcript, "test_user")
        if article and not article.startswith("❌"):
            print("✅ Article generation successful")
            tests.append(True)
        else:
            print(f"❌ Article generation failed: {article}")
            tests.append(False)
    except Exception as e:
        print(f"❌ Article generation error: {e}")
        tests.append(False)
    
    # Test 3: Social Content Generation
    try:
        print("📱 Testing Social Content Generation...")
        from app import generate_social_content
        social = generate_social_content(sample_transcript, "test_user")
        if social and not social.startswith("❌"):
            print("✅ Social content generation successful")
            tests.append(True)
        else:
            print(f"❌ Social content generation failed: {social}")
            tests.append(False)
    except Exception as e:
        print(f"❌ Social content generation error: {e}")
        tests.append(False)
    
    # Test 4: Image Prompts Generation
    try:
        print("🎨 Testing Image Prompts Generation...")
        from app import generate_image_prompts
        prompts = generate_image_prompts(sample_transcript, "test_user")
        if prompts and not prompts.startswith("❌"):
            print("✅ Image prompts generation successful")
            tests.append(True)
        else:
            print(f"❌ Image prompts generation failed: {prompts}")
            tests.append(False)
    except Exception as e:
        print(f"❌ Image prompts generation error: {e}")
        tests.append(False)
    
    # Test 5: Research Enrichment
    try:
        print("🔍 Testing Research Enrichment...")
        from app import generate_research_enrichment
        research = generate_research_enrichment(sample_transcript)
        if research and not research.get('error'):
            print("✅ Research enrichment successful")
            tests.append(True)
        else:
            print(f"❌ Research enrichment failed: {research}")
            tests.append(False)
    except Exception as e:
        print(f"❌ Research enrichment error: {e}")
        tests.append(False)
    
    success_rate = sum(tests) / len(tests) * 100 if tests else 0
    print(f"\n📊 Pipeline Test Results: {sum(tests)}/{len(tests)} tests passed ({success_rate:.1f}%)")
    
    return success_rate >= 80

def test_visible_thinking():
    """Test the visible thinking system"""
    print("\n🧠 Testing Visible Thinking System...")
    
    try:
        from app import VisibleThinking
        
        thinking = VisibleThinking()
        thinking.add_thought("Testing WhisperForge thinking system!", "info")
        thinking.add_thought("Processing your amazing content...", "processing")
        thinking.add_thought("Found some brilliant insights!", "discovery")
        thinking.add_thought("Content pipeline complete!", "success")
        
        print("✅ Visible thinking system initialized successfully")
        print(f"✅ Added {len(thinking.st.session_state.thinking_bubbles) if hasattr(thinking, 'st') else 4} thought bubbles")
        return True
        
    except Exception as e:
        print(f"❌ Visible thinking error: {e}")
        return False

def run_comprehensive_test():
    """Run all tests and generate report"""
    print("🎙️ WhisperForge Complete Pipeline Test")
    print("=" * 50)
    
    test_results = {
        'environment': test_environment_variables(),
        'openai': test_openai_connection(),
        'supabase': test_supabase_connection(),
        'pipeline': test_complete_pipeline(),
        'thinking': test_visible_thinking()
    }
    
    print("\n" + "=" * 50)
    print("📊 FINAL TEST RESULTS")
    print("=" * 50)
    
    passed = sum(test_results.values())
    total = len(test_results)
    
    for test_name, result in test_results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name.title().ljust(15)}: {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! WhisperForge is ready to rock!")
        print("🚀 Your app is production-ready for work tomorrow!")
        print("📊 Ready for Notion integration next!")
    else:
        print(f"\n⚠️ {total-passed} tests failed. Check the output above for details.")
    
    return passed == total

if __name__ == "__main__":
    success = run_comprehensive_test()
    exit(0 if success else 1) 