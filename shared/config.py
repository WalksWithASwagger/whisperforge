import os
import logging
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class Config:
    # API Keys
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
    NOTION_API_KEY = os.getenv("NOTION_API_KEY")
    SERVICE_TOKEN = os.getenv("SERVICE_TOKEN")

    # Service URLs (configurable via env)
    TRANSCRIPTION_SERVICE_URL = os.getenv(
        'TRANSCRIPTION_SERVICE_URL', 'http://transcription:8000')
    PROCESSING_SERVICE_URL = os.getenv(
        'PROCESSING_SERVICE_URL', 'http://processing:8000')
    STORAGE_SERVICE_URL = os.getenv(
        'STORAGE_SERVICE_URL', 'http://storage:8000')

    # Cache settings
    CACHE_DIR = os.getenv('CACHE_DIR', '/app/cache')

    # Model settings
    WHISPER_MODEL = os.getenv('WHISPER_MODEL', 'whisper-1')
    GPT_MODEL = os.getenv('GPT_MODEL', 'gpt-4o')

    @classmethod
    def log_status(cls):
        """Log configuration status on demand instead of at import time"""
        logger.info("=== Configuration Status ===")
        logger.info(f"OpenAI API Key present: {'Yes' if cls.OPENAI_API_KEY else 'No'}")
        logger.info(f"Anthropic API Key present: {'Yes' if cls.ANTHROPIC_API_KEY else 'No'}")
        logger.info(f"Notion API Key present: {'Yes' if cls.NOTION_API_KEY else 'No'}")
        logger.info(f"Service Token present: {'Yes' if cls.SERVICE_TOKEN else 'No'}")
