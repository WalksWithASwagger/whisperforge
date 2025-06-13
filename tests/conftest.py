"""
Pytest configuration and fixtures for WhisperForge testing
"""

import pytest
import os
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch
import streamlit as st
from streamlit.testing.v1 import AppTest

# Add project root to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load environment variables from .env file if it exists
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv not installed, skip

from core.logging_config import logger
from core.supabase_integration import get_supabase_client

@pytest.fixture(scope="session")
def test_env():
    """Set up test environment variables"""
    # Store original env vars
    original_env = {}
    test_vars = {
        'SUPABASE_URL': os.getenv('SUPABASE_URL', 'https://test.supabase.co'),
        'SUPABASE_ANON_KEY': os.getenv('SUPABASE_ANON_KEY', 'test-anon-key'),
        'OPENAI_API_KEY': os.getenv('OPENAI_API_KEY', 'test-openai-key'),
        'ANTHROPIC_API_KEY': os.getenv('ANTHROPIC_API_KEY', 'test-anthropic-key'),
        'GROQ_API_KEY': os.getenv('GROQ_API_KEY', 'test-groq-key'),
        'TESTING': 'true'
    }
    
    # Set test environment
    for key, value in test_vars.items():
        original_env[key] = os.getenv(key)
        os.environ[key] = value
    
    yield test_vars
    
    # Restore original environment
    for key, value in original_env.items():
        if value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = value

@pytest.fixture
def temp_dir():
    """Create temporary directory for test files"""
    temp_path = tempfile.mkdtemp()
    yield Path(temp_path)
    shutil.rmtree(temp_path)

@pytest.fixture
def sample_audio_file(temp_dir):
    """Create a sample audio file for testing"""
    # Create a minimal WAV file (just headers, no actual audio)
    audio_file = temp_dir / "test_audio.wav"
    
    # WAV file header (44 bytes)
    wav_header = b'RIFF\x24\x08\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x02\x00\x44\xac\x00\x00\x10\xb1\x02\x00\x04\x00\x10\x00data\x00\x08\x00\x00'
    
    with open(audio_file, 'wb') as f:
        f.write(wav_header)
        # Add some dummy audio data
        f.write(b'\x00' * 2048)
    
    return audio_file

@pytest.fixture
def large_audio_file(temp_dir):
    """Create a large audio file for testing chunking"""
    audio_file = temp_dir / "large_test_audio.wav"
    
    # WAV file header
    wav_header = b'RIFF\x24\x08\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x02\x00\x44\xac\x00\x00\x10\xb1\x02\x00\x04\x00\x10\x00data\x00\x08\x00\x00'
    
    with open(audio_file, 'wb') as f:
        f.write(wav_header)
        # Create ~30MB file to trigger chunking
        chunk_size = 1024 * 1024  # 1MB chunks
        for _ in range(30):
            f.write(b'\x00' * chunk_size)
    
    return audio_file

@pytest.fixture
def mock_supabase():
    """Mock Supabase client for testing"""
    with patch('core.supabase_client.create_client') as mock_create:
        mock_client = Mock()
        mock_create.return_value = mock_client
        
        # Mock successful responses
        mock_client.table.return_value.insert.return_value.execute.return_value.data = [{'id': 'test-id'}]
        mock_client.table.return_value.select.return_value.execute.return_value.data = []
        mock_client.table.return_value.update.return_value.eq.return_value.execute.return_value.data = [{'id': 'test-id'}]
        
        yield mock_client

@pytest.fixture
def real_supabase():
    """Real Supabase client for integration testing"""
    try:
        client = get_supabase_client()
        if client:
            yield client
        else:
            pytest.skip("Supabase not available for integration testing")
    except Exception as e:
        pytest.skip(f"Supabase connection failed: {e}")

@pytest.fixture
def streamlit_app():
    """Streamlit app test fixture - Updated to use app_simple.py"""
    app = AppTest.from_file("app_simple.py")
    return app

@pytest.fixture
def mock_openai():
    """Mock OpenAI API responses"""
    with patch('openai.OpenAI') as mock_openai:
        mock_client = Mock()
        mock_openai.return_value = mock_client
        
        # Mock transcription response
        mock_client.audio.transcriptions.create.return_value.text = "This is a test transcription."
        
        # Mock chat completion response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "This is a test AI response."
        mock_client.chat.completions.create.return_value = mock_response
        
        yield mock_client

@pytest.fixture
def mock_anthropic():
    """Mock Anthropic API responses"""
    with patch('anthropic.Anthropic') as mock_anthropic:
        mock_client = Mock()
        mock_anthropic.return_value = mock_client
        
        # Mock message response
        mock_response = Mock()
        mock_response.content = [Mock()]
        mock_response.content[0].text = "This is a test Anthropic response."
        mock_client.messages.create.return_value = mock_response
        
        yield mock_client

@pytest.fixture(autouse=True)
def setup_logging():
    """Set up logging for tests"""
    logger.logger.info("🧪 Starting test session")
    yield
    logger.logger.info("🧪 Test session completed")

# Test markers
def pytest_configure(config):
    """Configure pytest markers"""
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests (may be slow)"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests (fast)"
    )
    config.addinivalue_line(
        "markers", "supabase: marks tests that require Supabase connection"
    )
    config.addinivalue_line(
        "markers", "ai: marks tests that require AI API keys"
    ) 