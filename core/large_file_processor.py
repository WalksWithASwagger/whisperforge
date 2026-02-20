"""
Enhanced Large File Processor
=============================

FFmpeg-based large file processing with intelligent chunking and parallel transcription.
Supports files up to 2GB with memory-efficient streaming.
"""

import logging
import math
import os
import subprocess
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import openai
import streamlit as st

from .constants import (
    AUDIO_CHANNELS,
    AUDIO_SAMPLE_RATE,
    CHUNK_DURATION_MINUTES,
    CHUNK_SUCCESS_THRESHOLD_FFMPEG,
    FFMPEG_CHUNK_TIMEOUT,
    FFMPEG_VERSION_CHECK_TIMEOUT,
    FFPROBE_TIMEOUT,
    LARGE_FILE_THRESHOLD_BYTES,
    MAX_PARALLEL_CHUNKS_FFMPEG,
    MAX_UPLOAD_SIZE_BYTES,
)

logger = logging.getLogger(__name__)


class EnhancedLargeFileProcessor:
    """Enhanced Large File Processor with FFmpeg for 2GB+ files.

    Features:
    - FFmpeg-based processing for memory efficiency
    - Support for files up to 2GB
    - Intelligent 10-minute audio chunking
    - Parallel transcription with ThreadPoolExecutor
    - Memory-efficient streaming without loading entire files into RAM
    """

    def __init__(self):
        self.supported_formats = {
            "audio": [".mp3", ".wav", ".m4a", ".aac", ".ogg", ".flac", ".wma", ".webm", ".mpeg", ".mpga", ".oga"],
            "video": [".mp4", ".avi", ".mov", ".mkv", ".wmv", ".flv", ".webm"],
        }
        self.max_file_size = MAX_UPLOAD_SIZE_BYTES
        self.chunk_duration_minutes = CHUNK_DURATION_MINUTES
        self.max_parallel_chunks = MAX_PARALLEL_CHUNKS_FFMPEG
        self.temp_dir = None

    def check_ffmpeg_availability(self) -> bool:
        """Check if FFmpeg is available on the system."""
        try:
            import subprocess

            result = subprocess.run(
                ["ffmpeg", "-version"], capture_output=True, text=True, timeout=FFMPEG_VERSION_CHECK_TIMEOUT
            )  # noqa: S603
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
            return False

    def get_audio_info(self, file_path: str) -> dict:
        """Get audio file information using ffprobe."""
        try:
            import json
            import subprocess

            cmd = ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", "-show_streams", file_path]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=FFPROBE_TIMEOUT)  # noqa: S603
            if result.returncode != 0:
                return {"error": f"ffprobe failed: {result.stderr}"}

            data = json.loads(result.stdout)
            format_info = data.get("format", {})

            audio_stream = None
            for stream in data.get("streams", []):
                if stream.get("codec_type") == "audio":
                    audio_stream = stream
                    break

            if not audio_stream:
                return {"error": "No audio stream found"}

            duration = float(format_info.get("duration", 0))
            size = int(format_info.get("size", 0))

            return {
                "duration": duration,
                "size": size,
                "format": format_info.get("format_name", "unknown"),
                "codec": audio_stream.get("codec_name", "unknown"),
                "sample_rate": int(audio_stream.get("sample_rate", 0)),
                "channels": int(audio_stream.get("channels", 0)),
            }

        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, OSError) as e:
            return {"error": f"Failed to get audio info: {e!s}"}
        except Exception as e:
            return {"error": f"Unexpected error getting audio info: {e!s}"}

    def validate_file(self, uploaded_file) -> dict:
        """Enhanced file validation for large files."""
        if not uploaded_file:
            return {"valid": False, "error": "No file provided"}

        file_size = len(uploaded_file.getvalue())
        if file_size > self.max_file_size:
            size_gb = file_size / (1024 * 1024 * 1024)
            return {"valid": False, "error": f"File too large: {size_gb:.1f}GB (max 2GB)"}

        file_extension = os.path.splitext(uploaded_file.name)[1].lower()
        all_formats = self.supported_formats["audio"] + self.supported_formats["video"]
        if file_extension not in all_formats:
            return {"valid": False, "error": f"Unsupported format: {file_extension}"}

        if file_size > LARGE_FILE_THRESHOLD_BYTES and not self.check_ffmpeg_availability():
            return {
                "valid": False,
                "error": "FFmpeg required for large files but not available. Please install FFmpeg.",
            }

        return {
            "valid": True,
            "size": file_size,
            "size_mb": file_size / (1024 * 1024),
            "requires_chunking": file_size > LARGE_FILE_THRESHOLD_BYTES,
            "format": file_extension,
        }

    def create_enhanced_upload_interface(self):
        """Create enhanced upload interface for large files."""
        upload_html = """
        <div class="enhanced-upload-container">
            <div class="enhanced-upload-zone" id="enhanced-upload-zone">
                <div class="upload-icon-large">
                    <div class="upload-icon-inner">\U0001f3b5</div>
                    <div class="upload-pulse"></div>
                </div>
                <div class="upload-content">
                    <h2>Enhanced Large File Upload</h2>
                    <p class="upload-subtitle">Powered by FFmpeg \u2022 Up to 2GB \u2022 Intelligent Chunking</p>
                    <div class="upload-features-grid">
                        <div class="feature-card">
                            <span class="feature-icon">\u26a1</span>
                            <span class="feature-text">10-min chunks</span>
                        </div>
                        <div class="feature-card">
                            <span class="feature-icon">\U0001f504</span>
                            <span class="feature-text">Parallel processing</span>
                        </div>
                        <div class="feature-card">
                            <span class="feature-icon">\U0001f4be</span>
                            <span class="feature-text">Memory efficient</span>
                        </div>
                        <div class="feature-card">
                            <span class="feature-icon">\U0001f3af</span>
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

        from .file_upload import _load_upload_css

        st.markdown(_load_upload_css(), unsafe_allow_html=True)
        st.markdown(upload_html, unsafe_allow_html=True)

        uploaded_file = st.file_uploader(
            "Choose an audio or video file",
            type=[
                "mp3",
                "wav",
                "m4a",
                "aac",
                "ogg",
                "flac",
                "wma",
                "webm",
                "mpeg",
                "mpga",
                "oga",
                "mp4",
                "avi",
                "mov",
                "mkv",
                "wmv",
                "flv",
            ],
            help="Upload audio/video files up to 2GB. Large files automatically use FFmpeg chunking.",
            label_visibility="collapsed",
        )

        return uploaded_file

    def process_large_file(self, uploaded_file) -> dict:
        """Enhanced large file processing with FFmpeg."""
        validation = self.validate_file(uploaded_file)
        if not validation["valid"]:
            return {"success": False, "error": validation["error"]}

        file_size_mb = validation["size_mb"]
        requires_chunking = validation["requires_chunking"]

        st.info(f"\U0001f4c1 **File:** {uploaded_file.name} ({file_size_mb:.1f} MB)")

        if requires_chunking:
            st.info("\U0001f527 **Processing Method:** FFmpeg chunking (large file detected)")
            return self._process_with_ffmpeg_chunking(uploaded_file)
        else:
            st.info("\u26a1 **Processing Method:** Standard processing (small file)")
            return self._process_standard(uploaded_file)

    def _process_standard(self, uploaded_file) -> dict:
        """Process smaller files using standard method."""
        try:
            from core.content_generation import transcribe_audio

            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
                tmp_file_path = tmp_file.name

            try:
                with st.spinner("\U0001f3af Transcribing audio..."):
                    transcript = transcribe_audio(tmp_file_path)

                return {"success": True, "transcript": transcript, "method": "standard", "chunks_processed": 1}
            finally:
                if os.path.exists(tmp_file_path):
                    os.unlink(tmp_file_path)

        except (openai.APIError, OSError) as e:
            return {"success": False, "error": f"Standard processing failed: {e!s}"}
        except Exception as e:
            return {"success": False, "error": f"Unexpected standard processing error: {e!s}"}

    def _process_with_ffmpeg_chunking(self, uploaded_file) -> dict:
        """Process large files using FFmpeg chunking."""
        self.temp_dir = tempfile.mkdtemp(prefix="whisperforge_chunks_")

        try:
            input_file_path = os.path.join(self.temp_dir, uploaded_file.name)
            with open(input_file_path, "wb") as f:
                f.write(uploaded_file.getvalue())

            st.info("\U0001f50d Analyzing audio file...")
            audio_info = self.get_audio_info(input_file_path)

            if "error" in audio_info:
                return {"success": False, "error": audio_info["error"]}

            duration = audio_info["duration"]
            st.success(
                f"\U0001f4ca **Duration:** {duration / 60:.1f} minutes | "
                f"**Format:** {audio_info['format']} | **Codec:** {audio_info['codec']}"
            )

            st.info("\u2702\ufe0f Creating audio chunks...")
            chunks_result = self._create_ffmpeg_chunks(input_file_path, duration)

            if not chunks_result["success"]:
                return chunks_result

            chunks = chunks_result["chunks"]
            st.success(f"\u2705 Created {len(chunks)} chunks of ~{self.chunk_duration_minutes} minutes each")

            st.info("\U0001f680 Starting parallel transcription...")
            transcription_result = self._transcribe_chunks_parallel(chunks)

            if not transcription_result["success"]:
                return transcription_result

            full_transcript = self._reassemble_transcript(transcription_result["chunk_transcripts"])

            return {
                "success": True,
                "transcript": full_transcript,
                "method": "ffmpeg_chunking",
                "chunks_processed": len(chunks),
                "processing_time": transcription_result.get("total_time", "unknown"),
                "success_rate": transcription_result.get("success_rate", "unknown"),
            }

        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, OSError) as e:
            return {"success": False, "error": f"FFmpeg processing failed: {e!s}"}
        except Exception as e:
            return {"success": False, "error": f"Unexpected FFmpeg processing error: {e!s}"}

        finally:
            self._cleanup_temp_dir()

    def _create_ffmpeg_chunks(self, input_file_path: str, duration: float) -> dict:
        """Create audio chunks using FFmpeg."""
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

                cmd = [
                    "ffmpeg",
                    "-i",
                    input_file_path,
                    "-ss",
                    str(start_time),
                    "-t",
                    str(chunk_duration_seconds),
                    "-ar",
                    str(AUDIO_SAMPLE_RATE),
                    "-ac",
                    str(AUDIO_CHANNELS),
                    "-acodec",
                    "pcm_s16le",
                    "-y",
                    chunk_path,
                ]

                result = subprocess.run(cmd, capture_output=True, text=True, timeout=FFMPEG_CHUNK_TIMEOUT)  # noqa: S603

                if result.returncode != 0:
                    return {"success": False, "error": f"FFmpeg chunk creation failed: {result.stderr}"}

                if not os.path.exists(chunk_path) or os.path.getsize(chunk_path) == 0:
                    continue

                chunks.append(
                    {
                        "index": i,
                        "file_path": chunk_path,
                        "start_time": start_time,
                        "duration": min(chunk_duration_seconds, duration - start_time),
                    }
                )

                progress_bar.progress((i + 1) / num_chunks, f"Creating chunks: {i + 1}/{num_chunks}")

            return {"success": True, "chunks": chunks}

        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, OSError) as e:
            return {"success": False, "error": f"Chunk creation failed: {e!s}"}
        except Exception as e:
            return {"success": False, "error": f"Unexpected chunk creation error: {e!s}"}

    def _transcribe_chunks_parallel(self, chunks: list[dict]) -> dict:
        """Transcribe chunks in parallel using ThreadPoolExecutor."""
        from core.content_generation import transcribe_audio

        chunk_transcripts = {}
        total_chunks = len(chunks)

        progress_container = st.empty()
        status_container = st.empty()

        def transcribe_single_chunk(chunk_info: dict) -> tuple[int, str, bool]:
            """Transcribe a single chunk."""
            try:
                chunk_index = chunk_info["index"]
                file_path = chunk_info["file_path"]
                transcript = transcribe_audio(file_path)
                return chunk_index, transcript, True
            except (openai.APIError, OSError) as e:
                logger.error(f"Failed to transcribe chunk {chunk_info['index']}: {e}")
                return chunk_info["index"], f"[Transcription failed for chunk {chunk_info['index']}]", False
            except Exception as e:
                logger.error(f"Unexpected error transcribing chunk {chunk_info['index']}: {e}")
                return chunk_info["index"], f"[Unexpected error for chunk {chunk_info['index']}]", False

        start_time = time.time()
        completed_chunks = 0

        with ThreadPoolExecutor(max_workers=self.max_parallel_chunks) as executor:
            future_to_chunk = {executor.submit(transcribe_single_chunk, chunk): chunk for chunk in chunks}

            for future in as_completed(future_to_chunk):
                chunk_index, transcript, success = future.result()

                if success:
                    chunk_transcripts[chunk_index] = transcript

                completed_chunks += 1

                progress = completed_chunks / total_chunks
                with progress_container:
                    st.progress(progress, f"Transcribing: {completed_chunks}/{total_chunks} chunks")

                with status_container:
                    elapsed = time.time() - start_time
                    if completed_chunks > 0:
                        eta = (elapsed / completed_chunks) * (total_chunks - completed_chunks)
                        successful = len(chunk_transcripts)
                        st.info(
                            f"\u23f1\ufe0f Elapsed: {elapsed:.1f}s | ETA: {eta:.1f}s | Success: {successful}/{completed_chunks}"
                        )

        processing_time = time.time() - start_time
        successful_chunks = len(chunk_transcripts)

        if successful_chunks < total_chunks * CHUNK_SUCCESS_THRESHOLD_FFMPEG:
            return {"success": False, "error": f"Too many failed chunks: {successful_chunks}/{total_chunks} successful"}

        return {
            "success": True,
            "chunk_transcripts": chunk_transcripts,
            "total_time": f"{processing_time:.1f}s",
            "success_rate": f"{successful_chunks}/{total_chunks}",
        }

    def _reassemble_transcript(self, chunk_transcripts: dict[int, str]) -> str:
        """Reassemble transcript from chunks in correct order."""
        sorted_chunks = sorted(chunk_transcripts.items())
        return " ".join([transcript for _, transcript in sorted_chunks]).strip()

    def _cleanup_temp_dir(self):
        """Clean up temporary directory and all files."""
        if self.temp_dir and os.path.exists(self.temp_dir):
            try:
                import shutil

                shutil.rmtree(self.temp_dir)
                self.temp_dir = None
            except OSError as e:
                logger.warning(f"Failed to cleanup temp directory {self.temp_dir}: {e}")
