import os
import tempfile
import logging
import streamlit as st
import time
import json
from pydub import AudioSegment
import soundfile as sf
import librosa
import math
import concurrent.futures
import threading

# Import from config
from config import UPLOADS_DIR, TEMP_DIR, logger
# Import from integrations
from integrations.openai_service import get_openai_client, direct_transcribe_audio, HARD_CODED_OPENAI_API_KEY

def transcribe_audio(uploaded_file):
    """
    Process the uploaded file from Streamlit and transcribe it using the appropriate function.
    This is the main entry point for audio transcription from the UI.
    
    Args:
        uploaded_file (streamlit.UploadedFile): The uploaded audio file
        
    Returns:
        str: Transcription text
    """
    logger.info(f"Starting transcription of uploaded file: {uploaded_file.name}")
    
    try:
        # Create a temporary file to save the uploaded content
        temp_dir = tempfile.mkdtemp()
        temp_file_path = os.path.join(temp_dir, uploaded_file.name)
        
        # Save the uploaded file to the temporary path
        with open(temp_file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        # Get file size to determine whether to use chunked processing
        file_size_mb = os.path.getsize(temp_file_path) / (1024 * 1024)
        logger.info(f"File size: {file_size_mb:.2f} MB")
        
        # Choose transcription method based on file size
        if file_size_mb > 25:  # For files larger than 25MB, use chunked processing
            logger.info("Using chunked processing for large file")
            transcript = transcribe_large_file(temp_file_path)
        else:
            logger.info("Using standard transcription")
            transcript = transcribe_with_whisper(temp_file_path)
        
        # Clean up temporary file
        try:
            os.remove(temp_file_path)
            os.rmdir(temp_dir)
        except Exception as e:
            logger.warning(f"Error cleaning up temporary files: {str(e)}")
        
        return transcript
        
    except Exception as e:
        logger.exception("Error in transcribe_audio:")
        return f"Error transcribing audio: {str(e)}"

def transcribe_with_whisper(file_path):
    """
    Transcribe audio using the OpenAI Whisper API with progress tracking.
    
    Args:
        file_path (str): Path to the audio file
        
    Returns:
        str: Transcription text
    """
    # Create progress indicators
    progress_placeholder = st.empty()
    progress_bar = progress_placeholder.progress(0)
    status_text = st.empty()
    
    def update_progress(progress, message):
        """Update the progress bar and status message"""
        progress_bar.progress(progress)
        status_text.text(message)
    
    try:
        # Get an OpenAI client
        client = get_openai_client()
        if not client:
            update_progress(0.1, "OpenAI client not available, using direct method...")
            return direct_transcribe_audio(file_path)
        
        update_progress(0.2, "Initializing transcription...")
        
        # Calculate file size for logging and timeout
        file_size = os.path.getsize(file_path) / (1024 * 1024)  # Size in MB
        
        update_progress(0.3, f"Processing audio file ({file_size:.2f} MB)...")
        
        # Set a timeout proportional to file size
        timeout = max(300, int(file_size * 10))  # At least 5 minutes
        
        try:
            with open(file_path, "rb") as audio_file:
                update_progress(0.5, "Sending to OpenAI Whisper API...")
                # Use direct transcribe as a fallback if client-based approach fails
                try:
                    response = client.audio.transcriptions.create(
                        model="whisper-1",
                        file=audio_file,
                        timeout=timeout
                    )
                    transcript = response.text
                except Exception as e:
                    logger.info(f"Client-based transcription failed: {str(e)}")
                    logger.info("Trying direct_transcribe_audio as final fallback method")
                    # If client method fails, try direct method with hardcoded key
                    update_progress(0.6, "Using alternative transcription method...")
                    transcript = direct_transcribe_audio(file_path, HARD_CODED_OPENAI_API_KEY)
                
                update_progress(1.0, "Transcription complete!")
                # Remove the progress indicators
                progress_placeholder.empty()
                progress_bar.empty()
                status_text.empty()
    
                # Delay to show the completion message briefly
                time.sleep(0.5)
                
                return transcript
        except Exception as e:
            # If everything fails, try one more direct method
            logger.error(f"Error in transcribe_with_whisper: {str(e)}")
            try:
                update_progress(0.7, "Using fallback transcription method...")
                transcript = direct_transcribe_audio(file_path, HARD_CODED_OPENAI_API_KEY)
                update_progress(1.0, "Transcription complete with fallback method!")
                return transcript
            except Exception as final_e:
                logger.error(f"Final fallback also failed: {str(final_e)}")
                return f"Error in transcribe_with_whisper: {str(e)}"
    except Exception as e:
        logger.error(f"Error in transcribe_with_whisper: {str(e)}")
        return f"Error in transcribe_with_whisper: {str(e)}"

def transcribe_chunk(chunk_path, client=None):
    """
    Transcribe a single audio chunk using OpenAI's API.
    
    Args:
        chunk_path (str): Path to the audio chunk file
        client (OpenAI): OpenAI client, or None to create a new one
        
    Returns:
        str: Transcription text
    """
    logger.info(f"Transcribing chunk: {chunk_path}")
    
    # Get client if not provided
    if client is None:
        client = get_openai_client()
    
    # Check if file exists
    if not os.path.exists(chunk_path):
        return f"Error: File does not exist: {chunk_path}"
    
    # Try client-based transcription first
    if client:
        try:
            with open(chunk_path, "rb") as audio_file:
                response = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file
                )
                return response.text
        except Exception as e:
            logger.error(f"Error transcribing chunk with client: {str(e)}")
            # Fall back to direct method
    
    # Try direct transcription as fallback
    return direct_transcribe_audio(chunk_path)

def transcribe_large_file(file_path, service="openai", username=None, file_name=None):
    """
    Process large audio files by splitting into chunks and transcribing each chunk.
    
    Args:
        file_path (str): Path to the audio file
        service (str): Service to use for transcription ('openai' or 'anthropic')
        username (str): Username for storing results
        file_name (str): Original file name
        
    Returns:
        str: Combined transcription text
    """
    from audio.processing import chunk_audio
    
    logger.info(f"Transcribing large file: {file_path}")
    
    # Create progress indicators
    progress_placeholder = st.empty()
    progress_bar = progress_placeholder.progress(0)
    status_text = st.empty()
    
    def update_status(message, progress=None):
        """Update the status message and progress bar"""
        status_text.text(message)
        if progress is not None:
            progress_bar.progress(progress)
    
    # Split audio into chunks
    update_status("Analyzing audio file...", 0.1)
    
    try:
        # Determine target chunk size (25MB max for Whisper API)
        target_chunk_size_mb = 25
        
        # Calculate number of chunks
        file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
        num_chunks = math.ceil(file_size_mb / target_chunk_size_mb)
        
        logger.info(f"File size: {file_size_mb:.2f} MB, splitting into {num_chunks} chunks")
        update_status(f"Splitting {file_size_mb:.1f} MB audio into {num_chunks} chunks...", 0.2)
        
        # Create chunks
        try:
            y, sr = librosa.load(file_path, sr=None)
            duration = librosa.get_duration(y=y, sr=sr)
            
            # Calculate chunk size in samples
            chunk_duration = duration / num_chunks
            chunk_samples = int(chunk_duration * sr)
            
            # Create chunks directory
            chunks_dir = tempfile.mkdtemp(prefix="whisperforge_chunks_")
            chunk_paths = []
            
            update_status("Creating audio chunks...", 0.3)
            
            # Split the audio into chunks
            for i in range(num_chunks):
                start_sample = i * chunk_samples
                end_sample = min((i + 1) * chunk_samples, len(y))
                
                chunk_audio = y[start_sample:end_sample]
                chunk_path = os.path.join(chunks_dir, f"chunk_{i:03d}.wav")
                
                sf.write(chunk_path, chunk_audio, sr)
                chunk_paths.append(chunk_path)
            
            logger.info(f"Created {len(chunk_paths)} audio chunks")
        except Exception as e:
            logger.error(f"Error creating chunks with librosa: {str(e)}")
            # Fall back to original chunking method
            update_status("Using alternative chunking method...", 0.3)
            chunks_dir, chunk_paths = chunk_audio(file_path)
        
        # Get OpenAI client for transcription
        client = get_openai_client()
        
        # Create function to process a chunk and return its index and transcription
        def process_chunk(i, chunk_path):
            update_status(f"Transcribing chunk {i+1}/{len(chunk_paths)}...", 0.4 + 0.5 * (i / len(chunk_paths)))
            transcript = transcribe_chunk(chunk_path, client)
            return i, transcript
        
        # Process chunks in parallel
        update_status("Transcribing chunks in parallel...", 0.4)
        
        # Store results in correct order
        results = [""] * len(chunk_paths)
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=min(4, len(chunk_paths))) as executor:
            # Submit all chunks for processing
            future_to_chunk = {
                executor.submit(process_chunk, i, chunk_path): (i, chunk_path) 
                for i, chunk_path in enumerate(chunk_paths)
            }
            
            # Process results as they complete
            for future in concurrent.futures.as_completed(future_to_chunk):
                i, transcript = future.result()
                results[i] = transcript
        
        # Combine transcriptions
        update_status("Combining transcriptions...", 0.9)
        combined_transcript = " ".join(results)
        
        # Clean up chunks
        update_status("Cleaning up temporary files...", 0.95)
        for chunk_path in chunk_paths:
            try:
                os.remove(chunk_path)
            except:
                pass
        try:
            os.rmdir(chunks_dir)
        except:
            pass
        
        # Complete
        update_status("Transcription complete!", 1.0)
        # Remove progress indicators after a delay
        time.sleep(1)
        progress_placeholder.empty()
        progress_bar.empty()
        status_text.empty()
        
        return combined_transcript
        
    except Exception as e:
        logger.exception(f"Error in transcribe_large_file: {str(e)}")
        # Remove progress indicators
        progress_placeholder.empty()
        progress_bar.empty()
        status_text.empty()
        return f"Error processing large file: {str(e)}" 