#!/usr/bin/env python3
"""
WhisperForge App Validation Script
Tests all critical functionality to prevent deployment errors
"""

import sys
import os
import importlib
import traceback
from pathlib import Path

# Add the project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

class ValidationResult:
    def __init__(self):
        self.tests_passed = 0
        self.tests_failed = 0
        self.errors = []
        self.warnings = []
    
    def pass_test(self, test_name):
        self.tests_passed += 1
        print(f"✅ {test_name}")
    
    def fail_test(self, test_name, error):
        self.tests_failed += 1
        self.errors.append(f"{test_name}: {error}")
        print(f"❌ {test_name}: {error}")
    
    def warn_test(self, test_name, warning):
        self.warnings.append(f"{test_name}: {warning}")
        print(f"⚠️  {test_name}: {warning}")
    
    def summary(self):
        total = self.tests_passed + self.tests_failed
        print(f"\n{'='*50}")
        print(f"VALIDATION SUMMARY")
        print(f"{'='*50}")
        print(f"Tests Passed: {self.tests_passed}/{total}")
        print(f"Tests Failed: {self.tests_failed}")
        print(f"Warnings: {len(self.warnings)}")
        
        if self.errors:
            print(f"\n🚨 ERRORS:")
            for error in self.errors:
                print(f"  - {error}")
        
        if self.warnings:
            print(f"\n⚠️  WARNINGS:")
            for warning in self.warnings:
                print(f"  - {warning}")
        
        if self.tests_failed == 0:
            print(f"\n🎉 ALL TESTS PASSED! App is ready for deployment.")
            return True
        else:
            print(f"\n💥 {self.tests_failed} TESTS FAILED! Fix errors before deployment.")
            return False

def test_imports(result):
    """Test all critical imports"""
    print("\n🔍 Testing Imports...")
    
    imports_to_test = [
        # Core imports
        ("streamlit", "st"),
        ("os", None),
        ("json", None),
        ("time", None),
        ("datetime", "datetime"),
        ("tempfile", None),
        ("logging", None),
        
        # Third-party
        ("dotenv", None),
        ("supabase", None),
        ("openai", None),
        ("anthropic", None),
        
        # WhisperForge modules
        ("core.supabase_integration", None),
        ("core.utils", None),
        ("core.content_generation", None),
        ("core.streaming_pipeline", None),
        ("core.monitoring", None),
    ]
    
    for module_name, alias in imports_to_test:
        try:
            if alias:
                module = importlib.import_module(module_name)
                globals()[alias] = module
            else:
                importlib.import_module(module_name)
            result.pass_test(f"Import {module_name}")
        except ImportError as e:
            result.fail_test(f"Import {module_name}", str(e))
        except Exception as e:
            result.fail_test(f"Import {module_name}", f"Unexpected error: {e}")

def test_environment_variables(result):
    """Test required environment variables"""
    print("\n🔍 Testing Environment Variables...")
    
    required_vars = [
        "SUPABASE_URL",
        "SUPABASE_ANON_KEY"
    ]
    
    optional_vars = [
        "OPENAI_API_KEY",
        "ANTHROPIC_API_KEY",
        "OAUTH_REDIRECT_URL",
        "STREAMLIT_APP_URL"
    ]
    
    for var in required_vars:
        value = os.getenv(var)
        if value:
            result.pass_test(f"Required env var {var}")
        else:
            result.fail_test(f"Required env var {var}", "Not set")
    
    for var in optional_vars:
        value = os.getenv(var)
        if value:
            result.pass_test(f"Optional env var {var}")
        else:
            result.warn_test(f"Optional env var {var}", "Not set")

def test_file_structure(result):
    """Test required file structure"""
    print("\n🔍 Testing File Structure...")
    
    required_files = [
        "app.py",
        "requirements.txt",
        "core/__init__.py",
        "core/supabase_integration.py",
        "core/utils.py",
        "core/content_generation.py",
        "core/streaming_pipeline.py",
        "core/monitoring.py",
        "prompts/default/transcription.md",
        "prompts/default/wisdom_extraction.md",
        "prompts/default/outline_creation.md",
        "prompts/default/article_generation.md",
        "prompts/default/social_content.md",
        "prompts/default/image_prompts.md",
        "prompts/default/editor_feedback.md"
    ]
    
    optional_files = [
        "static/css/whisperforge_ui.css",
        "core/ui_components.py",
        ".env",
        "Procfile",
        "runtime.txt"
    ]
    
    for file_path in required_files:
        if Path(file_path).exists():
            result.pass_test(f"Required file {file_path}")
        else:
            result.fail_test(f"Required file {file_path}", "Missing")
    
    for file_path in optional_files:
        if Path(file_path).exists():
            result.pass_test(f"Optional file {file_path}")
        else:
            result.warn_test(f"Optional file {file_path}", "Missing")

def test_supabase_connection(result):
    """Test Supabase connection"""
    print("\n🔍 Testing Supabase Connection...")
    
    try:
        from core.supabase_integration import get_supabase_client
        db, mcp = get_supabase_client()
        
        if db:
            result.pass_test("Supabase client initialization")
            
            # Test basic connection
            try:
                # Simple health check
                response = db.client.table("users").select("count", count="exact").limit(1).execute()
                result.pass_test("Supabase database connection")
            except Exception as e:
                result.fail_test("Supabase database connection", str(e))
        else:
            result.fail_test("Supabase client initialization", "Failed to create client")
            
    except Exception as e:
        result.fail_test("Supabase import", str(e))

def test_oauth_configuration(result):
    """Test OAuth configuration"""
    print("\n🔍 Testing OAuth Configuration...")
    
    try:
        from core.supabase_integration import get_supabase_client
        db, _ = get_supabase_client()
        
        if db:
            try:
                # Test OAuth URL generation
                redirect_url = os.getenv("OAUTH_REDIRECT_URL", "http://localhost:8501")
                auth_response = db.client.auth.sign_in_with_oauth({
                    "provider": "google",
                    "options": {"redirect_to": redirect_url}
                })
                
                if hasattr(auth_response, 'url') and auth_response.url:
                    result.pass_test("OAuth URL generation")
                else:
                    result.warn_test("OAuth URL generation", "No URL returned")
                    
            except Exception as e:
                result.warn_test("OAuth URL generation", str(e))
        else:
            result.fail_test("OAuth test", "No Supabase client")
            
    except Exception as e:
        result.fail_test("OAuth test", str(e))

def test_prompt_files(result):
    """Test prompt files are readable"""
    print("\n🔍 Testing Prompt Files...")
    
    prompt_files = [
        "prompts/default/transcription.md",
        "prompts/default/wisdom_extraction.md", 
        "prompts/default/outline_creation.md",
        "prompts/default/article_generation.md",
        "prompts/default/social_content.md",
        "prompts/default/image_prompts.md",
        "prompts/default/editor_feedback.md"
    ]
    
    for prompt_file in prompt_files:
        try:
            with open(prompt_file, 'r', encoding='utf-8') as f:
                content = f.read()
                if len(content) > 10:  # Basic content check
                    result.pass_test(f"Prompt file {prompt_file}")
                else:
                    result.warn_test(f"Prompt file {prompt_file}", "Very short content")
        except FileNotFoundError:
            result.fail_test(f"Prompt file {prompt_file}", "File not found")
        except Exception as e:
            result.fail_test(f"Prompt file {prompt_file}", str(e))

def test_ai_providers(result):
    """Test AI provider configurations"""
    print("\n🔍 Testing AI Providers...")
    
    # Test OpenAI
    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key:
        try:
            import openai
            # Basic client test (don't make actual API calls in validation)
            client = openai.OpenAI(api_key=openai_key)
            result.pass_test("OpenAI configuration")
        except Exception as e:
            result.warn_test("OpenAI configuration", str(e))
    else:
        result.warn_test("OpenAI configuration", "API key not set")
    
    # Test Anthropic
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    if anthropic_key:
        try:
            import anthropic
            # Basic client test (don't make actual API calls in validation)
            client = anthropic.Anthropic(api_key=anthropic_key)
            result.pass_test("Anthropic configuration")
        except Exception as e:
            result.warn_test("Anthropic configuration", str(e))
    else:
        result.warn_test("Anthropic configuration", "API key not set")

def test_streamlit_compatibility(result):
    """Test Streamlit compatibility"""
    print("\n🔍 Testing Streamlit Compatibility...")
    
    try:
        import streamlit as st
        result.pass_test("Streamlit import")
        
        # Check version compatibility
        try:
            version = st.__version__
            major, minor = map(int, version.split('.')[:2])
            if major >= 1 and minor >= 28:
                result.pass_test("Streamlit version compatibility")
            else:
                result.warn_test("Streamlit version", f"Version {version} may be outdated")
        except:
            result.warn_test("Streamlit version", "Could not check version")
            
    except Exception as e:
        result.fail_test("Streamlit import", str(e))

def test_pipeline_components(result):
    """Test pipeline components"""
    print("\n🔍 Testing Pipeline Components...")
    
    try:
        from core.streaming_pipeline import get_pipeline_controller
        
        # Test pipeline initialization
        controller = get_pipeline_controller()
        if controller:
            result.pass_test("Pipeline controller initialization")
        else:
            result.fail_test("Pipeline controller initialization", "Failed to create controller")
            
    except Exception as e:
        result.fail_test("Pipeline controller", str(e))
    
    try:
        from core.content_generation import transcribe_audio
        result.pass_test("Content generation import")
    except Exception as e:
        result.fail_test("Content generation import", str(e))

def main():
    print("🚀 WhisperForge App Validation")
    print("=" * 50)
    
    result = ValidationResult()
    
    # Run all tests
    test_imports(result)
    test_environment_variables(result)
    test_file_structure(result)
    test_supabase_connection(result)
    test_oauth_configuration(result)
    test_prompt_files(result)
    test_ai_providers(result)
    test_streamlit_compatibility(result)
    test_pipeline_components(result)
    
    # Print summary
    success = result.summary()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main() 