import os
from pydub import AudioSegment
import tempfile
import math
import logging
import soundfile as sf
import librosa
import shutil

# Import from config
from config import TEMP_DIR, logger

def chunk_audio(audio_path, target_size_mb=25):
    """
    Split audio file into chunks of approximately target_size_mb.
    
    Args:
        audio_path (str): Path to the audio file
        target_size_mb (float): Target size of each chunk in MB
        
    Returns:
        tuple: (chunks_dir, list of chunk paths)
    """
    logger.info(f"Chunking audio file: {audio_path} into chunks of ~{target_size_mb}MB")
    
    # Create a directory for chunks
    chunks_dir = tempfile.mkdtemp(prefix="whisperforge_chunks_")
    chunk_files = []
    
    try:
        # Load the audio file
        audio = AudioSegment.from_file(audio_path)
        
        # Get duration in milliseconds and calculate chunks
        duration_ms = len(audio)
        file_size_bytes = os.path.getsize(audio_path)
        
        # Calculate chunk size based on original file size
        # Duration-to-size ratio (ms per byte)
        ms_per_byte = duration_ms / file_size_bytes
        
        # Calculate milliseconds per chunk
        bytes_per_chunk = target_size_mb * 1024 * 1024  # Convert MB to bytes
        ms_per_chunk = ms_per_byte * bytes_per_chunk
        
        # Ensure chunks are at least 1 second
        ms_per_chunk = max(ms_per_chunk, 1000)
        
        # Calculate number of chunks
        num_chunks = math.ceil(duration_ms / ms_per_chunk)
        
        logger.info(f"Splitting {duration_ms/1000:.2f}s audio into {num_chunks} chunks")
        
        # Split the audio into chunks
        for i in range(num_chunks):
            start_ms = i * ms_per_chunk
            end_ms = min((i + 1) * ms_per_chunk, duration_ms)
            
            chunk = audio[start_ms:end_ms]
            chunk_path = os.path.join(chunks_dir, f"chunk_{i:03d}.mp3")
            
            # Export chunk
            chunk.export(chunk_path, format="mp3")
            chunk_files.append(chunk_path)
            
        logger.info(f"Created {len(chunk_files)} chunks")
        return chunks_dir, chunk_files
        
    except Exception as e:
        logger.error(f"Error in chunk_audio: {str(e)}")
        # Try alternate chunking method
        return chunk_audio_with_librosa(audio_path, target_size_mb)

def chunk_audio_with_librosa(audio_path, target_size_mb=25):
    """
    Alternative audio chunking using librosa.
    
    Args:
        audio_path (str): Path to the audio file
        target_size_mb (float): Target size of each chunk in MB
        
    Returns:
        tuple: (chunks_dir, list of chunk paths)
    """
    logger.info(f"Using librosa to chunk audio file: {audio_path}")
    
    # Create a directory for chunks
    chunks_dir = tempfile.mkdtemp(prefix="whisperforge_librosa_chunks_")
    chunk_files = []
    
    try:
        # Load the audio file with librosa
        y, sr = librosa.load(audio_path, sr=None)
        
        # Get file size and calculate number of chunks
        file_size_bytes = os.path.getsize(audio_path)
        num_chunks = math.ceil(file_size_bytes / (target_size_mb * 1024 * 1024))
        
        # Calculate samples per chunk
        samples_per_chunk = len(y) // num_chunks
        
        logger.info(f"Splitting audio into {num_chunks} chunks with librosa")
        
        # Split and save chunks
        for i in range(num_chunks):
            start_sample = i * samples_per_chunk
            end_sample = min((i + 1) * samples_per_chunk, len(y))
            
            chunk = y[start_sample:end_sample]
            chunk_path = os.path.join(chunks_dir, f"chunk_{i:03d}.wav")
            
            # Save chunk
            sf.write(chunk_path, chunk, sr)
            chunk_files.append(chunk_path)
        
        logger.info(f"Created {len(chunk_files)} chunks with librosa")
        return chunks_dir, chunk_files
        
    except Exception as e:
        logger.error(f"Error in chunk_audio_with_librosa: {str(e)}")
        # Fall back to simple copy and return the whole file
        simple_chunk_dir = tempfile.mkdtemp(prefix="whisperforge_simple_chunk_")
        simple_chunk_path = os.path.join(simple_chunk_dir, "full_audio.wav")
        try:
            shutil.copy(audio_path, simple_chunk_path)
            return simple_chunk_dir, [simple_chunk_path]
        except Exception as copy_e:
            logger.error(f"Final fallback also failed: {str(copy_e)}")
            return simple_chunk_dir, []

def convert_audio_format(input_path, output_format="wav"):
    """
    Convert audio to a specific format.
    
    Args:
        input_path (str): Path to the input audio file
        output_format (str): Desired output format
        
    Returns:
        str: Path to the converted file
    """
    try:
        # Create output filename
        output_dir = TEMP_DIR
        os.makedirs(output_dir, exist_ok=True)
        
        base_name = os.path.basename(input_path)
        name_without_ext = os.path.splitext(base_name)[0]
        output_path = os.path.join(output_dir, f"{name_without_ext}.{output_format}")
        
        # Load and export
        audio = AudioSegment.from_file(input_path)
        audio.export(output_path, format=output_format)
        
        return output_path
    except Exception as e:
        logger.error(f"Error converting audio format: {str(e)}")
        return input_path  # Return original path on failure

def get_audio_duration(file_path):
    """
    Get the duration of an audio file in seconds.
    
    Args:
        file_path (str): Path to the audio file
        
    Returns:
        float: Duration in seconds
    """
    try:
        if not os.path.exists(file_path):
            return 0
            
        # Try librosa first
        try:
            y, sr = librosa.load(file_path, sr=None)
            return librosa.get_duration(y=y, sr=sr)
        except Exception as librosa_e:
            logger.warning(f"Failed to get duration with librosa: {str(librosa_e)}")
            
        # Fall back to pydub
        try:
            audio = AudioSegment.from_file(file_path)
            return len(audio) / 1000.0  # Convert ms to seconds
        except Exception as pydub_e:
            logger.warning(f"Failed to get duration with pydub: {str(pydub_e)}")
            
        return 0
    except Exception as e:
        logger.error(f"Error getting audio duration: {str(e)}")
        return 0 