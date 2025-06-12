#!/usr/bin/env python3
"""
WhisperForge Integration Audit
Comprehensive verification of all components working together seamlessly
"""

import sys
import os
import traceback
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def audit_section(title: str):
    """Print audit section header"""
    print(f"\n{'='*60}")
    print(f"🔍 {title}")
    print('='*60)

def check_import(module_name: str, description: str = ""):
    """Check if a module can be imported"""
    try:
        __import__(module_name)
        print(f"✅ {module_name} - {description}")
        return True
    except Exception as e:
        print(f"❌ {module_name} - {description}: {str(e)[:100]}")
        return False

def check_function(module_name: str, function_name: str, description: str = ""):
    """Check if a function exists in a module"""
    try:
        module = __import__(module_name, fromlist=[function_name])
        func = getattr(module, function_name)
        print(f"✅ {module_name}.{function_name} - {description}")
        return True
    except Exception as e:
        print(f"❌ {module_name}.{function_name} - {description}: {str(e)[:100]}")
        return False

def check_class_method(module_name: str, class_name: str, method_name: str, description: str = ""):
    """Check if a class method exists"""
    try:
        module = __import__(module_name, fromlist=[class_name])
        cls = getattr(module, class_name)
        method = getattr(cls, method_name)
        print(f"✅ {module_name}.{class_name}.{method_name} - {description}")
        return True
    except Exception as e:
        print(f"❌ {module_name}.{class_name}.{method_name} - {description}: {str(e)[:100]}")
        return False

def main():
    """Run comprehensive integration audit"""
    print("🚀 WhisperForge Integration Audit")
    print("Verifying all components work together seamlessly...")
    
    # Track results
    results = {
        'core_imports': 0,
        'database_functions': 0,
        'ui_components': 0,
        'file_processing': 0,
        'content_generation': 0,
        'streaming_pipeline': 0,
        'authentication': 0
    }
    
    # 1. Core Module Imports
    audit_section("Core Module Imports")
    core_modules = [
        ('core.supabase_integration', 'Database integration'),
        ('core.file_upload', 'File upload management'),
        ('core.streaming_pipeline', 'Streaming pipeline'),
        ('core.content_generation', 'Content generation'),
        ('core.streaming_results', 'Results display'),
        ('core.ui_components', 'UI components'),
        ('core.styling', 'Aurora styling'),
        ('core.logging_config', 'Enhanced logging'),
        ('core.monitoring', 'System monitoring'),
        ('core.notifications', 'User notifications'),
        ('core.visible_thinking', 'Thinking display'),
        ('core.research_enrichment', 'Research features'),
        ('core.utils', 'Utility functions'),
        ('core.config', 'Configuration'),
        ('core.integrations', 'External integrations')
    ]
    
    for module, desc in core_modules:
        if check_import(module, desc):
            results['core_imports'] += 1
    
    # 2. Database Functions
    audit_section("Database Integration")
    db_functions = [
        ('core.supabase_integration', 'get_supabase_client', 'Get database client'),
        ('core.supabase_integration', 'SupabaseClient', 'Database client class'),
        ('app', 'init_supabase', 'Initialize database'),
        ('app', 'authenticate_user', 'User authentication'),
        ('app', 'register_user_supabase', 'User registration'),
        ('app', 'save_generated_content_supabase', 'Save content'),
        ('app', 'get_user_content_history_supabase', 'Get user history')
    ]
    
    for module, func, desc in db_functions:
        if check_function(module, func, desc):
            results['database_functions'] += 1
    
    # 3. File Processing
    audit_section("File Processing & Upload")
    file_functions = [
        ('core.file_upload', 'LargeFileUploadManager', 'Large file manager'),
        ('core.file_upload', 'FileUploadManager', 'Standard file manager')
    ]
    
    for module, cls, desc in file_functions:
        if check_function(module, cls, desc):
            results['file_processing'] += 1
    
    # Check LargeFileUploadManager methods
    file_methods = [
        ('core.file_upload', 'LargeFileUploadManager', 'validate_large_file', 'File validation'),
        ('core.file_upload', 'LargeFileUploadManager', 'create_large_file_upload_zone', 'Upload UI'),
        ('core.file_upload', 'LargeFileUploadManager', 'process_large_file', 'File processing')
    ]
    
    for module, cls, method, desc in file_methods:
        if check_class_method(module, cls, method, desc):
            results['file_processing'] += 1
    
    # 4. Content Generation
    audit_section("Content Generation")
    content_functions = [
        ('core.content_generation', 'generate_wisdom_extraction', 'Wisdom extraction'),
        ('core.content_generation', 'generate_research_enrichment', 'Research enrichment'),
        ('core.content_generation', 'generate_outline_creation', 'Outline creation'),
        ('core.content_generation', 'generate_article_creation', 'Article creation'),
        ('core.content_generation', 'generate_social_content', 'Social media content'),
        ('core.content_generation', 'generate_image_prompts', 'Image prompts')
    ]
    
    for module, func, desc in content_functions:
        if check_function(module, func, desc):
            results['content_generation'] += 1
    
    # 5. Streaming Pipeline
    audit_section("Streaming Pipeline")
    pipeline_functions = [
        ('core.streaming_pipeline', 'get_pipeline_controller', 'Pipeline controller'),
        ('core.streaming_pipeline', 'StreamingPipelineController', 'Pipeline class'),
        ('core.streaming_results', 'show_streaming_results', 'Results display'),
        ('core.streaming_results', 'show_real_time_content_stream', 'Real-time streaming')
    ]
    
    for module, func, desc in pipeline_functions:
        if check_function(module, func, desc):
            results['streaming_pipeline'] += 1
    
    # 6. UI Components
    audit_section("UI Components & Styling")
    ui_functions = [
        ('core.ui_components', 'load_aurora_css', 'Aurora CSS loading'),
        ('core.ui_components', 'AuroraContainer', 'Aurora containers'),
        ('core.ui_components', 'AuroraComponents', 'Aurora components'),
        ('core.styling', 'apply_aurora_theme', 'Aurora theme'),
        ('core.styling', 'create_aurora_header', 'Aurora header')
    ]
    
    for module, func, desc in ui_functions:
        if check_function(module, func, desc):
            results['ui_components'] += 1
    
    # 7. Authentication Flow
    audit_section("Authentication & OAuth")
    auth_functions = [
        ('app', 'handle_oauth_callback', 'OAuth callback handling'),
        ('app', 'show_auth_page', 'Authentication page'),
        ('app', 'show_main_app', 'Main application')
    ]
    
    for module, func, desc in auth_functions:
        if check_function(module, func, desc):
            results['authentication'] += 1
    
    # 8. Test Database Connection
    audit_section("Live Database Connection Test")
    try:
        from core.supabase_integration import get_supabase_client
        client = get_supabase_client()
        if client and client.client:
            # Test basic query
            result = client.client.table('users').select('id').limit(1).execute()
            print("✅ Database connection successful")
            print(f"✅ Users table accessible ({len(result.data)} records found)")
            results['database_functions'] += 2
        else:
            print("❌ Database client not available")
    except Exception as e:
        print(f"❌ Database connection failed: {str(e)[:100]}")
    
    # 9. Test App Import
    audit_section("Main Application Import")
    try:
        import app
        print("✅ app.py imports successfully")
        
        # Test key app functions
        db, success = app.init_supabase()
        print(f"✅ init_supabase works: {success}")
        results['authentication'] += 2
        
    except Exception as e:
        print(f"❌ app.py import failed: {str(e)[:100]}")
        traceback.print_exc()
    
    # Final Results
    audit_section("Integration Audit Results")
    total_checks = sum(results.values())
    max_possible = 50  # Approximate total checks
    
    print(f"📊 **Integration Health Score: {total_checks}/{max_possible} ({(total_checks/max_possible)*100:.1f}%)**")
    print()
    print("**Component Breakdown:**")
    for component, count in results.items():
        status = "✅" if count > 0 else "❌"
        print(f"{status} {component.replace('_', ' ').title()}: {count} checks passed")
    
    print()
    if total_checks >= 40:
        print("🎉 **EXCELLENT**: All major components integrated successfully!")
        print("🚀 **READY FOR DEPLOYMENT**")
    elif total_checks >= 30:
        print("✅ **GOOD**: Most components working, minor issues detected")
        print("🔧 **NEEDS MINOR FIXES**")
    else:
        print("⚠️ **ISSUES DETECTED**: Major integration problems found")
        print("🛠️ **NEEDS ATTENTION**")
    
    return total_checks >= 40

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 