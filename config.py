import os
import logging
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

# Base paths
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = Path(os.getenv("DATA_DIR", os.path.join(BASE_DIR, "data")))
UPLOADS_DIR = Path(os.getenv("UPLOADS_DIR", os.path.join(BASE_DIR, "uploads")))
TEMP_DIR = Path(os.getenv("TEMP_DIR", os.path.join(BASE_DIR, "temp")))
LOGS_DIR = Path(os.getenv("LOGS_DIR", os.path.join(BASE_DIR, "logs")))
PROMPTS_DIR = Path(os.getenv("PROMPTS_DIR", os.path.join(BASE_DIR, "prompts")))

# Ensure directories exist
for dir_path in [DATA_DIR, UPLOADS_DIR, TEMP_DIR, LOGS_DIR, PROMPTS_DIR]:
    dir_path.mkdir(exist_ok=True, parents=True)

# Database
DATABASE_PATH = os.getenv("DATABASE_PATH", os.path.join(DATA_DIR, "whisperforge.db"))

# API Keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
NOTION_API_KEY = os.getenv("NOTION_API_KEY")
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID")
GROK_API_KEY = os.getenv("GROK_API_KEY")

# JWT Configuration
JWT_SECRET = os.getenv("JWT_SECRET", "whisperforge-default-jwt-secret-change-me")
JWT_EXPIRATION_HOURS = int(os.getenv("JWT_EXPIRATION_HOURS", "24"))

# Admin user settings
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@whisperforge.ai")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "WhisperForge2024!")

# Logging configuration
def setup_logging():
    log_file = os.path.join(LOGS_DIR, "whisperforge.log")
    
    logging.basicConfig(
        level=logging.DEBUG if os.getenv("DEBUG", "false").lower() == "true" else logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger("whisperforge")

logger = setup_logging() 