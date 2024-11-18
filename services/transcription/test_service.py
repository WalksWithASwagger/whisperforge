import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
import io
from service import app, validate_audio_file, TranscriptionError
from fastapi import UploadFile, HTTPException

client = TestClient(app)


# Mock audio file
def create_mock_audio_file(filename: str, content: bytes = b"test audio content"):
    return UploadFile(
        filename=filename, file=io.BytesIO(content), content_type="audio/mpeg"
    )


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_validate_audio_file_valid():
    mock_file = create_mock_audio_file("test.mp3")
    try:
        validate_audio_file(mock_file)
    except HTTPException:
        pytest.fail("validate_audio_file raised HTTPException unexpectedly")


def test_validate_audio_file_invalid_extension():
    mock_file = create_mock_audio_file("test.txt")
    with pytest.raises(HTTPException) as exc_info:
        validate_audio_file(mock_file)
    assert exc_info.value.status_code == 400
    assert "Invalid file format" in str(exc_info.value.detail)


@patch("openai.OpenAI")
def test_transcribe_audio_success(mock_openai):
    # Mock OpenAI response
    mock_response = Mock()
    mock_response.text = "Test transcription"
    mock_openai.return_value.audio.transcriptions.create.return_value = mock_response

    # Create test file
    test_file = create_mock_audio_file("test.mp3")

    # Mock authentication
    with patch("service.security.verify_token", return_value=True):
        response = client.post(
            "/transcribe", files={"file": ("test.mp3", test_file.file, "audio/mpeg")}
        )

    assert response.status_code == 200
    assert response.json()["text"] == "Test transcription"


@patch("openai.OpenAI")
def test_transcribe_audio_api_error(mock_openai):
    # Mock OpenAI error
    mock_openai.return_value.audio.transcriptions.create.side_effect = openai.APIError(
        "API Error"
    )

    test_file = create_mock_audio_file("test.mp3")

    with patch("service.security.verify_token", return_value=True):
        response = client.post(
            "/transcribe", files={"file": ("test.mp3", test_file.file, "audio/mpeg")}
        )

    assert response.status_code == 500
    assert "API Error" in response.json()["detail"]
