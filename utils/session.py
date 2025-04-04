import streamlit as st
import json
import time
import uuid
import os
from datetime import datetime
import logging

# Default values for all session state variables
DEFAULT_STATE = {
    # Core application state
    "page": "home",
    "user_id": 1,
    "authenticated": True,
    "session_id": None,
    
    # Input and processing
    "transcription": "",
    "audio_file": None,
    "language_code": "en",
    
    # AI provider settings
    "ai_provider": "Anthropic",
    "ai_model": "claude-3-7-sonnet-20250219",
    "transcription_provider": "OpenAI",
    "transcription_model": "whisper-1",
    "editor_enabled": False,
    
    # Generated content
    "wisdom": "",                # String of extracted wisdom
    "outline": "",               # String of content outline
    "social": "",                # String of generated social media content
    "image_prompts": [],         # List of image prompt strings
    "article": "",               # String of full article text
    "content_title_value": "",   # String for content title
    
    # UI state
    "show_cookie_banner": True,
    "user_profile_sidebar": "Default",
    "custom_result": "",
    "clipboard": "",             # String for clipboard operations
    "edit_user": None,           # ID or reference for user being edited
    
    # Integration data
    "notion_export_data": None,  # Data for Notion export
    "api_keys": {},              # Dictionary of API keys
}

# Group keys by their logical category for organized output
KEY_CATEGORIES = {
    "Authentication": ["user_id", "authenticated", "session_id"],
    "Navigation": ["page", "show_cookie_banner", "user_profile_sidebar", "edit_user"],
    "Input": ["transcription", "audio_file", "language_code", "clipboard"],
    "AI Configuration": ["ai_provider", "ai_model", "transcription_provider", "transcription_model", "editor_enabled"],
    "Generated Content": ["wisdom", "outline", "social", "image_prompts", "article", "content_title_value", "custom_result"],
    "Integration": ["notion_export_data", "api_keys"]
}

def initialize_session_state():
    """Initialize all session state variables from defaults"""
    for key, default_value in DEFAULT_STATE.items():
        if key not in st.session_state:
            st.session_state[key] = default_value

def get_page():
    """Get current page, ensuring it's initialized"""
    if "page" not in st.session_state:
        st.session_state.page = "home"
    return st.session_state.page

def set_page(page_name):
    """Set current page and trigger rerun"""
    st.session_state.page = page_name
    st.rerun()

def get_current_user_id():
    """Get current user ID with fallback"""
    if "user_id" not in st.session_state:
        st.session_state.user_id = 1
    return st.session_state.user_id

def is_authenticated():
    """Check if user is authenticated"""
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = True  # Default for development
    return st.session_state.authenticated

def get_selected_models():
    """Get currently selected AI and transcription models"""
    return {
        "ai_provider": st.session_state.get("ai_provider", "Anthropic"),
        "ai_model": st.session_state.get("ai_model", "claude-3-7-sonnet-20250219"),
        "transcription_provider": st.session_state.get("transcription_provider", "OpenAI"),
        "transcription_model": st.session_state.get("transcription_model", "whisper-1"),
    }

def get_or_create_session_id():
    """Get current session ID or create a new one and store in session state.

    Returns:
        str: Unique session identifier
    """
    if "session_id" not in st.session_state:
        # Create a unique session ID combining timestamp and random UUID
        timestamp = int(time.time())
        random_suffix = uuid.uuid4().hex[:8]
        st.session_state.session_id = f"session_{timestamp}_{random_suffix}"

    return st.session_state.session_id

def log_generation_step(user_id, session_id, step_name, data):
    """
    Log generation step details to a JSON file.

    Args:
        user_id (str): User identifier
        session_id (str): Session identifier
        step_name (str): Name of the generation step (e.g., 'wisdom', 'article')
        data (dict): Data to log (original_draft, editor_feedback, etc.)

    Returns:
        str: Path to the created log file, or None if logging failed
    """
    try:
        # Create logs directory if it doesn't exist
        log_dir = os.path.join(os.getcwd(), "logs")
        os.makedirs(log_dir, exist_ok=True)

        # Add timestamp to data
        timestamp = datetime.now().isoformat()
        data["timestamp"] = timestamp
        data["user_id"] = user_id
        data["session_id"] = session_id
        data["step_name"] = step_name

        # Generate filename with timestamp
        filename = f"{user_id}_{session_id}_{step_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        file_path = os.path.join(log_dir, filename)

        # Write data to JSON file with formatting
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        # Return the path to the created file
        return file_path

    except Exception as e:
        # Log the error but don't crash the application
        error_file = os.path.join(os.getcwd(), "logs", "error_log.txt")
        try:
            # Create error log with timestamp
            os.makedirs(os.path.dirname(error_file), exist_ok=True)
            with open(error_file, "a", encoding="utf-8") as f:
                f.write(
                    f"{datetime.now().isoformat()} - Error logging {step_name}: {str(e)}\n"
                )
        except:
            # If even error logging fails, just continue silently
            pass

        # Return None to indicate logging failed
        return None

def dump_session_state(display=True, truncate_length=200, exclude_keys=None):
    """
    Create a categorized dump of the current session state for debugging.
    
    Args:
        display (bool): Whether to display the state directly (True) or return it (False)
        truncate_length (int): Maximum length for string values before truncation
        exclude_keys (list): List of keys to exclude from the output
        
    Returns:
        dict or None: Categorized session state if display=False, otherwise None
    """
    if exclude_keys is None:
        exclude_keys = []

    # Create a categorized representation of session state
    categorized_state = {}
    uncategorized_keys = []
    
    # First, process known categories
    for category, keys in KEY_CATEGORIES.items():
        category_data = {}
        for key in keys:
            if key in st.session_state and key not in exclude_keys:
                # Truncate long string values for readability
                value = st.session_state[key]
                if isinstance(value, str) and len(value) > truncate_length:
                    value = value[:truncate_length] + "... [truncated]"
                category_data[key] = value
        
        if category_data:
            categorized_state[category] = category_data
    
    # Find uncategorized keys
    for key in st.session_state:
        if key not in exclude_keys:
            found = False
            for category_keys in KEY_CATEGORIES.values():
                if key in category_keys:
                    found = True
                    break
            if not found:
                uncategorized_keys.append(key)
    
    # Add uncategorized keys if any exist
    if uncategorized_keys:
        categorized_state["Other"] = {
            key: (
                st.session_state[key][:truncate_length] + "... [truncated]" 
                if isinstance(st.session_state[key], str) and len(st.session_state[key]) > truncate_length
                else st.session_state[key]
            ) 
            for key in uncategorized_keys
        }
    
    # Display the state directly or return it
    if display:
        try:
            st.write("## Session State")
            for category, data in categorized_state.items():
                st.write(f"### {category}")
                st.json(data)
        except Exception as e:
            # Fallback to print if st.write fails (when running in script mode)
            print("## Session State")
            for category, data in categorized_state.items():
                print(f"### {category}")
                print(data)
        return None
    else:
        # Also print to console for debugging
        print("## Session State")
        for category, data in categorized_state.items():
            print(f"### {category}")
            print(data)
        return categorized_state
