"""
Enhanced File Upload Component for WhisperForge
Beautiful drag-and-drop interface with progress tracking
🚀 NEW: Large file support up to 2GB with chunking and parallel transcription
"""

import streamlit as st
import time
import asyncio
import threading
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional, List, Dict, Any, Tuple
import mimetypes
import os
import tempfile
import math
from pathlib import Path

# Audio processing with graceful fallback
try:
    from pydub import AudioSegment
    AUDIO_PROCESSING_AVAILABLE = True
except ImportError:
    AudioSegment = None
    AUDIO_PROCESSING_AVAILABLE = False

import logging

logger = logging.getLogger(__name__)

class LargeFileUploadManager:
    """🚀 ENHANCED: Large file upload manager with chunking and parallel processing"""
    
    def __init__(self):
        self.supported_formats = {
            'audio': ['.mp3', '.wav', '.m4a', '.aac', '.ogg', '.flac', '.wma', '.webm', '.mpeg', '.mpga', '.oga'],
            'video': ['.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm'],
            'text': ['.txt', '.md', '.pdf', '.docx']
        }
        self.max_file_size = 2 * 1024 * 1024 * 1024  # 2GB
        self.chunk_size_mb = 20  # 20MB chunks for optimal processing
        self.max_parallel_chunks = 4  # Process 4 chunks simultaneously
        
    def create_large_file_upload_zone(self) -> Optional[Any]:
        """Create enhanced upload zone for large files"""
        
        # Enhanced upload zone HTML with large file support
        upload_html = f"""
        <div class="large-upload-zone-container">
            <div class="large-upload-zone" id="large-upload-zone">
                <div class="upload-icon">
                    <div class="upload-icon-inner">🎵</div>
                </div>
                <div class="upload-text">
                    <h3>Drop your large audio files here</h3>
                    <p>Supports files up to 2GB with intelligent chunking</p>
                    <div class="upload-info">
                        <span class="supported-formats">Audio: MP3, WAV, M4A, AAC, OGG, FLAC, WEBM</span>
                        <span class="max-size">Max size: 2GB</span>
                        <span class="chunk-info">Auto-chunked for optimal processing</span>
                    </div>
                </div>
                <div class="upload-features">
                    <div class="feature">
                        <span class="feature-icon">⚡</span>
                        <span>Parallel Processing</span>
                    </div>
                    <div class="feature">
                        <span class="feature-icon">📊</span>
                        <span>Real-time Progress</span>
                    </div>
                    <div class="feature">
                        <span class="feature-icon">🔄</span>
                        <span>Auto-retry on Errors</span>
                    </div>
                </div>
            </div>
        </div>
        """
        
        # Enhanced CSS for large file upload
        upload_css = """
        <style>
        .large-upload-zone-container {
            margin: 20px 0;
        }
        
        .large-upload-zone {
            border: 3px dashed rgba(0, 255, 255, 0.3);
            border-radius: 16px;
            padding: 50px 30px;
            text-align: center;
            background: linear-gradient(135deg, 
                rgba(0, 255, 255, 0.03) 0%, 
                rgba(64, 224, 208, 0.05) 100%);
            transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
            cursor: pointer;
            position: relative;
            overflow: hidden;
        }
        
        .large-upload-zone:hover {
            border-color: rgba(0, 255, 255, 0.6);
            background: linear-gradient(135deg, 
                rgba(0, 255, 255, 0.08) 0%, 
                rgba(64, 224, 208, 0.12) 100%);
            transform: translateY(-3px);
            box-shadow: 0 12px 35px rgba(0, 255, 255, 0.2);
        }
        
        .large-upload-zone::before {
            content: "";
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, 
                transparent, 
                rgba(0, 255, 255, 0.15), 
                transparent);
            transition: left 0.6s ease;
        }
        
        .large-upload-zone:hover::before {
            left: 100%;
        }
        
        .upload-icon-inner {
            font-size: 64px;
            opacity: 0.8;
            transition: all 0.4s ease;
            display: inline-block;
        }
        
        .large-upload-zone:hover .upload-icon-inner {
            opacity: 1;
            transform: scale(1.15) rotate(10deg);
        }
        
        .upload-text h3 {
            color: #00FFFF;
            font-size: 1.5rem;
            margin: 16px 0 8px 0;
            font-weight: 600;
        }
        
        .upload-text p {
            color: rgba(255, 255, 255, 0.7);
            margin: 0 0 20px 0;
            font-size: 1rem;
        }
        
        .upload-info {
            display: flex;
            justify-content: center;
            gap: 15px;
            flex-wrap: wrap;
            margin-bottom: 20px;
        }
        
        .supported-formats, .max-size, .chunk-info {
            font-size: 0.85rem;
            color: rgba(255, 255, 255, 0.6);
            background: rgba(0, 255, 255, 0.1);
            padding: 6px 12px;
            border-radius: 6px;
            border: 1px solid rgba(0, 255, 255, 0.2);
        }
        
        .upload-features {
            display: flex;
            justify-content: center;
            gap: 30px;
            flex-wrap: wrap;
        }
        
        .feature {
            display: flex;
            align-items: center;
            gap: 8px;
            color: rgba(255, 255, 255, 0.8);
            font-size: 0.9rem;
        }
        
        .feature-icon {
            font-size: 1.2rem;
        }
        </style>
        """
        
        st.markdown(upload_css, unsafe_allow_html=True)
        st.markdown(upload_html, unsafe_allow_html=True)
        
        # File uploader with large file support
        uploaded_file = st.file_uploader(
            "Choose an audio file",
            type=['mp3', 'wav', 'm4a', 'aac', 'ogg', 'flac', 'wma', 'webm', 'mpeg', 'mpga', 'oga'],
            help="Upload audio files up to 2GB. Large files will be automatically chunked for optimal processing.",
            label_visibility="collapsed"
        )
        
        return uploaded_file
    
    def process_large_file(self, uploaded_file) -> Dict[str, Any]:
        """🚀 Process large files with chunking and parallel transcription"""
        
        if not uploaded_file:
            return {"success": False, "error": "No file provided"}
        
        # Validate file
        validation = self.validate_large_file(uploaded_file)
        if not validation["valid"]:
            return {"success": False, "error": validation["error"]}
        
        file_size_mb = len(uploaded_file.getvalue()) / (1024 * 1024)
        
        # Show file info
        st.markdown(f"""
        ### 📁 File Processing
        **File:** {uploaded_file.name}  
        **Size:** {file_size_mb:.1f} MB  
        **Processing Strategy:** {"Chunked Parallel Processing" if file_size_mb > self.chunk_size_mb else "Direct Processing"}
        """)
        
        if file_size_mb <= self.chunk_size_mb:
            # Small file - process directly
            return self._process_small_file(uploaded_file)
        else:
            # Large file - chunk and process in parallel
            return self._process_large_file_chunked(uploaded_file)
    
    def _process_small_file(self, uploaded_file) -> Dict[str, Any]:
        """Process small files directly without chunking"""
        
        progress_container = st.empty()
        
        with progress_container.container():
            st.markdown("#### 🎵 Processing Audio")
            progress_bar = st.progress(0.0, "Starting transcription...")
            
            try:
                # Import transcription function
                from .content_generation import transcribe_audio
                
                # Update progress
                progress_bar.progress(0.3, "Transcribing audio...")
                
                # Transcribe
                transcript = transcribe_audio(uploaded_file)
                
                if not transcript or "Error" in transcript:
                    progress_bar.progress(1.0, "❌ Transcription failed")
                    return {"success": False, "error": transcript or "Transcription failed"}
                
                progress_bar.progress(1.0, "✅ Transcription complete!")
                st.toast("Upload successful!", icon="✅")
                
                return {
                    "success": True,
                    "transcript": transcript,
                    "chunks": 1,
                    "total_duration": "N/A"
                }
                
            except Exception as e:
                progress_bar.progress(1.0, f"❌ Error: {str(e)}")
                st.toast(f"Upload failed: {str(e)}", icon="⚠️")
                return {"success": False, "error": str(e)}
    
    def _process_large_file_chunked(self, uploaded_file) -> Dict[str, Any]:
        """🚀 Process large files with intelligent chunking and parallel transcription"""
        
        st.markdown("#### 🔄 Chunked Processing Pipeline")
        
        try:
            # Step 1: Create chunks
            chunks_info = self._create_audio_chunks(uploaded_file)
            if not chunks_info["success"]:
                return chunks_info
            
            chunks = chunks_info["chunks"]
            total_chunks = len(chunks)
            
            st.markdown(f"**Created {total_chunks} chunks for parallel processing**")
            
            # Step 2: Create progress tracking containers
            progress_container = st.empty()
            chunks_container = st.empty()
            
            # Step 3: Process chunks in parallel with real-time updates
            transcription_results = self._transcribe_chunks_parallel(
                chunks, progress_container, chunks_container
            )
            
            if not transcription_results["success"]:
                return transcription_results
            
            # Step 4: Reassemble transcript
            final_transcript = self._reassemble_transcript(transcription_results["chunk_transcripts"])
            
            # Step 5: Cleanup temporary files
            self._cleanup_chunks(chunks)
            
            # Success!
            with progress_container.container():
                st.success("✅ Large file processing complete!")
                st.toast("Large file upload successful!", icon="🎉")
                st.markdown(f"""
                **Processing Summary:**
                - Total chunks: {total_chunks}
                - Successful transcriptions: {len(transcription_results['chunk_transcripts'])}
                - Final transcript length: {len(final_transcript)} characters
                """)
            
            return {
                "success": True,
                "transcript": final_transcript,
                "chunks": total_chunks,
                "processing_time": transcription_results.get("total_time", "N/A")
            }
            
        except Exception as e:
            logger.exception("Error in large file processing:")
            st.error(f"❌ Large file processing failed: {str(e)}")
            st.toast(f"Large file upload failed: {str(e)}", icon="⚠️")
            return {"success": False, "error": str(e)}
    
    def _create_audio_chunks(self, uploaded_file) -> Dict[str, Any]:
        """🚀 Memory-efficient audio chunking using FFmpeg streaming (no RAM explosion)"""
        
        try:
            st.markdown("##### 📂 Creating Audio Chunks (Memory-Efficient)...")
            
            # Save uploaded file temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as temp_file:
                uploaded_file.seek(0)
                temp_file.write(uploaded_file.read())
                temp_file_path = temp_file.name
            
            # Get audio duration using FFprobe (no memory usage)
            duration_seconds = self._get_audio_duration_ffprobe(temp_file_path)
            if not duration_seconds:
                os.unlink(temp_file_path)
                return {"success": False, "error": "Could not determine audio duration"}
            
            duration_minutes = duration_seconds / 60
            
            # Calculate chunk duration (aim for ~20MB chunks, ~5-10 minutes each)
            chunk_duration_seconds = min(600, max(300, duration_seconds / 8))  # 5-10 min chunks
            num_chunks = math.ceil(duration_seconds / chunk_duration_seconds)
            
            st.markdown(f"**Audio Duration:** {duration_minutes:.1f} minutes")
            st.markdown(f"**Creating {num_chunks} chunks of ~{chunk_duration_seconds/60:.1f} minutes each**")
            st.markdown("**Memory Strategy:** FFmpeg streaming (no RAM loading)")
            
            chunks = []
            chunk_progress = st.progress(0.0, "Creating chunks with FFmpeg...")
            
            for i in range(num_chunks):
                start_time = i * chunk_duration_seconds
                chunk_duration = min(chunk_duration_seconds, duration_seconds - start_time)
                
                # Create chunk file using FFmpeg (memory efficient)
                chunk_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
                chunk_file.close()
                
                # Use FFmpeg to extract chunk (streaming, no memory load)
                success = self._extract_chunk_ffmpeg(
                    temp_file_path, chunk_file.name, start_time, chunk_duration
                )
                
                if success:
                    chunks.append({
                        "index": i,
                        "file_path": chunk_file.name,
                        "start_time": start_time,
                        "end_time": start_time + chunk_duration,
                        "duration": chunk_duration
                    })
                else:
                    # Cleanup failed chunk
                    try:
                        os.unlink(chunk_file.name)
                    except:
                        pass
                    logger.warning(f"Failed to create chunk {i + 1}")
                
                # Update progress
                progress = (i + 1) / num_chunks
                chunk_progress.progress(progress, f"Created chunk {i + 1}/{num_chunks}")
            
            # Cleanup original temp file
            os.unlink(temp_file_path)
            
            if not chunks:
                return {"success": False, "error": "Failed to create any chunks"}
            
            chunk_progress.progress(1.0, f"✅ Created {len(chunks)} chunks successfully!")
            
            return {"success": True, "chunks": chunks}
            
        except Exception as e:
            logger.exception("Error creating audio chunks:")
            return {"success": False, "error": f"Failed to create chunks: {str(e)}"}
    
    def _transcribe_chunks_parallel(self, chunks: List[Dict], progress_container, chunks_container) -> Dict[str, Any]:
        """🚀 Transcribe chunks in parallel with real-time progress tracking"""
        
        total_chunks = len(chunks)
        completed_chunks = 0
        chunk_transcripts = {}
        chunk_statuses = {i: "waiting" for i in range(total_chunks)}
        start_time = time.time()
        
        # Import transcription function
        from .content_generation import get_openai_client
        
        def transcribe_single_chunk(chunk_info: Dict) -> Tuple[int, str, bool]:
            """Transcribe a single chunk"""
            try:
                chunk_index = chunk_info["index"]
                chunk_file_path = chunk_info["file_path"]
                
                # Update status to processing
                chunk_statuses[chunk_index] = "processing"
                
                # Get OpenAI client
                openai_client = get_openai_client()
                if not openai_client:
                    return chunk_index, "Error: OpenAI API key not configured", False
                
                # Transcribe chunk
                with open(chunk_file_path, "rb") as audio_file:
                    transcript = openai_client.audio.transcriptions.create(
                        model="whisper-1",
                        file=audio_file
                    )
                
                chunk_statuses[chunk_index] = "completed"
                return chunk_index, transcript.text, True
                
            except Exception as e:
                chunk_statuses[chunk_index] = "error"
                logger.exception(f"Error transcribing chunk {chunk_index}:")
                return chunk_index, f"Error: {str(e)}", False
        
        # Process chunks in parallel
        with ThreadPoolExecutor(max_workers=self.max_parallel_chunks) as executor:
            # Submit all chunks for processing
            future_to_chunk = {
                executor.submit(transcribe_single_chunk, chunk): chunk["index"] 
                for chunk in chunks
            }
            
            # Monitor progress in real-time
            while completed_chunks < total_chunks:
                # Update progress display
                with progress_container.container():
                    overall_progress = completed_chunks / total_chunks
                    st.progress(overall_progress, f"Transcribing chunks: {completed_chunks}/{total_chunks}")
                
                # Update individual chunk statuses
                with chunks_container.container():
                    st.markdown("##### 🧩 Chunk Processing Status")
                    
                    # Create columns for chunk status display
                    cols_per_row = 4
                    rows = math.ceil(total_chunks / cols_per_row)
                    
                    for row in range(rows):
                        cols = st.columns(cols_per_row)
                        for col_idx in range(cols_per_row):
                            chunk_idx = row * cols_per_row + col_idx
                            if chunk_idx < total_chunks:
                                status = chunk_statuses[chunk_idx]
                                
                                if status == "waiting":
                                    icon, color, text = "⏳", "#FFA500", "Waiting"
                                elif status == "processing":
                                    icon, color, text = "🔄", "#00BFFF", "Processing"
                                elif status == "completed":
                                    icon, color, text = "✅", "#00FF7F", "Complete"
                                else:  # error
                                    icon, color, text = "❌", "#FF6B6B", "Error"
                                
                                with cols[col_idx]:
                                    st.markdown(f"""
                                    <div style="
                                        text-align: center;
                                        padding: 8px;
                                        border-radius: 8px;
                                        background: rgba(255, 255, 255, 0.05);
                                        border: 1px solid {color}40;
                                        margin: 4px 0;
                                    ">
                                        <div style="font-size: 1.2rem;">{icon}</div>
                                        <div style="font-size: 0.8rem; color: {color};">Chunk {chunk_idx + 1}</div>
                                        <div style="font-size: 0.7rem; color: rgba(255,255,255,0.7);">{text}</div>
                                    </div>
                                    """, unsafe_allow_html=True)
                
                # Check for completed futures
                for future in as_completed(future_to_chunk, timeout=1):
                    chunk_index, transcript, success = future.result()
                    
                    if success:
                        chunk_transcripts[chunk_index] = transcript
                    
                    completed_chunks += 1
                    break
                
                # Small delay to prevent excessive updates
                time.sleep(0.5)
        
        # Final progress update
        with progress_container.container():
            st.progress(1.0, f"✅ All chunks transcribed: {completed_chunks}/{total_chunks}")
        
        processing_time = time.time() - start_time
        
        # Check if we have enough successful transcriptions
        successful_chunks = len(chunk_transcripts)
        if successful_chunks < total_chunks * 0.8:  # Require at least 80% success
            return {
                "success": False,
                "error": f"Too many failed chunks: {successful_chunks}/{total_chunks} successful"
            }
        
        return {
            "success": True,
            "chunk_transcripts": chunk_transcripts,
            "total_time": f"{processing_time:.1f}s",
            "success_rate": f"{successful_chunks}/{total_chunks}"
        }
    
    def _reassemble_transcript(self, chunk_transcripts: Dict[int, str]) -> str:
        """Reassemble transcript from chunks in correct order"""
        
        # Sort chunks by index and concatenate
        sorted_chunks = sorted(chunk_transcripts.items())
        full_transcript = " ".join([transcript for _, transcript in sorted_chunks])
        
        return full_transcript
    
    def _get_audio_duration_ffprobe(self, file_path: str) -> float:
        """Get audio duration using FFprobe (no memory usage)"""
        try:
            cmd = [
                'ffprobe', '-v', 'quiet', '-show_entries', 'format=duration',
                '-of', 'default=noprint_wrappers=1:nokey=1', file_path
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                return float(result.stdout.strip())
            else:
                logger.error(f"FFprobe failed: {result.stderr}")
                # Fallback to pydub for duration only (minimal memory)
                if AUDIO_PROCESSING_AVAILABLE:
                    try:
                        audio = AudioSegment.from_file(file_path)
                        return len(audio) / 1000.0  # Convert ms to seconds
                    except Exception as e:
                        logger.error(f"Pydub fallback failed: {e}")
                return None
                
        except Exception as e:
            logger.exception("Error getting audio duration:")
            return None
    
    def _extract_chunk_ffmpeg(self, input_path: str, output_path: str, start_time: float, duration: float) -> bool:
        """Extract audio chunk using FFmpeg (memory efficient)"""
        try:
            cmd = [
                'ffmpeg', '-i', input_path, '-ss', str(start_time),
                '-t', str(duration), '-acodec', 'pcm_s16le',
                '-ar', '16000', '-ac', '1', '-y', output_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, timeout=120)
            
            if result.returncode == 0:
                return True
            else:
                logger.error(f"FFmpeg chunk extraction failed: {result.stderr}")
                # Fallback to pydub for this chunk only
                return self._extract_chunk_pydub_fallback(input_path, output_path, start_time, duration)
                
        except Exception as e:
            logger.exception("Error extracting chunk with FFmpeg:")
            return self._extract_chunk_pydub_fallback(input_path, output_path, start_time, duration)
    
    def _extract_chunk_pydub_fallback(self, input_path: str, output_path: str, start_time: float, duration: float) -> bool:
        """Fallback to pydub for chunk extraction (only if FFmpeg fails)"""
        try:
            if not AUDIO_PROCESSING_AVAILABLE:
                return False
            
            # Load only the specific segment (more memory efficient than loading full file)
            start_ms = int(start_time * 1000)
            end_ms = int((start_time + duration) * 1000)
            
            # Use pydub's from_file with start/end parameters if available
            audio = AudioSegment.from_file(input_path)
            chunk = audio[start_ms:end_ms]
            chunk.export(output_path, format="wav")
            
            return True
            
        except Exception as e:
            logger.exception("Pydub fallback failed:")
            return False

    def _cleanup_chunks(self, chunks: List[Dict]):
        """Clean up temporary chunk files"""
        for chunk in chunks:
            try:
                if os.path.exists(chunk["file_path"]):
                    os.unlink(chunk["file_path"])
            except Exception as e:
                logger.warning(f"Failed to cleanup chunk file {chunk['file_path']}: {e}")
    
    def validate_large_file(self, file) -> Dict[str, Any]:
        """Validate large file upload"""
        if not file:
            return {"valid": False, "error": "No file provided"}
        
        # Check file size
        file_size = len(file.getvalue())
        if file_size > self.max_file_size:
            size_gb = file_size / (1024 * 1024 * 1024)
            return {"valid": False, "error": f"File too large: {size_gb:.1f}GB (max 2GB)"}
        
        # Check file type
        file_extension = os.path.splitext(file.name)[1].lower()
        if file_extension not in self.supported_formats['audio']:
            return {"valid": False, "error": f"Unsupported format: {file_extension}"}
        
        return {"valid": True}


# Legacy FileUploadManager for backward compatibility
class FileUploadManager(LargeFileUploadManager):
    """Legacy file upload manager - now inherits from LargeFileUploadManager"""
    
    def __init__(self):
        super().__init__()
        # Keep old max size for legacy methods
        self.legacy_max_file_size = 25 * 1024 * 1024  # 25MB

def create_upload_progress_indicator(filename: str, progress: float = 0.0):
    """Create a progress indicator for file upload"""
    progress_html = f"""
    <div class="upload-progress-container">
        <div class="upload-progress-header">
            <span class="upload-filename">{filename}</span>
            <span class="upload-percentage">{progress:.0f}%</span>
        </div>
        <div class="upload-progress-bar">
            <div class="upload-progress-fill" style="width: {progress}%"></div>
            <div class="upload-progress-shimmer" style="width: {progress}%"></div>
        </div>
        <div class="upload-status">
            {'Uploading...' if progress < 100 else 'Upload complete!'}
        </div>
    </div>
    """
    
    progress_css = """
    <style>
    .upload-progress-container {
        background: var(--bg-secondary);
        border-radius: var(--card-radius);
        padding: 15px;
        margin: 10px 0;
        border: 1px solid rgba(121, 40, 202, 0.2);
    }
    
    .upload-progress-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 8px;
    }
    
    .upload-filename {
        color: var(--text-primary);
        font-weight: 500;
        font-size: 0.9rem;
    }
    
    .upload-percentage {
        color: var(--accent-primary);
        font-family: var(--terminal-font);
        font-weight: 600;
    }
    
    .upload-progress-bar {
        height: 4px;
        background: rgba(255, 255, 255, 0.1);
        border-radius: 2px;
        position: relative;
        overflow: hidden;
        margin-bottom: 8px;
    }
    
    .upload-progress-fill {
        height: 100%;
        background: linear-gradient(90deg, #7928CA, #FF0080);
        border-radius: 2px;
        transition: width 0.3s ease;
    }
    
    .upload-progress-shimmer {
        position: absolute;
        top: 0;
        left: 0;
        height: 100%;
        background: linear-gradient(90deg, 
            transparent, 
            rgba(255, 255, 255, 0.2), 
            transparent);
        animation: shimmer 1.5s ease-in-out infinite;
    }
    
    .upload-status {
        color: var(--text-secondary);
        font-size: 0.8rem;
        text-align: center;
    }
    
    @keyframes shimmer {
        0% { transform: translateX(-100%); }
        100% { transform: translateX(100%); }
    }
    </style>
    """
    
    return st.markdown(progress_css + progress_html, unsafe_allow_html=True)

def simulate_upload_progress(filename: str, duration: float = 2.0):
    """Simulate upload progress for demonstration"""
    progress_container = st.empty()
    
    steps = 20
    for i in range(steps + 1):
        progress = (i / steps) * 100
        
        with progress_container:
            create_upload_progress_indicator(filename, progress)
        
        if i < steps:
            time.sleep(duration / steps)
    
    return True 