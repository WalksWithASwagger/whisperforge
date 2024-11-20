from fastapi import FastAPI, UploadFile, File, Depends, HTTPException
from shared.security import SecurityHandler
from shared.config import Config
import tempfile
import os
import logging
from typing import List
from openai import OpenAI
import math
from pydub import AudioSegment

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="WhisperForge Transcription Service")
security = SecurityHandler()
client = OpenAI(api_key=Config.OPENAI_API_KEY)

ALLOWED_EXTENSIONS = {".mp3", ".wav", ".m4a", ".ogg"}
MAX_FILE_SIZE = 25 * 1024 * 1024  # 25MB
CHUNK_SIZE = 10 * 1024 * 1024  # 10MB chunks for faster processing

def validate_audio_file(file: UploadFile) -> None:
    """Validate audio file format"""
    ext = os.path.splitext(file.filename)[1].lower()
    logger.info(f"File extension: {ext}")
    
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file format. Allowed formats: {', '.join(ALLOWED_EXTENSIONS)}"
        )

def chunk_audio(file_path: str) -> List[str]:
    """Split audio file into chunks under 10MB"""
    try:
        logger.info(f"Loading audio file for chunking: {file_path}")
        audio = AudioSegment.from_file(file_path)
        
        file_size = os.path.getsize(file_path)
        chunk_count = math.ceil(file_size / CHUNK_SIZE)
        chunk_length = len(audio) / chunk_count
        
        logger.info(f"Splitting {file_size/1024/1024:.2f}MB file into {chunk_count} chunks")
        
        chunk_files = []
        for i in range(chunk_count):
            start_time = int(i * chunk_length)
            end_time = int((i + 1) * chunk_length)
            
            chunk = audio[start_time:end_time]
            chunk_path = f"{file_path}_chunk_{i}.mp3"
            chunk.export(chunk_path, format="mp3", bitrate="128k")
            chunk_files.append(chunk_path)
            logger.info(f"Created chunk {i+1}/{chunk_count}")
            
        return chunk_files
    except Exception as e:
        logger.error(f"Error chunking audio: {str(e)}")
        raise

@app.post("/transcribe")
async def transcribe_audio(
    file: UploadFile = File(...),
    language: str = None,
    authenticated: bool = Depends(security.verify_token)
):
    """Transcribe audio file using OpenAI's Whisper model"""
    try:
        logger.info(f"Received file: {file.filename}")
        
        if not Config.OPENAI_API_KEY:
            raise HTTPException(status_code=500, detail="OpenAI API key not configured")

        validate_audio_file(file)
        
        # Create temp file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1])
        temp_path = temp_file.name
        
        try:
            content = await file.read()
            temp_file.write(content)
            temp_file.close()
            
            file_size = os.path.getsize(temp_path)
            logger.info(f"File size: {file_size/1024/1024:.2f}MB")

            if file_size > MAX_FILE_SIZE:
                logger.info("File exceeds size limit, chunking...")
                chunks = chunk_audio(temp_path)
                full_transcript = []

                for chunk_path in chunks:
                    try:
                        with open(chunk_path, "rb") as audio_chunk:
                            response = client.audio.transcriptions.create(
                                model="whisper-1",
                                file=audio_chunk,
                                language=language if language and language != "AUTO" else None
                            )
                            full_transcript.append(response.text)
                    finally:
                        if os.path.exists(chunk_path):
                            os.unlink(chunk_path)

                return {
                    "status": "success",
                    "text": " ".join(full_transcript),
                    "filename": file.filename
                }
            else:
                logger.info("Starting transcription with OpenAI...")
                with open(temp_path, "rb") as audio_file:
                    response = client.audio.transcriptions.create(
                        model="whisper-1",
                        file=audio_file,
                        language=language if language and language != "AUTO" else None
                    )
                    return {
                        "status": "success",
                        "text": response.text,
                        "filename": file.filename
                    }
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
                logger.info(f"Cleaned up temporary file: {temp_path}")

    except Exception as e:
        logger.error(f"Transcription error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "transcription",
        "openai_api": "connected" if Config.OPENAI_API_KEY else "not configured"
    }
