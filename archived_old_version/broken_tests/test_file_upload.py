"""
Tests for core.file_upload module
Minimal test coverage for file upload functionality
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
from pathlib import Path
import io
import os

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.file_upload import LargeFileUploadManager, FileUploadManager


class TestLargeFileUploadManager:
    """Test cases for LargeFileUploadManager class"""
    
    @pytest.fixture
    def upload_manager(self):
        """Create upload manager instance for testing"""
        return LargeFileUploadManager()
    
    @pytest.fixture
    def mock_wav_file(self):
        """Create a mock WAV file for testing"""
        mock_file = Mock()
        mock_file.name = "test_audio.wav"
        mock_file.getvalue.return_value = b"fake_wav_data" * 1000  # Small file
        return mock_file
    
    @pytest.fixture
    def mock_large_wav_file(self):
        """Create a mock large WAV file for testing"""
        mock_file = Mock()
        mock_file.name = "large_audio.wav"
        # Simulate 100MB file
        mock_file.getvalue.return_value = b"fake_wav_data" * (100 * 1024 * 1024 // 13)
        return mock_file
    
    @pytest.fixture
    def mock_unsupported_file(self):
        """Create a mock unsupported file for testing"""
        mock_file = Mock()
        mock_file.name = "document.txt"
        mock_file.getvalue.return_value = b"text content"
        return mock_file
    
    def test_upload_manager_initialization(self, upload_manager):
        """Test that upload manager initializes with correct settings"""
        assert upload_manager.max_file_size == 2 * 1024 * 1024 * 1024  # 2GB
        assert upload_manager.chunk_size_mb == 20
        assert upload_manager.max_parallel_chunks == 4
        assert 'audio' in upload_manager.supported_formats
        assert '.wav' in upload_manager.supported_formats['audio']
        assert '.mp3' in upload_manager.supported_formats['audio']
    
    def test_validate_small_wav_file_returns_valid(self, upload_manager, mock_wav_file):
        """Test that upload of a small wav returns valid result"""
        result = upload_manager.validate_large_file(mock_wav_file)
        
        assert result["valid"] is True
        assert "error" not in result
    
    def test_validate_large_wav_file_returns_valid(self, upload_manager, mock_large_wav_file):
        """Test that upload of a large wav file returns valid result"""
        result = upload_manager.validate_large_file(mock_large_wav_file)
        
        assert result["valid"] is True
        assert "error" not in result
    
    def test_validate_unsupported_extension_raises_error(self, upload_manager, mock_unsupported_file):
        """Test that unsupported extension raises ValueError"""
        result = upload_manager.validate_large_file(mock_unsupported_file)
        
        assert result["valid"] is False
        assert "error" in result
        assert "Unsupported format" in result["error"]
        assert ".txt" in result["error"]
    
    def test_validate_oversized_file_raises_error(self, upload_manager):
        """Test that oversized file raises error"""
        # Create mock file larger than 2GB
        mock_oversized_file = Mock()
        mock_oversized_file.name = "huge_audio.wav"
        mock_oversized_file.getvalue.return_value = b"x" * (3 * 1024 * 1024 * 1024)  # 3GB
        
        result = upload_manager.validate_large_file(mock_oversized_file)
        
        assert result["valid"] is False
        assert "error" in result
        assert "File too large" in result["error"]
        assert "3.0GB" in result["error"]
    
    def test_validate_no_file_returns_error(self, upload_manager):
        """Test that no file provided returns error"""
        result = upload_manager.validate_large_file(None)
        
        assert result["valid"] is False
        assert "error" in result
        assert "No file provided" in result["error"]
    
    @patch('core.file_upload.st')
    def test_create_upload_zone_returns_file_uploader(self, mock_st, upload_manager):
        """Test that create_upload_zone creates file uploader"""
        mock_st.markdown = Mock()
        mock_st.file_uploader = Mock(return_value="mock_uploaded_file")
        
        result = upload_manager.create_large_file_upload_zone()
        
        # Should call markdown for CSS and HTML
        assert mock_st.markdown.call_count >= 2
        
        # Should call file_uploader
        mock_st.file_uploader.assert_called_once()
        
        # Check file_uploader was called with correct parameters
        call_args = mock_st.file_uploader.call_args
        assert "Choose an audio file" in call_args[0]
        assert 'mp3' in call_args[1]['type']
        assert 'wav' in call_args[1]['type']
    
    @patch('core.file_upload.tempfile')
    @patch('core.file_upload.os.path.getsize')
    def test_process_large_file_handles_small_file(self, mock_getsize, mock_tempfile, upload_manager, mock_wav_file):
        """Test that process_large_file correctly handles small files"""
        # Mock file size to be small (under 100MB)
        mock_getsize.return_value = 10 * 1024 * 1024  # 10MB
        
        # Mock tempfile operations
        mock_temp_file = Mock()
        mock_temp_file.name = "/tmp/test_audio.wav"
        mock_tempfile.NamedTemporaryFile.return_value.__enter__.return_value = mock_temp_file
        
        with patch.object(upload_manager, '_process_small_file') as mock_process_small:
            mock_process_small.return_value = {"success": True, "file_id": "test_123"}
            
            result = upload_manager.process_large_file(mock_wav_file)
            
            # Should call _process_small_file for small files
            mock_process_small.assert_called_once()
            assert result["success"] is True
            assert result["file_id"] == "test_123"
    
    def test_supported_audio_formats_comprehensive(self, upload_manager):
        """Test that all expected audio formats are supported"""
        expected_formats = ['.mp3', '.wav', '.m4a', '.aac', '.ogg', '.flac', '.wma', '.webm', '.mpeg', '.mpga', '.oga']
        
        for format_ext in expected_formats:
            assert format_ext in upload_manager.supported_formats['audio'], f"Format {format_ext} should be supported"


class TestFileUploadManager:
    """Test cases for legacy FileUploadManager class"""
    
    def test_file_upload_manager_inherits_from_large_manager(self):
        """Test that FileUploadManager inherits from LargeFileUploadManager"""
        manager = FileUploadManager()
        
        assert isinstance(manager, LargeFileUploadManager)
        assert hasattr(manager, 'legacy_max_file_size')
        assert manager.legacy_max_file_size == 25 * 1024 * 1024  # 25MB
    
    def test_file_upload_manager_has_large_file_capabilities(self):
        """Test that FileUploadManager has all large file capabilities"""
        manager = FileUploadManager()
        
        # Should have all the methods from LargeFileUploadManager
        assert hasattr(manager, 'validate_large_file')
        assert hasattr(manager, 'process_large_file')
        assert hasattr(manager, 'create_large_file_upload_zone')
        
        # Should still have large file limits
        assert manager.max_file_size == 2 * 1024 * 1024 * 1024  # 2GB


class TestFileUploadUtilities:
    """Test cases for utility functions"""
    
    @patch('core.file_upload.st')
    def test_create_upload_progress_indicator(self, mock_st):
        """Test progress indicator creation"""
        from core.file_upload import create_upload_progress_indicator
        
        mock_st.markdown = Mock()
        
        create_upload_progress_indicator("test.wav", 50.0)
        
        # Should call markdown to render progress indicator
        mock_st.markdown.assert_called_once()
        
        # Check that the HTML contains expected elements
        call_args = mock_st.markdown.call_args[0][0]
        assert "test.wav" in call_args
        assert "50%" in call_args
        assert "upload-progress-container" in call_args
    
    @patch('core.file_upload.st')
    @patch('core.file_upload.time.sleep')
    def test_simulate_upload_progress(self, mock_sleep, mock_st):
        """Test upload progress simulation"""
        from core.file_upload import simulate_upload_progress
        
        # Create a mock that supports context manager protocol
        mock_container = Mock()
        mock_container.__enter__ = Mock(return_value=mock_container)
        mock_container.__exit__ = Mock(return_value=None)
        mock_st.empty.return_value = mock_container
        
        result = simulate_upload_progress("test.wav", duration=0.1)
        
        assert result is True
        # Should call sleep multiple times for animation
        assert mock_sleep.call_count > 0


if __name__ == "__main__":
    pytest.main([__file__]) 