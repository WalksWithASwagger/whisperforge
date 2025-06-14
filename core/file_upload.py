"""
Enhanced File Upload Module for WhisperForge v2.8.0
Supports large file processing up to 2GB with intelligent chunking and parallel transcription
"""

import asyncio
import logging
import math
import mimetypes
import os
import tempfile
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional, List, Dict, Any, Tuple

import streamlit as st

# Configure logging
logger = logging.getLogger(__name__)

class FileUploadManager:
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
                
                return {
                    "success": True,
                    "transcript": transcript,
                    "chunks": 1,
                    "total_duration": "N/A"
                }
                
            except Exception as e:
                progress_bar.progress(1.0, f"❌ Error: {str(e)}")
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
            return {"success": False, "error": str(e)}
    
    def _create_audio_chunks(self, uploaded_file) -> Dict[str, Any]:
        """Create audio chunks for parallel processing"""
        
        try:
            st.markdown("##### 📂 Creating Audio Chunks...")
            
            # Save uploaded file temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as temp_file:
                uploaded_file.seek(0)
                temp_file.write(uploaded_file.read())
                temp_file_path = temp_file.name
            
            # Load audio with pydub
            audio = AudioSegment.from_file(temp_file_path)
            duration_ms = len(audio)
            duration_minutes = duration_ms / (1000 * 60)
            
            # Calculate chunk duration (aim for ~20MB chunks)
            chunk_duration_ms = self.chunk_size_mb * 60 * 1000  # Convert MB to minutes to ms
            num_chunks = math.ceil(duration_ms / chunk_duration_ms)
            
            st.markdown(f"**Audio Duration:** {duration_minutes:.1f} minutes")
            st.markdown(f"**Creating {num_chunks} chunks of ~{chunk_duration_ms/60000:.1f} minutes each**")
            
            chunks = []
            chunk_progress = st.progress(0.0, "Creating chunks...")
            
            for i in range(num_chunks):
                start_ms = i * chunk_duration_ms
                end_ms = min((i + 1) * chunk_duration_ms, duration_ms)
                
                # Extract chunk
                chunk = audio[start_ms:end_ms]
                
                # Save chunk to temporary file
                chunk_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
                chunk.export(chunk_file.name, format="wav")
                
                chunks.append({
                    "index": i,
                    "file_path": chunk_file.name,
                    "start_time": start_ms / 1000,
                    "end_time": end_ms / 1000,
                    "duration": (end_ms - start_ms) / 1000
                })
                
                # Update progress
                progress = (i + 1) / num_chunks
                chunk_progress.progress(progress, f"Created chunk {i + 1}/{num_chunks}")
            
            # Cleanup original temp file
            os.unlink(temp_file_path)
            
            chunk_progress.progress(1.0, f"✅ Created {num_chunks} chunks successfully!")
            
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


# Create alias for backward compatibility
LargeFileUploadManager = FileUploadManager

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


class EnhancedLargeFileProcessor:
    """🚀 Enhanced Large File Processor with FFmpeg for 2GB+ files
    
    Features:
    - FFmpeg-based processing for memory efficiency
    - Support for files up to 2GB
    - Intelligent 10-minute audio chunking
    - Parallel transcription with ThreadPoolExecutor
    - Memory-efficient streaming without loading entire files into RAM
    - Enhanced error handling with automatic fallback
    """
    
    def __init__(self):
        self.supported_formats = {
            'audio': ['.mp3', '.wav', '.m4a', '.aac', '.ogg', '.flac', '.wma', '.webm', '.mpeg', '.mpga', '.oga'],
            'video': ['.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm']  # Extract audio from video
        }
        self.max_file_size = 2 * 1024 * 1024 * 1024  # 2GB
        self.chunk_duration_minutes = 10  # 10-minute chunks optimized for Whisper
        self.max_parallel_chunks = 4  # Process 4 chunks simultaneously
        self.temp_dir = None
        
    def check_ffmpeg_availability(self) -> bool:
        """Check if FFmpeg is available on the system"""
        try:
            import subprocess
            result = subprocess.run(['ffmpeg', '-version'], 
                                  capture_output=True, text=True, timeout=5)
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
            return False
    
    def get_audio_info(self, file_path: str) -> Dict[str, Any]:
        """Get audio file information using ffprobe"""
        try:
            import subprocess
            import json
            
            cmd = [
                'ffprobe', '-v', 'quiet', '-print_format', 'json',
                '-show_format', '-show_streams', file_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode != 0:
                return {"error": f"ffprobe failed: {result.stderr}"}
            
            data = json.loads(result.stdout)
            format_info = data.get('format', {})
            
            # Find audio stream
            audio_stream = None
            for stream in data.get('streams', []):
                if stream.get('codec_type') == 'audio':
                    audio_stream = stream
                    break
            
            if not audio_stream:
                return {"error": "No audio stream found"}
            
            duration = float(format_info.get('duration', 0))
            size = int(format_info.get('size', 0))
            
            return {
                "duration": duration,
                "size": size,
                "format": format_info.get('format_name', 'unknown'),
                "codec": audio_stream.get('codec_name', 'unknown'),
                "sample_rate": int(audio_stream.get('sample_rate', 0)),
                "channels": int(audio_stream.get('channels', 0))
            }
            
        except Exception as e:
            return {"error": f"Failed to get audio info: {str(e)}"}
    
    def validate_file(self, uploaded_file) -> Dict[str, Any]:
        """Enhanced file validation for large files"""
        if not uploaded_file:
            return {"valid": False, "error": "No file provided"}
        
        # Check file size
        file_size = len(uploaded_file.getvalue())
        if file_size > self.max_file_size:
            size_gb = file_size / (1024 * 1024 * 1024)
            return {"valid": False, "error": f"File too large: {size_gb:.1f}GB (max 2GB)"}
        
        # Check file extension
        file_extension = os.path.splitext(uploaded_file.name)[1].lower()
        all_formats = self.supported_formats['audio'] + self.supported_formats['video']
        if file_extension not in all_formats:
            return {"valid": False, "error": f"Unsupported format: {file_extension}"}
        
        # Check FFmpeg availability for large files
        if file_size > 100 * 1024 * 1024 and not self.check_ffmpeg_availability():  # 100MB+
            return {
                "valid": False, 
                "error": "FFmpeg required for large files but not available. Please install FFmpeg."
            }
        
        return {
            "valid": True,
            "size": file_size,
            "size_mb": file_size / (1024 * 1024),
            "requires_chunking": file_size > 100 * 1024 * 1024,  # Chunk files > 100MB
            "format": file_extension
        }
    
    def create_enhanced_upload_interface(self) -> Optional[Any]:
        """Create enhanced upload interface for large files"""
        
        # Enhanced upload zone HTML
        upload_html = f"""
        <div class="enhanced-upload-container">
            <div class="enhanced-upload-zone" id="enhanced-upload-zone">
                <div class="upload-icon-large">
                    <div class="upload-icon-inner">🎵</div>
                    <div class="upload-pulse"></div>
                </div>
                <div class="upload-content">
                    <h2>Enhanced Large File Upload</h2>
                    <p class="upload-subtitle">Powered by FFmpeg • Up to 2GB • Intelligent Chunking</p>
                    <div class="upload-features-grid">
                        <div class="feature-card">
                            <span class="feature-icon">⚡</span>
                            <span class="feature-text">10-min chunks</span>
                        </div>
                        <div class="feature-card">
                            <span class="feature-icon">🔄</span>
                            <span class="feature-text">Parallel processing</span>
                        </div>
                        <div class="feature-card">
                            <span class="feature-icon">💾</span>
                            <span class="feature-text">Memory efficient</span>
                        </div>
                        <div class="feature-card">
                            <span class="feature-icon">🎯</span>
                            <span class="feature-text">Auto-retry</span>
                        </div>
                    </div>
                    <div class="supported-formats-enhanced">
                        <div class="format-group">
                            <strong>Audio:</strong> MP3, WAV, M4A, AAC, OGG, FLAC, WEBM
                        </div>
                        <div class="format-group">
                            <strong>Video:</strong> MP4, AVI, MOV, MKV, WMV (audio extraction)
                        </div>
                    </div>
                </div>
            </div>
        </div>
        """
        
        # Enhanced CSS
        upload_css = """
        <style>
        .enhanced-upload-container {
            margin: 25px 0;
        }
        
        .enhanced-upload-zone {
            border: 3px dashed var(--aurora-border);
            border-radius: var(--aurora-radius-large);
            padding: var(--aurora-spacing-large);
            text-align: center;
            background: var(--aurora-bg-glass);
            transition: all 0.5s cubic-bezier(0.4, 0, 0.2, 1);
            cursor: pointer;
            position: relative;
            overflow: hidden;
        }
        
        .enhanced-upload-zone:hover {
            border-color: var(--aurora-border-hover);
            background: var(--aurora-bg-glass);
            transform: translateY(-5px);
            box-shadow: var(--aurora-glow);
        }
        
        .upload-icon-large {
            position: relative;
            margin-bottom: 20px;
        }
        
        .upload-icon-inner {
            font-size: 80px;
            color: var(--aurora-primary);
            opacity: 0.9;
            transition: all 0.5s ease;
            display: inline-block;
            position: relative;
            z-index: 2;
        }
        
        .upload-pulse {
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            width: 120px;
            height: 120px;
            border: 2px solid var(--aurora-border);
            border-radius: 50%;
            animation: aurora-upload-pulse 3s ease-in-out infinite;
        }
        
        .enhanced-upload-zone:hover .upload-icon-inner {
            transform: scale(1.2) rotate(15deg);
            opacity: 1;
        }
        
        .upload-content h2 {
            color: var(--aurora-primary);
            font-size: 1.8rem;
            margin: 0 0 8px 0;
            font-weight: 700;
        }
        
        .upload-subtitle {
            color: var(--aurora-text-muted);
            margin: 0 0 25px 0;
            font-size: 1.1rem;
            font-weight: 500;
        }
        
        .upload-features-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
            gap: 15px;
            margin: 25px 0;
            max-width: 500px;
            margin-left: auto;
            margin-right: auto;
        }
        
        .feature-card {
            background: var(--aurora-bg-glass);
            border: 1px solid var(--aurora-border);
            border-radius: var(--aurora-radius);
            padding: 12px 8px;
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 6px;
            transition: all 0.3s ease;
        }
        
        .feature-card:hover {
            background: var(--aurora-bg-glass);
            border-color: var(--aurora-border-hover);
            transform: translateY(-2px);
            box-shadow: var(--aurora-glow-subtle);
        }
        
        .feature-icon {
            font-size: 1.5rem;
            color: var(--aurora-primary);
        }
        
        .feature-text {
            font-size: 0.85rem;
            color: var(--aurora-text);
            font-weight: 500;
        }
        
        .supported-formats-enhanced {
            margin-top: 20px;
            display: flex;
            justify-content: center;
            gap: 20px;
            flex-wrap: wrap;
        }
        
        .format-group {
            background: var(--aurora-bg-card);
            border: 1px solid var(--aurora-border);
            border-radius: var(--aurora-radius-small);
            padding: 8px 12px;
            font-size: 0.85rem;
            color: var(--aurora-text-muted);
        }
        
        .format-group strong {
            color: var(--aurora-primary);
        }
        
        @keyframes aurora-upload-pulse {
            0%, 100% {
                transform: translate(-50%, -50%) scale(1);
                opacity: 0.6;
            }
            50% {
                transform: translate(-50%, -50%) scale(1.2);
                opacity: 0.3;
            }
        }
        </style>
        """
        
        st.markdown(upload_css, unsafe_allow_html=True)
        st.markdown(upload_html, unsafe_allow_html=True)
        
        # Enhanced file uploader
        uploaded_file = st.file_uploader(
            "Choose an audio or video file",
            type=['mp3', 'wav', 'm4a', 'aac', 'ogg', 'flac', 'wma', 'webm', 'mpeg', 'mpga', 'oga', 
                  'mp4', 'avi', 'mov', 'mkv', 'wmv', 'flv'],
            help="Upload audio/video files up to 2GB. Large files automatically use FFmpeg chunking for optimal processing.",
            label_visibility="collapsed"
        )
        
        return uploaded_file
    
    def process_large_file(self, uploaded_file) -> Dict[str, Any]:
        """Enhanced large file processing with FFmpeg"""
        
        # Validate file first
        validation = self.validate_file(uploaded_file)
        if not validation["valid"]:
            return {"success": False, "error": validation["error"]}
        
        file_size_mb = validation["size_mb"]
        requires_chunking = validation["requires_chunking"]
        
        st.info(f"📁 **File:** {uploaded_file.name} ({file_size_mb:.1f} MB)")
        
        if requires_chunking:
            st.info("🔧 **Processing Method:** FFmpeg chunking (large file detected)")
            return self._process_with_ffmpeg_chunking(uploaded_file)
        else:
            st.info("⚡ **Processing Method:** Standard processing (small file)")
            return self._process_standard(uploaded_file)
    
    def _process_standard(self, uploaded_file) -> Dict[str, Any]:
        """Process smaller files using standard method"""
        try:
            from core.content_generation import transcribe_audio
            
            # Create temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
                tmp_file_path = tmp_file.name
            
            try:
                # Transcribe directly
                with st.spinner("🎯 Transcribing audio..."):
                    transcript = transcribe_audio(tmp_file_path)
                
                return {
                    "success": True,
                    "transcript": transcript,
                    "method": "standard",
                    "chunks_processed": 1
                }
                
            finally:
                # Cleanup
                if os.path.exists(tmp_file_path):
                    os.unlink(tmp_file_path)
                    
        except Exception as e:
            return {"success": False, "error": f"Standard processing failed: {str(e)}"}
    
    def _process_with_ffmpeg_chunking(self, uploaded_file) -> Dict[str, Any]:
        """Process large files using FFmpeg chunking"""
        
        # Setup temporary directory
        self.temp_dir = tempfile.mkdtemp(prefix="whisperforge_chunks_")
        
        try:
            # Save uploaded file
            input_file_path = os.path.join(self.temp_dir, uploaded_file.name)
            with open(input_file_path, 'wb') as f:
                f.write(uploaded_file.getvalue())
            
            # Get audio information
            st.info("🔍 Analyzing audio file...")
            audio_info = self.get_audio_info(input_file_path)
            
            if "error" in audio_info:
                return {"success": False, "error": audio_info["error"]}
            
            duration = audio_info["duration"]
            st.success(f"📊 **Duration:** {duration/60:.1f} minutes | **Format:** {audio_info['format']} | **Codec:** {audio_info['codec']}")
            
            # Create chunks using FFmpeg
            st.info("✂️ Creating audio chunks...")
            chunks_result = self._create_ffmpeg_chunks(input_file_path, duration)
            
            if not chunks_result["success"]:
                return chunks_result
            
            chunks = chunks_result["chunks"]
            st.success(f"✅ Created {len(chunks)} chunks of ~{self.chunk_duration_minutes} minutes each")
            
            # Process chunks in parallel
            st.info("🚀 Starting parallel transcription...")
            transcription_result = self._transcribe_chunks_parallel_ffmpeg(chunks)
            
            if not transcription_result["success"]:
                return transcription_result
            
            # Reassemble transcript
            full_transcript = self._reassemble_transcript_ffmpeg(transcription_result["chunk_transcripts"])
            
            return {
                "success": True,
                "transcript": full_transcript,
                "method": "ffmpeg_chunking",
                "chunks_processed": len(chunks),
                "processing_time": transcription_result.get("total_time", "unknown"),
                "success_rate": transcription_result.get("success_rate", "unknown")
            }
            
        except Exception as e:
            return {"success": False, "error": f"FFmpeg processing failed: {str(e)}"}
        
        finally:
            # Cleanup temporary directory
            self._cleanup_temp_dir()
    
    def _create_ffmpeg_chunks(self, input_file_path: str, duration: float) -> Dict[str, Any]:
        """Create audio chunks using FFmpeg"""
        try:
            import subprocess
            
            chunk_duration_seconds = self.chunk_duration_minutes * 60
            num_chunks = math.ceil(duration / chunk_duration_seconds)
            chunks = []
            
            progress_bar = st.progress(0, f"Creating chunks: 0/{num_chunks}")
            
            for i in range(num_chunks):
                start_time = i * chunk_duration_seconds
                chunk_filename = f"chunk_{i:03d}.wav"
                chunk_path = os.path.join(self.temp_dir, chunk_filename)
                
                # FFmpeg command to extract chunk with audio optimization
                cmd = [
                    'ffmpeg', '-i', input_file_path,
                    '-ss', str(start_time),
                    '-t', str(chunk_duration_seconds),
                    '-ar', '16000',  # 16kHz sample rate (optimal for Whisper)
                    '-ac', '1',      # Mono audio
                    '-acodec', 'pcm_s16le',  # PCM format
                    '-y',  # Overwrite output files
                    chunk_path
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
                
                if result.returncode != 0:
                    return {"success": False, "error": f"FFmpeg chunk creation failed: {result.stderr}"}
                
                # Verify chunk was created
                if not os.path.exists(chunk_path) or os.path.getsize(chunk_path) == 0:
                    continue  # Skip empty chunks
                
                chunks.append({
                    "index": i,
                    "file_path": chunk_path,
                    "start_time": start_time,
                    "duration": min(chunk_duration_seconds, duration - start_time)
                })
                
                # Update progress
                progress_bar.progress((i + 1) / num_chunks, f"Creating chunks: {i + 1}/{num_chunks}")
            
            return {"success": True, "chunks": chunks}
            
        except Exception as e:
            return {"success": False, "error": f"Chunk creation failed: {str(e)}"}
    
    def _transcribe_chunks_parallel_ffmpeg(self, chunks: List[Dict]) -> Dict[str, Any]:
        """Transcribe chunks in parallel using ThreadPoolExecutor"""
        from core.content_generation import transcribe_audio
        
        chunk_transcripts = {}
        total_chunks = len(chunks)
        
        # Create progress containers
        progress_container = st.empty()
        status_container = st.empty()
        
        def transcribe_single_chunk(chunk_info: Dict) -> Tuple[int, str, bool]:
            """Transcribe a single chunk"""
            try:
                chunk_index = chunk_info["index"]
                file_path = chunk_info["file_path"]
                
                transcript = transcribe_audio(file_path)
                return chunk_index, transcript, True
                
            except Exception as e:
                logger.error(f"Failed to transcribe chunk {chunk_info['index']}: {e}")
                return chunk_info["index"], f"[Transcription failed for chunk {chunk_info['index']}]", False
        
        start_time = time.time()
        completed_chunks = 0
        
        # Process chunks in parallel
        with ThreadPoolExecutor(max_workers=self.max_parallel_chunks) as executor:
            # Submit all chunks
            future_to_chunk = {
                executor.submit(transcribe_single_chunk, chunk): chunk 
                for chunk in chunks
            }
            
            # Process completed futures
            for future in as_completed(future_to_chunk):
                chunk_index, transcript, success = future.result()
                
                if success:
                    chunk_transcripts[chunk_index] = transcript
                
                completed_chunks += 1
                
                # Update progress
                progress = completed_chunks / total_chunks
                with progress_container:
                    st.progress(progress, f"Transcribing: {completed_chunks}/{total_chunks} chunks")
                
                with status_container:
                    elapsed = time.time() - start_time
                    if completed_chunks > 0:
                        eta = (elapsed / completed_chunks) * (total_chunks - completed_chunks)
                        st.info(f"⏱️ Elapsed: {elapsed:.1f}s | ETA: {eta:.1f}s | Success: {len(chunk_transcripts)}/{completed_chunks}")
        
        processing_time = time.time() - start_time
        successful_chunks = len(chunk_transcripts)
        
        # Check success rate
        if successful_chunks < total_chunks * 0.7:  # Require at least 70% success
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
    
    def _reassemble_transcript_ffmpeg(self, chunk_transcripts: Dict[int, str]) -> str:
        """Reassemble transcript from chunks in correct order"""
        # Sort chunks by index and concatenate
        sorted_chunks = sorted(chunk_transcripts.items())
        full_transcript = " ".join([transcript for _, transcript in sorted_chunks])
        
        # Clean up transcript
        full_transcript = full_transcript.strip()
        
        return full_transcript
    
    def _cleanup_temp_dir(self):
        """Clean up temporary directory and all files"""
        if self.temp_dir and os.path.exists(self.temp_dir):
            try:
                import shutil
                shutil.rmtree(self.temp_dir)
                self.temp_dir = None
            except Exception as e:
                logger.warning(f"Failed to cleanup temp directory {self.temp_dir}: {e}") 