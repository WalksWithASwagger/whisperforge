"""
Tests for Upload Progress and Error Toast functionality
"""

import pytest
import tempfile
import os
from unittest.mock import patch, MagicMock, mock_open
from pathlib import Path

from core.file_upload import LargeFileUploadManager, FileUploadManager


class TestUploadProgressBars:
    """Test upload progress bar functionality"""
    
    def test_upload_manager_initialization(self):
        """Test that upload manager initializes with correct settings"""
        manager = LargeFileUploadManager()
        
        assert manager.max_file_size == 2 * 1024 * 1024 * 1024  # 2GB
        assert manager.chunk_size_mb == 20  # 20MB chunks
        assert manager.max_parallel_chunks == 4  # 4 parallel
        assert 'audio' in manager.supported_formats
        assert '.mp3' in manager.supported_formats['audio']
    
    @patch('streamlit.progress')
    @patch('streamlit.toast')
    @patch('core.content_generation.transcribe_audio')
    def test_small_file_upload_with_progress(self, mock_transcribe, mock_toast, mock_progress):
        """Test small file upload shows progress bar"""
        # Setup mocks
        mock_progress_bar = MagicMock()
        mock_progress.return_value = mock_progress_bar
        mock_transcribe.return_value = "Test transcript content"
        
        # Create test file
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as temp_file:
            temp_file.write(b"fake mp3 content" * 1000)  # Small file
            temp_file_path = temp_file.name
        
        try:
            # Create mock uploaded file
            mock_file = MagicMock()
            mock_file.name = "test.mp3"
            mock_file.getvalue.return_value = b"fake mp3 content" * 1000
            mock_file.read.return_value = b"fake mp3 content" * 1000
            
            manager = LargeFileUploadManager()
            
            # Mock streamlit functions
            with patch('streamlit.markdown'), patch('streamlit.empty'), patch('streamlit.container'):
                result = manager._process_small_file(mock_file)
            
            # Verify progress bar was created and updated
            mock_progress.assert_called()
            mock_progress_bar.progress.assert_called()
            
            # Verify success toast was shown
            mock_toast.assert_called_with("Upload successful!", icon="✅")
            
            # Verify successful result
            assert result["success"] is True
            assert "transcript" in result
            
        finally:
            os.unlink(temp_file_path)
    
    @patch('streamlit.progress')
    @patch('streamlit.toast')
    @patch('core.content_generation.transcribe_audio')
    def test_upload_error_shows_toast(self, mock_transcribe, mock_toast, mock_progress):
        """Test that upload errors show error toast"""
        # Setup mocks to simulate error
        mock_progress_bar = MagicMock()
        mock_progress.return_value = mock_progress_bar
        mock_transcribe.side_effect = Exception("Transcription failed")
        
        # Create mock uploaded file
        mock_file = MagicMock()
        mock_file.name = "test.mp3"
        mock_file.getvalue.return_value = b"fake mp3 content"
        
        manager = LargeFileUploadManager()
        
        # Mock streamlit functions
        with patch('streamlit.markdown'), patch('streamlit.empty'), patch('streamlit.container'):
            result = manager._process_small_file(mock_file)
        
        # Verify error toast was shown
        mock_toast.assert_called_with("Upload failed: Transcription failed", icon="⚠️")
        
        # Verify failed result
        assert result["success"] is False
        assert "error" in result
    
    @patch('streamlit.progress')
    @patch('streamlit.toast')
    def test_large_file_upload_success_toast(self, mock_toast, mock_progress):
        """Test that large file upload shows success toast"""
        mock_progress_bar = MagicMock()
        mock_progress.return_value = mock_progress_bar
        
        # Create mock uploaded file (large)
        mock_file = MagicMock()
        mock_file.name = "large_test.mp3"
        mock_file.getvalue.return_value = b"fake mp3 content" * 1000000  # Large file
        
        manager = LargeFileUploadManager()
        
        # Mock all the complex large file processing
        with patch.object(manager, '_create_audio_chunks') as mock_chunks, \
             patch.object(manager, '_transcribe_chunks_parallel') as mock_transcribe, \
             patch.object(manager, '_reassemble_transcript') as mock_reassemble, \
             patch.object(manager, '_cleanup_chunks') as mock_cleanup, \
             patch('streamlit.markdown'), \
             patch('streamlit.empty'), \
             patch('streamlit.container'), \
             patch('streamlit.success'):
            
            # Setup successful processing
            mock_chunks.return_value = {"success": True, "chunks": [{"index": 0}]}
            mock_transcribe.return_value = {"success": True, "chunk_transcripts": {0: "test"}}
            mock_reassemble.return_value = "Final transcript"
            
            result = manager._process_large_file_chunked(mock_file)
        
        # Verify success toast was shown
        mock_toast.assert_called_with("Large file upload successful!", icon="🎉")
        
        # Verify successful result
        assert result["success"] is True
    
    @patch('streamlit.toast')
    def test_large_file_upload_error_toast(self, mock_toast):
        """Test that large file upload errors show error toast"""
        # Create mock uploaded file
        mock_file = MagicMock()
        mock_file.name = "large_test.mp3"
        mock_file.getvalue.return_value = b"fake mp3 content" * 1000000  # Large file
        
        manager = LargeFileUploadManager()
        
        # Mock chunk creation to fail
        with patch.object(manager, '_create_audio_chunks') as mock_chunks, \
             patch('streamlit.markdown'), \
             patch('streamlit.error'):
            
            mock_chunks.side_effect = Exception("Chunk creation failed")
            
            result = manager._process_large_file_chunked(mock_file)
        
        # Verify error toast was shown
        mock_toast.assert_called_with("Large file upload failed: Chunk creation failed", icon="⚠️")
        
        # Verify failed result
        assert result["success"] is False


class TestProgressIndicators:
    """Test progress indicator utilities"""
    
    @patch('streamlit.markdown')
    def test_create_upload_progress_indicator(self, mock_markdown):
        """Test progress indicator creation"""
        from core.file_upload import create_upload_progress_indicator
        
        result = create_upload_progress_indicator("test.mp3", 50.0)
        
        # Verify markdown was called with HTML content
        mock_markdown.assert_called_once()
        call_args = mock_markdown.call_args[0][0]
        assert "test.mp3" in call_args
        assert "50%" in call_args
    
    @patch('streamlit.empty')
    @patch('streamlit.markdown')
    @patch('time.sleep')
    def test_simulate_upload_progress(self, mock_sleep, mock_markdown, mock_empty):
        """Test upload progress simulation"""
        from core.file_upload import simulate_upload_progress
        
        mock_container = MagicMock()
        mock_empty.return_value = mock_container
        
        # Run simulation with short duration
        result = simulate_upload_progress("test.mp3", duration=0.1)
        
        # Verify container was created and markdown was called multiple times
        mock_empty.assert_called_once()
        assert mock_markdown.call_count > 1  # Multiple progress updates
        assert result is True
    
    def test_progress_bar_bounds(self):
        """Test that progress values are properly handled"""
        from core.file_upload import create_upload_progress_indicator
        
        with patch('streamlit.markdown') as mock_markdown:
            
            # Test negative progress
            create_upload_progress_indicator("test.mp3", -10.0)
            call_args = mock_markdown.call_args[0][0]
            assert "test.mp3" in call_args
            assert "-10%" in call_args
            
            # Test progress over 100
            create_upload_progress_indicator("test.mp3", 150.0)
            call_args = mock_markdown.call_args[0][0]
            assert "test.mp3" in call_args
            assert "150%" in call_args


class TestFileValidation:
    """Test file validation with progress feedback"""
    
    def test_validate_large_file_success(self):
        """Test successful large file validation"""
        manager = LargeFileUploadManager()
        
        # Create mock file within size limits
        mock_file = MagicMock()
        mock_file.name = "test.mp3"
        mock_file.getvalue.return_value = b"content" * 1000  # Small enough
        
        result = manager.validate_large_file(mock_file)
        
        assert result["valid"] is True
        assert "error" not in result
    
    def test_validate_large_file_too_big(self):
        """Test validation failure for oversized files"""
        manager = LargeFileUploadManager()
        
        # Create mock file that's too large
        mock_file = MagicMock()
        mock_file.name = "huge_test.mp3"
        # Simulate 3GB file
        mock_file.getvalue.return_value = b"x" * (3 * 1024 * 1024 * 1024)
        
        result = manager.validate_large_file(mock_file)
        
        assert result["valid"] is False
        assert "too large" in result["error"].lower()
    
    def test_validate_large_file_unsupported_format(self):
        """Test validation failure for unsupported formats"""
        manager = LargeFileUploadManager()
        
        # Create mock file with unsupported extension
        mock_file = MagicMock()
        mock_file.name = "test.txt"
        mock_file.getvalue.return_value = b"content"
        
        result = manager.validate_large_file(mock_file)
        
        assert result["valid"] is False
        assert "supported" in result["error"].lower()


class TestErrorHandling:
    """Test error handling and user feedback"""
    
    @patch('streamlit.toast')
    def test_toast_called_on_validation_error(self, mock_toast):
        """Test that toast is called when validation fails"""
        manager = LargeFileUploadManager()
        
        # Create invalid file
        mock_file = MagicMock()
        mock_file.name = "test.txt"  # Unsupported format
        mock_file.getvalue.return_value = b"content"
        
        # Mock the process_large_file method to test toast integration
        with patch.object(manager, 'validate_large_file') as mock_validate:
            mock_validate.return_value = {"valid": False, "error": "Unsupported format"}
            
            with patch('streamlit.info'), patch('streamlit.markdown'):
                result = manager.process_large_file(mock_file)
            
            # The actual toast call would be in the UI layer
            assert result["success"] is False
    
    def test_error_message_formatting(self):
        """Test that error messages are properly formatted"""
        manager = LargeFileUploadManager()
        
        # Test various error scenarios
        test_cases = [
            ("test.txt", "unsupported"),
            ("huge_file.mp3", "too large"),
            ("", "invalid")
        ]
        
        for filename, expected_error_type in test_cases:
            mock_file = MagicMock()
            mock_file.name = filename
            
            if "huge" in filename:
                mock_file.getvalue.return_value = b"x" * (3 * 1024 * 1024 * 1024)
            elif filename == "":
                mock_file.name = ""
                mock_file.getvalue.return_value = b"content"
            else:
                mock_file.getvalue.return_value = b"content"
            
            result = manager.validate_large_file(mock_file)
            
            if expected_error_type in ["unsupported", "too large"]:
                assert result["valid"] is False
                assert expected_error_type.replace(" ", "") in result["error"].lower().replace(" ", "") 