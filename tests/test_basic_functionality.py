"""
Basic functionality tests for WhisperForge v3.0.0
"""

import pytest
import os
from pathlib import Path
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_imports():
    """Test that core modules can be imported without errors"""
    try:
        from core.content_generation import transcribe_audio, generate_wisdom
        from core.file_upload import FileUploadManager, LargeFileUploadManager
        from core.supabase_integration import get_supabase_client
        from core.utils import hash_password, DEFAULT_PROMPTS
        from core.visible_thinking import thinking_step_start
        assert True, "All core imports successful"
    except ImportError as e:
        pytest.fail(f"Import error: {e}")

def test_version_file():
    """Test that VERSION file exists and contains valid version"""
    version_file = Path(__file__).parent.parent / "VERSION"
    assert version_file.exists(), "VERSION file should exist"
    
    version = version_file.read_text().strip()
    assert version == "3.0.0", f"Expected version 3.0.0, got {version}"

def test_app_files_exist():
    """Test that required app files exist"""
    root = Path(__file__).parent.parent
    
    # Main app should exist
    assert (root / "app_simple.py").exists(), "app_simple.py should exist"
    
    # Redirect app should exist
    assert (root / "app.py").exists(), "app.py redirect should exist"
    
    # Procfile should exist and point to app_simple.py
    procfile = root / "Procfile"
    assert procfile.exists(), "Procfile should exist"
    
    content = procfile.read_text()
    assert "app_simple.py" in content, "Procfile should reference app_simple.py"

def test_requirements_file():
    """Test that requirements.txt exists and has core dependencies"""
    req_file = Path(__file__).parent.parent / "requirements.txt"
    assert req_file.exists(), "requirements.txt should exist"
    
    content = req_file.read_text()
    required_deps = ["streamlit", "openai", "supabase", "pydub"]
    
    for dep in required_deps:
        assert dep in content, f"Required dependency {dep} not found in requirements.txt"

@pytest.mark.unit
def test_hash_password():
    """Test password hashing utility"""
    from core.utils import hash_password
    
    password = "test_password_123"
    hashed = hash_password(password)
    
    assert hashed != password, "Password should be hashed"
    assert len(hashed) > 20, "Hashed password should be longer than original"

@pytest.mark.unit
def test_default_prompts():
    """Test that default prompts are available"""
    from core.utils import DEFAULT_PROMPTS
    
    assert isinstance(DEFAULT_PROMPTS, dict), "DEFAULT_PROMPTS should be a dictionary"
    assert len(DEFAULT_PROMPTS) > 0, "Should have at least one default prompt"

@pytest.mark.unit
def test_visible_thinking_functions():
    """Test that visible thinking functions work without errors"""
    from core.visible_thinking import thinking_step_start, thinking_step_complete, thinking_error
    
    # These should not raise exceptions
    thinking_step_start("test_step")
    thinking_step_complete("test_step")
    thinking_error("test_step", "test error")
    
    assert True, "Visible thinking functions executed without errors"

def test_core_directory_structure():
    """Test that core directory has expected modules"""
    core_dir = Path(__file__).parent.parent / "core"
    assert core_dir.exists(), "core directory should exist"
    
    expected_modules = [
        "content_generation.py",
        "file_upload.py", 
        "supabase_integration.py",
        "utils.py",
        "visible_thinking.py"
    ]
    
    for module in expected_modules:
        module_path = core_dir / module
        assert module_path.exists(), f"Core module {module} should exist"

if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 