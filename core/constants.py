"""
Application-wide constants for WhisperForge.

These are compile-time invariants. For runtime configuration
(API keys, environment, etc.), see core/config.py.
"""

# ---------------------------------------------------------------------------
# File size limits
# ---------------------------------------------------------------------------
MAX_UPLOAD_SIZE_BYTES: int = 2 * 1024 * 1024 * 1024  # 2 GB
LARGE_FILE_THRESHOLD_BYTES: int = 100 * 1024 * 1024  # 100 MB (triggers FFmpeg)
LARGE_FILE_THRESHOLD_MB: int = 20  # Pipeline routing threshold

# ---------------------------------------------------------------------------
# Audio processing
# ---------------------------------------------------------------------------
CHUNK_DURATION_MINUTES: int = 10  # FFmpeg chunk length
MAX_PARALLEL_CHUNKS_STANDARD: int = 3  # pydub-based processing
MAX_PARALLEL_CHUNKS_FFMPEG: int = 4  # FFmpeg-based processing
AUDIO_SAMPLE_RATE: int = 16_000  # Hz for Whisper input
AUDIO_CHANNELS: int = 1  # Mono for Whisper input

# ---------------------------------------------------------------------------
# Transcription success thresholds
# ---------------------------------------------------------------------------
CHUNK_SUCCESS_THRESHOLD_STANDARD: float = 0.8  # file_upload.py
CHUNK_SUCCESS_THRESHOLD_FFMPEG: float = 0.7  # large_file_processor.py

# ---------------------------------------------------------------------------
# Subprocess timeouts (seconds)
# ---------------------------------------------------------------------------
FFMPEG_VERSION_CHECK_TIMEOUT: int = 5
FFPROBE_TIMEOUT: int = 30
FFMPEG_CHUNK_TIMEOUT: int = 300

# ---------------------------------------------------------------------------
# Database defaults
# ---------------------------------------------------------------------------
DEFAULT_USAGE_QUOTA_MINUTES: int = 60  # New user monthly quota
DEFAULT_CONTENT_QUERY_LIMIT: int = 50  # get_user_content()
DEFAULT_ANALYTICS_DAYS: int = 30  # get_user_analytics()

# ---------------------------------------------------------------------------
# Content generation
# ---------------------------------------------------------------------------
MAX_TOKENS_DEFAULT: int = 1500
MAX_TOKENS_ARTICLE: int = 2000
TRANSCRIPT_PREVIEW_LENGTH: int = 2000
ARTICLE_PREVIEW_LENGTH: int = 1500

# ---------------------------------------------------------------------------
# Notion integration
# ---------------------------------------------------------------------------
NOTION_CHUNK_SIZE: int = 1800
MAX_NOTION_BLOCKS: int = 50
NOTION_TITLE_EXCERPT_LENGTH: int = 500
NOTION_TITLE_MAX_TOKENS: int = 30
NOTION_TITLE_MAX_LENGTH: int = 60

# ---------------------------------------------------------------------------
# Content display
# ---------------------------------------------------------------------------
CONTENT_PREVIEW_LENGTH: int = 300

# ---------------------------------------------------------------------------
# Session
# ---------------------------------------------------------------------------
SESSION_EXPIRY_DAYS: int = 7
DEFAULT_PAGE: str = "Transform"
