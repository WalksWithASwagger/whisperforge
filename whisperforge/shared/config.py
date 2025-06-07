import os
import logging
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

class Config:
    # API Keys
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    NOTION_API_KEY = os.getenv("NOTION_API_KEY")
    SERVICE_TOKEN = os.getenv("SERVICE_TOKEN")
    
    # Log configuration status
    logger.info("=== Configuration Status ===")
    logger.info(f"OpenAI API Key present: {'Yes' if OPENAI_API_KEY else 'No'}")
    logger.info(f"Claude API Key present: {'Yes' if CLAUDE_API_KEY else 'No'}")
    logger.info(f"Notion API Key present: {'Yes' if NOTION_API_KEY else 'No'}")
    logger.info(f"Service Token present: {'Yes' if SERVICE_TOKEN else 'No'}")
    
    # Service URLs
    TRANSCRIPTION_SERVICE_URL = 'http://transcription:8000'
    PROCESSING_SERVICE_URL = 'http://processing:8000'
    STORAGE_SERVICE_URL = 'http://storage:8000'
    
    # Cache settings
    CACHE_DIR = '/app/cache'
    
    # Model settings
    WHISPER_MODEL = 'whisper-1'
    GPT_MODEL = 'gpt-4'
