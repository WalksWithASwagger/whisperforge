import os
import json
import logging
import streamlit as st
import tempfile
import time
from datetime import datetime
import re
import glob

# Import from config
from config import OPENAI_API_KEY, ANTHROPIC_API_KEY, NOTION_API_KEY, GROK_API_KEY, logger
# Import from database
from database.db import get_user_api_keys

def load_api_key_from_file(file_path="/app/openai_api_key.txt"):
    """
    Load API key from file, used especially for Docker environment.
    
    Args:
        file_path (str): Path to the API key file
        
    Returns:
        str or None: The API key if valid, None otherwise
    """
    try:
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                key = f.read().strip()
                if key and len(key) > 10 and not any(placeholder in key.lower() for placeholder in ["your_", "placeholder", "api_key"]):
                    logger.info(f"Loaded API key from file (length: {len(key)})")
                    return key
    except Exception as e:
        logger.error(f"Error loading API key from file: {str(e)}")
    return None

def get_api_key_for_service(service_name, user_id=None):
    """
    Get the API key for a specific service with fallbacks.
    
    Priority:
    1. User-specific key from the database
    2. Environment variable
    3. Hardcoded fallback for critical services
    
    Args:
        service_name (str): Name of the service ('openai', 'anthropic', etc.)
        user_id (int): The user's ID, or None for the current user
        
    Returns:
        str or None: The API key if found, None otherwise
    """
    # Use current user's ID if not specified
    if user_id is None and 'user_id' in st.session_state:
        user_id = st.session_state.user_id
    
    # Priority 1: Get from user's database record
    if user_id:
        api_keys = get_user_api_keys(user_id)
        if api_keys and service_name in api_keys and api_keys[service_name]:
            key = api_keys[service_name]
            # Verify it's not a placeholder
            if len(key) > 10 and not any(placeholder in key.lower() for placeholder in ["your_", "placeholder", "api_key"]):
                return key
    
    # Priority 2: Get from environment variables
    env_var_map = {
        "openai": OPENAI_API_KEY,
        "anthropic": ANTHROPIC_API_KEY,
        "notion": NOTION_API_KEY,
        "grok": GROK_API_KEY
    }
    
    if service_name in env_var_map and env_var_map[service_name]:
        return env_var_map[service_name]
    
    # Priority 3: Fallback to hardcoded for critical services (used only as absolute last resort)
    if service_name == "openai" and 'HARDCODED_OPENAI_API_KEY' in globals():
        return globals()['HARDCODED_OPENAI_API_KEY']
    
    return None

def format_time_ago(dt):
    """
    Format a datetime to a human-readable "time ago" string.
    
    Args:
        dt (datetime): The datetime object
        
    Returns:
        str: Human-readable time string
    """
    now = datetime.utcnow()
    diff = now - dt
    
    seconds = diff.total_seconds()
    
    if seconds < 60:
        return "just now"
    elif seconds < 3600:
        minutes = int(seconds / 60)
        return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
    elif seconds < 86400:
        hours = int(seconds / 3600)
        return f"{hours} hour{'s' if hours > 1 else ''} ago"
    elif seconds < 604800:
        days = int(seconds / 86400)
        return f"{days} day{'s' if days > 1 else ''} ago"
    else:
        return dt.strftime("%b %d, %Y")

def sanitize_filename(filename):
    """
    Sanitize a filename to remove invalid characters.
    
    Args:
        filename (str): The original filename
        
    Returns:
        str: Sanitized filename
    """
    # Remove invalid chars and replace spaces with underscores
    clean_name = re.sub(r'[^\w\s-]', '', filename)
    clean_name = re.sub(r'[\s-]+', '_', clean_name).lower()
    return clean_name

def create_temp_file(content, suffix=".txt"):
    """
    Create a temporary file with given content.
    
    Args:
        content (bytes or str): File content
        suffix (str): File extension
        
    Returns:
        str: Path to the temporary file
    """
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    
    # Handle both string and binary content
    if isinstance(content, str):
        temp_file.write(content.encode('utf-8'))
    else:
        temp_file.write(content)
        
    temp_file.close()
    return temp_file.name

def get_file_extension(filename):
    """
    Get the file extension from a filename.
    
    Args:
        filename (str): The filename
        
    Returns:
        str: The file extension (lowercase)
    """
    return os.path.splitext(filename)[1].lower()

def is_valid_audio_extension(extension):
    """
    Check if a file extension is for an audio file.
    
    Args:
        extension (str): The file extension
        
    Returns:
        bool: True if valid audio extension, False otherwise
    """
    valid_extensions = ['.mp3', '.wav', '.ogg', '.m4a', '.flac', '.aac', '.wma', '.aiff']
    return extension.lower() in valid_extensions

def show_progress(message, progress=None):
    """
    Show a progress message or update an existing progress bar.
    
    Args:
        message (str): The progress message
        progress (streamlit.Progress): Existing progress bar, or None to create a new one
        
    Returns:
        streamlit.Progress: The progress bar
    """
    if progress is None:
        progress = st.progress(0)
    
    progress.progress(progress)
    st.text(message)
    
    # Give UI time to update
    time.sleep(0.1)
    
    return progress

def list_knowledge_base_files(user_profile):
    """
    List knowledge base files for a user profile.
    
    Args:
        user_profile (str): The user profile name
        
    Returns:
        list: List of file paths
    """
    kb_dir = os.path.join("prompts", user_profile, "knowledge_base")
    os.makedirs(kb_dir, exist_ok=True)
    
    # Get all markdown files
    files = glob.glob(os.path.join(kb_dir, "*.md"))
    return sorted(files) 