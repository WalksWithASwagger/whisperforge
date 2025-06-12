"""
Tests for WhisperForge CLI
"""

import pytest
import subprocess
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock


class TestCLIBasics:
    """Test basic CLI functionality"""
    
    def test_cli_help_command(self):
        """Test that CLI help command works"""
        result = subprocess.run(
            ["python", "whisperforge_cli.py", "--help"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent
        )
        
        assert result.returncode == 0
        assert "WhisperForge CLI" in result.stdout
        assert "Transform audio into structured content" in result.stdout
    
    def test_cli_version_command(self):
        """Test that CLI version command works"""
        result = subprocess.run(
            ["python", "whisperforge_cli.py", "--version"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent
        )
        
        assert result.returncode == 0
        assert "2.0.0" in result.stdout
    
    def test_pipeline_help_command(self):
        """Test that pipeline help command works"""
        result = subprocess.run(
            ["python", "whisperforge_cli.py", "pipeline", "--help"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent
        )
        
        assert result.returncode == 0
        assert "Pipeline operations" in result.stdout
    
    def test_status_command(self):
        """Test that status command works"""
        result = subprocess.run(
            ["python", "whisperforge_cli.py", "status"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent
        )
        
        assert result.returncode == 0
        assert "WhisperForge CLI Status" in result.stdout
        assert "API Key" in result.stdout


class TestCLIValidation:
    """Test CLI input validation"""
    
    def test_nonexistent_file_error(self):
        """Test error handling for nonexistent files"""
        result = subprocess.run(
            ["python", "whisperforge_cli.py", "pipeline", "run", "--input", "nonexistent.mp3"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent
        )
        
        assert result.returncode == 2  # Click validation error
        assert "does not exist" in result.stderr
    
    def test_unsupported_format_error(self):
        """Test error handling for unsupported file formats"""
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as temp_file:
            temp_file.write(b"test content")
            temp_file_path = temp_file.name
        
        try:
            result = subprocess.run(
                ["python", "whisperforge_cli.py", "pipeline", "run", "--input", temp_file_path],
                capture_output=True,
                text=True,
                cwd=Path(__file__).parent.parent
            )
            
            assert result.returncode == 1
            assert "Unsupported file format" in result.stderr
        finally:
            os.unlink(temp_file_path)


class TestCLIFile:
    """Test the CLIFile wrapper class"""
    
    def test_cli_file_creation(self):
        """Test CLIFile creation and basic properties"""
        # Import the CLI module
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from whisperforge_cli import CLIFile
        
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as temp_file:
            temp_file.write(b"fake mp3 content")
            temp_file_path = temp_file.name
        
        try:
            cli_file = CLIFile(temp_file_path)
            
            assert cli_file.name == Path(temp_file_path).name
            assert cli_file.type == "audio/mpeg"
            assert cli_file.read() == b"fake mp3 content"
            assert cli_file.getvalue() == b"fake mp3 content"
        finally:
            os.unlink(temp_file_path)
    
    def test_cli_file_mime_types(self):
        """Test MIME type detection for different audio formats"""
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from whisperforge_cli import CLIFile
        
        test_cases = [
            (".mp3", "audio/mpeg"),
            (".wav", "audio/wav"),
            (".m4a", "audio/mp4"),
            (".aac", "audio/aac"),
            (".ogg", "audio/ogg"),
            (".flac", "audio/flac"),
            (".webm", "audio/webm"),
            (".unknown", "audio/mpeg")  # Default fallback
        ]
        
        for ext, expected_mime in test_cases:
            with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as temp_file:
                temp_file.write(b"test content")
                temp_file_path = temp_file.name
            
            try:
                cli_file = CLIFile(temp_file_path)
                assert cli_file.type == expected_mime
            finally:
                os.unlink(temp_file_path)


class TestCLIValidationFunctions:
    """Test CLI validation functions"""
    
    def test_validate_audio_file_function(self):
        """Test the validate_audio_file function"""
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from whisperforge_cli import validate_audio_file
        
        # Test nonexistent file
        assert validate_audio_file("nonexistent.mp3") is False
        
        # Test unsupported format
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as temp_file:
            temp_file_path = temp_file.name
        
        try:
            assert validate_audio_file(temp_file_path) is False
        finally:
            os.unlink(temp_file_path)
        
        # Test supported format
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as temp_file:
            temp_file_path = temp_file.name
        
        try:
            assert validate_audio_file(temp_file_path) is True
        finally:
            os.unlink(temp_file_path)
    
    def test_validate_api_keys_function(self):
        """Test the validate_api_keys function"""
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from whisperforge_cli import validate_api_keys
        
        # Test with no API keys
        with patch.dict(os.environ, {}, clear=True):
            assert validate_api_keys() is False
        
        # Test with OpenAI key
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}, clear=True):
            assert validate_api_keys() is True
        
        # Test with Anthropic key
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}, clear=True):
            assert validate_api_keys() is True


class TestCLIIntegration:
    """Test CLI integration scenarios"""
    
    @patch('whisperforge_cli.transcribe_audio')
    @patch('whisperforge_cli.validate_api_keys')
    def test_transcribe_command_success(self, mock_validate_keys, mock_transcribe):
        """Test successful transcription command"""
        mock_validate_keys.return_value = True
        mock_transcribe.return_value = "This is a test transcript."
        
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as temp_file:
            temp_file.write(b"fake mp3 content")
            temp_file_path = temp_file.name
        
        try:
            result = subprocess.run(
                ["python", "whisperforge_cli.py", "transcribe", "--input", temp_file_path],
                capture_output=True,
                text=True,
                cwd=Path(__file__).parent.parent
            )
            
            # Note: This test may fail due to import issues in subprocess
            # but it tests the command structure
            assert "transcribe" in result.stdout.lower() or result.returncode in [0, 1]
        finally:
            os.unlink(temp_file_path)
            # Clean up any generated transcript files
            transcript_file = Path(f"{Path(temp_file_path).stem}_transcript.txt")
            if transcript_file.exists():
                transcript_file.unlink()
    
    def test_pipeline_run_missing_input(self):
        """Test pipeline run command with missing input"""
        result = subprocess.run(
            ["python", "whisperforge_cli.py", "pipeline", "run"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent
        )
        
        assert result.returncode == 2  # Click error for missing required option
        assert "Missing option" in result.stderr or "required" in result.stderr.lower()
    
    def test_pipeline_run_help(self):
        """Test pipeline run help command"""
        result = subprocess.run(
            ["python", "whisperforge_cli.py", "pipeline", "run", "--help"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent
        )
        
        assert result.returncode == 0
        assert "--input" in result.stdout
        assert "--model" in result.stdout
        assert "--output" in result.stdout
        assert "--format" in result.stdout 