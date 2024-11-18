from fastapi import FastAPI, UploadFile, File, Depends, HTTPException
from shared.security import SecurityHandler
from shared.config import Config
import openai
import tempfile
import os
import logging
from typing import List

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="WhisperForge Transcription Service")
security = SecurityHandler()
client = openai.OpenAI(api_key=Config.OPENAI_API_KEY)

# Allowed file extensions
ALLOWED_EXTENSIONS = {".mp3", ".wav", ".m4a", ".ogg"}
MAX_FILE_SIZE = 25 * 1024 * 1024  # 25MB


class TranscriptionError(Exception):
    """Custom exception for transcription errors"""

    pass


def validate_audio_file(file: UploadFile) -> None:
    """Validate audio file format and size"""
    # Check file extension
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file format. Allowed formats: {', '.join(ALLOWED_EXTENSIONS)}",
        )

    # Check file size
    file.file.seek(0, 2)  # Seek to end of file
    size = file.file.tell()
    file.file.seek(0)  # Reset file pointer

    if size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size: {MAX_FILE_SIZE/1024/1024}MB",
        )


@app.post("/transcribe")
async def transcribe_audio(
    file: UploadFile = File(...), authenticated: bool = Depends(security.verify_token)
):
    """
    Transcribe audio file using OpenAI's Whisper model.
    Returns transcribed text.
    """
    try:
        logger.info(f"Received file: {file.filename}")

        # Validate file
        validate_audio_file(file)

        # Create temp file
        with tempfile.NamedTemporaryFile(
            delete=False, suffix=os.path.splitext(file.filename)[1]
        ) as temp_file:
            try:
                content = await file.read()
                temp_file.write(content)
                temp_path = temp_file.name

                logger.info("Starting transcription...")
                with open(temp_path, "rb") as audio_file:
                    try:
                        response = client.audio.transcriptions.create(
                            model=Config.WHISPER_MODEL, file=audio_file
                        )
                    except openai.APIError as e:
                        logger.error(f"OpenAI API error: {str(e)}")
                        raise TranscriptionError(f"OpenAI API error: {str(e)}")
                    except openai.RateLimitError:
                        logger.error("Rate limit exceeded")
                        raise HTTPException(
                            status_code=429,
                            detail="Rate limit exceeded. Please try again later.",
                        )

                logger.info("Transcription completed successfully")
                return {
                    "status": "success",
                    "text": response.text,
                    "filename": file.filename,
                    "duration": None,  # TODO: Add audio duration
                }

            finally:
                # Cleanup temp file
                if os.path.exists(temp_path):
                    os.unlink(temp_path)

    except TranscriptionError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "transcription",
        "openai_api": "connected" if Config.OPENAI_API_KEY else "not configured",
    }
