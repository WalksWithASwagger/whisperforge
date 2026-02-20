"""
File Upload Module
==================

Upload zone UI, progress indicators, and pydub-based chunked processing
for standard audio files. For FFmpeg-based large file processing (2GB+),
see large_file_processor.py.
"""

import logging
import math
import os
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import streamlit as st

from .large_file_processor import EnhancedLargeFileProcessor  # noqa: F401 - re-export

logger = logging.getLogger(__name__)

_UPLOAD_CSS_CACHE = None


def _load_upload_css():
    """Load upload CSS from static file (cached)."""
    global _UPLOAD_CSS_CACHE  # noqa: PLW0603
    if _UPLOAD_CSS_CACHE is None:
        css_path = os.path.join("static", "css", "upload.css")
        if os.path.exists(css_path):
            with open(css_path, encoding="utf-8") as f:
                _UPLOAD_CSS_CACHE = f"<style>{f.read()}</style>"
        else:
            _UPLOAD_CSS_CACHE = ""
    return _UPLOAD_CSS_CACHE


class FileUploadManager:
    """Large file upload manager with chunking and parallel processing."""

    def __init__(self):
        self.supported_formats = {
            "audio": [".mp3", ".wav", ".m4a", ".aac", ".ogg", ".flac", ".wma", ".webm", ".mpeg", ".mpga", ".oga"],
            "video": [".mp4", ".avi", ".mov", ".mkv", ".wmv", ".flv", ".webm"],
            "text": [".txt", ".md", ".pdf", ".docx"],
        }
        self.max_file_size = 2 * 1024 * 1024 * 1024  # 2GB
        self.chunk_size_mb = 20  # 20MB chunks for pydub processing
        self.max_parallel_chunks = 3

    def create_upload_zone(self):
        """Create enhanced upload zone for large files."""
        upload_html = """
        <div class="large-upload-zone-container">
            <div class="large-upload-zone" id="large-upload-zone">
                <div class="upload-icon">
                    <div class="upload-icon-inner">\U0001f3b5</div>
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
                        <span class="feature-icon">\u26a1</span>
                        <span>Parallel Processing</span>
                    </div>
                    <div class="feature">
                        <span class="feature-icon">\U0001f4ca</span>
                        <span>Real-time Progress</span>
                    </div>
                    <div class="feature">
                        <span class="feature-icon">\U0001f504</span>
                        <span>Auto-retry on Errors</span>
                    </div>
                </div>
            </div>
        </div>
        """

        st.markdown(_load_upload_css(), unsafe_allow_html=True)
        st.markdown(upload_html, unsafe_allow_html=True)

        uploaded_file = st.file_uploader(
            "Choose an audio file",
            type=["mp3", "wav", "m4a", "aac", "ogg", "flac", "wma", "webm", "mpeg", "mpga", "oga"],
            help="Upload audio files up to 2GB. Large files will be automatically chunked for optimal processing.",
            label_visibility="collapsed",
        )

        return uploaded_file

    def process_large_file(self, uploaded_file) -> dict:
        """Process large files with chunking and parallel transcription."""
        if not uploaded_file:
            return {"success": False, "error": "No file provided"}

        validation = self.validate_large_file(uploaded_file)
        if not validation["valid"]:
            return {"success": False, "error": validation["error"]}

        file_size_mb = len(uploaded_file.getvalue()) / (1024 * 1024)

        st.markdown(
            f"### \U0001f4c1 File Processing\n"
            f"**File:** {uploaded_file.name}\n"
            f"**Size:** {file_size_mb:.1f} MB\n"
            f"**Processing Strategy:** {'Chunked Parallel Processing' if file_size_mb > self.chunk_size_mb else 'Direct Processing'}"
        )

        if file_size_mb <= self.chunk_size_mb:
            return self._process_small_file(uploaded_file)
        else:
            return self._process_large_file_chunked(uploaded_file)

    def _process_small_file(self, uploaded_file) -> dict:
        """Process small files directly without chunking."""
        progress_container = st.empty()

        with progress_container.container():
            st.markdown("#### \U0001f3b5 Processing Audio")
            progress_bar = st.progress(0.0, "Starting transcription...")

            try:
                from .content_generation import transcribe_audio

                progress_bar.progress(0.3, "Transcribing audio...")
                transcript = transcribe_audio(uploaded_file)

                if not transcript or "Error" in transcript:
                    progress_bar.progress(1.0, "\u274c Transcription failed")
                    return {"success": False, "error": transcript or "Transcription failed"}

                progress_bar.progress(1.0, "\u2705 Transcription complete!")
                return {"success": True, "transcript": transcript, "chunks": 1, "total_duration": "N/A"}

            except Exception as e:
                progress_bar.progress(1.0, f"\u274c Error: {e!s}")
                return {"success": False, "error": str(e)}

    def _process_large_file_chunked(self, uploaded_file) -> dict:
        """Process large files with intelligent chunking and parallel transcription."""
        st.markdown("#### \U0001f504 Chunked Processing Pipeline")

        try:
            chunks_info = self._create_audio_chunks(uploaded_file)
            if not chunks_info["success"]:
                return chunks_info

            chunks = chunks_info["chunks"]
            total_chunks = len(chunks)
            st.markdown(f"**Created {total_chunks} chunks for parallel processing**")

            progress_container = st.empty()
            chunks_container = st.empty()

            transcription_results = self._transcribe_chunks_parallel(chunks, progress_container, chunks_container)

            if not transcription_results["success"]:
                return transcription_results

            final_transcript = self._reassemble_transcript(transcription_results["chunk_transcripts"])
            self._cleanup_chunks(chunks)

            with progress_container.container():
                st.success("\u2705 Large file processing complete!")
                st.markdown(
                    f"**Processing Summary:**\n"
                    f"- Total chunks: {total_chunks}\n"
                    f"- Successful transcriptions: {len(transcription_results['chunk_transcripts'])}\n"
                    f"- Final transcript length: {len(final_transcript)} characters"
                )

            return {
                "success": True,
                "transcript": final_transcript,
                "chunks": total_chunks,
                "processing_time": transcription_results.get("total_time", "N/A"),
            }

        except Exception as e:
            logger.exception("Error in large file processing:")
            st.error(f"\u274c Large file processing failed: {e!s}")
            return {"success": False, "error": str(e)}

    def _create_audio_chunks(self, uploaded_file) -> dict:
        """Create audio chunks for parallel processing."""
        try:
            from pydub import AudioSegment

            st.markdown("##### \U0001f4c2 Creating Audio Chunks...")

            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as temp_file:
                uploaded_file.seek(0)
                temp_file.write(uploaded_file.read())
                temp_file_path = temp_file.name

            audio = AudioSegment.from_file(temp_file_path)
            duration_ms = len(audio)
            duration_minutes = duration_ms / (1000 * 60)

            chunk_duration_ms = self.chunk_size_mb * 60 * 1000
            num_chunks = math.ceil(duration_ms / chunk_duration_ms)

            st.markdown(f"**Audio Duration:** {duration_minutes:.1f} minutes")
            st.markdown(f"**Creating {num_chunks} chunks of ~{chunk_duration_ms / 60000:.1f} minutes each**")

            chunks = []
            chunk_progress = st.progress(0.0, "Creating chunks...")

            for i in range(num_chunks):
                start_ms = i * chunk_duration_ms
                end_ms = min((i + 1) * chunk_duration_ms, duration_ms)

                chunk = audio[start_ms:end_ms]
                with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as chunk_file:
                    chunk.export(chunk_file.name, format="wav")

                chunks.append(
                    {
                        "index": i,
                        "file_path": chunk_file.name,
                        "start_time": start_ms / 1000,
                        "end_time": end_ms / 1000,
                        "duration": (end_ms - start_ms) / 1000,
                    }
                )

                progress = (i + 1) / num_chunks
                chunk_progress.progress(progress, f"Created chunk {i + 1}/{num_chunks}")

            os.unlink(temp_file_path)
            chunk_progress.progress(1.0, f"\u2705 Created {num_chunks} chunks successfully!")

            return {"success": True, "chunks": chunks}

        except Exception as e:
            logger.exception("Error creating audio chunks:")
            return {"success": False, "error": f"Failed to create chunks: {e!s}"}

    def _transcribe_chunks_parallel(self, chunks: list[dict], progress_container, chunks_container) -> dict:
        """Transcribe chunks in parallel with real-time progress tracking."""
        total_chunks = len(chunks)
        completed_chunks = 0
        chunk_transcripts = {}
        chunk_statuses = {i: "waiting" for i in range(total_chunks)}
        start_time = time.time()

        from .content_generation import get_openai_client

        def transcribe_single_chunk(chunk_info: dict) -> tuple[int, str, bool]:
            """Transcribe a single chunk."""
            try:
                chunk_index = chunk_info["index"]
                chunk_file_path = chunk_info["file_path"]
                chunk_statuses[chunk_index] = "processing"

                openai_client = get_openai_client()
                if not openai_client:
                    return chunk_index, "Error: OpenAI API key not configured", False

                with open(chunk_file_path, "rb") as audio_file:
                    transcript = openai_client.audio.transcriptions.create(model="whisper-1", file=audio_file)

                chunk_statuses[chunk_index] = "completed"
                return chunk_index, transcript.text, True

            except Exception as e:
                chunk_statuses[chunk_index] = "error"
                logger.exception(f"Error transcribing chunk {chunk_index}:")
                return chunk_index, f"Error: {e!s}", False

        with ThreadPoolExecutor(max_workers=self.max_parallel_chunks) as executor:
            future_to_chunk = {executor.submit(transcribe_single_chunk, chunk): chunk["index"] for chunk in chunks}

            while completed_chunks < total_chunks:
                with progress_container.container():
                    overall_progress = completed_chunks / total_chunks
                    st.progress(overall_progress, f"Transcribing chunks: {completed_chunks}/{total_chunks}")

                with chunks_container.container():
                    st.markdown("##### \U0001f9e9 Chunk Processing Status")
                    cols_per_row = 4
                    rows = math.ceil(total_chunks / cols_per_row)

                    for row in range(rows):
                        cols = st.columns(cols_per_row)
                        for col_idx in range(cols_per_row):
                            chunk_idx = row * cols_per_row + col_idx
                            if chunk_idx < total_chunks:
                                status = chunk_statuses[chunk_idx]
                                status_map = {
                                    "waiting": ("\u23f3", "#FFA500", "Waiting"),
                                    "processing": ("\U0001f504", "#00BFFF", "Processing"),
                                    "completed": ("\u2705", "#00FF7F", "Complete"),
                                }
                                icon, color, text = status_map.get(status, ("\u274c", "#FF6B6B", "Error"))

                                with cols[col_idx]:
                                    st.markdown(
                                        f'<div style="text-align:center;padding:8px;border-radius:8px;'
                                        f'background:rgba(255,255,255,0.05);border:1px solid {color}40;margin:4px 0">'
                                        f'<div style="font-size:1.2rem">{icon}</div>'
                                        f'<div style="font-size:0.8rem;color:{color}">Chunk {chunk_idx + 1}</div>'
                                        f'<div style="font-size:0.7rem;color:rgba(255,255,255,0.7)">{text}</div></div>',
                                        unsafe_allow_html=True,
                                    )

                for future in as_completed(future_to_chunk, timeout=1):
                    chunk_index, transcript, success = future.result()
                    if success:
                        chunk_transcripts[chunk_index] = transcript
                    completed_chunks += 1
                    break

                time.sleep(0.5)

        with progress_container.container():
            st.progress(1.0, f"\u2705 All chunks transcribed: {completed_chunks}/{total_chunks}")

        processing_time = time.time() - start_time
        successful_chunks = len(chunk_transcripts)

        if successful_chunks < total_chunks * 0.8:
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
        return " ".join([transcript for _, transcript in sorted_chunks])

    def _cleanup_chunks(self, chunks: list[dict]):
        """Clean up temporary chunk files."""
        for chunk in chunks:
            try:
                if os.path.exists(chunk["file_path"]):
                    os.unlink(chunk["file_path"])
            except Exception as e:
                logger.warning(f"Failed to cleanup chunk file {chunk['file_path']}: {e}")

    def validate_large_file(self, file) -> dict:
        """Validate large file upload."""
        if not file:
            return {"valid": False, "error": "No file provided"}

        file_size = len(file.getvalue())
        if file_size > self.max_file_size:
            size_gb = file_size / (1024 * 1024 * 1024)
            return {"valid": False, "error": f"File too large: {size_gb:.1f}GB (max 2GB)"}

        file_extension = os.path.splitext(file.name)[1].lower()
        if file_extension not in self.supported_formats["audio"]:
            return {"valid": False, "error": f"Unsupported format: {file_extension}"}

        return {"valid": True}


# Backward compatibility alias
LargeFileUploadManager = FileUploadManager


def create_upload_progress_indicator(filename: str, progress: float = 0.0):
    """Create a progress indicator for file upload."""
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
            {"Uploading..." if progress < 100 else "Upload complete!"}
        </div>
    </div>
    """

    css = _load_upload_css()
    return st.markdown(css + progress_html, unsafe_allow_html=True)


def simulate_upload_progress(filename: str, duration: float = 2.0):
    """Simulate upload progress for demonstration."""
    progress_container = st.empty()

    steps = 20
    for i in range(steps + 1):
        progress = (i / steps) * 100
        with progress_container:
            create_upload_progress_indicator(filename, progress)
        time.sleep(duration / steps)
