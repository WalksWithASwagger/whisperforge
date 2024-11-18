import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # API Keys
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    NOTION_API_KEY = os.getenv('NOTION_API_KEY')
    SERVICE_TOKEN = os.getenv('SERVICE_TOKEN')
    
    # Service URLs
    TRANSCRIPTION_SERVICE_URL = 'http://transcription:8000'
    PROCESSING_SERVICE_URL = 'http://processing:8000'
    STORAGE_SERVICE_URL = 'http://storage:8000'
    
    # Cache settings
    CACHE_DIR = '/app/cache'
    
    # Model settings
    WHISPER_MODEL = 'whisper-1'
    GPT_MODEL = 'gpt-4'
