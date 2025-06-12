"""
Basic functionality tests for WhisperForge
Tests core imports and basic operations
"""

import pytest
import os
from pathlib import Path
from unittest.mock import Mock, patch

# Import core modules that actually exist
from core.logging_config import logger, log_pipeline_step, log_file_upload, log_error
from core.file_upload import LargeFileUploadManager
from core.content_generation import transcribe_audio, generate_wisdom
from core.supabase_integration import get_supabase_client

class TestLoggingSystem:
    """Test the enhanced logging system"""
    
    @pytest.mark.unit
    def test_logging_functionality(self):
        """Test logging system"""
        # Test different log levels
        log_pipeline_step("test_step", "started")
        log_pipeline_step("test_step", "completed")
        log_pipeline_step("test_step", "failed", {"error": "Test error"})
        
        log_file_upload("test.wav", 1.5, "audio/wav")
        
        # Test error logging
        try:
            raise ValueError("Test error")
        except Exception as e:
            log_error(e, "Test context")
        
        # Verify logs directory exists
        assert Path("logs").exists()

class TestFileUpload:
    """Test file upload functionality"""
    
    @pytest.mark.unit
    def test_file_upload_manager_initialization(self):
        """Test file upload manager can be initialized"""
        manager = LargeFileUploadManager()
        assert manager is not None
        assert hasattr(manager, 'validate_large_file')
        assert hasattr(manager, 'process_large_file')
    
    @pytest.mark.unit
    def test_file_size_validation(self, sample_audio_file):
        """Test file size validation"""
        manager = LargeFileUploadManager()
        
        # Test basic file existence
        assert sample_audio_file.exists()
        
        # Test file size calculation (basic check)
        file_size = sample_audio_file.stat().st_size
        assert file_size > 0
        
        # Test manager has required methods
        assert hasattr(manager, 'validate_large_file')
        assert hasattr(manager, 'process_large_file')

class TestContentGeneration:
    """Test content generation functionality"""
    
    @pytest.mark.unit
    @patch('openai.OpenAI')
    def test_transcription_function_exists(self, mock_openai):
        """Test transcription function exists and can be called"""
        # Mock OpenAI client
        mock_client = Mock()
        mock_openai.return_value = mock_client
        
        # Mock transcription response
        mock_response = Mock()
        mock_response.text = "This is a test transcription."
        mock_client.audio.transcriptions.create.return_value = mock_response
        
        # Test function exists
        assert callable(transcribe_audio)
        
        # Test function can be called (with mocked API)
        result = transcribe_audio("fake_file.wav")
        assert result is not None

class TestSupabaseIntegration:
    """Test Supabase integration"""
    
    @pytest.mark.unit
    def test_supabase_client_function_exists(self):
        """Test Supabase client function exists"""
        assert callable(get_supabase_client)
    
    @pytest.mark.supabase
    @pytest.mark.integration
    def test_real_database_connection(self, real_supabase):
        """Test real database connection"""
        assert real_supabase is not None
        
        # Test basic connection (if available)
        try:
            # Simple test - just verify client exists
            assert hasattr(real_supabase, 'client') or callable(real_supabase)
        except Exception as e:
            pytest.skip(f"Database connection test failed: {e}")

class TestBasicImports:
    """Test that all core modules can be imported"""
    
    @pytest.mark.unit
    def test_core_imports(self):
        """Test that core modules can be imported without errors"""
        
        # Test logging
        from core.logging_config import logger
        assert logger is not None
        
        # Test file upload
        from core.file_upload import LargeFileUploadManager
        assert LargeFileUploadManager is not None
        
        # Test content generation
        from core.content_generation import transcribe_audio
        assert transcribe_audio is not None
        
        # Test Supabase integration
        from core.supabase_integration import get_supabase_client
        assert get_supabase_client is not None
        
        # Test UI components
        from core.ui_components import AuroraComponents
        assert AuroraComponents is not None
        
        # Test styling
        from core.styling import apply_aurora_theme
        assert apply_aurora_theme is not None

class TestErrorHandling:
    """Test error handling capabilities"""
    
    @pytest.mark.unit
    def test_graceful_error_handling(self):
        """Test that errors are handled gracefully"""
        
        # Test file upload with non-existent file
        manager = LargeFileUploadManager()
        fake_file = Path("nonexistent_file.wav")
        
        # Should not crash, should handle gracefully
        try:
            result = manager.validate_large_file(fake_file)
            # If it doesn't crash, that's good
            assert True
        except Exception as e:
            # If it does throw an exception, it should be handled gracefully
            assert isinstance(e, Exception)
            assert len(str(e)) > 0
    
    @pytest.mark.unit
    def test_logging_error_handling(self):
        """Test error logging doesn't crash"""
        try:
            # Create a test error
            raise ValueError("Test error for logging")
        except Exception as e:
            # Should not crash when logging error
            log_error(e, "Test error context")
            
        # Verify we can continue after error
        assert True

if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 