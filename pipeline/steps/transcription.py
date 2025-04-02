"""
WhisperForge Transcription Module

This module handles audio transcription using various providers (OpenAI, etc.).
It includes logic for large file chunking and transcript combination.
"""

import os
import logging
import tempfile
import asyncio
from typing import Dict, Any, List, BinaryIO, Optional
import mimetypes

# Configure logging
logger = logging.getLogger("whisperforge.pipeline.transcription")

# Maximum size for OpenAI transcriptions (in bytes)
MAX_OPENAI_FILE_SIZE = 25 * 1024 * 1024  # 25MB

async def transcribe_audio(context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transcribe audio file to text using the specified provider.
    
    Args:
        context: Dictionary containing:
            - audio_file: Path to the audio file
            - config: Step configuration with params for transcription
            
    Returns:
        Dictionary containing the transcript
    """
    audio_file = context.get("audio_file")
    if not audio_file:
        raise ValueError("No audio file provided for transcription")
    
    if not os.path.exists(audio_file):
        raise FileNotFoundError(f"Audio file not found: {audio_file}")
    
    config = context.get("config", {})
    params = config.get("params", {})
    
    # Get transcription provider from config or use default
    provider = params.get("provider", "openai")
    model = params.get("model", "whisper-1")
    response_format = params.get("response_format", "verbose_json")
    
    file_size = os.path.getsize(audio_file)
    logger.info(f"Transcribing audio file: {audio_file} ({file_size/1024/1024:.2f} MB)")
    
    if provider == "openai":
        return await transcribe_with_openai(audio_file, model, response_format, file_size)
    else:
        raise ValueError(f"Unsupported transcription provider: {provider}")

async def transcribe_with_openai(
    audio_file: str,
    model: str = "whisper-1",
    response_format: str = "verbose_json",
    file_size: Optional[int] = None
) -> Dict[str, Any]:
    """
    Transcribe audio using OpenAI's Whisper API.
    
    Args:
        audio_file: Path to the audio file
        model: The OpenAI Whisper model to use
        response_format: Format for the response (text, json, verbose_json, etc.)
        file_size: Size of the file in bytes (if already known)
        
    Returns:
        Dictionary containing the transcript and metadata
    """
    try:
        # Lazy import to avoid dependencies if not using OpenAI
        from openai import OpenAI
        
        # Get API key
        from config import load_api_key_for_service
        api_key = load_api_key_for_service("openai")
        
        if not api_key:
            raise ValueError("OpenAI API key not configured")
        
        client = OpenAI(api_key=api_key)
        
        if file_size is None:
            file_size = os.path.getsize(audio_file)
        
        # For large files, implement chunking
        if file_size > MAX_OPENAI_FILE_SIZE:
            logger.info(f"Large file detected ({file_size/1024/1024:.2f} MB), using chunked transcription")
            chunks = await split_audio_file(audio_file)
            
            # Process chunks in parallel (up to 3 at a time)
            semaphore = asyncio.Semaphore(3)
            
            async def process_chunk(chunk_file):
                async with semaphore:
                    logger.info(f"Transcribing chunk: {os.path.basename(chunk_file)}")
                    with open(chunk_file, "rb") as f:
                        response = await asyncio.to_thread(
                            client.audio.transcriptions.create,
                            model=model,
                            file=f,
                            response_format=response_format
                        )
                    return response
            
            # Create tasks for all chunks
            chunk_tasks = [process_chunk(chunk) for chunk in chunks]
            chunk_results = await asyncio.gather(*chunk_tasks)
            
            # Combine chunks
            combined_transcript = combine_transcripts(chunk_results, response_format)
            
            # Clean up temporary files
            for chunk in chunks:
                try:
                    os.unlink(chunk)
                except Exception as e:
                    logger.warning(f"Failed to delete temporary chunk file {chunk}: {str(e)}")
            
            return {
                "transcript": combined_transcript["text"],
                "segments": combined_transcript.get("segments", []),
                "metadata": {
                    "model": model,
                    "provider": "openai",
                    "chunked": True,
                    "chunk_count": len(chunks)
                }
            }
        else:
            # Standard transcription for smaller files
            logger.info(f"Transcribing file with OpenAI ({file_size/1024/1024:.2f} MB)")
            with open(audio_file, "rb") as f:
                response = await asyncio.to_thread(
                    client.audio.transcriptions.create,
                    model=model,
                    file=f,
                    response_format=response_format
                )
            
            if response_format == "text":
                transcript_text = response
                segments = []
            else:
                # For JSON formats
                transcript_text = response.text
                segments = response.get("segments", [])
            
            return {
                "transcript": transcript_text,
                "segments": segments,
                "metadata": {
                    "model": model,
                    "provider": "openai",
                    "chunked": False
                }
            }
    
    except Exception as e:
        logger.error(f"Error in OpenAI transcription: {str(e)}", exc_info=True)
        
        # Try fallback method if the standard method fails
        try:
            logger.info("Attempting fallback transcription method")
            return await transcribe_with_openai_fallback(audio_file, model, response_format)
        except Exception as fallback_e:
            logger.error(f"Fallback transcription also failed: {str(fallback_e)}", exc_info=True)
            raise

async def transcribe_with_openai_fallback(
    audio_file: str,
    model: str = "whisper-1",
    response_format: str = "verbose_json"
) -> Dict[str, Any]:
    """
    Alternative implementation for transcription that uses direct API calls.
    This can be more reliable in some environments with proxy issues.
    """
    import requests
    import json
    
    # Get API key
    from config import load_api_key_for_service
    api_key = load_api_key_for_service("openai")
    
    if not api_key:
        raise ValueError("OpenAI API key not configured")
    
    url = "https://api.openai.com/v1/audio/transcriptions"
    headers = {
        "Authorization": f"Bearer {api_key}"
    }
    
    with open(audio_file, "rb") as f:
        files = {
            "file": (os.path.basename(audio_file), f, "audio/mpeg"),
            "model": (None, model),
            "response_format": (None, response_format)
        }
        
        response = requests.post(url, headers=headers, files=files, timeout=300)
        
    if response.status_code != 200:
        raise Exception(f"OpenAI API error: {response.status_code} - {response.text}")
    
    if response_format == "text":
        transcript_text = response.text
        segments = []
    else:
        # For JSON formats
        response_data = response.json()
        transcript_text = response_data.get("text", "")
        segments = response_data.get("segments", [])
    
    return {
        "transcript": transcript_text,
        "segments": segments,
        "metadata": {
            "model": model,
            "provider": "openai",
            "chunked": False,
            "fallback_method": True
        }
    }

async def split_audio_file(audio_file: str, max_size: int = MAX_OPENAI_FILE_SIZE) -> List[str]:
    """
    Split a large audio file into smaller chunks for processing.
    
    Args:
        audio_file: Path to the audio file to split
        max_size: Maximum size for each chunk in bytes
        
    Returns:
        List of paths to the temporary chunk files
    """
    try:
        import subprocess
        from pydub import AudioSegment
        
        # Load the audio file
        logger.info(f"Loading audio file for chunking: {audio_file}")
        audio = AudioSegment.from_file(audio_file)
        
        # Get audio duration in milliseconds
        duration_ms = len(audio)
        file_size = os.path.getsize(audio_file)
        
        # Calculate number of chunks needed
        # Add 10% margin to account for encoding overhead
        num_chunks = max(1, int((file_size * 1.1) / max_size) + 1)
        
        # Calculate chunk duration
        chunk_duration_ms = duration_ms // num_chunks
        
        # Create temporary directory for chunks
        temp_dir = tempfile.mkdtemp(prefix="whisperforge_chunks_")
        chunk_files = []
        
        logger.info(f"Splitting {audio_file} into {num_chunks} chunks of {chunk_duration_ms/1000:.1f} seconds each")
        
        # Extract audio mimetype
        mimetype, _ = mimetypes.guess_type(audio_file)
        if not mimetype:
            mimetype = "audio/mp3"  # Default to mp3
        
        # Get extension from mimetype
        extension = mimetype.split('/')[-1]
        
        # Split audio and save chunks
        for i in range(num_chunks):
            start_ms = i * chunk_duration_ms
            end_ms = min((i + 1) * chunk_duration_ms, duration_ms)
            
            chunk = audio[start_ms:end_ms]
            chunk_file = os.path.join(temp_dir, f"chunk_{i:03d}.{extension}")
            chunk.export(chunk_file, format=extension)
            chunk_files.append(chunk_file)
            
            logger.debug(f"Created chunk {i+1}/{num_chunks}: {chunk_file} ({os.path.getsize(chunk_file)/1024/1024:.2f} MB)")
        
        return chunk_files
    
    except ImportError:
        logger.warning("pydub not installed. Falling back to ffmpeg directly.")
        # Fallback to using ffmpeg directly
        return await split_audio_file_ffmpeg(audio_file, max_size)

async def split_audio_file_ffmpeg(audio_file: str, max_size: int = MAX_OPENAI_FILE_SIZE) -> List[str]:
    """Fallback method to split audio using ffmpeg directly"""
    import subprocess
    import math
    
    # Get audio duration using ffprobe
    cmd = [
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", audio_file
    ]
    
    try:
        duration = float(subprocess.check_output(cmd).decode('utf-8').strip())
    except subprocess.CalledProcessError as e:
        logger.error(f"Error getting audio duration: {e}")
        raise
    
    file_size = os.path.getsize(audio_file)
    
    # Calculate number of chunks needed (with 10% margin)
    num_chunks = max(1, int((file_size * 1.1) / max_size) + 1)
    
    # Calculate chunk duration in seconds
    chunk_duration = math.ceil(duration / num_chunks)
    
    # Create temporary directory for chunks
    temp_dir = tempfile.mkdtemp(prefix="whisperforge_chunks_")
    chunk_files = []
    
    # Get extension
    _, extension = os.path.splitext(audio_file)
    if not extension:
        extension = ".mp3"
    
    # Split audio using ffmpeg
    for i in range(num_chunks):
        start_time = i * chunk_duration
        output_file = os.path.join(temp_dir, f"chunk_{i:03d}{extension}")
        
        cmd = [
            "ffmpeg", "-y", "-i", audio_file, "-ss", str(start_time),
            "-t", str(chunk_duration), "-c", "copy", output_file
        ]
        
        try:
            subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            chunk_files.append(output_file)
            logger.debug(f"Created chunk {i+1}/{num_chunks}: {output_file}")
        except subprocess.CalledProcessError as e:
            logger.error(f"Error creating chunk {i+1}: {e}")
            raise
    
    return chunk_files

def combine_transcripts(results: List[Any], response_format: str = "verbose_json") -> Dict[str, Any]:
    """
    Combine multiple transcript chunks into a single transcript.
    
    Args:
        results: List of transcription results from OpenAI
        response_format: The format of the transcription responses
        
    Returns:
        Combined transcript with adjusted timestamps
    """
    if not results:
        return {"text": "", "segments": []}
    
    if response_format == "text":
        # Simple concatenation for text format
        combined_text = " ".join(result for result in results)
        return {"text": combined_text, "segments": []}
    
    # For JSON formats
    combined_text = ""
    combined_segments = []
    
    current_offset = 0
    
    for i, result in enumerate(results):
        if hasattr(result, 'text'):
            # For OpenAI SDK response objects
            text = result.text
            segments = result.segments
        elif isinstance(result, dict):
            # For direct API JSON responses
            text = result.get("text", "")
            segments = result.get("segments", [])
        else:
            # Fallback for text responses
            text = str(result)
            segments = []
        
        # Add spacing between chunks if needed
        if combined_text and not combined_text.endswith(('.', '!', '?', '\n')):
            combined_text += " "
        
        combined_text += text
        
        # Adjust segment timestamps and add to combined list
        for segment in segments:
            if isinstance(segment, dict):
                # Deep copy to avoid modifying the original
                adjusted_segment = segment.copy()
                
                # Adjust start and end times
                if "start" in adjusted_segment:
                    adjusted_segment["start"] += current_offset
                if "end" in adjusted_segment:
                    adjusted_segment["end"] += current_offset
                
                # Add chunk information
                adjusted_segment["chunk_index"] = i
                
                combined_segments.append(adjusted_segment)
        
        # Update offset for next chunk
        # Estimate duration from last segment or use fixed value
        if segments and isinstance(segments[-1], dict) and "end" in segments[-1]:
            current_offset += segments[-1]["end"]
        else:
            # If no segments with timing, estimate 30 seconds per chunk
            current_offset += 30
    
    return {
        "text": combined_text,
        "segments": combined_segments
    } 