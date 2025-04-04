import streamlit as st
from openai import OpenAI  # Make sure this is using the OpenAI v1 API
from dotenv import load_dotenv
import os
from notion_client import Client
from datetime import datetime
from pydub import AudioSegment
import tempfile
import math
import glob
from anthropic import Anthropic
import requests  # for Grok API
import shutil
from pathlib import Path
import hashlib
import uuid
import sqlite3
import jwt
from datetime import datetime, timedelta
import time
import re
import json
import streamlit.components.v1 as components
import concurrent.futures
import threading
import openai
import logging
import sys
import soundfile as sf
import base64
import subprocess
import traceback

# Define diagnostic mode - set to True to enable diagnostics
DIAGNOSTIC_MODE = False

# Define test mode with sample data
TEST_MODE = True

# Import session management
from utils.session import (
    initialize_session_state, 
    get_page, 
    set_page, 
    is_authenticated,
    get_current_user_id,
    get_or_create_session_id,
    log_generation_step,
    dump_session_state,
    get_selected_models,
)

# Initialize session state immediately
initialize_session_state()

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("whisperforge.log"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger("whisperforge")

# This must be the very first st.* command
st.set_page_config(
    page_title="WhisperForge | Audio to Content Platform",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Load environment variables
load_dotenv()


# Database setup
def get_db_connection():
    conn = sqlite3.connect("whisperforge.db", check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            api_keys TEXT,
            usage_quota INTEGER DEFAULT 60,  -- Minutes per month
            usage_current INTEGER DEFAULT 0,
            is_admin INTEGER DEFAULT 0,
            subscription_tier TEXT DEFAULT 'free'
        )
    """
    )
    conn.commit()
    conn.close()


# Initialize database
init_db()


# Password hashing
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


# JWT functions
def create_jwt_token(user_id):
    expiration = datetime.utcnow() + timedelta(hours=24)
    payload = {"user_id": user_id, "exp": expiration}
    secret = os.getenv("JWT_SECRET", "whisperforge-secret-key")
    token = jwt.encode(payload, secret, algorithm="HS256")
    return token


def validate_jwt_token(token):
    try:
        secret = os.getenv("JWT_SECRET", "whisperforge-secret-key")
        payload = jwt.decode(token, secret, algorithms=["HS256"])
        return payload["user_id"]
    except:
        return None


# Initialization of clients - will be called as needed with user-specific API keys
def get_openai_client():
    logger.debug("Entering get_openai_client function")
    api_key = get_api_key_for_service("openai")
    if not api_key:
        logger.error("OpenAI API key is not set")
        st.error("OpenAI API key is not set. Please add your API key in the settings.")
        return None
    
    logger.debug(f"Got API key (length: {len(api_key)})")
    
    # Log environment variables that might affect client initialization
    logger.debug(
        "Checking environment variables that might affect client initialization:"
    )
    for env_var in os.environ:
        if (
            "proxy" in env_var.lower()
            or "http_" in env_var.lower()
            or "openai" in env_var.lower()
        ):
            logger.debug(f"  Found environment variable: {env_var}")
    
    # Create client with just the API key, no extra parameters
    try:
        logger.debug(
            "Attempting to initialize OpenAI client with ONLY api_key parameter"
        )
        
        # Create a completely clean approach - don't use any environment variables
        client_kwargs = {"api_key": api_key}
        
        # Log what we're passing to OpenAI
        logger.debug(f"OpenAI initialization parameters: {client_kwargs}")
        
        # Try direct initialization as a last resort
        client = OpenAI(**client_kwargs)
        logger.debug("Successfully initialized OpenAI client")
        return client
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Error initializing OpenAI client: {error_msg}")
        logger.exception("Full exception details:")
        
        # Try alternative initialization if 'proxies' is in the error
        if "proxies" in error_msg:
            logger.debug(
                "Trying alternative initialization approach due to proxies error"
            )
            try:
                # Alternative approach - don't use OpenAI client class directly
                # Instead use a simple function-based approach
                
                # Define a simple function to make API requests directly
                def simple_transcribe(audio_file):
                    import requests

                    url = "https://api.openai.com/v1/audio/transcriptions"
                    headers = {"Authorization": f"Bearer {api_key}"}
                    files = {"file": audio_file, "model": (None, "whisper-1")}
                    response = requests.post(url, headers=headers, files=files)
                    return response.json()
                
                # Create a minimal client object that just has the transcribe method
                class MinimalOpenAIClient:
                    def __init__(self, api_key):
                        self.api_key = api_key
                        self.audio = type("", (), {})()
                        self.audio.transcriptions = type("", (), {})()
                        self.audio.transcriptions.create = simple_transcribe
                
                logger.debug("Created minimal OpenAI client replacement")
                return MinimalOpenAIClient(api_key)
            except Exception as alt_e:
                logger.error(f"Alternative initialization also failed: {str(alt_e)}")
        
        st.error(f"Error initializing OpenAI client: {error_msg}")
        return None


def get_anthropic_client():
    api_key = get_api_key_for_service("anthropic")
    if not api_key:
        st.error(
            "Anthropic API key is not set. Please add your API key in the settings."
        )
        return None
    return Anthropic(api_key=api_key)


def get_notion_client():
    api_key = get_api_key_for_service("notion")
    if not api_key:
        st.error("Notion API key is not set. Please add your API key in the settings.")
        return None
    return Client(auth=api_key)


def get_notion_database_id():
    api_keys = get_user_api_keys()
    db_id = api_keys.get("notion_database_id")
    if not db_id:
        db_id = os.getenv("NOTION_DATABASE_ID")
    return db_id


def get_grok_api_key():
    return get_api_key_for_service("grok")


# Available LLM models grouped by provider
LLM_MODELS = {
    "OpenAI": {
        "GPT-4 (Most Capable)": "gpt-4",
        "GPT-4 Turbo": "gpt-4-turbo-preview",
        "GPT-3.5 Turbo (Faster)": "gpt-3.5-turbo",
    },
    "Anthropic": {
        "Claude 3 Opus": "claude-3-opus-20240229",
        "Claude 3 Sonnet": "claude-3-sonnet-20240229",
        "Claude 3 Haiku": "claude-3-haiku-20240307",
    },
    "Grok": {
        "Grok-1": "grok-1",
    },
}


def local_css():
    """Apply refined cyberpunk styling inspired by Luma's interface"""
    with open("static/css/main.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    
    # Add the scanner line animation div
    st.markdown('<div class="scanner-line"></div>', unsafe_allow_html=True)


def load_prompts():
    """Load prompt templates from the prompts directory"""
    users = []
    users_prompts = {}  # Initialize as dictionary
    
    # Check if prompts directory exists
    if not os.path.exists("prompts"):
        os.makedirs("prompts")
        st.info("Created prompts directory. Please add prompt templates.")
        return users, users_prompts
    
    # Get list of user directories
    user_dirs = [
        d for d in os.listdir("prompts") if os.path.isdir(os.path.join("prompts", d))
    ]
    
    # If no user directories, create a default one
    if not user_dirs:
        default_dir = os.path.join("prompts", "default_user")
        os.makedirs(default_dir, exist_ok=True)
        user_dirs = ["default_user"]
        
    # Add users to the list
    for user in user_dirs:
        users.append(user)
        users_prompts[user] = {}  # Initialize each user with an empty dictionary
        
        # Get prompt files for each user
        user_dir = os.path.join("prompts", user)
        prompt_files = []
        try:
            prompt_files = [f for f in os.listdir(user_dir) if f.endswith(".md")]
        except Exception as e:
            st.warning(f"Error accessing prompts for {user}: {str(e)}")
        
        # Load each prompt file
        for prompt_file in prompt_files:
            prompt_name = os.path.splitext(prompt_file)[0]
            try:
                with open(os.path.join(user_dir, prompt_file), "r") as f:
                    prompt_content = f.read()
                users_prompts[user][prompt_name] = prompt_content
            except Exception as e:
                st.warning(f"Error loading prompt {prompt_file}: {str(e)}")
    
    return users, users_prompts


def apply_prompt(text, prompt_content, provider, model):
    """Apply a specific prompt using the selected model and provider"""
    try:
        prompt_parts = prompt_content.split("## Prompt")
        if len(prompt_parts) > 1:
            prompt_text = prompt_parts[1].strip()
        else:
            prompt_text = prompt_content

        # Use the existing configure_prompts function
        configure_prompts(selected_user, users_prompts)
        
        # Add explanation of prompt variables
        with st.expander("Prompt Template Help"):
            st.markdown(
                """
            ### Prompt Template Variables
            
            Your prompt templates can include the following variables which will be replaced with actual content:
            
            - `{transcript}` - The full transcript text
            
            ### Prompt Template Format
            
            For best results, structure your prompts as follows:
            
            ```
            ## Instructions
            Instructions for the AI on how to approach the task.
            
            ## Context
            Any contextual information about your style, preferences, or requirements.
            
            ## Prompt
            The actual prompt that will be sent to the AI.
            ```
            
            Only the section after "## Prompt" is required, but adding instructions and context helps organize your templates.
            """
            )

        if provider == "OpenAI":
            response = openai_client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": prompt_text},
                    {
                        "role": "user",
                        "content": f"Here's the transcription to analyze:\n\n{text}",
                    },
                ],
                max_tokens=1500,
            )
            return response.choices[0].message.content

        elif provider == "Anthropic":
            response = anthropic_client.messages.create(
                model=model,
                max_tokens=1500,
                system=prompt_text,
                messages=[
                    {
                        "role": "user",
                        "content": f"Here's the transcription to analyze:\n\n{text}",
                    }
                ],
            )
            return response.content[0].text

        elif provider == "Grok":
            # Grok API endpoint (you'll need to adjust this based on actual Grok API documentation)
            headers = {
                "Authorization": f"Bearer {GROK_API_KEY}",
                "Content-Type": "application/json",
            }
            payload = {
                "model": model,
                "messages": [
                    {"role": "system", "content": prompt_text},
                    {
                        "role": "user",
                        "content": f"Here's the transcription to analyze:\n\n{text}",
                    },
                ],
            }
            response = requests.post(
                "https://api.grok.x.ai/v1/chat/completions",  # Adjust URL as needed
                headers=headers,
                json=payload,
            )
            return response.json()["choices"][0]["message"]["content"]

    except Exception as e:
        st.error(f"Analysis error with {provider} {model}: {str(e)}")
        return None


def chunk_audio(audio_path, target_size_mb=25):
    """Split audio file into chunks of approximately target_size_mb"""
    try:
        # Log the start of the chunking process
        logger.debug(f"Starting to chunk audio file: {audio_path}")
        logger.debug(f"Target chunk size: {target_size_mb}MB")
        
        # Create temporary directory for chunks
        temp_dir = tempfile.mkdtemp()
        logger.debug(f"Created temporary directory for chunks: {temp_dir}")
        
        # Load the audio file
        try:
            audio = AudioSegment.from_file(audio_path)
            logger.debug(f"Successfully loaded audio file. Duration: {len(audio)}ms")
        except Exception as load_error:
            logger.error(f"Failed to load audio file: {str(load_error)}")
            st.error(f"Error loading audio file: {str(load_error)}")
            return [], None
            
        # Get file size and adjust chunk size for very large files
        file_size_mb = os.path.getsize(audio_path) / (1024 * 1024)
        chunks = []
        
        # Adjust strategy based on file size
        if file_size_mb > 100:  # For very large files
            # Use silence detection for more natural chunking
            logger.debug(
                f"Large file detected ({file_size_mb:.2f} MB). Using silence-based chunking."
            )
            
            # Detect silences in the audio
            try:
                silence_thresh = -40  # dB
                min_silence_len = 700  # ms
                
                # Get silence ranges
                silence_ranges = silence.detect_silence(
                    audio, 
                    min_silence_len=min_silence_len, 
                    silence_thresh=silence_thresh,
                )
                
                # Convert silence ranges to chunk points
                chunk_points = [0]  # Start with the beginning of the audio
                
                for start, end in silence_ranges:
                    # Use the middle of each silence as a potential split point
                    chunk_points.append((start + end) // 2)
                
                # Add the end of the audio
                chunk_points.append(len(audio))
                
                # Ensure we don't create too many tiny chunks for very large files
                # Filter points to create chunks of roughly the target size
                target_chunk_len_ms = (
                    target_size_mb * 5 * 60 * 1000 / file_size_mb
                )  # Scale based on file size
                
                filtered_points = [chunk_points[0]]  # Always keep the first point
                current_pos = chunk_points[0]
                
                for point in chunk_points[1:]:
                    if (
                        point - current_pos >= target_chunk_len_ms
                        or point == chunk_points[-1]
                    ):
                        filtered_points.append(point)
                        current_pos = point
                
                logger.debug(
                    f"Created {len(filtered_points)-1} chunk boundaries using silence detection"
                )
                chunk_points = filtered_points
                
                # Create progress bar
                progress_bar = st.progress(0)
                
                # Process each chunk
                for i in range(len(chunk_points) - 1):
                    start = chunk_points[i]
                    end = chunk_points[i + 1]
                    
                    # Skip if segment is too short (less than 1 second)
                    if end - start < 1000:
                        logger.debug(
                            f"Skipping segment {i+1} (too short: {end-start}ms)"
                        )
                        continue
                    
                    try:
                        chunk = audio[start:end]
                        chunk_path = os.path.join(temp_dir, f"chunk_{i}.mp3")
                        
                        # Export with specific parameters that work well with OpenAI's API
                        chunk.export(
                            chunk_path, 
                            format="mp3",
                            parameters=["-ac", "1", "-ar", "16000"],  # Mono, 16kHz
                        )
                        
                        # Verify the exported file exists and has content
                        if (
                            os.path.exists(chunk_path)
                            and os.path.getsize(chunk_path) > 0
                        ):
                            chunks.append(chunk_path)
                            logger.debug(
                                f"Created chunk {i+1}: {chunk_path} (Duration: {len(chunk)}ms)"
                            )
                        else:
                            logger.warning(
                                f"Failed to create chunk {i+1}: File is empty or doesn't exist"
                            )
                    except Exception as chunk_error:
                        logger.error(f"Error creating chunk {i+1}: {str(chunk_error)}")
                    
                    # Update progress
                    progress = (i + 1) / (len(chunk_points) - 1)
                    progress_bar.progress(progress)
                
                # Clear progress bar
                progress_bar.empty()
                
            except Exception as silence_error:
                logger.error(f"Error in silence detection: {str(silence_error)}")
                # Fall back to simple chunking if silence detection fails
                st.warning("Silence detection failed, falling back to uniform chunking")
        
        # Either silence detection failed or it's a smaller file, use simple chunking
        if not chunks:
            logger.debug("Using uniform chunking method")
            
            # Calculate chunk size based on target MB
            target_chunk_bytes = target_size_mb * 1024 * 1024
            bytes_per_ms = file_size_mb * 1024 * 1024 / len(audio)
            chunk_length_ms = int(target_chunk_bytes / bytes_per_ms)
            
            # Ensure chunk length is reasonable
            if chunk_length_ms < 5000:  # 5 seconds minimum
                chunk_length_ms = 5000
            elif chunk_length_ms > 300000:  # 5 minutes maximum
                chunk_length_ms = 300000
                
            logger.debug(f"Uniform chunk length: {chunk_length_ms}ms")
            
            # Create progress bar
            progress_bar = st.progress(0)
            
            # Create chunks of uniform size
            chunk_count = 0
            for i in range(0, len(audio), chunk_length_ms):
                # Skip if less than 1 second is remaining
                if i + 1000 > len(audio):
                    logger.debug(
                        f"Skipping final segment (too short: {len(audio) - i}ms)"
                    )
                    continue
                
                try:
                    # Extract chunk
                    chunk = audio[i : min(i + chunk_length_ms, len(audio))]
                    
                    # Save chunk with index in filename
                    chunk_path = os.path.join(temp_dir, f"chunk_{chunk_count}.mp3")
                    
                    # Export with specific parameters for OpenAI
                    chunk.export(
                        chunk_path, 
                        format="mp3",
                        parameters=["-ac", "1", "-ar", "16000"],  # Mono, 16kHz
                    )
                    
                    # Verify the exported file exists and has content
                    if os.path.exists(chunk_path) and os.path.getsize(chunk_path) > 0:
                        chunks.append(chunk_path)
                        chunk_count += 1
                        logger.debug(
                            f"Created chunk {chunk_count}: {chunk_path} (Duration: {len(chunk)}ms)"
                        )
                    else:
                        logger.warning(
                            f"Failed to create chunk at position {i}ms: File is empty or doesn't exist"
                        )
                except Exception as chunk_error:
                    logger.error(
                        f"Error creating chunk at position {i}ms: {str(chunk_error)}"
                    )
                
                # Update progress
                progress = (i + chunk_length_ms) / len(audio)
                progress_bar.progress(min(progress, 1.0))
            
            # Clear progress bar
            progress_bar.empty()
        
        # Check if any chunks were created
        if not chunks:
            logger.error("Failed to create any valid chunks from the audio file")
            st.error("Failed to process the audio file into chunks.")
            return [], None
            
        logger.debug(f"Successfully created {len(chunks)} chunks from audio file")
        return chunks, temp_dir
        
    except Exception as e:
        logger.error(f"Error in chunk_audio: {str(e)}", exc_info=True)
        st.error(f"Error chunking audio: {str(e)}")
        return [], None


def transcribe_chunk(chunk_path, i, total_chunks):
    """Transcribe a single audio chunk using OpenAI's API"""
    try:
        # Log the processing of this chunk
        logger.debug(
            f"Processing chunk {i+1}/{total_chunks} ({os.path.getsize(chunk_path)/1024:.1f}KB): {chunk_path}"
        )
        
        # Get API key
        api_key = get_api_key_for_service("openai")
        if not api_key:
            error_msg = "OpenAI API key is not configured"
            logger.error(error_msg)
            return f"[Error: {error_msg}]"
        
        # Check if file exists
        if not os.path.exists(chunk_path):
            error_msg = f"Chunk file not found: {chunk_path}"
            logger.error(error_msg)
            return f"[Error: {error_msg}]"
        
        # Check if file size is valid
        file_size = os.path.getsize(chunk_path)
        if file_size == 0:
            error_msg = f"Chunk file is empty: {chunk_path}"
            logger.error(error_msg)
            return f"[Error: {error_msg}]"
        
        # Try direct API call
        try:
            logger.debug(f"Making direct API call for chunk {i+1}")
            
            import requests
            
            headers = {"Authorization": f"Bearer {api_key}"}
            
            url = "https://api.openai.com/v1/audio/transcriptions"
            
            # Set transcription options
            model = st.session_state.get("transcription_model", "whisper-1")
            
            # Create form data
            files = {"file": open(chunk_path, "rb")}
            
            data = {"model": model, "response_format": "text"}
            
            # Check for language code in session state
            if (
                st.session_state.get("language_code")
                and st.session_state.get("language_code") != "auto"
            ):
                data["language"] = st.session_state.get("language_code")
                logger.debug(f"Setting language for chunk {i+1} to: {data['language']}")
            
            # Make the API request
            response = requests.post(url, headers=headers, files=files, data=data)
            
            # Handle different response codes
            if response.status_code == 200:
                transcript = response.text
                logger.debug(
                    f"Successfully transcribed chunk {i+1} (Length: {len(transcript)} chars)"
                )
                return transcript
                
            elif response.status_code == 429:
                error_msg = f"Rate limit exceeded for chunk {i+1}"
                logger.error(f"API Rate Limit (429): {error_msg}")
                return f"[Rate limit exceeded: Try again later for chunk {i+1}]"
                
            elif response.status_code == 401:
                error_msg = f"Invalid API key when processing chunk {i+1}"
                logger.error(f"API Authentication Error (401): {error_msg}")
                return f"[Failed: Invalid API key for chunk {i+1}]"
                
            else:
                # Try to parse error details
                try:
                    error_data = response.json()
                    error_msg = error_data.get("error", {}).get(
                        "message", f"Unknown API error for chunk {i+1}"
                    )
                except:
                    error_msg = f"API error (status {response.status_code}) for chunk {i+1}: {response.text}"
                
                logger.error(f"API Error in chunk {i+1}: {error_msg}")
                return f"[Error: {error_msg}]"
                
        except requests.exceptions.RequestException as req_error:
            # Handle connection errors
            error_msg = f"API request failed for chunk {i+1}: {str(req_error)}"
            logger.error(error_msg)
            
            # Try OpenAI client as fallback
            try:
                logger.debug(f"Attempting fallback with client library for chunk {i+1}")
                
                from openai import OpenAI
                
                # Create client
                client = OpenAI(api_key=api_key)
                
                # Set options
                options = {}
                if (
                    st.session_state.get("language_code")
                    and st.session_state.get("language_code") != "auto"
                ):
                    options["language"] = st.session_state.get("language_code")
                
                # Get model preference or use default
                model = st.session_state.get("transcription_model", "whisper-1")
                
                with open(chunk_path, "rb") as audio_file:
                    # Use client library as fallback
                    response = client.audio.transcriptions.create(
                        model=model, file=audio_file, response_format="text", **options
                    )
                
                # If we get here, the fallback worked
                transcript = response
                logger.debug(
                    f"Fallback succeeded for chunk {i+1} (Length: {len(transcript)} chars)"
                )
                return transcript
                
            except Exception as client_error:
                error_msg = f"Fallback also failed for chunk {i+1}: {str(client_error)}"
                logger.error(error_msg)
                return f"[Failed: {error_msg}]"
    
    except Exception as e:
        error_msg = f"Unexpected error processing chunk {i+1}: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return f"[Error: {error_msg}]"


def generate_title(text, ai_provider, model, custom_prompt=None):
    """Generate a title from the text.

    Args:
        text (str): The text to generate a title for
        ai_provider (str): The AI provider to use (openai, anthropic, etc.)
        model (str): The model to use
        custom_prompt (str, optional): Custom prompt to override default

    Returns:
        dict: {"title": generated_title, "error": error_message if any}
    """
    # Input validation
    if not text or not isinstance(text, str):
        return {"title": "", "error": "Invalid input text"}

    try:
        client = get_client_for_provider(ai_provider)
        prompt = custom_prompt or load_default_prompt("title")
        # API call with appropriate client
        title = client.generate(prompt, text, model)
        return {"title": title, "error": None}
    except Exception as e:
        return {"title": "", "error": str(e)}


def generate_summary(text, ai_provider, model, custom_prompt=None):
    """Generate a summary from the text.

    Args:
        text (str): The text to summarize
        ai_provider (str): The AI provider to use
        model (str): The model to use
        custom_prompt (str, optional): Custom prompt to override default

    Returns:
        dict: {"summary": generated_summary, "error": error_message if any}
    """
    # Input validation
    if not text or not isinstance(text, str):
        return {"summary": "", "error": "Invalid input text"}

    try:
        client = get_client_for_provider(ai_provider)
        prompt = custom_prompt or load_default_prompt("summary")
        # API call with appropriate client
        summary = client.generate(prompt, text, model)
        return {"summary": summary, "error": None}
    except Exception as e:
        return {"summary": "", "error": str(e)}


def generate_short_title(text, ai_provider, model, custom_prompt=None):
    """Generate a short title from the text.

    Args:
        text (str): The text to generate a short title for
        ai_provider (str): The AI provider to use
        model (str): The model to use
        custom_prompt (str, optional): Custom prompt to override default

    Returns:
        dict: {"short_title": generated_short_title, "error": error_message if any}
    """
    # Input validation
    if not text or not isinstance(text, str):
        return {"short_title": "", "error": "Invalid input text"}

    try:
        client = get_client_for_provider(ai_provider)
        prompt = custom_prompt or load_default_prompt("short_title")
        # API call with appropriate client
        short_title = client.generate(prompt, text, model)
        return {"short_title": short_title, "error": None}
    except Exception as e:
        return {"short_title": "", "error": str(e)}


def chunk_text_for_notion(text, chunk_size=1900):
    """Split text into chunks that respect Notion's character limit"""
    if not text:
        return []
    return [text[i : i + chunk_size] for i in range(0, len(text), chunk_size)]


def create_content_notion_entry(
    title,
    transcript,
    wisdom=None,
    outline=None,
    social=None,
    image_prompts=None,
    article=None,
):
    """Create a new entry in the Notion database with all content sections"""
    try:
        # Get Notion client and database ID
        notion_client = get_notion_client()
        if not notion_client:
            st.error(
                "Notion API key is not configured. Please add your API key in the settings."
            )
            return False
            
        NOTION_DATABASE_ID = get_notion_database_id()
        if not NOTION_DATABASE_ID:
            st.error(
                "Notion Database ID is not configured. Please add it in the settings."
            )
            return False
        
        # Initialize audio_filename at the beginning of the function
        audio_filename = "None"
        if hasattr(st.session_state, "audio_file") and st.session_state.audio_file:
            audio_filename = st.session_state.audio_file.name
        
        # Generate AI title if none provided
        if (
            not title
            or title.startswith("Transcription -")
            or title.startswith("Content -")
        ):
            ai_title = generate_short_title(transcript)
            title = f"WHISPER: {ai_title}"
        
        # Generate tags for the content
        content_tags = generate_content_tags(transcript, wisdom)
        
        # Generate summary
        summary = generate_summary(transcript)
        
        # Track model usage for metadata
        used_models = []
        if hasattr(st.session_state, "ai_provider") and hasattr(
            st.session_state, "ai_model"
        ):
            if st.session_state.ai_provider and st.session_state.ai_model:
                used_models.append(
                    f"{st.session_state.ai_provider} {st.session_state.ai_model}"
                )
        if transcript:  # If we have a transcript, we likely used Whisper
            used_models.append("OpenAI Whisper-1")
            
        # Estimate token usage
        total_tokens = estimate_token_usage(
            transcript, wisdom, outline, social, image_prompts, article
        )
        
        # Format content with toggles
        content = []
        
        # Add summary section with AI-generated summary
        content.extend(
            [
            {
                "type": "callout",
                "callout": {
                    "rich_text": [{"type": "text", "text": {"content": summary}}],
                    "color": "purple_background",
                        "icon": {"type": "emoji", "emoji": "💜"},
                    },
                },
                {"type": "divider", "divider": {}},
            ]
        )
        
        # Add Transcript section with chunked content and color
        content.extend(
            [
            {
                "type": "toggle",
                "toggle": {
                        "rich_text": [
                            {"type": "text", "text": {"content": "Transcription"}}
                        ],
                        "color": "default",  # dark gray/black
                    "children": [
                        {
                            "type": "paragraph",
                            "paragraph": {
                                    "rich_text": [
                                        {"type": "text", "text": {"content": chunk}}
                    ]
                                },
                }
                            for chunk in chunk_text_for_notion(transcript)
                        ],
                    },
            }
            ]
        )

        # Add Wisdom section if available
        if wisdom:
            content.extend(
                [
                {
                    "type": "toggle",
                    "toggle": {
                            "rich_text": [
                                {"type": "text", "text": {"content": "Wisdom"}}
                            ],
                        "color": "brown_background",
                        "children": [
                            {
                                "type": "paragraph",
                                "paragraph": {
                                        "rich_text": [
                                            {"type": "text", "text": {"content": chunk}}
                        ]
                                    },
                    }
                                for chunk in chunk_text_for_notion(wisdom)
                            ],
                        },
                }
                ]
            )

        # Add Socials section with golden brown background
        if social:
            content.extend(
                [
                {
                    "type": "toggle",
                    "toggle": {
                            "rich_text": [
                                {"type": "text", "text": {"content": "Socials"}}
                            ],
                            "color": "orange_background",  # closest to golden brown
                        "children": [
                            {
                                "type": "paragraph",
                                "paragraph": {
                                        "rich_text": [
                                            {"type": "text", "text": {"content": chunk}}
                        ]
                                    },
                    }
                                for chunk in chunk_text_for_notion(social)
                            ],
                        },
                }
                ]
            )

        # Add Image Prompts with green background
        if image_prompts:
            content.extend(
                [
                {
                    "type": "toggle",
                    "toggle": {
                            "rich_text": [
                                {"type": "text", "text": {"content": "Image Prompts"}}
                            ],
                        "color": "green_background",
                        "children": [
                            {
                                "type": "paragraph",
                                "paragraph": {
                                        "rich_text": [
                                            {"type": "text", "text": {"content": chunk}}
                        ]
                                    },
                    }
                                for chunk in chunk_text_for_notion(image_prompts)
                            ],
                        },
                }
                ]
            )

        # Add Outline with blue background
        if outline:
            content.extend(
                [
                {
                    "type": "toggle",
                    "toggle": {
                            "rich_text": [
                                {"type": "text", "text": {"content": "Outline"}}
                            ],
                        "color": "blue_background",
                        "children": [
                            {
                                "type": "paragraph",
                                "paragraph": {
                                        "rich_text": [
                                            {"type": "text", "text": {"content": chunk}}
                        ]
                                    },
                    }
                                for chunk in chunk_text_for_notion(outline)
                            ],
                        },
                }
                ]
            )

        # Add Draft Post with purple background
        if article:
            content.extend(
                [
                {
                    "type": "toggle",
                    "toggle": {
                            "rich_text": [
                                {"type": "text", "text": {"content": "Draft Post"}}
                            ],
                        "color": "purple_background",
                        "children": [
                            {
                                "type": "paragraph",
                                "paragraph": {
                                        "rich_text": [
                                            {"type": "text", "text": {"content": chunk}}
                        ]
                                    },
                    }
                                for chunk in chunk_text_for_notion(article)
                            ],
                        },
                }
                ]
            )

        # Add Original Audio section with maroon/red background if audio file exists
        if audio_filename != "None":
            content.extend(
                [
                {
                    "type": "toggle",
                    "toggle": {
                            "rich_text": [
                                {"type": "text", "text": {"content": "Original Audio"}}
                            ],
                        "color": "red_background",
                        "children": [
                            {
                                "type": "paragraph",
                                "paragraph": {
                                        "rich_text": [
                                            {
                                                "type": "text",
                                                "text": {"content": audio_filename},
                                            }
                                        ]
                                    },
                                }
                            ],
                        },
                    }
                ]
            )

        # Add metadata section
            content.extend(
                [
                    {"type": "divider", "divider": {}},
                {
                    "type": "heading_2",
                    "heading_2": {
                            "rich_text": [
                                {"type": "text", "text": {"content": "Metadata"}}
                            ]
                        },
            },
            {
                "type": "paragraph",
                "paragraph": {
                            "rich_text": [
                                {
                                    "type": "text",
                                    "text": {
                                        "content": f"**Original Audio:** {audio_filename}"
                                    },
                                }
                            ]
                        },
            },
                            {
                                "type": "paragraph",
                                "paragraph": {
                            "rich_text": [
                                {
                                    "type": "text",
                                    "text": {
                                        "content": f"**Created:** {datetime.now().strftime('%Y-%m-%d %H:%M')}"
                                    },
                                }
                            ]
                        },
            },
            {
                "type": "paragraph",
                "paragraph": {
                            "rich_text": [
                                {
                                    "type": "text",
                                    "text": {
                                        "content": f"**Models Used:** {', '.join(used_models) if used_models else 'None'}"
                                    },
                                }
                            ]
                        },
            },
            {
                "type": "paragraph",
                "paragraph": {
                            "rich_text": [
                                {
                                    "type": "text",
                                    "text": {
                                        "content": f"**Estimated Tokens:** {total_tokens:,}"
                                    },
                                }
                            ]
                        },
                    },
                ]
            )

        # Create the page in Notion
        response = notion_client.pages.create(
            parent={"database_id": NOTION_DATABASE_ID},
            properties={
                "Name": {"title": [{"text": {"content": title}}]},
                "Tags": {"multi_select": [{"name": tag} for tag in content_tags]},
            },
            children=content,
        )
        
        # Make the Notion link clickable in the UI
        if response and isinstance(response, dict) and "id" in response:
            page_id = response["id"]
            page_url = f"https://notion.so/{page_id.replace('-', '')}"
            st.success(f"Successfully saved to Notion!")
            st.markdown(f"[Open in Notion]({page_url})")
            return page_url
        else:
            st.error("Notion API returned an invalid response")
            st.write("Response:", response)  # Debug info
            return False
            
    except Exception as e:
        st.error(f"Detailed error creating Notion entry: {str(e)}")
        return False


def estimate_token_usage(
    transcript,
    wisdom=None,
    outline=None,
    social=None,
    image_prompts=None,
    article=None,
):
    """Estimate token usage for all content generated"""
    # Approximate token count (roughly 4 chars per token for English)
    token_count = 0
    
    # Count tokens in all content
    if transcript:
        token_count += len(transcript) / 4
    if wisdom:
        token_count += len(wisdom) / 4
    if outline:
        token_count += len(outline) / 4
    if social:
        token_count += len(social) / 4
    if image_prompts:
        token_count += len(image_prompts) / 4
    if article:
        token_count += len(article) / 4
        
    # Add approximate prompt tokens and overhead
    token_count += 1000  # For system prompts, etc.
    
    return int(token_count)


def generate_content_tags(transcript, wisdom=None):
    """Generate relevant tags based on content"""
    try:
        # Use Anthropic Claude 3.7 Sonnet for generating tags
        api_key = get_api_key_for_service("anthropic")
        if not api_key:
            return ["audio", "transcription", "content", "notes", "whisperforge"]
            
        # Create prompt for tag generation
        content_sample = transcript[:1000] if transcript else ""
        wisdom_sample = wisdom[:500] if wisdom else ""
        
        prompt = f"""Based on the following content, generate 5-7 descriptive, specific tags that accurately capture the main topics, themes, and concepts. 
        Each tag can be 1-3 words and should be specific enough to categorize the content effectively.

        Content sample:
        {content_sample}

        Key insights:
        {wisdom_sample}

        Return only the tags, separated by commas, with each tag being 1-3 words. Make them descriptive and specific to this content.
        For example, instead of just 'technology', use 'AI ethics' or 'blockchain adoption'.
        """
        
        # Use direct API call to Claude
        result = direct_anthropic_completion(
            prompt, api_key, model="claude-3-7-sonnet-20250219"
        )
        
        if result and not result.startswith("Error"):
            # Split the response into individual tags and clean them
            tags = [tag.strip() for tag in result.split(",") if tag.strip()]
            
            # Ensure we have at least 3 tags but no more than 7
            while len(tags) < 3:
                tags.append("whisperforge content")
            
            return tags[:7]
        else:
            return [
                "audio content",
                "transcription",
                "whisperforge",
                "ai generated",
                "content notes",
            ]
    except Exception as e:
        logger.exception("Error generating content tags:")
        # Return default tags if there's an error
        return ["audio", "transcription", "content", "notes", "whisperforge"]


def get_available_openai_models():
    """Get current list of available OpenAI models"""
    try:
        openai_client = get_openai_client()
        if not openai_client:
            st.error("OpenAI API key is not configured.")
            return {}

        models = openai_client.models.list()
        gpt_models = {
            model.id: model.id
            for model in models
            if any(x in model.id for x in ["gpt-4", "gpt-3.5"])
        }
        return gpt_models
    except Exception as e:
        st.error(f"Error fetching OpenAI models: {str(e)}")
        return {}


def get_available_anthropic_models():
    """Get current list of available Anthropic models"""
    # Current as of May 2024
    return {
        "Claude 3.7 Sonnet": "claude-3-7-sonnet-20250219",
        "Claude 3 Opus": "claude-3-opus-20240229",
        "Claude 3 Sonnet": "claude-3-sonnet-20240229", 
        "Claude 3 Haiku": "claude-3-haiku-20240307",
    }


def get_available_grok_models():
    """Get current list of available Grok models"""
    # Current as of March 2024
    return {
        "Grok-1": "grok-1",
    }


# Update the LLM_MODELS dictionary dynamically
def get_current_models():
    return {
        "OpenAI": get_available_openai_models(),
        "Anthropic": get_available_anthropic_models(),
        "Grok": get_available_grok_models(),
    }


# Add this function to get available users
def get_available_users():
    """Get a list of available users by scanning the prompts directory"""
    users = []
    prompts_dir = "prompts"
    
    if not os.path.exists(prompts_dir):
        os.makedirs(prompts_dir)
        return ["Default"]
    
    # Get all user directories
    for user_dir in os.listdir(prompts_dir):
        user_path = os.path.join(prompts_dir, user_dir)
        if os.path.isdir(user_path) and not user_dir.startswith("."):
            users.append(user_dir)
    
    # If no users found, return a default user
    if not users:
        users = ["Default"]
    
    return users


# Make sure this function exists and works properly
def get_custom_prompt(user, prompt_type, users_prompts, default_prompts):
    """Safely retrieve a custom prompt for the user, or use default if not available"""
    # Ensure users_prompts is a dictionary
    if not isinstance(users_prompts, dict):
        return default_prompts.get(prompt_type, "")
        
    # Get user's prompts or empty dict if user not found
    user_prompts = users_prompts.get(user, {})
    if not isinstance(user_prompts, dict):
        return default_prompts.get(prompt_type, "")
    
    # Return the custom prompt if available, otherwise use the default
    return user_prompts.get(prompt_type, default_prompts.get(prompt_type, ""))


# Add this function to save custom prompts
def save_custom_prompt(user, prompt_type, prompt_content):
    """Save a custom prompt for a specific user and prompt type"""
    user_dir = os.path.join("prompts", user, "custom_prompts")
    os.makedirs(user_dir, exist_ok=True)
    
    prompt_path = os.path.join(user_dir, f"{prompt_type}.txt")
    try:
        with open(prompt_path, "w") as f:
            f.write(prompt_content)
        return True
    except Exception as e:
        st.error(f"Error saving custom prompt: {str(e)}")
        return False


def get_available_models(provider):
    """Get available models for a given provider"""
    try:
        openai_client = get_openai_client()
        
        # Default models in case API calls fail
        default_models = {
            "OpenAI": ["gpt-4-turbo-preview", "gpt-4", "gpt-3.5-turbo"],
            "Anthropic": [
                "claude-3-7-sonnet-20250219",
                "claude-3-opus-20240229",
                "claude-3-sonnet-20240229",
                "claude-3-haiku-20240307",
            ],
            "Grok": ["grok-1"],
        }
        
        if provider == "OpenAI":
            try:
                if openai_client:
                    models = openai_client.models.list()
                    available_models = []
                    
                    # Filter for chat and text generation models
                    for model in models.data:
                        model_id = model.id
                        if (
                            "gpt" in model_id.lower()
                            and "instruct" not in model_id.lower()
                            and any(ver in model_id.lower() for ver in ["3.5", "4"])
                        ):
                            available_models.append(model_id)
                    
                    # Add standard model options
                    standard_models = ["gpt-4", "gpt-4-turbo-preview", "gpt-3.5-turbo"]
                    
                    # Add standard models not in the list
                    for model in standard_models:
                        if model not in available_models:
                            available_models.append(model)
                    
                    return sorted(available_models)
                else:
                    return default_models["OpenAI"]
            except:
                # Return default OpenAI models if API call fails
                return default_models["OpenAI"]
        
        elif provider == "Anthropic":
            # Anthropic doesn't have a list models endpoint in the Python SDK
            return default_models["Anthropic"]
        
        elif provider == "Grok":
            # Grok currently only has one model
            return default_models["Grok"]
        
        # Return empty list for unknown providers
        return []
    except Exception as e:
        st.error(f"Error fetching models: {str(e)}")
        # Return default models if available
        if provider in default_models:
            return default_models[provider]
        return []


def configure_prompts(selected_user, users_prompts):
    """Configure custom prompts for the selected user"""
    # Convert users_prompts to a dictionary if it's not already
    if not isinstance(users_prompts, dict):
        users_prompts_dict = {}
    else:
        users_prompts_dict = users_prompts
        
    st.subheader("Custom Prompts")
    st.write("Configure custom prompts for different content types:")
    
    # List of prompt types
    prompt_types = [
        "wisdom_extraction",
        "summary",
        "outline_creation",
        "social_media",
        "image_prompts",
    ]
    
    for prompt_type in prompt_types:
        # Get current prompt for the user and type
        current_prompt = get_custom_prompt(
            selected_user, prompt_type, users_prompts_dict, DEFAULT_PROMPTS
        )
        
        # Display text area for editing
        new_prompt = st.text_area(
            f"{prompt_type.replace('_', ' ').title()}",
            value=current_prompt,
            height=150,
            key=f"prompt_{prompt_type}",
        )
        
        # Save button for this prompt
        if st.button(f"Save {prompt_type.replace('_', ' ').title()} Prompt"):
            # Create user directory if it doesn't exist
            user_dir = os.path.join("prompts", selected_user)
            os.makedirs(user_dir, exist_ok=True)
            
            # Save the prompt
            with open(os.path.join(user_dir, f"{prompt_type}.md"), "w") as f:
                f.write(new_prompt)
            
            st.success(f"Saved custom {prompt_type} prompt for {selected_user}")
            
            # Update the in-memory prompts
            if selected_user not in users_prompts_dict:
                users_prompts_dict[selected_user] = {}
            users_prompts_dict[selected_user][prompt_type] = new_prompt
    
    # Return the updated dictionary
    return users_prompts_dict


def transcribe_large_file(file_path):
    """Process a large audio file by chunking it and transcribing each chunk with concurrent processing"""
    try:
        # Start with info message
        st.info("Processing large audio file in chunks...")
        logger.info(f"Starting transcription of large file: {file_path}")
        
        # Split audio into chunks
        chunks, temp_dir = chunk_audio(file_path)
        
        # Validate chunks
        if not chunks or len(chunks) == 0:
            error_msg = "Failed to create audio chunks for processing"
            logger.error(error_msg)
            st.error(error_msg)
            return ""
        
        # Create progress indicators
        progress_text = st.empty()
        overall_status = st.empty()
        progress_bar = st.progress(0)
        
        # Log and display info about chunks
        logger.info(f"Created {len(chunks)} chunks for processing")
        overall_status.info(
            f"Beginning transcription of {len(chunks)} audio segments..."
        )
        
        # Determine optimal number of concurrent processes
        import os
        import concurrent.futures
        import time
        
        # Adjust concurrency based on number of chunks
        if len(chunks) > 20:
            max_workers = min(
                6, len(chunks)
            )  # Reduced to 6 workers for very large files
        elif len(chunks) > 10:
            max_workers = min(4, len(chunks))  # Reduced to 4 workers for medium files
        else:
            max_workers = min(2, len(chunks))  # Reduced to 2 workers for smaller files
            
        logger.debug(f"Using {max_workers} concurrent workers for {len(chunks)} chunks")
        
        # Set up shared variables for progress tracking
        import threading

        lock = threading.Lock()
        progress_tracker = {
            "completed": 0,
            "success": 0,
            "failed": 0,
            "results": [None] * len(chunks),
            "errors": [],  # Track detailed error information
        }
        
        # Create a thread-safe structure for progress updates
        progress_updates_lock = threading.Lock()
        progress_updates = []
        
        # Function for processing a single chunk with progress tracking
        def process_chunk(args):
            chunk_path, idx, total = args
            try:
                # Process the chunk
                chunk_text = transcribe_chunk(chunk_path, idx, total)
                
                # Update progress tracker
                with lock:
                    progress_tracker["completed"] += 1
                    
                    # Check for error markers or empty results
                    is_error = False
                    if not chunk_text:
                        is_error = True
                        progress_tracker["errors"].append(
                            f"Empty result for chunk {idx+1}"
                        )
                    elif any(
                        error_marker in chunk_text
                        for error_marker in ["[Error", "[Failed", "[Rate limit"]
                    ):
                        is_error = True
                        progress_tracker["errors"].append(chunk_text)
                    
                    if is_error:
                        progress_tracker["failed"] += 1
                    else:
                        progress_tracker["success"] += 1
                    
                    progress_tracker["results"][idx] = chunk_text
                    
                    # Calculate progress but don't update UI directly from thread
                    # This avoids NoSessionContext errors
                    completed = progress_tracker["completed"]
                    progress = completed / total
                    
                    # Add to a separate list that the main thread can safely read
                    with progress_updates_lock:
                        progress_updates.append(
                            {
                                "progress": progress,
                                "completed": completed,
                                "total": total,
                                "success": progress_tracker["success"],
                                "failed": progress_tracker["failed"],
                            }
                        )
                
                # Clean up chunk file
                try:
                    os.remove(chunk_path)
                    logger.debug(f"Removed chunk file: {chunk_path}")
                except Exception as clean_error:
                    logger.warning(
                        f"Failed to remove chunk file {chunk_path}: {str(clean_error)}"
                    )
                
                return chunk_text
            except Exception as e:
                error_msg = f"Error processing chunk {idx+1}: {str(e)}"
                logger.error(error_msg, exc_info=True)
                
                with lock:
                    progress_tracker["completed"] += 1
                    progress_tracker["failed"] += 1
                    progress_tracker["errors"].append(error_msg)
                    progress_tracker["results"][
                        idx
                    ] = f"[Error processing chunk {idx+1}: {str(e)}]"
                    
                    # Calculate progress but don't update UI directly
                    completed = progress_tracker["completed"]
                    progress = completed / total
                    with progress_updates_lock:
                        progress_updates.append(
                            {
                                "progress": progress,
                                "completed": completed,
                                "total": total,
                                "success": progress_tracker["success"],
                                "failed": progress_tracker["failed"],
                            }
                        )
                
                # Try to clean up even on error
                try:
                    if os.path.exists(chunk_path):
                        os.remove(chunk_path)
                except:
                    pass
                    
                return f"[Error processing chunk {idx+1}: {str(e)}]"
        
        # Process chunks with concurrent execution
        chunk_args = [
            (chunk_path, i, len(chunks)) for i, chunk_path in enumerate(chunks)
        ]
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Show processing message
            st.info(f"Transcribing audio using {max_workers} concurrent processes...")
            logger.debug(f"Starting {max_workers} workers for {len(chunks)} chunks")
            
            # Start all tasks
            future_to_chunk = {
                executor.submit(process_chunk, arg): arg for arg in chunk_args
            }
            
            # Create a thread-safe way to track cancellation
            should_terminate = threading.Event()
            
            # Main loop to update UI from the main thread while tasks are running
            while not should_terminate.is_set():
                # Check if all tasks are done
                all_done = all(future.done() for future in future_to_chunk)
                
                # Process any UI updates from worker threads
                updates_to_process = []
                with progress_updates_lock:
                    if progress_updates:
                        updates_to_process = progress_updates.copy()
                        progress_updates.clear()
                
                # Apply UI updates from the main thread
                if updates_to_process:
                    # Use the latest update
                    latest = updates_to_process[-1]
                    
                    # Update progress indicators (safely from main thread)
                    progress_bar.progress(latest["progress"])
                    progress_text.text(
                        f"Transcribing: {latest['completed']}/{latest['total']} chunks processed..."
                    )
                    
                    # Update overall status occasionally
                    if (
                        latest["completed"] % 2 == 0
                        or latest["completed"] == latest["total"]
                        or all_done
                    ):
                        overall_status.info(
                            f"Progress: {latest['completed']}/{latest['total']} chunks "
                            f"({latest['success']} successful, {latest['failed']} failed)"
                        )
                
                # If all done, exit the loop
                if all_done:
                    break
                    
                # Sleep briefly to avoid hogging CPU
                time.sleep(0.1)
            
            try:
            # Wait for all tasks to complete
                done, not_done = concurrent.futures.wait(
                    future_to_chunk, 
                    timeout=600,  # 10 minute timeout for all chunks
                    return_when=concurrent.futures.ALL_COMPLETED,
                )
                
                if not_done:
                    logger.warning(
                        f"{len(not_done)} chunk processing tasks did not complete within the timeout"
                    )
                    for future in not_done:
                        chunk_idx = future_to_chunk[future][1]
                        progress_tracker["errors"].append(
                            f"Timeout processing chunk {chunk_idx+1}"
                        )
                        progress_tracker["results"][
                            chunk_idx
                        ] = f"[Error: Processing timeout for chunk {chunk_idx+1}]"
            except Exception as wait_error:
                logger.error(f"Error waiting for tasks to complete: {str(wait_error)}")
        
        # Collect results in correct order, filtering out None or error entries
        transcriptions = []
        for idx, result in enumerate(progress_tracker["results"]):
            if result and not result.startswith("[Error"):
                transcriptions.append(result)
            elif result and result.startswith("[Error"):
                logger.debug(f"Skipping error result from chunk {idx+1}: {result}")
                # Include a placeholder for failed chunks to maintain context
                transcriptions.append(f"[...]")
        
        # Clean up temporary directory
        if temp_dir:
            try:
                shutil.rmtree(temp_dir)
                logger.debug(f"Removed temporary directory: {temp_dir}")
            except Exception as rmdir_error:
                logger.warning(
                    f"Failed to remove temporary directory: {str(rmdir_error)}"
                )
        
        # Combine all transcriptions with proper spacing
        full_transcript = " ".join([t for t in transcriptions if t])
        
        # Log the results
        logger.info(
            f"Transcription complete: {progress_tracker['success']} successful chunks, {progress_tracker['failed']} failed chunks"
        )
        if progress_tracker["failed"] > 0:
            logger.warning(f"Errors during transcription: {progress_tracker['errors']}")
        
        # Calculate character count for successful transcript
        char_count = len(full_transcript) if full_transcript else 0
        logger.debug(f"Generated transcript with {char_count} characters")
        
        # Clear progress indicators
        progress_text.empty()
        progress_bar.empty()
        
        # Final status message
        if progress_tracker["failed"] > 0:
            if progress_tracker["success"] > 0:
                # Partial success
                overall_status.warning(
                    f"⚠️ Transcription partially complete. Processed {progress_tracker['success']} of {len(chunks)} chunks successfully. {progress_tracker['failed']} chunks had errors."
                )
                st.success(f"✅ Transcription complete! ({char_count} characters)")
            else:
                # Complete failure
                overall_status.error(
                    f"❌ Transcription failed. All {len(chunks)} chunks had errors."
                )
                if progress_tracker["errors"]:
                    st.error(f"Error details: {progress_tracker['errors'][0]}")
        else:
            # Complete success
            overall_status.success(
                f"✅ Transcription complete! Successfully processed all {len(chunks)} audio segments."
            )
            st.success(f"✅ Transcription complete! ({char_count} characters)")
        
        return full_transcript
    except Exception as e:
        error_msg = f"Error in large file transcription: {str(e)}"
        logger.error(error_msg, exc_info=True)
        st.error(error_msg)
        return f"Error transcribing audio: {str(e)}"


def transcribe_audio(audio_file):
    """Transcribe an audio file using the appropriate method based on file size"""
    try:
        if audio_file is None:
            logger.warning("No audio file provided for transcription")
            return ""
        
        # Save the uploaded file to a temporary location
        with tempfile.NamedTemporaryFile(
            delete=False, suffix=os.path.splitext(audio_file.name)[1]
        ) as tmp_file:
            tmp_file.write(audio_file.getbuffer())
            temp_path = tmp_file.name
        
        logger.info(
            f"Processing audio file: {audio_file.name} (Size: {audio_file.size/1024/1024:.2f} MB)"
        )
        
        try:
            # Check if file is valid audio
            try:
                audio_info = sf.info(temp_path)
                logger.info(
                    f"Audio file details: {audio_file.name}, Duration: {audio_info.duration:.2f}s, "
                    f"Sample rate: {audio_info.samplerate}Hz, Channels: {audio_info.channels}"
                )
                
                # Add file details to the UI
                st.write(
                    f"📊 **File details**: Duration: {audio_info.duration:.2f}s, "
                    f"Sample rate: {audio_info.samplerate}Hz, Channels: {audio_info.channels}"
                )
            except Exception as audio_error:
                logger.warning(f"Could not read audio details: {str(audio_error)}")
                st.warning("⚠️ Could not read detailed audio information from file")
            
            # Determine processing method based on file size
            file_size_mb = os.path.getsize(temp_path) / (1024 * 1024)
            
            # Decision logic for transcription method
            if file_size_mb > 25:  # Large file threshold
                logger.info(
                    f"Large file detected ({file_size_mb:.2f} MB), using chunked processing"
                )
                st.info(
                    f"🔄 Large audio file detected ({file_size_mb:.2f} MB), processing in chunks for reliability..."
                )
                transcript = transcribe_large_file(temp_path)
            else:
                logger.info(
                    f"Standard file size ({file_size_mb:.2f} MB), using direct transcription"
                )
                st.info(f"🔄 Processing audio file ({file_size_mb:.2f} MB)...")
                transcript = transcribe_with_whisper(temp_path)
        
            # Clean up the temporary file
            try:
                os.unlink(temp_path)
                logger.debug(f"Removed temporary file: {temp_path}")
            except Exception as cleanup_error:
                logger.warning(f"Failed to remove temporary file: {str(cleanup_error)}")
            
            return transcript
        
        except Exception as process_error:
            # Clean up on error
            try:
                os.unlink(temp_path)
            except:
                pass
            
            # Re-raise for outer exception handler
            raise process_error
        
    except Exception as e:
        error_msg = f"Error processing audio file: {str(e)}"
        logger.error(error_msg, exc_info=True)
        
        # Provide more specific error messages based on error type
        if "ffmpeg" in str(e).lower():
            st.error(
                "❌ FFmpeg error. Please ensure FFmpeg is properly installed on your system."
            )
        elif "memory" in str(e).lower():
            st.error(
                "❌ Memory error. File may be too large for processing with current system resources."
            )
        elif "format" in str(e).lower() or "invalid" in str(e).lower():
            st.error(
                "❌ Invalid audio format. Please upload a supported audio file type."
            )
        elif "api" in str(e).lower() or "key" in str(e).lower():
            st.error("❌ API error. Please check your OpenAI API key configuration.")
        else:
            st.error(f"❌ Error processing audio: {str(e)}")
        
        return ""


def generate_wisdom(
    text, ai_provider, model, custom_prompt=None, editor_enabled=False, user_id=None
):
    """Generate wisdom insights from the text with optional editor step.

    Args:
        text (str): The text to generate wisdom from
        ai_provider (str): The AI provider to use
        model (str): The model to use
        custom_prompt (str, optional): Custom prompt to override default
        editor_enabled (bool): Whether to use the editor step
        user_id (str, optional): User ID for logging

    Returns:
        dict: {"wisdom": generated_wisdom, "editor_feedback": feedback if used, "error": error_message if any}
    """
    # Use default user ID if none provided
    if user_id is None:
        user_id = "anonymous"

    # Get session ID
    session_id = get_or_create_session_id()

    step_name = "wisdom_generation"

    # Input validation
    if not text or not isinstance(text, str):
        error_result = {
            "wisdom": "",
            "editor_feedback": "",
            "error": "Invalid input text",
        }

        # Log the error
        log_generation_step(
            user_id,
            session_id,
            step_name,
            {"stage": "input_validation", "error": "Invalid input text"},
        )

        return error_result

    try:
        client = get_client_for_provider(ai_provider)
        prompt = custom_prompt or load_default_prompt("wisdom")

        # Log the input and prompt
        log_generation_step(
            user_id,
            session_id,
            step_name,
            {
                "stage": "input",
                "text": (
                    text[:500] + "..." if len(text) > 500 else text
                ),  # Truncate long text for logs
                "prompt": prompt,
                "ai_provider": ai_provider,
                "model": model,
            },
        )

        # First draft generation
        wisdom_draft = client.generate(prompt, text, model)

        # Log the first draft
        log_generation_step(
            user_id,
            session_id,
            step_name,
            {"stage": "first_draft", "draft": wisdom_draft},
        )

        # Apply editor if enabled
        if editor_enabled:
            editor_result = run_editor_step(
                wisdom_draft, ai_provider, model, user_id, step_name
            )

            if editor_result["error"]:
                error_result = {
                    "wisdom": wisdom_draft,
                    "editor_feedback": "",
                    "error": editor_result["error"],
                }

                # Log the editor error
                log_generation_step(
                    user_id,
                    session_id,
                    step_name,
                    {
                        "stage": "editor_error",
                        "error": editor_result["error"],
                        "draft": wisdom_draft,
                    },
                )

                return error_result

            # Use the editor feedback to enhance the second generation
            enhanced_prompt = (
                f"{prompt}\n\nEditor Feedback: {editor_result['feedback_notes']}"
            )

            # Log the enhanced prompt
            log_generation_step(
                user_id,
                session_id,
                step_name,
                {
                    "stage": "enhanced_prompt",
                    "enhanced_prompt": enhanced_prompt,
                    "editor_feedback": editor_result["feedback_notes"],
                },
            )

            # Generate final wisdom with feedback
            wisdom = client.generate(enhanced_prompt, text, model)

            # Log the final output
            log_generation_step(
                user_id,
                session_id,
                step_name,
                {
                    "stage": "final_output",
                    "wisdom": wisdom,
                    "editor_feedback": editor_result["feedback_notes"],
                    "original_draft": wisdom_draft,
                    "editor_revised_draft": editor_result["revised_draft"],
                },
            )

            return {
                "wisdom": wisdom,
                "editor_feedback": editor_result["feedback_notes"],
                "error": None,
            }
        else:
            # Log the final output (no editor)
            log_generation_step(
                user_id,
                session_id,
                step_name,
                {"stage": "final_output_no_editor", "wisdom": wisdom_draft},
            )

            return {"wisdom": wisdom_draft, "editor_feedback": "", "error": None}
        
    except Exception as e:
        error_result = {"wisdom": "", "editor_feedback": "", "error": str(e)}

        # Log the exception
        log_generation_step(
            user_id, session_id, step_name, {"stage": "exception", "error": str(e)}
        )

        return error_result


def generate_outline(
    text,
    wisdom,
    ai_provider,
    model,
    custom_prompt=None,
    editor_enabled=False,
    user_id=None,
):
    """Generate content outline based on text and wisdom with optional editor step.

    Args:
        text (str): The original text
        wisdom (str): Generated wisdom insights
        ai_provider (str): The AI provider to use
        model (str): The model to use
        custom_prompt (str, optional): Custom prompt to override default
        editor_enabled (bool): Whether to use the editor step
        user_id (str, optional): User ID for logging

    Returns:
        dict: {"outline": generated_outline, "editor_feedback": feedback if used, "error": error_message if any}
    """
    # Use default user ID if none provided
    if user_id is None:
        user_id = "anonymous"

    # Get session ID
    session_id = get_or_create_session_id()

    step_name = "outline_generation"

    # Input validation
    if not text or not isinstance(text, str):
        error_result = {
            "outline": "",
            "editor_feedback": "",
            "error": "Invalid input text",
        }
        log_generation_step(
            user_id,
            session_id,
            step_name,
            {"stage": "input_validation", "error": "Invalid input text"},
        )
        return error_result

    try:
        client = get_client_for_provider(ai_provider)
        prompt = custom_prompt or load_default_prompt("outline")

        # Log the input and prompt
        log_generation_step(
            user_id,
            session_id,
            step_name,
            {
                "stage": "input",
                "text_sample": text[:500] + "..." if len(text) > 500 else text,
                "wisdom_sample": wisdom[:500] + "..." if len(wisdom) > 500 else wisdom,
                "prompt": prompt,
                "ai_provider": ai_provider,
                "model": model,
            },
        )

        # First draft generation
        outline_draft = client.generate(prompt, text, wisdom, model)

        # Log the first draft
        log_generation_step(
            user_id,
            session_id,
            step_name,
            {"stage": "first_draft", "draft": outline_draft},
        )

        # Apply editor if enabled
        if editor_enabled:
            editor_result = run_editor_step(
                outline_draft, ai_provider, model, user_id, step_name
            )

            if editor_result["error"]:
                error_result = {
                    "outline": outline_draft,
                    "editor_feedback": "",
                    "error": editor_result["error"],
                }
                log_generation_step(
                    user_id,
                    session_id,
                    step_name,
                    {
                        "stage": "editor_error",
                        "error": editor_result["error"],
                        "draft": outline_draft,
                    },
                )
                return error_result

            # Use the editor feedback to enhance the second generation
            enhanced_prompt = (
                f"{prompt}\n\nEditor Feedback: {editor_result['feedback_notes']}"
            )

            # Log the enhanced prompt
            log_generation_step(
                user_id,
                session_id,
                step_name,
                {
                    "stage": "enhanced_prompt",
                    "enhanced_prompt": enhanced_prompt,
                    "editor_feedback": editor_result["feedback_notes"],
                },
            )

            # Generate final outline with feedback
            outline = client.generate(enhanced_prompt, text, wisdom, model)

            # Log the final output
            log_generation_step(
                user_id,
                session_id,
                step_name,
                {
                    "stage": "final_output",
                    "outline": outline,
                    "editor_feedback": editor_result["feedback_notes"],
                    "original_draft": outline_draft,
                    "editor_revised_draft": editor_result["revised_draft"],
                },
            )

            return {
                "outline": outline,
                "editor_feedback": editor_result["feedback_notes"],
                "error": None,
            }
        else:
            # Log the final output (no editor)
            log_generation_step(
                user_id,
                session_id,
                step_name,
                {"stage": "final_output_no_editor", "outline": outline_draft},
            )

            return {"outline": outline_draft, "editor_feedback": "", "error": None}
        
    except Exception as e:
        error_result = {"outline": "", "editor_feedback": "", "error": str(e)}
        log_generation_step(
            user_id, session_id, step_name, {"stage": "exception", "error": str(e)}
        )
        return error_result


def generate_image_prompts(
    wisdom,
    outline,
    ai_provider,
    model,
    custom_prompt=None,
    editor_enabled=False,
    user_id=None,
):
    """Generate image prompts with optional editor step.

    Args:
        wisdom (str): Generated wisdom insights
        outline (str): Generated content outline
        ai_provider (str): The AI provider to use
        model (str): The model to use
        custom_prompt (str, optional): Custom prompt to override default
        editor_enabled (bool): Whether to use the editor step
        user_id (str, optional): User ID for logging

    Returns:
        dict: {"image_prompts": generated_prompts, "editor_feedback": feedback if used, "error": error_message if any}
    """
    # Use default user ID if none provided
    if user_id is None:
        user_id = "anonymous"

    # Get session ID
    session_id = get_or_create_session_id()

    step_name = "image_prompts_generation"

    # Input validation
    if not wisdom or not outline:
        error_result = {
            "image_prompts": "",
            "editor_feedback": "",
            "error": "Missing required inputs",
        }
        log_generation_step(
            user_id,
            session_id,
            step_name,
            {"stage": "input_validation", "error": "Missing required inputs"},
        )
        return error_result

    try:
        client = get_client_for_provider(ai_provider)
        prompt = custom_prompt or load_default_prompt("image_prompts")

        # Log the input and prompt
        log_generation_step(
            user_id,
            session_id,
            step_name,
            {
                "stage": "input",
                "wisdom_sample": wisdom[:500] + "..." if len(wisdom) > 500 else wisdom,
                "outline_sample": (
                    outline[:500] + "..." if len(outline) > 500 else outline
                ),
                "prompt": prompt,
                "ai_provider": ai_provider,
                "model": model,
            },
        )

        # First draft generation
        prompts_draft = client.generate(prompt, wisdom, outline, model)

        # Log the first draft
        log_generation_step(
            user_id,
            session_id,
            step_name,
            {"stage": "first_draft", "draft": prompts_draft},
        )

        # Apply editor if enabled
        if editor_enabled:
            editor_result = run_editor_step(
                prompts_draft, ai_provider, model, user_id, step_name
            )

            if editor_result["error"]:
                error_result = {
                    "image_prompts": prompts_draft,
                    "editor_feedback": "",
                    "error": editor_result["error"],
                }
                log_generation_step(
                    user_id,
                    session_id,
                    step_name,
                    {
                        "stage": "editor_error",
                        "error": editor_result["error"],
                        "draft": prompts_draft,
                    },
                )
                return error_result

            # Use the editor feedback to enhance the second generation
            enhanced_prompt = (
                f"{prompt}\n\nEditor Feedback: {editor_result['feedback_notes']}"
            )

            # Log the enhanced prompt
            log_generation_step(
                user_id,
                session_id,
                step_name,
                {
                    "stage": "enhanced_prompt",
                    "enhanced_prompt": enhanced_prompt,
                    "editor_feedback": editor_result["feedback_notes"],
                },
            )

            # Generate final image prompts with feedback
            image_prompts = client.generate(enhanced_prompt, wisdom, outline, model)

            # Log the final output
            log_generation_step(
                user_id,
                session_id,
                step_name,
                {
                    "stage": "final_output",
                    "image_prompts": image_prompts,
                    "editor_feedback": editor_result["feedback_notes"],
                    "original_draft": prompts_draft,
                    "editor_revised_draft": editor_result["revised_draft"],
                },
            )

            return {
                "image_prompts": image_prompts,
                "editor_feedback": editor_result["feedback_notes"],
                "error": None,
            }
        else:
            # Log the final output (no editor)
            log_generation_step(
                user_id,
                session_id,
                step_name,
                {"stage": "final_output_no_editor", "image_prompts": prompts_draft},
            )

            return {
                "image_prompts": prompts_draft,
                "editor_feedback": "",
                "error": None,
            }

    except Exception as e:
        error_result = {"image_prompts": "", "editor_feedback": "", "error": str(e)}
        log_generation_step(
            user_id, session_id, step_name, {"stage": "exception", "error": str(e)}
        )
        return error_result


def generate_social_content(
    wisdom,
    outline,
    ai_provider,
    model,
    custom_prompt=None,
    editor_enabled=False,
    user_id=None,
):
    """Generate social media content with optional editor step.

    Args:
        wisdom (str): Generated wisdom insights
        outline (str): Generated content outline
        ai_provider (str): The AI provider to use
        model (str): The model to use
        custom_prompt (str, optional): Custom prompt to override default
        editor_enabled (bool): Whether to use the editor step
        user_id (str, optional): User ID for logging

    Returns:
        dict: {"social": generated_content, "editor_feedback": feedback if used, "error": error_message if any}
    """
    # Use default user ID if none provided
    if user_id is None:
        user_id = "anonymous"

    # Get session ID
    session_id = get_or_create_session_id()

    step_name = "social_content_generation"

    # Input validation
    if not wisdom or not outline:
        error_result = {
            "social": "",
            "editor_feedback": "",
            "error": "Missing required inputs",
        }
        log_generation_step(
            user_id,
            session_id,
            step_name,
            {"stage": "input_validation", "error": "Missing required inputs"},
        )
        return error_result

    try:
        client = get_client_for_provider(ai_provider)
        prompt = custom_prompt or load_default_prompt("social_content")

        # Log the input and prompt
        log_generation_step(
            user_id,
            session_id,
            step_name,
            {
                "stage": "input",
                "wisdom_sample": wisdom[:500] + "..." if len(wisdom) > 500 else wisdom,
                "outline_sample": (
                    outline[:500] + "..." if len(outline) > 500 else outline
                ),
                "prompt": prompt,
                "ai_provider": ai_provider,
                "model": model,
            },
        )

        # First draft generation
        social_draft = client.generate(prompt, wisdom, outline, model)

        # Log the first draft
        log_generation_step(
            user_id,
            session_id,
            step_name,
            {"stage": "first_draft", "draft": social_draft},
        )

        # Apply editor if enabled
        if editor_enabled:
            editor_result = run_editor_step(
                social_draft, ai_provider, model, user_id, step_name
            )

            if editor_result["error"]:
                error_result = {
                    "social": social_draft,
                    "editor_feedback": "",
                    "error": editor_result["error"],
                }
                log_generation_step(
                    user_id,
                    session_id,
                    step_name,
                    {
                        "stage": "editor_error",
                        "error": editor_result["error"],
                        "draft": social_draft,
                    },
                )
                return error_result

            # Use the editor feedback to enhance the second generation
            enhanced_prompt = (
                f"{prompt}\n\nEditor Feedback: {editor_result['feedback_notes']}"
            )

            # Log the enhanced prompt
            log_generation_step(
                user_id,
                session_id,
                step_name,
                {
                    "stage": "enhanced_prompt",
                    "enhanced_prompt": enhanced_prompt,
                    "editor_feedback": editor_result["feedback_notes"],
                },
            )

            # Generate final social content with feedback
            social_content = client.generate(enhanced_prompt, wisdom, outline, model)

            # Log the final output
            log_generation_step(
                user_id,
                session_id,
                step_name,
                {
                    "stage": "final_output",
                    "social": social_content,
                    "editor_feedback": editor_result["feedback_notes"],
                    "original_draft": social_draft,
                    "editor_revised_draft": editor_result["revised_draft"],
                },
            )

            return {
                "social": social_content,
                "editor_feedback": editor_result["feedback_notes"],
                "error": None,
            }
        else:
            # Log the final output (no editor)
            log_generation_step(
                user_id,
                session_id,
                step_name,
                {"stage": "final_output_no_editor", "social": social_draft},
            )

            return {
                "social": social_draft,
                "editor_feedback": "",
                "error": None,
            }

    except Exception as e:
        error_result = {"social": "", "editor_feedback": "", "error": str(e)}
        log_generation_step(
            user_id, session_id, step_name, {"stage": "exception", "error": str(e)}
        )
        return error_result


def generate_article(
    text,
    wisdom,
    outline,
    ai_provider,
    model,
    custom_prompt=None,
    editor_enabled=False,
    user_id=None,
):
    """Generate full article with optional editor step.

    Args:
        text (str): The original text
        wisdom (str): Generated wisdom insights
        outline (str): Generated content outline
        ai_provider (str): The AI provider to use
        model (str): The model to use
        custom_prompt (str, optional): Custom prompt to override default
        editor_enabled (bool): Whether to use the editor step
        user_id (str, optional): User ID for logging

    Returns:
        dict: {"article": generated_article, "editor_feedback": feedback if used, "error": error_message if any}
    """
    # Use default user ID if none provided
    if user_id is None:
        user_id = "anonymous"

    # Get session ID
    session_id = get_or_create_session_id()

    step_name = "article_generation"

    # Input validation
    if not text or not wisdom or not outline:
        error_result = {
            "article": "",
            "editor_feedback": "",
            "error": "Missing required inputs",
        }
        log_generation_step(
            user_id,
            session_id,
            step_name,
            {"stage": "input_validation", "error": "Missing required inputs"},
        )
        return error_result

    try:
        client = get_client_for_provider(ai_provider)
        prompt = custom_prompt or load_default_prompt("article")

        # Log the input and prompt
        log_generation_step(
            user_id,
            session_id,
            step_name,
            {
                "stage": "input",
                "text_sample": text[:500] + "..." if len(text) > 500 else text,
                "wisdom_sample": wisdom[:500] + "..." if len(wisdom) > 500 else wisdom,
                "outline_sample": (
                    outline[:500] + "..." if len(outline) > 500 else outline
                ),
                "prompt": prompt,
                "ai_provider": ai_provider,
                "model": model,
            },
        )

        # First draft generation
        article_draft = client.generate(prompt, text, wisdom, outline, model)

        # Log the first draft
        log_generation_step(
            user_id,
            session_id,
            step_name,
            {"stage": "first_draft", "draft": article_draft},
        )

        # Apply editor if enabled
        if editor_enabled:
            editor_result = run_editor_step(
                article_draft, ai_provider, model, user_id, step_name
            )

            if editor_result["error"]:
                error_result = {
                    "article": article_draft,
                    "editor_feedback": "",
                    "error": editor_result["error"],
                }
                log_generation_step(
                    user_id,
                    session_id,
                    step_name,
                    {
                        "stage": "editor_error",
                        "error": editor_result["error"],
                        "draft": article_draft,
                    },
                )
                return error_result

            # Use the editor feedback to enhance the second generation
            enhanced_prompt = (
                f"{prompt}\n\nEditor Feedback: {editor_result['feedback_notes']}"
            )

            # Log the enhanced prompt
            log_generation_step(
                user_id,
                session_id,
                step_name,
                {
                    "stage": "enhanced_prompt",
                    "enhanced_prompt": enhanced_prompt,
                    "editor_feedback": editor_result["feedback_notes"],
                },
            )

            # Generate final article with feedback
            article = client.generate(enhanced_prompt, text, wisdom, outline, model)

            # Log the final output
            log_generation_step(
                user_id,
                session_id,
                step_name,
                {
                    "stage": "final_output",
                    "article": article,
                    "editor_feedback": editor_result["feedback_notes"],
                    "original_draft": article_draft,
                    "editor_revised_draft": editor_result["revised_draft"],
                },
            )

            return {
                "article": article,
                "editor_feedback": editor_result["feedback_notes"],
                "error": None,
            }
        else:
            # Log the final output (no editor)
            log_generation_step(
                user_id,
                session_id,
                step_name,
                {"stage": "final_output_no_editor", "article": article_draft},
            )

            return {"article": article_draft, "editor_feedback": "", "error": None}

    except Exception as e:
        error_result = {"article": "", "editor_feedback": "", "error": str(e)}
        log_generation_step(
            user_id, session_id, step_name, {"stage": "exception", "error": str(e)}
        )
        return error_result


def generate_seo_metadata(text, title, ai_provider, model, custom_prompt=None):
    """Generate SEO metadata based on content and title.

    Args:
        text (str): The content text
        title (str): The content title
        ai_provider (str): The AI provider to use
        model (str): The model to use
        custom_prompt (str, optional): Custom prompt to override default

    Returns:
        dict: {"seo_metadata": generated_metadata, "error": error_message if any}
    """
    # Input validation
    if not text or not title:
        return {"seo_metadata": {}, "error": "Missing required inputs"}

    try:
        client = get_client_for_provider(ai_provider)
        prompt = custom_prompt or load_default_prompt("seo_metadata")
        # API call with appropriate client
        metadata = client.generate(prompt, text, title, model)
        return {"seo_metadata": metadata, "error": None}
    except Exception as e:
        return {"seo_metadata": {}, "error": str(e)}


def process_all_content(text, ai_provider, model, editor_enabled=False):
    """Process all content with optional editor step.

    Args:
        text (str): The text to process
        ai_provider (str): The AI provider to use
        model (str): The model to use
        editor_enabled (bool): Whether to use the editor step

    Returns:
        dict: The processed content with all components
    """
    results = {}

    # Generate title
    title_result = generate_title(text, ai_provider, model)
    results["title"] = title_result["title"]

    # Generate wisdom with optional editor
    wisdom_result = generate_wisdom(
        text, ai_provider, model, editor_enabled=editor_enabled
    )
    results["wisdom"] = wisdom_result["wisdom"]
    results["wisdom_feedback"] = wisdom_result.get("editor_feedback", "")

    # Generate outline with optional editor
    outline_result = generate_outline(
        text, results["wisdom"], ai_provider, model, editor_enabled=editor_enabled
    )
    results["outline"] = outline_result["outline"]
    results["outline_feedback"] = outline_result.get("editor_feedback", "")

    # Generate social content with optional editor
    social_result = generate_social_content(
        results["wisdom"],
        results["outline"],
        ai_provider,
        model,
        editor_enabled=editor_enabled,
    )
    results["social"] = social_result["social"]
    results["social_feedback"] = social_result.get("editor_feedback", "")

    # Generate image prompts with optional editor
    image_result = generate_image_prompts(
        results["wisdom"],
        results["outline"],
        ai_provider,
        model,
        editor_enabled=editor_enabled,
    )
    results["image_prompts"] = image_result["image_prompts"]
    results["image_feedback"] = image_result.get("editor_feedback", "")

    # Generate article with optional editor
    article_result = generate_article(
        text,
        results["wisdom"],
        results["outline"],
        ai_provider,
        model,
        editor_enabled=editor_enabled,
    )
    results["article"] = article_result["article"]
    results["article_feedback"] = article_result.get("editor_feedback", "")

    return results


def process_all_content_enhanced(
    text,
    ai_provider,
    model,
    wisdom_container=None,
    outline_container=None,
    social_container=None,
    image_container=None,
    article_container=None,
):
    """Enhanced version of process_all_content with UI container support."""
    # Initialize results dictionary
    results = {}

    # Initialize progress indicators
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        # Generate title first
        status_text.text("Step 1/5: Generating core insights...")
        with st.status("Extracting wisdom from your content...") as status:
            results["wisdom"] = generate_wisdom(text, ai_provider, model)
            if results["wisdom"]:
                progress_bar.progress(0.2)
                status.update(
                    label="✅ Wisdom extracted successfully!", state="complete"
                )
                
                # Display in designated container if provided
                if wisdom_container:
                    wisdom_container.markdown("### 💡 Core Insights")
                    wisdom_container.markdown(results["wisdom"])
            else:
                status.update(label="❌ Wisdom extraction failed.", state="error")
        
        # Generate outline
        status_text.text("Step 2/5: Creating content structure...")
        with st.status("Organizing content into a structured outline...") as status:
            results["outline"] = generate_outline(
                text, results["wisdom"], ai_provider, model
            )
            if results["outline"]:
                progress_bar.progress(0.4)
                status.update(
                    label="✅ Outline created successfully!", state="complete"
                )
                
                # Display in designated container if provided
                if outline_container:
                    outline_container.markdown("### 📋 Content Outline")
                    outline_container.markdown(results["outline"])
            else:
                status.update(label="❌ Outline creation failed.", state="error")
        
        # Generate social content
        status_text.text("Step 3/5: Generating social media content...")
        with st.status("Creating social media posts from your content...") as status:
            results["social"] = generate_social_content(
                results["wisdom"], results["outline"], ai_provider, model
            )
            if results["social"]:
                progress_bar.progress(0.6)
                status.update(
                    label="✅ Social media content generated!", state="complete"
                )
                
                # Display in designated container if provided
                if social_container:
                    social_container.markdown("### 📱 Social Media Content")
                    social_container.markdown(results["social"])
            else:
                status.update(
                    label="❌ Social content generation failed.", state="error"
                )
        
        # Generate image prompts
        status_text.text("Step 4/5: Creating image prompts...")
        with st.status("Generating image description prompts...") as status:
            results["image_prompts"] = generate_image_prompts(
                results["wisdom"], results["outline"], ai_provider, model
            )
            if results["image_prompts"]:
                progress_bar.progress(0.8)
                status.update(
                    label="✅ Image prompts created successfully!", state="complete"
                )
                
                # Display in designated container if provided
                if image_container:
                    image_container.markdown("### 🖼️ Image Prompts")
                    image_container.markdown(results["image_prompts"])
            else:
                status.update(label="❌ Image prompt creation failed.", state="error")
        
        # Generate article
        status_text.text("Step 5/5: Writing full article...")
        with st.status("Crafting a complete article...") as status:
            results["article"] = generate_article(
                text, results["wisdom"], results["outline"], ai_provider, model
            )
            if results["article"]:
                progress_bar.progress(1.0)
                status.update(
                    label="✅ Article written successfully!", state="complete"
                )
                
                # Display in designated container if provided
                if article_container:
                    article_container.markdown("### 📄 Full Article")
                    article_container.markdown(results["article"])
            else:
                status.update(label="❌ Article generation failed.", state="error")
        
        # Clean up progress indicators
        status_text.empty()
        
    except Exception as e:
        st.error(f"Error processing content: {str(e)}")

    # Fix indentation here - this should be at the function body level (4 spaces)
        return results
        

def run_diagnostic():
    """Run a comprehensive diagnostic and output a report"""
    print("\n" + "=" * 80)
    print("WHISPERFORGE DIAGNOSTIC REPORT")
    print("=" * 80)
    
    # Get session id
    session_id = get_or_create_session_id()
    
    # Print session state
    print("\nSESSION STATE DUMP:")
    print("-" * 80)
    state_data = dump_session_state(display=False)
    
    # Print UI rendering conditions
    print("\nUI RENDERING CONDITIONS:")
    print("-" * 80)
    print(f"User authenticated: {is_authenticated()}")
    print(f"Current page: {st.session_state.get('page', 'Not set')}")
    print(f"Transcription available: {bool(st.session_state.get('transcription', ''))}")
    print(f"Session ID: {session_id}")
    
    # Print potential issues
    print("\nPOTENTIAL ISSUES:")
    print("-" * 80)
    issues = []
    
    if not is_authenticated():
        issues.append("- User is not authenticated, will show login page instead of main pipeline")
    
    if not st.session_state.get('transcription', ''):
        issues.append("- No transcription in session state, content generation pipeline won't be displayed")
    
    if not st.session_state.get('api_keys', {}):
        issues.append("- No API keys in session state, will show warnings in UI")
    
    if not issues:
        issues.append("- No obvious issues detected in session state")
    
    for issue in issues:
        print(issue)
    
    print("\nRECOMMENDATIONS:")
    print("-" * 80)
    print("1. Ensure initialize_session_state() is called at the start of the application")
    print("2. Set st.session_state.authenticated = True to bypass login screen")
    print("3. Add sample transcription data with st.session_state.transcription = 'Sample text'")
    print("4. Check auth flow in main() function for potential redirect issues")
    
    print("\n" + "=" * 80)


def main():
    """Main application entry point."""
    # Initialize session state variables
    initialize_session_state()

    # Ensure session_id is created
    session_id = get_or_create_session_id()
    
    # Add sample data for testing if needed
    if TEST_MODE and not st.session_state.get('transcription'):
        st.session_state.transcription = """This podcast episode was about the future of artificial intelligence and its impact on content creation. The speakers discussed how AI tools like ChatGPT and Claude are transforming how we create blog posts, articles, and social media content. They covered the ethical implications of AI-generated content, including issues around attribution, copyright, and the future of human creativity. The conversation also touched on best practices for using AI tools effectively while maintaining authenticity and the human touch that audiences connect with. Overall, the speakers were optimistic about AI as an augmentation to human creativity rather than a replacement for it."""
        print("Test mode enabled - added sample transcription data")
    
    # Check if in diagnostic mode
    if DIAGNOSTIC_MODE:
        run_diagnostic()
        return
    
    # Diagnostic: dump session state to console for debugging
    print("=" * 50)
    print("SESSION STATE DIAGNOSTIC")
    print("=" * 50)
    dump_session_state(display=False)
    print(f"Session ID: {session_id}")
    print(f"Authenticated: {st.session_state.get('authenticated', 'Not set')}")
    print(f"User ID: {st.session_state.get('user_id', 'Not set')}")
    print(f"Page: {st.session_state.get('page', 'Not set')}")
    print(f"Transcription available: {bool(st.session_state.get('transcription', ''))}")
    print("=" * 50)

    # Add security headers for production
    add_security_headers()

    # Initialize the database
    init_db()

    # Initialize the admin user
    init_admin_user()
    
    # Add CSS
    local_css()

    # Conditional CSS for production
    if os.environ.get("ENVIRONMENT") == "production":
        add_production_css()

    # Load JavaScript
    load_js()

    # Create custom header
    create_custom_header()
    
    # Cookie banner
    show_cookie_banner()

    # Check if user is authenticated
    if not is_authenticated():
        show_login_page()
    else:
        # Show the account sidebar
        show_account_sidebar()

        # Show the main application page
        if st.session_state.page == "home":
            show_main_page()
        elif st.session_state.page == "api":
            show_api_keys_page()
        elif st.session_state.page == "usage":
            show_usage_page()
        elif st.session_state.page == "config":
            show_user_config_page()
        elif st.session_state.page == "templates":
            show_templates_page()
        elif st.session_state.page == "admin":
            show_admin_page()
        elif st.session_state.page == "legal":
            show_legal_page()
    

def show_main_page():
    # This function contains the original main app functionality
    
    # Diagnostic: check UI rendering conditions for main pipeline
    print("=" * 50)
    print("UI RENDERING DIAGNOSTIC")
    print("=" * 50)
    print(f"User authenticated: {is_authenticated()}")
    print(f"Current page: {st.session_state.get('page', 'Not set')}")
    print(f"Transcription available: {bool(st.session_state.get('transcription', ''))}")
    print(f"Wisdom available: {bool(st.session_state.get('wisdom', ''))}")
    print(f"Outline available: {bool(st.session_state.get('outline', ''))}")
    print(f"Current AI provider: {st.session_state.get('ai_provider', 'Not set')}")
    print(f"Current AI model: {st.session_state.get('ai_model', 'Not set')}")
    print("=" * 50)
    
    # Get user's API keys
    api_keys = get_user_api_keys()
    
    # Check if API keys are set up
    openai_key = api_keys.get("openai")
    anthropic_key = api_keys.get("anthropic")
    notion_key = api_keys.get("notion")
    
    if not openai_key:
        st.warning(
            "⚠️ Your OpenAI API key is not set up. Some features may not work properly. [Set up your API keys](?page=api)"
        )
    
    if not anthropic_key:
        st.warning(
            "⚠️ Your Anthropic API key is not set up. Some features may not work properly. [Set up your API keys](?page=api)"
        )
    
    # Get selected user from the sidebar
    selected_user = st.session_state.get("user_profile_sidebar", "Default")
    
    # Display the current models being used
    st.info(
        f"Using {st.session_state.transcription_provider} {st.session_state.transcription_model} for transcription and {st.session_state.ai_provider} {st.session_state.ai_model} for content processing. Model settings can be changed in the Admin panel."
    )
    
    # Add tabs for input selection
    input_tabs = st.tabs(["Audio Upload", "Text Input"])
    
    # Tab 1: Audio Upload
    with input_tabs[0]:
        st.markdown(
            '<div class="section-header">Audio Transcription</div>',
            unsafe_allow_html=True,
        )
        
        # Update the file uploader with clear message about 500MB limit
        uploaded_file = st.file_uploader(
            "Upload your audio file", 
            type=["mp3", "wav", "ogg", "m4a"],
            key="audio_uploader",
            help="Files up to 500MB are supported. Large files will be automatically chunked for parallel processing.",
        )
        
        # Transcribe Button
        if uploaded_file is not None:
            if st.button(
                "🎙️ Transcribe Audio", key="transcribe_button", use_container_width=True
            ):
                with st.spinner("Transcribing your audio..."):
                    transcription = transcribe_audio(uploaded_file)
                    if transcription:
                        st.session_state.transcription = transcription
                        st.session_state.audio_file = uploaded_file
        
        # Display transcription result if available
        if st.session_state.transcription:
            st.markdown("### Transcription Result")
            st.text_area(
                "Transcript",
                st.session_state.transcription,
                height=200,
                key="transcript_display",
            )
            
            # Content generation section
            st.markdown(
                '<div class="section-header">Content Generation</div>',
                unsafe_allow_html=True,
            )
            
            # Show content generation options
            content_tabs = st.tabs(["Step-by-Step", "I'm Feeling Lucky", "Custom"])
            
            with content_tabs[0]:
                # Wisdom extraction
                wisdom_expander = st.expander("📝 Extract Wisdom", expanded=True)
                with wisdom_expander:
                    if st.button(
                        "Generate Wisdom", key="wisdom_button", use_container_width=True
                    ):
                        with st.spinner("Extracting key insights..."):
                            wisdom = generate_wisdom(
                                st.session_state.transcription, 
                                st.session_state.ai_provider,
                                st.session_state.ai_model,
                            )
                            if wisdom:
                                st.session_state.wisdom = wisdom
                    
                    if st.session_state.get("wisdom"):
                        st.markdown("### Extracted Wisdom")
                        st.markdown(st.session_state.wisdom)
                
                # Outline creation
                outline_expander = st.expander("📋 Create Outline", expanded=False)
                with outline_expander:
                    if st.button(
                        "Generate Outline",
                        key="outline_button",
                        use_container_width=True,
                    ):
                        if not st.session_state.get("wisdom"):
                            st.warning("Please extract wisdom first.")
                        else:
                            with st.spinner("Creating outline..."):
                                outline = generate_outline(
                                    st.session_state.transcription,
                                    st.session_state.wisdom,
                                    st.session_state.ai_provider,
                                    st.session_state.ai_model,
                                )
                                if outline:
                                    st.session_state.outline = outline
                    
                    if st.session_state.get("outline"):
                        st.markdown("### Content Outline")
                        st.markdown(st.session_state.outline)
                
                # Social media content
                social_expander = st.expander("📱 Social Media Content", expanded=False)
                with social_expander:
                    if st.button(
                        "Generate Social Posts",
                        key="social_button",
                        use_container_width=True,
                    ):
                        if not st.session_state.get(
                            "wisdom"
                        ) or not st.session_state.get("outline"):
                            st.warning(
                                "Please extract wisdom and create an outline first."
                            )
                        else:
                            with st.spinner("Creating social media content..."):
                                social = generate_social_content(
                                    st.session_state.wisdom,
                                    st.session_state.outline,
                                    st.session_state.ai_provider,
                                    st.session_state.ai_model,
                                )
                                if social:
                                    st.session_state.social = social
                    
                    if st.session_state.get("social"):
                        st.markdown("### Social Media Content")
                        st.markdown(st.session_state.social)
                
                # Image prompts
                image_expander = st.expander("🖼️ Image Prompts", expanded=False)
                with image_expander:
                    if st.button(
                        "Generate Image Prompts",
                        key="image_button",
                        use_container_width=True,
                    ):
                        if not st.session_state.get(
                            "wisdom"
                        ) or not st.session_state.get("outline"):
                            st.warning(
                                "Please extract wisdom and create an outline first."
                            )
                        else:
                            with st.spinner("Creating image prompts..."):
                                prompts = generate_image_prompts(
                                    st.session_state.wisdom,
                                    st.session_state.outline,
                                    st.session_state.ai_provider,
                                    st.session_state.ai_model,
                                )
                                if prompts:
                                    st.session_state.image_prompts = prompts
                    
                    if st.session_state.get("image_prompts"):
                        st.markdown("### Image Prompts")
                        st.markdown(st.session_state.image_prompts)
                
                # Full article
                article_expander = st.expander("📄 Full Article", expanded=False)
                with article_expander:
                    if st.button(
                        "Generate Article",
                        key="article_button",
                        use_container_width=True,
                    ):
                        if not st.session_state.get(
                            "wisdom"
                        ) or not st.session_state.get("outline"):
                            st.warning(
                                "Please extract wisdom and create an outline first."
                            )
                        else:
                            with st.spinner("Writing full article..."):
                                article = generate_article(
                                    st.session_state.transcription,
                                    st.session_state.wisdom,
                                    st.session_state.outline,
                                    st.session_state.ai_provider,
                                    st.session_state.ai_model,
                                )
                                if article:
                                    st.session_state.article = article
                    
                    if st.session_state.get("article"):
                        st.markdown("### Generated Article")
                        st.markdown(st.session_state.article)
            
            with content_tabs[1]:
                # I'm Feeling Lucky mode (formerly All-in-One)
                # Create containers for each content type
                wisdom_container = st.empty()
                outline_container = st.empty()
                social_container = st.empty()
                image_container = st.empty()
                article_container = st.empty()
                
                # Add a checkbox for auto-save to Notion
                auto_save_to_notion = False
                notion_key = api_keys.get("notion") or os.getenv("NOTION_API_KEY")
                notion_db = api_keys.get("notion_database_id") or os.getenv(
                    "NOTION_DATABASE_ID"
                )
                
                if notion_key and notion_db:
                    auto_save_to_notion = st.checkbox(
                        "Auto-save to Notion when complete", key="auto_save_checkbox"
                    )
                
                # Changed button text to match the tab name
                if st.button(
                    "🚀 I'm Feeling Lucky!",
                    key="generate_all",
                    use_container_width=True,
                ):
                    # Process all content with enhanced function that displays results in containers
                    results = process_all_content_enhanced(
                        st.session_state.transcription,
                        st.session_state.ai_provider,
                        st.session_state.ai_model,
                        wisdom_container=wisdom_container,
                        outline_container=outline_container,
                        social_container=social_container,
                        image_container=image_container,
                        article_container=article_container,
                    )
                    
                    if results:
                        st.session_state.wisdom = results.get("wisdom", "")
                        st.session_state.outline = results.get("outline", "")
                        st.session_state.social = results.get("social", "")
                        st.session_state.image_prompts = results.get(
                            "image_prompts", ""
                        )
                        st.session_state.article = results.get("article", "")
                        
                        # Auto-save to Notion if enabled
                        if auto_save_to_notion:
                            with st.spinner("Saving to Notion..."):
                                try:
                                    # Generate a title
                                    with st.status(
                                        "Generating a descriptive title..."
                                    ) as status:
                                        title_to_use = generate_short_title(
                                            st.session_state.transcription
                                        )
                                        status.update(
                                            label=f'Title generated: "{title_to_use}"',
                                            state="complete",
                                        )
                                    
                                    # Save to Notion
                                    with st.status("Saving to Notion...") as status:
                                        result = create_content_notion_entry(
                                            title_to_use,
                                            st.session_state.transcription,
                                            wisdom=st.session_state.get("wisdom"),
                                            outline=st.session_state.get("outline"),
                                            social=st.session_state.get("social"),
                                            image_prompts=st.session_state.get(
                                                "image_prompts"
                                            ),
                                            article=st.session_state.get("article"),
                                        )
                                        
                                        if result:
                                            status.update(
                                                label="Successfully saved to Notion!",
                                                state="complete",
                                            )
                                        else:
                                            status.update(
                                                label="Failed to save to Notion",
                                                state="error",
                                            )
                                except Exception as e:
                                    logger.exception("Error saving to Notion:")
                                    st.error(f"Error saving to Notion: {str(e)}")
                            
                            st.success("✅ All content generated successfully!")
            
            with content_tabs[2]:
                # Custom prompt generation
                st.markdown("### Custom Prompt")
                custom_prompt = st.text_area(
                    "Enter your custom prompt",
                    placeholder="Ask anything about the transcription...",
                    height=100,
                )

                if st.button(
                    "Send Custom Prompt",
                    key="custom_prompt_button",
                    use_container_width=True,
                ):
                    if custom_prompt:
                        with st.spinner("Processing custom prompt..."):
                            result = apply_prompt(
                                st.session_state.transcription, 
                                custom_prompt,
                                st.session_state.ai_provider,
                                st.session_state.ai_model,
                            )
                            if result:
                                st.markdown("### Result")
                                st.markdown(result)
            
            # Notion export
            st.markdown(
                '<div class="section-header">Export to Notion</div>',
                unsafe_allow_html=True,
            )
            
            # Check if Notion API key is configured
            notion_key = api_keys.get("notion") or os.getenv("NOTION_API_KEY")
            notion_db = api_keys.get("notion_database_id") or os.getenv(
                "NOTION_DATABASE_ID"
            )
            
            if not notion_key or not notion_db:
                st.warning(
                    "⚠️ Notion integration is not configured. Please set up your Notion API key and database ID in Settings."
                )
            else:
                title = st.session_state.content_title_value or "Untitled Content"
                
                if st.button(
                    "💾 Save to Notion", key="notion_save", use_container_width=True
                ):
                    with st.spinner("Saving to Notion..."):
                        try:
                            # Always generate an AI title for better results
                            if st.session_state.transcription:
                                with st.status(
                                    "Generating a descriptive title..."
                                ) as status:
                                    title_to_use = generate_short_title(
                                        st.session_state.transcription
                                    )
                                    status.update(
                                        label=f'Title generated: "{title_to_use}"',
                                        state="complete",
                                    )
                            else:
                                title_to_use = "WhisperForge Content"
                            
                            with st.status("Saving to Notion...") as status:
                                result = create_content_notion_entry(
                                    title_to_use,
                                    st.session_state.transcription,
                                    wisdom=st.session_state.get("wisdom"),
                                    outline=st.session_state.get("outline"),
                                    social=st.session_state.get("social"),
                                    image_prompts=st.session_state.get("image_prompts"),
                                    article=st.session_state.get("article"),
                                )
                                
                                if result:
                                    status.update(
                                        label="Successfully saved to Notion!",
                                        state="complete",
                                    )
                                else:
                                    status.update(
                                        label="Failed to save to Notion", state="error"
                                    )
                        except Exception as e:
                            logger.exception("Error saving to Notion:")
                            st.error(f"Error saving to Notion: {str(e)}")
    
    # Tab 2: Text Input
    with input_tabs[1]:
        st.markdown(
            '<div class="section-header">Manual Text Input</div>',
            unsafe_allow_html=True,
        )
        
        text_input = st.text_area(
            "Enter your text",
            placeholder="Paste your transcript or any text to process...",
            height=300,
            key="manual_text",
        )
        
        if st.button("Use This Text", key="use_text_button", use_container_width=True):
            if text_input:
                st.session_state.transcription = text_input
                st.success("Text loaded for processing!")
                st.rerun()


def show_api_keys_page():
    st.markdown("## API Keys Management")
    st.markdown(
        "Set up your API keys to use with WhisperForge. Your keys are encrypted and stored securely."
    )
    
    # Get current API keys
    api_keys = get_user_api_keys()
    
    # OpenAI API Key
    st.markdown("### OpenAI API Key")
    st.markdown("Required for audio transcription and most AI capabilities.")
    
    # Create a masked display of the current key if it exists
    openai_key = api_keys.get("openai", "")
    openai_key_display = (
        f"••••••••••••••••••{openai_key[-4:]}" if openai_key else "Not set"
    )
    
    st.markdown(f"**Current key:** {openai_key_display}")
    
    # Input for new key
    new_openai_key = st.text_input(
        "Enter new OpenAI API key", type="password", key="new_openai_key"
    )
    if st.button("Save OpenAI Key"):
        if new_openai_key:
            update_api_key("openai", new_openai_key)
            st.success("OpenAI API key updated successfully!")
            time.sleep(1)
            st.rerun()
    
    st.markdown("---")
    
    # Anthropic API Key
    st.markdown("### Anthropic API Key")
    st.markdown("Optional: Used for Claude AI models.")
    
    anthropic_key = api_keys.get("anthropic", "")
    anthropic_key_display = (
        f"••••••••••••••••••{anthropic_key[-4:]}" if anthropic_key else "Not set"
    )
    
    st.markdown(f"**Current key:** {anthropic_key_display}")
    
    new_anthropic_key = st.text_input(
        "Enter new Anthropic API key", type="password", key="new_anthropic_key"
    )
    if st.button("Save Anthropic Key"):
        update_api_key("anthropic", new_anthropic_key)
        st.success("Anthropic API key updated successfully!")
        time.sleep(1)
        st.rerun()
    
    st.markdown("---")
    
    # Notion API Key
    st.markdown("### Notion API Key")
    st.markdown("Optional: Used for exporting content to Notion.")
    
    notion_key = api_keys.get("notion", "")
    notion_key_display = (
        f"••••••••••••••••••{notion_key[-4:]}" if notion_key else "Not set"
    )
    
    st.markdown(f"**Current key:** {notion_key_display}")
    
    col1, col2 = st.columns(2)
    with col1:
        new_notion_key = st.text_input(
            "Enter new Notion API key", type="password", key="new_notion_key"
        )
    with col2:
        notion_database_id = st.text_input(
            "Notion Database ID",
            value=api_keys.get("notion_database_id", ""),
            key="notion_database_id",
        )
    
    if st.button("Save Notion Settings"):
        update_api_key("notion", new_notion_key)
        update_api_key("notion_database_id", notion_database_id)
        st.success("Notion settings updated successfully!")
        time.sleep(1)
        st.rerun()
    
    st.markdown("---")
    
    # Grok API Key
    st.markdown("### Grok API Key (Experimental)")
    st.markdown("Optional: Used for Grok AI models.")
    
    grok_key = api_keys.get("grok", "")
    grok_key_display = f"••••••••••••••••••{grok_key[-4:]}" if grok_key else "Not set"
    
    st.markdown(f"**Current key:** {grok_key_display}")
    
    new_grok_key = st.text_input(
        "Enter new Grok API key", type="password", key="new_grok_key"
    )
    if st.button("Save Grok Key"):
        update_api_key("grok", new_grok_key)
        st.success("Grok API key updated successfully!")
        time.sleep(1)
        st.rerun()


def show_usage_page():
    st.markdown("## Usage Statistics")
    
    # Get user info
    conn = get_db_connection()
    user = conn.execute(
        "SELECT email, subscription_tier, usage_quota, usage_current, created_at FROM users WHERE id = ?",
        (st.session_state.user_id,),
    ).fetchone()
    conn.close()
    
    if not user:
        st.error("Error retrieving user data")
        return
    
    # User info section
    st.markdown("### Account Information")
    st.write(f"**Email:** {user['email']}")
    st.write(f"**Account created:** {user['created_at']}")
    st.write(f"**Subscription tier:** {user['subscription_tier'].title()}")
    
    # Usage statistics
    st.markdown("### Current Usage")
    
    # Calculate percentage
    usage_percent = (
        min(100, (user["usage_current"] / user["usage_quota"]) * 100)
        if user["usage_quota"] > 0
        else 0
    )
    
    # Show progress bar
    st.progress(usage_percent / 100)
    st.write(
        f"**Usage this month:** {user['usage_current']} / {user['usage_quota']} minutes ({usage_percent:.1f}%)"
    )
    
    # Upgrade options
    st.markdown("### Upgrade Your Plan")
    st.markdown(
        """
    | Plan | Monthly Price | Minutes/Month | Features |
    |------|---------------|---------------|----------|
    | Free | $0 | 60 | Basic transcription |
    | Basic | $9.99 | 300 | + Claude AI models |
    | Pro | $19.99 | 1,000 | + Advanced processing |
    | Enterprise | Contact us | Custom | Custom integrations |
    """
    )
    
    if user["subscription_tier"] != "enterprise":
        if st.button("Upgrade Now"):
            st.info("This would redirect to a payment page in the production version.")
    
    # Reset usage manually (for testing)
    if st.button("Reset Usage Counter"):
        conn = get_db_connection()
        conn.execute(
            "UPDATE users SET usage_current = 0 WHERE id = ?",
            (st.session_state.user_id,),
        )
        conn.commit()
        conn.close()
        st.success("Usage counter reset to 0")
        time.sleep(1)
        st.rerun()


def update_api_key(key_name, key_value):
    if not st.session_state.authenticated:
        return False
    
    conn = get_db_connection()
    
    # Get current api_keys JSON
    user = conn.execute(
        "SELECT api_keys FROM users WHERE id = ?", (st.session_state.user_id,)
    ).fetchone()
    
    if not user:
        conn.close()
        return False
    
    # Update the specific key
    api_keys = json.loads(user["api_keys"]) if user["api_keys"] else {}
    
    # If key value is empty, remove the key
    if key_value:
        api_keys[key_name] = key_value
    else:
        api_keys.pop(key_name, None)
    
    # Save back to the database
    conn.execute(
        "UPDATE users SET api_keys = ? WHERE id = ?",
        (json.dumps(api_keys), st.session_state.user_id),
    )
    conn.commit()
    conn.close()
    return True
    
    
def get_api_key_for_service(service_name):
    """Get the API key for a specific service from the user's stored keys"""
    # Prioritize environment variables for testing
    if service_name == "openai":
        env_key = os.getenv("OPENAI_API_KEY")
        if env_key:
            return env_key
    elif service_name == "anthropic":
        env_key = os.getenv("ANTHROPIC_API_KEY")
        if env_key:
            return env_key
    elif service_name == "notion":
        env_key = os.getenv("NOTION_API_KEY")
        if env_key:
            return env_key
    elif service_name == "grok":
        env_key = os.getenv("GROK_API_KEY")
        if env_key:
            return env_key
    
    if not st.session_state.authenticated:
        # Fallback to environment variables
        if service_name == "openai":
            return os.getenv("OPENAI_API_KEY")
        elif service_name == "anthropic":
            return os.getenv("ANTHROPIC_API_KEY")
        elif service_name == "notion":
            return os.getenv("NOTION_API_KEY")
        elif service_name == "grok":
            return os.getenv("GROK_API_KEY")
        return None
    
    # Get from user's stored keys
    api_keys = get_user_api_keys()
    key = api_keys.get(service_name)
    
    # Fallback to environment if user doesn't have a key
    if not key:
        if service_name == "openai":
            return os.getenv("OPENAI_API_KEY")
        elif service_name == "anthropic":
            return os.getenv("ANTHROPIC_API_KEY")
        elif service_name == "notion":
            return os.getenv("NOTION_API_KEY")
        elif service_name == "grok":
            return os.getenv("GROK_API_KEY")
    
    return key


# Authentication UI
def show_login_page():
    st.markdown(
        f"""
    <div class="header-container">
        <div class="header-title">WhisperForge // Authentication</div>
        <div class="header-date">{datetime.now().strftime('%a %d %b %Y · %H:%M')}</div>
    </div>
    """,
        unsafe_allow_html=True,
    )
    
    tab1, tab2 = st.tabs(["Login", "Register"])
    
    with tab1:
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Password", type="password", key="login_password")
        
        if st.button("Login", key="login_button"):
            if email and password:
                if authenticate_user(email, password):
                    st.success("Login successful!")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("Invalid email or password")
            else:
                st.warning("Please enter both email and password")
    
    with tab2:
        email = st.text_input("Email", key="register_email")
        password = st.text_input("Password", type="password", key="register_password")
        confirm_password = st.text_input(
            "Confirm Password", type="password", key="register_confirm_password"
        )
        
        if st.button("Register", key="register_button"):
            if not email or not password or not confirm_password:
                st.warning("Please fill out all fields")
            elif not re.match(r"[^@]+@[^@]+\.[^@]+", email):
                st.error("Please enter a valid email address")
            elif password != confirm_password:
                st.error("Passwords do not match")
            elif len(password) < 8:
                st.error("Password must be at least 8 characters long")
            else:
                if register_user(email, password):
                    st.success("Registration successful! Please login.")
                else:
                    st.error("Email already exists")


def authenticate_user(email, password):
    conn = get_db_connection()
    hashed_password = hash_password(password)
    
    user = conn.execute(
        "SELECT id FROM users WHERE email = ? AND password = ?",
        (email, hashed_password),
    ).fetchone()
    
    conn.close()
    
    if user:
        st.session_state.user_id = user["id"]
        st.session_state.authenticated = True
        return True
    return False


def register_user(email, password):
    conn = get_db_connection()
    hashed_password = hash_password(password)
    
    # Check if user already exists
    existing_user = conn.execute(
        "SELECT id FROM users WHERE email = ?", (email,)
    ).fetchone()
    
    if existing_user:
        conn.close()
        return False
    
    # Create new user
    conn.execute(
        "INSERT INTO users (email, password, api_keys) VALUES (?, ?, ?)",
        (email, hashed_password, json.dumps({})),
    )
    conn.commit()
    conn.close()
    return True


def show_account_sidebar():
    st.markdown("### Account")
    
    # Get user info
    conn = get_db_connection()
    user = conn.execute(
        "SELECT email, subscription_tier, usage_quota, usage_current FROM users WHERE id = ?",
        (st.session_state.user_id,),
    ).fetchone()
    conn.close()
    
    if user:
        st.write(f"**Email:** {user['email']}")
        st.write(f"**Plan:** {user['subscription_tier'].title()}")
        
        # Show usage meter
        usage_percent = (
            min(100, (user["usage_current"] / user["usage_quota"]) * 100)
            if user["usage_quota"] > 0
            else 0
        )
        st.progress(usage_percent / 100)
        st.write(f"Usage: {user['usage_current']} / {user['usage_quota']} minutes")
        
        # Upgrade account link
        st.markdown("[Upgrade Account](#)")
    
    # Logout button
    if st.button("Logout"):
        st.session_state.authenticated = False
        st.session_state.user_id = None
        st.rerun()


def get_user_api_keys():
    if not st.session_state.authenticated:
        return {}
    
    conn = get_db_connection()
    user = conn.execute(
        "SELECT api_keys FROM users WHERE id = ?", (st.session_state.user_id,)
    ).fetchone()
    conn.close()
    
    if user and user["api_keys"]:
        return json.loads(user["api_keys"])
    return {}


def update_usage_tracking(duration_seconds):
    if not st.session_state.authenticated:
        return
    
    # Convert seconds to minutes and round up
    minutes = math.ceil(duration_seconds / 60)
    
    conn = get_db_connection()
    conn.execute(
        "UPDATE users SET usage_current = usage_current + ? WHERE id = ?",
        (minutes, st.session_state.user_id),
    )
    conn.commit()
    conn.close()


# Default prompts in case user prompts are not available
DEFAULT_PROMPTS = {}


# Set up security headers
def add_security_headers():
    st.markdown(
        """
        <meta http-equiv="Content-Security-Policy" content="default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'">
        <meta http-equiv="X-Frame-Options" content="DENY">
        <meta http-equiv="X-Content-Type-Options" content="nosniff">
    """,
        unsafe_allow_html=True,
    )


# Add extended CSS for production look and feel
def add_production_css():
    with open("static/css/production.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


# Initialize database with admin user if not exists
def init_admin_user():
    """Create an admin user if none exists"""
    conn = get_db_connection()
    admin_exists = conn.execute(
        "SELECT COUNT(*) FROM users WHERE is_admin = 1"
    ).fetchone()[0]
    
    if admin_exists == 0:
        # Create admin user with default password
        admin_email = os.getenv("ADMIN_EMAIL", "admin@whisperforge.ai")
        admin_password = os.getenv("ADMIN_PASSWORD", "WhisperForge2024!")
        
        hashed_password = hash_password(admin_password)
        
        conn.execute(
            "INSERT INTO users (email, password, is_admin, subscription_tier, usage_quota) VALUES (?, ?, ?, ?, ?)",
            (admin_email, hashed_password, 1, "enterprise", 100000),
        )
        conn.commit()
    
    conn.close()


# Admin tools
def show_admin_page():
    """Show admin dashboard with user management"""
    st.markdown("## Admin Dashboard")
    
    # Check if current user is admin
    conn = get_db_connection()
    is_admin = conn.execute(
        "SELECT is_admin FROM users WHERE id = ?", (st.session_state.user_id,)
    ).fetchone()[0]
    
    if not is_admin:
        st.error("You do not have permission to access this page.")
        conn.close()
        return
    
    # Create tabs for different admin functions
    admin_tabs = st.tabs(
        [
            "System Overview",
            "User Management",
            "Model Configuration",
            "App Configuration",
        ]
    )
    
    # System Overview Tab
    with admin_tabs[0]:
        st.markdown("### System Overview")
        
        # Get statistics
        user_count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        active_users = conn.execute(
            "SELECT COUNT(*) FROM users WHERE usage_current > 0"
        ).fetchone()[0]
        paying_users = conn.execute(
            "SELECT COUNT(*) FROM users WHERE subscription_tier != 'free'"
        ).fetchone()[0]
        
        # Display stats in a grid
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Users", user_count)
        with col2:
            st.metric("Active Users", active_users)
        with col3:
            st.metric("Paying Users", paying_users)
    
    # User Management Tab
    with admin_tabs[1]:
        st.markdown("### User Management")
        
        # List all users
        users = conn.execute(
            "SELECT id, email, created_at, subscription_tier, usage_quota, usage_current, is_admin FROM users ORDER BY id"
        ).fetchall()
        
        if not users:
            st.info("No users found.")
        else:
            # Create table
            data = []
            for user in users:
                data.append(
                    {
                    "ID": user["id"],
                    "Email": user["email"],
                        "Created": (
                            user["created_at"].split(" ")[0]
                            if " " in user["created_at"]
                            else user["created_at"]
                        ),
                    "Plan": user["subscription_tier"],
                    "Usage": f"{user['usage_current']}/{user['usage_quota']} min",
                        "Admin": "Yes" if user["is_admin"] else "No",
                    }
                )
            
            st.dataframe(data)
        
        # Edit user form
        st.markdown("### Edit User")
        user_id = st.number_input("User ID", min_value=1, step=1)
        
        if st.button("Load User"):
            user = conn.execute(
                "SELECT * FROM users WHERE id = ?", (user_id,)
            ).fetchone()
            
            if user:
                st.session_state.edit_user = dict(user)
                st.success(f"Loaded user: {user['email']}")
            else:
                st.error("User not found")
        
        if hasattr(st.session_state, "edit_user"):
            user = st.session_state.edit_user
            
            email = st.text_input("Email", value=user["email"])
            subscription = st.selectbox(
                "Subscription Tier", 
                options=["free", "basic", "pro", "enterprise"],
                index=["free", "basic", "pro", "enterprise"].index(
                    user["subscription_tier"]
                ),
            )
            quota = st.number_input(
                "Usage Quota (minutes)", value=user["usage_quota"], min_value=0
            )
            reset_usage = st.checkbox("Reset current usage to 0")
            is_admin = st.checkbox("Admin", value=bool(user["is_admin"]))
            
            if st.button("Save Changes"):
                if reset_usage:
                    usage_current = 0
                else:
                    usage_current = user["usage_current"]
                    
                conn.execute(
                    """
                    UPDATE users 
                    SET email = ?, subscription_tier = ?, usage_quota = ?, 
                        usage_current = ?, is_admin = ?
                    WHERE id = ?
                    """,
                    (email, subscription, quota, usage_current, int(is_admin), user_id),
                )
                conn.commit()
                st.success("User updated successfully")
    
    # Model Configuration Tab
    with admin_tabs[2]:
        st.markdown("### Model Configuration")
        
        config_tab1, config_tab2 = st.tabs(
            ["Transcription Model", "Content Processing Model"]
        )
        
        with config_tab1:
            st.subheader("Transcription Model Settings")
            
            # Display current default
            st.markdown(
                f"**Current default:** {st.session_state.transcription_provider}/{st.session_state.transcription_model}"
            )
            
            transcription_provider = st.selectbox(
                "Transcription Provider",
                options=["OpenAI"],  # Currently only OpenAI supports transcription
                index=0,
            )
            
            transcription_models = ["whisper-1"]
            if transcription_provider == "OpenAI":
                transcription_models = ["whisper-1"]
            
            transcription_model = st.selectbox(
                "Transcription Model", options=transcription_models, index=0
            )
            
            if st.button("Set as Default Transcription Model"):
                st.session_state.transcription_provider = transcription_provider
                st.session_state.transcription_model = transcription_model
                
                # Save to database for persistence (if you want to implement this)
                # conn.execute("UPDATE system_settings SET value = ? WHERE key = 'default_transcription_provider'", (transcription_provider,))
                # conn.execute("UPDATE system_settings SET value = ? WHERE key = 'default_transcription_model'", (transcription_model,))
                # conn.commit()
                
                st.success(
                    f"Default transcription model set to {transcription_provider}/{transcription_model}"
                )
        
        with config_tab2:
            st.subheader("Content Processing Model Settings")
            
            # Display current default
            st.markdown(
                f"**Current default:** {st.session_state.ai_provider}/{st.session_state.ai_model}"
            )
            
            ai_provider = st.selectbox(
                "AI Provider",
                options=["Anthropic", "OpenAI"],
                index=0 if st.session_state.ai_provider == "Anthropic" else 1,
            )
            
            # Show different model options based on provider
            if ai_provider == "Anthropic":
                anthropic_models = get_available_models("Anthropic")
                default_index = (
                    anthropic_models.index("claude-3-7-sonnet-20250219")
                    if "claude-3-7-sonnet-20250219" in anthropic_models
                    else 0
                )
                ai_model = st.selectbox(
                    "AI Model", options=anthropic_models, index=default_index
                )
            else:  # OpenAI
                openai_models = get_available_models("OpenAI")
                default_index = 0
                ai_model = st.selectbox(
                    "AI Model", options=openai_models, index=default_index
                )
            
            if st.button("Set as Default Content Processing Model"):
                st.session_state.ai_provider = ai_provider
                st.session_state.ai_model = ai_model
                
                # Save to database for persistence (if you want to implement this)
                # conn.execute("UPDATE system_settings SET value = ? WHERE key = 'default_ai_provider'", (ai_provider,))
                # conn.execute("UPDATE system_settings SET value = ? WHERE key = 'default_ai_model'", (ai_model,))
                # conn.commit()
                
                st.success(
                    f"Default content processing model set to {ai_provider}/{ai_model}"
                )
    
    # App Configuration Tab
    with admin_tabs[3]:
        st.markdown("### App Configuration")
        
        # User Profile Settings
        st.subheader("User Profile Settings")
        
        # Use a string value for the selectbox, NOT updating session state directly
        selected_user = st.selectbox(
            "User Profile",
            options=get_available_users(),
            index=(
                get_available_users().index(
                    st.session_state.get("user_profile_sidebar", "Default")
                )
                if st.session_state.get("user_profile_sidebar", "Default")
                in get_available_users()
                else 0
            ),
            key="admin_user_profile",  # Different key to avoid collision
        )
        
        # Only update session state when button is clicked
        if st.button("Set as Default User Profile"):
            st.session_state.user_profile_sidebar = selected_user
            st.success(f"Default user profile set to {selected_user}")
        
        # Custom Prompts Configuration
        st.subheader("Custom Prompts")
        users_prompts = load_prompts()
        
        # Call the fixed configure_prompts function that handles tuples correctly
        users_prompts = configure_prompts(selected_user, users_prompts)
    
    conn.close()
    
    
# Show terms and privacy
def show_legal_page():
    """Show terms of service and privacy policy"""
    st.markdown("## Legal Information")
    
    tab1, tab2 = st.tabs(["Terms of Service", "Privacy Policy"])
    
    with tab1:
        st.markdown(
            """
        # WhisperForge Terms of Service
        
        Last updated: April 1, 2024
        
        ## 1. Acceptance of Terms
        
        By accessing or using WhisperForge ("the Service"), you agree to be bound by these Terms of Service. If you do not agree to these terms, please do not use the Service.
        
        ## 2. Description of Service
        
        WhisperForge is an AI-powered audio transcription and content generation tool that provides transcription services, content analysis, and content creation capabilities.
        
        ## 3. User Accounts
        
        To use certain features of the Service, you must register for an account. You agree to provide accurate information and to keep this information updated. You are responsible for maintaining the confidentiality of your account credentials and for all activities that occur under your account.
        
        ## 4. Usage Limitations
        
        Different subscription tiers have different usage limits. You agree not to exceed the limits of your subscription tier.
        
        ## 5. API Keys and Third-Party Services
        
        The Service allows you to use your own API keys for third-party services such as OpenAI, Anthropic, and Notion. You are responsible for:
        - Obtaining and maintaining valid API keys
        - Any costs associated with your use of these third-party services
        - Complying with the terms of service of these third-party providers
        
        ## 6. Content Ownership
        
        You retain ownership of all content you upload or create using the Service. However, you grant WhisperForge a non-exclusive license to use, store, and process your content for the purpose of providing the Service.
        
        ## 7. Prohibited Uses
        
        You agree not to use the Service for any illegal or prohibited purpose, including but not limited to:
        - Violating intellectual property rights
        - Distributing malware or engaging in phishing
        - Generating harmful, abusive, or deceptive content
        - Attempting to gain unauthorized access to the system
        
        ## 8. Termination
        
        WhisperForge reserves the right to terminate or suspend your account at any time for violation of these terms or for any other reason.
        
        ## 9. Changes to Terms
        
        WhisperForge may modify these terms at any time. Continued use of the Service after such changes constitutes your acceptance of the new terms.
        
        ## 10. Contact
        
        If you have any questions about these Terms, please contact us at support@whisperforge.ai.
        """
        )
    
    with tab2:
        st.markdown(
            """
        # WhisperForge Privacy Policy
        
        Last updated: April 1, 2024
        
        ## 1. Information We Collect
        
        We collect the following types of information:
        
        ### 1.1 Account Information
        - Email address
        - Hashed password
        - Subscription details
        
        ### 1.2 Content Data
        - Audio files you upload for transcription
        - Transcriptions and content generated from your audio
        - API keys you provide for third-party services
        
        ### 1.3 Usage Information
        - Features you use
        - Time spent using the Service
        - Error logs and performance data
        
        ## 2. How We Use Your Information
        
        We use your information to:
        - Provide and improve the Service
        - Process payments and manage subscriptions
        - Communicate with you about your account
        - Monitor and analyze usage patterns
        
        ## 3. Data Security
        
        We implement reasonable security measures to protect your information. Your API keys are encrypted in our database. We do not store your audio files longer than necessary to process them.
        
        ## 4. Third-Party Services
        
        When you use your own API keys, your content may be processed by these third-party services according to their privacy policies:
        - OpenAI (for transcription and AI processing)
        - Anthropic (for AI processing)
        - Notion (for content export)
        
        ## 5. Cookies and Tracking
        
        We use cookies and similar technologies to track usage of our Service and remember your preferences.
        
        ## 6. Your Rights
        
        Depending on your location, you may have rights to:
        - Access your personal information
        - Correct inaccurate information
        - Delete your data
        - Object to processing
        - Export your data
        
        ## 7. Changes to Privacy Policy
        
        We may update this privacy policy from time to time. We will notify you of any significant changes.
        
        ## 8. Contact
        
        If you have questions about our privacy practices, please contact us at privacy@whisperforge.ai.
        """
        )


def direct_transcribe_audio(audio_file_path, api_key=None):
    """
    Transcribe audio directly using the OpenAI API without relying on the OpenAI Python client.
    This is a fallback method to use when the OpenAI client has initialization issues.
    """
    logger.debug(f"Starting direct transcription of {audio_file_path}")
    
    if not api_key:
        api_key = get_api_key_for_service("openai")
        if not api_key:
            logger.error("No OpenAI API key available")
            return "Error: OpenAI API key is not provided or configured"
    
    try:
        import requests
        
        logger.debug("Preparing API request for direct transcription")
        url = "https://api.openai.com/v1/audio/transcriptions"
        headers = {"Authorization": f"Bearer {api_key}"}
        
        # Check file exists
        if not os.path.exists(audio_file_path):
            logger.error(f"Audio file not found: {audio_file_path}")
            return "Error: Audio file not found"
        
        # Log file details
        file_size = os.path.getsize(audio_file_path)
        logger.debug(f"Audio file size: {file_size/1024/1024:.2f} MB")
        
        # Open the file in binary mode
        with open(audio_file_path, "rb") as audio_file:
            files = {
                "file": (os.path.basename(audio_file_path), audio_file, "audio/mpeg"),
                "model": (None, "whisper-1"),
            }
            
            logger.debug("Sending request to OpenAI API")
            response = requests.post(url, headers=headers, files=files, timeout=120)
            
            # Check for errors
            if response.status_code != 200:
                logger.error(f"API Error: {response.status_code} - {response.text}")
                return f"Error: API returned status code {response.status_code}: {response.text}"
            
            # Parse the response
            try:
                result = response.json()
                logger.debug("Successfully received transcription from API")
                return result.get("text", "")
            except Exception as parse_error:
                logger.error(f"Error parsing API response: {str(parse_error)}")
                return f"Error parsing API response: {str(parse_error)}"
                
    except Exception as e:
        logger.exception("Exception in direct_transcribe_audio:")
        return f"Error transcribing audio directly: {str(e)}"


def direct_anthropic_completion(
    prompt, api_key=None, model="claude-3-7-sonnet-20250219"
):
    """
    Generate content directly using the Anthropic API without relying on the Anthropic client.
    This is a fallback method to use when the Anthropic client has initialization issues.
    """
    logger.debug(f"Starting direct Anthropic API call for model: {model}")
    
    if not api_key:
        api_key = get_api_key_for_service("anthropic")
        if not api_key:
            logger.error("No Anthropic API key available")
            return "Error: Anthropic API key is not provided or configured"
    
    try:
        import requests
        import json
        
        logger.debug("Preparing API request for Anthropic")
        url = "https://api.anthropic.com/v1/messages"
        headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        
        # Prepare the payload
        payload = {
            "model": model,
            "max_tokens": 1500,
            "messages": [{"role": "user", "content": prompt}],
        }
        
        logger.debug(f"Payload prepared, content length: {len(prompt)} characters")
        
        # Send the request
        logger.debug("Sending request to Anthropic API")
        response = requests.post(url, headers=headers, json=payload, timeout=120)
        
        # Check for errors
        if response.status_code != 200:
            logger.error(f"API Error: {response.status_code} - {response.text}")
            return f"Error: API returned status code {response.status_code}: {response.text}"
        
        # Parse the response
        try:
            result = response.json()
            logger.debug("Successfully received content from Anthropic API")
            # Extract the content
            if "content" in result and len(result["content"]) > 0:
                return result["content"][0]["text"]
            else:
                logger.error("Response did not contain expected content")
                return "Error: Response did not contain expected content"
        except Exception as parse_error:
            logger.error(f"Error parsing API response: {str(parse_error)}")
            return f"Error parsing Anthropic API response: {str(parse_error)}"
            
    except Exception as e:
        logger.exception("Exception in direct_anthropic_completion:")
        return f"Error generating content directly with Anthropic: {str(e)}"


def export_to_notion():
    """Export content to Notion using the create_content_notion_entry function"""
    try:
        logger.debug("Starting export to Notion")
        
        # Gather content
        title = st.session_state.get("file_name", "Untitled Audio")
        transcript = st.session_state.get("transcript", "")
        wisdom = st.session_state.get("wisdom", None)
        outline = st.session_state.get("outline", None)
        social = st.session_state.get("social", None)
        image_prompts = st.session_state.get("image_prompts", None)
        article = st.session_state.get("article", None)
        
        # Create content in Notion
        result = create_content_notion_entry(
            title=title,
            transcript=transcript,
            wisdom=wisdom,
            outline=outline,
            social=social,
            image_prompts=image_prompts,
            article=article,
        )
        
        if result:
            logger.debug(f"Successfully exported to Notion: {result}")
            return result
        else:
            logger.error("Failed to export to Notion")
            st.error(
                "Failed to export to Notion. Please check your Notion API configuration."
            )
            return None
    
    except Exception as e:
        logger.exception("Error in export_to_notion:")
        st.error(f"Error exporting to Notion: {str(e)}")
        return None


def direct_notion_save(
    title,
    transcript,
    wisdom=None,
    outline=None,
    social=None,
    image_prompts=None,
    article=None,
):
    """
    Save content directly to Notion API without relying on the notion_client library.
    """
    logger.debug(f"Starting direct Notion save for title: {title}")
    
    # Get API key and database ID
    api_key = get_api_key_for_service("notion")
    database_id = get_notion_database_id()
    
    if not api_key:
        logger.error("No Notion API key available")
        return {"error": "Error: Notion API key is not provided or configured"}
        
    if not database_id:
        logger.error("No Notion database ID available")
        return {"error": "Error: Notion database ID is not provided or configured"}
    
    try:
        import requests
        import json
        from datetime import datetime
        
        # Generate AI title if none provided or generic title
        if (
            not title
            or title == "Untitled Audio"
            or title == "Untitled Content"
            or title.startswith("WhisperForge")
        ):
            logger.debug("Generating AI title for Notion page")
            ai_title = generate_short_title(transcript)
            title = ai_title
            logger.debug(f"Generated title: {title}")
        
        # Generate tags for the content
        logger.debug("Generating tags for Notion page")
        content_tags = generate_content_tags(transcript, wisdom)
        logger.debug(f"Generated tags: {content_tags}")
        
        logger.debug("Preparing API request for Notion")
        url = "https://api.notion.com/v1/pages"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28",
        }
        
        # Initialize content blocks
        children = []
        
        # Add summary if wisdom is available
        if wisdom:
            children.append(
                {
                "object": "block",
                "type": "callout",
                "callout": {
                        "rich_text": [
                            {"type": "text", "text": {"content": wisdom[:2000]}}
                        ],
                    "color": "purple_background",
                        "icon": {"type": "emoji", "emoji": "💜"},
                    },
                }
            )
        
        # Add transcript toggle
        if transcript:
            # Split transcript into chunks to respect Notion's block size limit
            transcript_chunks = [
                transcript[i : i + 2000] for i in range(0, len(transcript), 2000)
            ]
            
            # Create transcript toggle
            transcript_blocks = [
                {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"type": "text", "text": {"content": chunk}}]
                    },
                }
                for chunk in transcript_chunks
            ]
            
            children.append(
                {
                "object": "block",
                "type": "toggle",
                "toggle": {
                        "rich_text": [
                            {"type": "text", "text": {"content": "▶️ Transcription"}}
                        ],
                        "children": transcript_blocks,
                    },
                }
            )
        
        # Add wisdom toggle
        if wisdom:
            children.append(
                {
                "object": "block",
                "type": "toggle",
                "toggle": {
                        "rich_text": [
                            {"type": "text", "text": {"content": "▶️ Wisdom"}}
                        ],
                        "children": [
                            {
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {
                                    "rich_text": [
                                        {
                                            "type": "text",
                                            "text": {"content": wisdom[:2000]},
                        }
                                    ]
                                },
                }
                        ],
                    },
                }
            )
        
        # Add outline toggle
        if outline:
            children.append(
                {
                "object": "block",
                "type": "toggle",
                "toggle": {
                        "rich_text": [
                            {"type": "text", "text": {"content": "▶️ Outline"}}
                        ],
                        "children": [
                            {
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {
                                    "rich_text": [
                                        {
                                            "type": "text",
                                            "text": {"content": outline[:2000]},
                        }
                                    ]
                                },
                }
                        ],
                    },
                }
            )
        
        # Add metadata section
        children.append(
            {
            "object": "block",
            "type": "heading_2",
            "heading_2": {
                "rich_text": [{"type": "text", "text": {"content": "Metadata"}}]
                },
            }
        )
        
        children.append(
            {
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [
                    {"type": "text", "text": {"content": "Created with "}},
                        {
                            "type": "text",
                            "text": {"content": "WhisperForge"},
                            "annotations": {"bold": True, "color": "purple"},
                        },
                    ]
                },
            }
        )
        
        # Add tags to metadata
        if content_tags:
            tags_text = ", ".join(content_tags)
            children.append(
                {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [
                            {
                                "type": "text",
                                "text": {"content": "Tags: "},
                                "annotations": {"bold": True},
                            },
                            {"type": "text", "text": {"content": tags_text}},
                        ]
                    },
                }
            )
        
        # Prepare the payload
        payload = {
            "parent": {"database_id": database_id},
            "properties": {
                "Name": {"title": [{"text": {"content": title}}]},
                "Created": {"date": {"start": datetime.now().isoformat()}},
            },
            "children": children,
        }
        
        # Add tags to properties if the database has a multi-select Tags property
        if content_tags:
            payload["properties"]["Tags"] = {
                "multi_select": [{"name": tag} for tag in content_tags]
            }
        
        logger.debug(f"Payload prepared with {len(children)} content blocks")
        
        # Send the request
        logger.debug("Sending request to Notion API")
        response = requests.post(url, headers=headers, json=payload)
        
        # Check for errors
        if response.status_code != 200:
            logger.error(f"API Error: {response.status_code} - {response.text}")
            return {
                "error": f"Error: API returned status code {response.status_code}: {response.text}"
            }
        
        # Parse the response
        result = response.json()
        logger.debug("Successfully saved page to Notion")
        
        return {"url": result.get("url", ""), "id": result.get("id", "")}
            
    except Exception as e:
        logger.exception("Exception in direct_notion_save:")
        return {"error": f"Error saving to Notion: {str(e)}"}


def is_admin_user():
    """Check if the current user is an admin"""
    try:
        conn = get_db_connection()
        is_admin = conn.execute(
            "SELECT is_admin FROM users WHERE id = ?", (st.session_state.user_id,)
        ).fetchone()
        conn.close()
        
        return is_admin and is_admin[0]
    except Exception:
        return False


def create_custom_header():
    """Create header with working navigation using session utils"""
    # Note: get_page and set_page should already be imported at the top of the file
    
    # Create the title part
    st.markdown(
        f"""
    <div class="header-container">
        <div class="header-title">WhisperForge // Control_Center</div>
        <div class="header-date">{datetime.now().strftime('%Y-%m-%d %H:%M')}</div>
    </div>
    """,
        unsafe_allow_html=True,
    )
    
    # Get current page
    current_page = get_page()
    
    # Create navigation using buttons
    cols = st.columns([1, 1, 1, 1, 1, 1, 1])
    
    # Define nav items - list of (label, page_id) tuples
    nav_items = [
        ("Home", "home"),
        ("API Keys", "api"),
        ("Usage", "usage"),
        ("User Config", "config"),
        ("Templates", "templates"),
        ("Admin", "admin"),
        ("Legal", "legal"),
    ]
    
    # Create navigation buttons
    for i, (label, page_id) in enumerate(nav_items):
        with cols[i]:
            button_type = "primary" if current_page == page_id else "secondary"
            if st.button(
                label, key=f"nav_{page_id}", type=button_type, use_container_width=True
            ):
                set_page(page_id)


def load_js():
    """Load JavaScript files"""
    # Load cookie consent JavaScript
    with open("static/js/cookie-consent.js") as f:
        st.markdown(f"<script>{f.read()}</script>", unsafe_allow_html=True)
        
    # Load UI interactions JavaScript
    with open("static/js/ui-interactions.js") as f:
        st.markdown(f"<script>{f.read()}</script>", unsafe_allow_html=True)
        
    # Load diagnostic tool in development environment
    if os.environ.get("ENVIRONMENT") != "production":
        try:
            with open("static/js/diagnostic.js") as f:
                st.markdown(f"<script>{f.read()}</script>", unsafe_allow_html=True)
        except FileNotFoundError:
            # Diagnostic tool is optional
            pass


# Show cookie consent banner if necessary
def show_cookie_banner():
    if st.session_state.show_cookie_banner:
        cookie_banner_html = """
        <div class="cookie-banner">
            <div>
                We use cookies to improve your experience. By continuing, you consent to our use of cookies.
                <a href="?page=legal">Learn more</a>
            </div>
            <div class="cookie-banner-buttons">
                <button>Accept</button>
            </div>
        </div>
        """
        st.markdown(cookie_banner_html, unsafe_allow_html=True)


def transcribe_with_whisper(file_path):
    """Transcribe an audio file directly using OpenAI's Whisper API"""
    try:
        api_key = get_api_key_for_service("openai")
        if not api_key:
            error_msg = "OpenAI API key is not configured"
            logger.error(error_msg)
            st.error(f"❌ {error_msg}. Please set up your API key in the settings.")
            return ""
        
        logger.info(f"Starting direct transcription of file: {file_path}")
        
        # Verify file exists and is readable
        if not os.path.exists(file_path):
            error_msg = f"File not found: {file_path}"
            logger.error(error_msg)
            st.error(f"❌ {error_msg}")
            return ""
        
        # Check file size
        file_size = os.path.getsize(file_path)
        if file_size == 0:
            error_msg = "Audio file is empty"
            logger.error(error_msg)
            st.error(f"❌ {error_msg}")
            return ""
        
        # Create progress indicators
        progress_text = st.empty()
        progress_text.text("Preparing audio for transcription...")
        progress_bar = st.progress(0)
        
        # Progress update function for use in both methods
        def update_progress(progress, message):
            progress_bar.progress(progress)
            progress_text.text(message)
        
        # Try direct API call first (more robust method)
        try:
            update_progress(0.2, "Uploading audio to OpenAI API...")
            
            # Use requests for direct API call
            import requests
            import json
            
            # Prepare the API request
            headers = {"Authorization": f"Bearer {api_key}"}
            
            url = "https://api.openai.com/v1/audio/transcriptions"
            
            # Set transcription options
            options = {}
            
            # Check for language code in session state
            if (
                st.session_state.get("language_code")
                and st.session_state.get("language_code") != "auto"
            ):
                options["language"] = st.session_state.get("language_code")
                logger.debug(f"Setting language to: {options['language']}")
            
            # Check for response format preference
            response_format = st.session_state.get("response_format", "text")
            options["response_format"] = response_format
            
            # Get model preference or use default
            model = st.session_state.get("transcription_model", "whisper-1")
            
            # Create form data
            files = {"file": open(file_path, "rb")}
            
            data = {"model": model, **options}
            
            # Attempt the API call
            update_progress(0.4, "Sending request to OpenAI API...")
            logger.debug(
                f"Making OpenAI API request with model: {model}, options: {options}"
            )
            
            response = requests.post(url, headers=headers, files=files, data=data)
            
            # Process the response
            update_progress(0.8, "Processing API response...")
            
            if response.status_code == 200:
                if response_format == "text":
                    transcript = response.text
                else:
                    result = response.json()
                    transcript = result.get("text", "")
                
                update_progress(1.0, "Transcription complete!")
                logger.info(
                    f"Transcription successful, received {len(transcript)} characters"
                )
                return transcript
            
            elif response.status_code == 429:
                error_msg = "OpenAI API rate limit exceeded. Please try again later."
                logger.error(f"API Rate Limit (429): {error_msg}")
                raise Exception(error_msg)
            
            elif response.status_code == 401:
                error_msg = "Invalid API key. Please check your OpenAI API key."
                logger.error(f"API Authentication Error (401): {error_msg}")
                raise Exception(error_msg)
            
            else:
                # Try to parse error details
                try:
                    error_data = response.json()
                    error_msg = error_data.get("error", {}).get(
                        "message", "Unknown API error"
                    )
                except:
                    error_msg = (
                        f"API error (status {response.status_code}): {response.text}"
                    )
                
                logger.error(f"API Error: {error_msg}")
                raise Exception(error_msg)
        
        except requests.exceptions.RequestException as req_error:
            # If direct API call fails due to request issues, try OpenAI client library
            logger.warning(
                f"Direct API request failed: {str(req_error)}. Falling back to client library."
            )
            update_progress(0.3, "Direct API call failed, trying alternative method...")
            
            # Use OpenAI client library as fallback
            try:
                from openai import OpenAI
                
                # Create client
                client = OpenAI(api_key=api_key)
                
                update_progress(0.5, "Processing with OpenAI client...")
                
                # Set transcription options
                options = {}
                
                # Check for language code in session state
                if (
                    st.session_state.get("language_code")
                    and st.session_state.get("language_code") != "auto"
                ):
                    options["language"] = st.session_state.get("language_code")
                
                # Get model preference or use default
                model = st.session_state.get("transcription_model", "whisper-1")
                
                response_format = st.session_state.get("response_format", "text")
                
                # Make the API call
                with open(file_path, "rb") as audio_file:
                    update_progress(0.7, "Sending to OpenAI service...")
                    response = client.audio.transcriptions.create(
                        model=model,
                        file=audio_file,
                        response_format=response_format,
                        **options,
                    )
                
                update_progress(0.9, "Processing response...")
                
                # Extract transcript based on response format
                if response_format == "text":
                    transcript = response
                else:
                    transcript = response.text
                
                update_progress(1.0, "Transcription complete!")
                logger.info(
                    f"Client library transcription successful, received {len(transcript)} characters"
                )
                return transcript
            except Exception as client_error:
                logger.error(
                    f"Client library transcription failed: {str(client_error)}"
                )
                raise Exception(f"Transcription failed: {str(client_error)}")
        
        finally:
            # Clean up progress indicators
            progress_text.empty()
            progress_bar.empty()
    
    except Exception as e:
        error_msg = f"Error in transcribe_with_whisper: {str(e)}"
        logger.error(error_msg, exc_info=True)
        st.error(f"❌ {error_msg}")
        return f"[Error transcribing audio: {str(e)}]"


def show_user_config_page():
    """Show user configuration page for managing profiles and prompts"""
    st.title("User Configuration")
    
    # Get available users and prompts
    users, users_prompts = load_prompts()
    
    # Add tabs for different configuration sections
    config_tabs = st.tabs(["User Profiles", "Prompt Templates"])
    
    # Tab 1: User Profiles Management
    with config_tabs[0]:
        st.header("User Profiles")
        st.write(
            "Manage user profiles for different content generation styles and preferences."
        )
        
        # Current users list
        st.subheader("Current Profiles")
        user_table = {"Profile Name": [], "Custom Prompts": []}
        
        for user in users:
            # Count custom prompts
            if user in users_prompts:
                prompt_count = len(users_prompts[user])
            else:
                prompt_count = 0
                
            user_table["Profile Name"].append(user)
            user_table["Custom Prompts"].append(prompt_count)
        
        # Display user profiles as a table
        st.dataframe(user_table)
        
        # Create new profile
        st.subheader("Create New Profile")
        new_user = st.text_input(
            "New Profile Name",
            key="new_profile_name",
            help="Enter a name for the new user profile. Use only letters, numbers, and underscores.",
        )
        
        if st.button("Create Profile", key="create_profile_btn"):
            if not new_user:
                st.error("Please enter a valid profile name")
            elif not re.match(r"^[a-zA-Z0-9_]+$", new_user):
                st.error(
                    "Profile name can only contain letters, numbers, and underscores"
                )
            elif new_user in users:
                st.error(f"Profile '{new_user}' already exists")
            else:
                # Create user directories
                user_dir = os.path.join("prompts", new_user)
                
                try:
                    os.makedirs(user_dir, exist_ok=True)
                    st.success(f"Created new profile: {new_user}")
                    st.session_state.user_profile_sidebar = new_user
                    st.rerun()
                except Exception as e:
                    st.error(f"Error creating profile: {str(e)}")
    
    # Tab 2: Prompt Template Management
    with config_tabs[1]:
        st.header("Prompt Templates")
        st.write("Customize prompt templates for different content generation tasks.")
        
        # Select user profile
        selected_user = st.selectbox(
            "Select Profile", options=users, key="prompt_profile_select"
        )
        
        if selected_user:
            # Use the existing configure_prompts function
            configure_prompts(selected_user, users_prompts)
            
            # Add explanation of prompt variables
            with st.expander("Prompt Template Help"):
                st.markdown(
                    """
                ### Prompt Template Variables
                
                Your prompt templates can include the following variables which will be replaced with actual content:
                
                - `{transcript}` - The full transcript text
                
                ### Prompt Template Format
                
                For best results, structure your prompts as follows:
                
                ```
                ## Instructions
                Instructions for the AI on how to approach the task.
                
                ## Context
                Any contextual information about your style, preferences, or requirements.
                
                ## Prompt
                The actual prompt that will be sent to the AI.
                ```
                
                Only the section after "## Prompt" is required, but adding instructions and context helps organize your templates.
                """
                )


# Create the prompts table
def create_prompts_table():
    conn = get_db_connection()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS prompts (
            id INTEGER PRIMARY KEY,
            user_id TEXT NOT NULL,
            prompt_type TEXT NOT NULL,
            content TEXT NOT NULL,
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, prompt_type)
        )
    """
    )
    conn.commit()
    conn.close()


# Get prompt from database or filesystem
def get_prompt(user_id, prompt_type):
    """Get active prompt for user, falling back to default if none exists"""
    conn = get_db_connection()
    row = conn.execute(
        "SELECT content FROM prompts WHERE user_id = ? AND prompt_type = ? AND is_active = 1",
        (user_id, prompt_type),
    ).fetchone()
    conn.close()
    
    if row:
        return row["content"]
    else:
        # Fall back to default prompt from filesystem
        return load_default_prompt(prompt_type)
        
        
def save_prompt(user_id, prompt_type, content):
    """Save or update a prompt"""
    conn = get_db_connection()
    conn.execute(
        """INSERT INTO prompts (user_id, prompt_type, content) 
           VALUES (?, ?, ?)
           ON CONFLICT(user_id, prompt_type) 
           DO UPDATE SET content = ?, updated_at = CURRENT_TIMESTAMP""",
        (user_id, prompt_type, content, content),
    )
    conn.commit()
    conn.close()
    
    # Also save to filesystem for backward compatibility
    user_dir = os.path.join("prompts", user_id)
    os.makedirs(user_dir, exist_ok=True)
    
    with open(os.path.join(user_dir, f"{prompt_type}.md"), "w") as f:
        f.write(content)


def load_default_prompt(prompt_type):
    """Load default prompt from filesystem"""
    default_file = f"prompts/default_user/{prompt_type}.md"
    try:
        with open(default_file, "r") as f:
            return f.read()
    except Exception as e:
        # If we can't find the file, return an empty string
        return ""


def show_templates_page():
    """Show the templates management page"""
    st.title("Template Management")
    
    # Get current user profile
    selected_user = st.session_state.get("user_profile_sidebar", "default_user")
    
    # Display current user profile
    st.info(f"Editing templates for profile: **{selected_user}**")
    
    # Create template categories
    categories = {
        "Content Creation": ["wisdom_extraction", "outline_creation", "summary"],
        "Social Media": ["social_media"],
        "Image Generation": ["image_prompts"],
    }
    
    # Create category tabs
    category_tabs = st.tabs(list(categories.keys()))
    
    # Load prompts
    users, users_prompts = load_prompts()
    
    # Handle each category
    for i, (category, template_types) in enumerate(categories.items()):
        with category_tabs[i]:
            template_type = st.selectbox(
                "Select template type", template_types, key=f"template_type_{category}"
            )
            
            current_prompt = get_custom_prompt(
                selected_user, template_type, users_prompts, DEFAULT_PROMPTS
            )
            
            new_prompt = st.text_area(
                "Edit template",
                value=current_prompt,
                height=400,
                key=f"template_editor_{category}",
            )
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Save Template", key=f"save_{category}"):
                    # Create user directory if needed
                    user_dir = os.path.join("prompts", selected_user)
                    os.makedirs(user_dir, exist_ok=True)
                    
                    # Save the prompt
                    with open(os.path.join(user_dir, f"{template_type}.md"), "w") as f:
                        f.write(new_prompt)
                    
                    st.success("Template saved successfully!")
            
            with col2:
                if st.button("Reset to Default", key=f"reset_{category}"):
                    # Get default prompt
                    default_file = f"prompts/default_user/{template_type}.md"
                    try:
                        with open(default_file, "r") as f:
                            default_content = f.read()
                    except:
                        default_content = ""
                    
                    # Save to user directory
                    user_dir = os.path.join("prompts", selected_user)
                    os.makedirs(user_dir, exist_ok=True)
                    
                    with open(os.path.join(user_dir, f"{template_type}.md"), "w") as f:
                        f.write(default_content)
                    
                    st.success("Reset to default template")
                    st.rerun()


def get_client_for_provider(ai_provider):
    """Get the appropriate client for the AI provider.

    Args:
        ai_provider (str): The AI provider name (openai, anthropic, etc.)

    Returns:
        object: The client object for the specified provider

    Raises:
        ValueError: If provider is invalid or not supported
    """
    if ai_provider == "openai":
        return get_openai_client()
    elif ai_provider == "anthropic":
        return get_anthropic_client()
    elif ai_provider == "grok":
        # Assuming this function exists
        return get_grok_client()
    else:
        raise ValueError(f"Unsupported AI provider: {ai_provider}")


def run_editor_step(draft_text, ai_provider, model, user_id=None, step_name="unknown"):
    """Run the editor step on a draft to get feedback and suggestions.

    Args:
        draft_text (str): The draft text to edit
        ai_provider (str): The AI provider to use
        model (str): The model to use
        user_id (str, optional): User ID for logging
        step_name (str): Name of the step for logging

    Returns:
        dict: {"feedback_notes": editor_feedback, "revised_draft": edited_text, "error": error_message if any}
    """
    # Use default user ID if none provided
    if user_id is None:
        user_id = "anonymous"

    # Get session ID
    session_id = get_or_create_session_id()

    # Input validation
    if not draft_text or not isinstance(draft_text, str):
        error_result = {
            "feedback_notes": "",
            "revised_draft": "",
            "error": "Invalid draft text",
        }
        # Log the error
        log_generation_step(
            user_id,
            session_id,
            step_name,
            {"stage": "editor_input_validation", "error": "Invalid draft text"},
        )
        return error_result

    # Log the input
    log_generation_step(
        user_id,
        session_id,
        step_name,
        {"stage": "editor_input", "draft_text": draft_text},
    )

    try:
        client = get_client_for_provider(ai_provider)

        # Read the editor prompt
        editor_prompt_path = "prompts/editor_prompt.md"
        with open(editor_prompt_path, "r") as f:
            editor_prompt = f.read()

        # Call the AI with the editor prompt and draft text
        response = client.generate(editor_prompt, draft_text, model)

        # Log the raw response
        log_generation_step(
            user_id,
            session_id,
            step_name,
            {"stage": "editor_raw_response", "response": response},
        )

        # Parse the response to extract feedback and revised draft
        try:
            feedback_parts = response.split("FEEDBACK:", 1)
            if len(feedback_parts) < 2:
                error_result = {
                    "feedback_notes": "",
                    "revised_draft": response,
                    "error": "Could not parse editor response",
                }
                # Log the parsing error
                log_generation_step(
                    user_id,
                    session_id,
                    step_name,
                    {
                        "stage": "editor_parse_error",
                        "error": "Could not parse editor response",
                        "response": response,
                    },
                )
                return error_result

            parts = feedback_parts[1].split("REVISED_DRAFT:", 1)
            feedback_notes = parts[0].strip()
            revised_draft = parts[1].strip() if len(parts) > 1 else ""

            result = {
                "feedback_notes": feedback_notes,
                "revised_draft": revised_draft,
                "error": None,
            }

            # Log the successful result
            log_generation_step(
                user_id,
                session_id,
                step_name,
                {
                    "stage": "editor_success",
                    "feedback_notes": feedback_notes,
                    "revised_draft": revised_draft,
                },
            )

            return result
        except Exception as parse_error:
            error_result = {
                "feedback_notes": "",
                "revised_draft": response,
                "error": f"Error parsing editor response: {str(parse_error)}",
            }
            # Log the parsing exception
            log_generation_step(
                user_id,
                session_id,
                step_name,
                {
                    "stage": "editor_parse_exception",
                    "error": str(parse_error),
                    "response": response,
                },
            )
            return error_result

    except Exception as e:
        error_result = {
            "feedback_notes": "",
            "revised_draft": "",
            "error": f"Editor step failed: {str(e)}",
        }
        # Log the general exception
        log_generation_step(
            user_id,
            session_id,
            step_name,
            {"stage": "editor_exception", "error": str(e)},
        )
        return error_result


def process_content(
    text,
    ai_provider,
    model,
    editor_enabled=False,
    wisdom_container=None,
    outline_container=None,
    social_container=None,
    image_container=None,
    article_container=None,
    title_container=None,
    seo_container=None,
    user_id=None,
):
    """Process content through the full generation pipeline with comprehensive error handling.

    Args:
        text (str): Source transcript text
        ai_provider (str): AI provider name (openai, anthropic, etc.)
        model (str): Model name to use
        editor_enabled (bool): Whether to use editor review step
        wisdom_container: Optional UI container for wisdom output
        outline_container: Optional UI container for outline output
        social_container: Optional UI container for social content
        image_container: Optional UI container for image prompts
        article_container: Optional UI container for article output
        title_container: Optional UI container for title output
        seo_container: Optional UI container for SEO metadata
        user_id (str, optional): User ID for logging

    Returns:
        dict: Results containing all generated content with any error messages
    """
    # Use default user ID if none provided
    if user_id is None:
        # Try to get the user ID from the session
        user_id = st.session_state.get("user_id", "anonymous")

    # Get session ID
    session_id = get_or_create_session_id()

    # Initialize results dictionary with error tracking
    results = {"success": True, "error": None, "stage_failed": None}

    # Log the process start
    log_generation_step(
        user_id,
        session_id,
        "process_content",
        {
            "stage": "process_start",
            "text_length": len(text) if text else 0,
            "ai_provider": ai_provider,
            "model": model,
            "editor_enabled": editor_enabled,
        },
    )

    # Input validation
    if not text or not isinstance(text, str):
        results["success"] = False
        results["error"] = "Invalid input text"
        log_generation_step(
            user_id,
            session_id,
            "process_content",
            {"stage": "input_validation_error", "error": "Invalid input text"},
        )
        return results

    if not ai_provider or not model:
        results["success"] = False
        results["error"] = "Missing AI provider or model"
        log_generation_step(
            user_id,
            session_id,
            "process_content",
            {
                "stage": "input_validation_error",
                "error": "Missing AI provider or model",
            },
        )
        return results

    try:
        # Stage 1: Generate title
        if title_container:
            title_container.info("Generating title...")

        title_result = generate_title(text, ai_provider, model, user_id=user_id)
        if title_result.get("error"):
            results["success"] = False
            results["error"] = f"Title generation failed: {title_result['error']}"
            results["stage_failed"] = "title"
            log_generation_step(
                user_id,
                session_id,
                "process_content",
                {"stage": "title_generation_error", "error": title_result["error"]},
            )
            return results

        results["title"] = title_result["title"]
        if title_container:
            title_container.success("Title generated")

        # Stage 2: Generate wisdom insights
        if wisdom_container:
            wisdom_container.info("Generating wisdom insights...")

        wisdom_result = generate_wisdom(
            text, ai_provider, model, editor_enabled=editor_enabled, user_id=user_id
        )
        if wisdom_result.get("error"):
            results["success"] = False
            results["error"] = f"Wisdom generation failed: {wisdom_result['error']}"
            results["stage_failed"] = "wisdom"
            log_generation_step(
                user_id,
                session_id,
                "process_content",
                {"stage": "wisdom_generation_error", "error": wisdom_result["error"]},
            )
            return results

        results["wisdom"] = wisdom_result["wisdom"]
        results["wisdom_feedback"] = wisdom_result.get("editor_feedback", "")
        if wisdom_container:
            wisdom_container.success("Wisdom insights generated")

        # Stage 3: Generate outline
        if outline_container:
            outline_container.info("Generating content outline...")

        outline_result = generate_outline(
            text,
            results["wisdom"],
            ai_provider,
            model,
            editor_enabled=editor_enabled,
            user_id=user_id,
        )
        if outline_result.get("error"):
            results["success"] = False
            results["error"] = f"Outline generation failed: {outline_result['error']}"
            results["stage_failed"] = "outline"
            log_generation_step(
                user_id,
                session_id,
                "process_content",
                {"stage": "outline_generation_error", "error": outline_result["error"]},
            )
            return results

        results["outline"] = outline_result["outline"]
        results["outline_feedback"] = outline_result.get("editor_feedback", "")
        if outline_container:
            outline_container.success("Content outline generated")

        # Stage 4: Generate social content
        if social_container:
            social_container.info("Generating social media content...")

        social_result = generate_social_content(
            results["wisdom"],
            results["outline"],
            ai_provider,
            model,
            editor_enabled=editor_enabled,
            user_id=user_id,
        )
        if social_result.get("error"):
            results["success"] = False
            results["error"] = (
                f"Social content generation failed: {social_result['error']}"
            )
            results["stage_failed"] = "social_content"
            log_generation_step(
                user_id,
                session_id,
                "process_content",
                {
                    "stage": "social_content_generation_error",
                    "error": social_result["error"],
                },
            )
            return results

        results["social"] = social_result["social"]
        results["social_feedback"] = social_result.get("editor_feedback", "")
        if social_container:
            social_container.success("Social media content generated")

        # Stage 5: Generate image prompts
        if image_container:
            image_container.info("Generating image prompts...")

        image_result = generate_image_prompts(
            results["wisdom"],
            results["outline"],
            ai_provider,
            model,
            editor_enabled=editor_enabled,
            user_id=user_id,
        )
        if image_result.get("error"):
            results["success"] = False
            results["error"] = (
                f"Image prompts generation failed: {image_result['error']}"
            )
            results["stage_failed"] = "image_prompts"
            log_generation_step(
                user_id,
                session_id,
                "process_content",
                {
                    "stage": "image_prompts_generation_error",
                    "error": image_result["error"],
                },
            )
            return results

        results["image_prompts"] = image_result["image_prompts"]
        results["image_feedback"] = image_result.get("editor_feedback", "")
        if image_container:
            image_container.success("Image prompts generated")

        # Stage 6: Generate article
        if article_container:
            article_container.info("Generating article...")

        article_result = generate_article(
            text,
            results["wisdom"],
            results["outline"],
            ai_provider,
            model,
            editor_enabled=editor_enabled,
            user_id=user_id,
        )
        if article_result.get("error"):
            results["success"] = False
            results["error"] = f"Article generation failed: {article_result['error']}"
            results["stage_failed"] = "article"
            log_generation_step(
                user_id,
                session_id,
                "process_content",
                {"stage": "article_generation_error", "error": article_result["error"]},
            )
            return results

        results["article"] = article_result["article"]
        results["article_feedback"] = article_result.get("editor_feedback", "")
        if article_container:
            article_container.success("Article generated")

        # Stage 7: Generate SEO metadata
        if seo_container:
            seo_container.info("Generating SEO metadata...")

        seo_result = generate_seo_metadata(text, results["title"], ai_provider, model)
        if seo_result.get("error"):
            results["success"] = False
            results["error"] = f"SEO metadata generation failed: {seo_result['error']}"
            results["stage_failed"] = "seo_metadata"
            log_generation_step(
                user_id,
                session_id,
                "process_content",
                {
                    "stage": "seo_metadata_generation_error",
                    "error": seo_result["error"],
                },
            )
            return results

        results["seo_metadata"] = seo_result["seo_metadata"]
        if seo_container:
            seo_container.success("SEO metadata generated")

        # Stage 8: Generate content tags
        try:
            results["tags"] = generate_content_tags(text, results.get("wisdom", ""))
        except Exception as e:
            # Non-critical error, continue but log the issue
            results["tags"] = []
            results["tag_error"] = str(e)
            log_generation_step(
                user_id,
                session_id,
                "process_content",
                {"stage": "tag_generation_error", "error": str(e)},
            )

        # Final step: Calculate token usage estimate
        try:
            results["token_usage"] = estimate_token_usage(
                text,
                results.get("wisdom", ""),
                results.get("outline", ""),
                results.get("social", ""),
                results.get("image_prompts", ""),
                results.get("article", ""),
            )
        except Exception as e:
            # Non-critical error, continue but log the issue
            results["token_usage"] = 0
            results["token_error"] = str(e)
            log_generation_step(
                user_id,
                session_id,
                "process_content",
                {"stage": "token_usage_error", "error": str(e)},
            )

        # Log the successful completion
        log_generation_step(
            user_id,
            session_id,
            "process_content",
            {"stage": "process_complete", "success": True},
        )

        return results

    except Exception as e:
        # Catch-all for any unexpected errors
        results["success"] = False
        results["error"] = f"Unexpected error: {str(e)}"
        results["stage_failed"] = "unknown"

        log_generation_step(
            user_id,
            session_id,
            "process_content",
            {"stage": "unexpected_error", "error": str(e)},
        )

        return results


if __name__ == "__main__":
    # Check for diagnostic mode
    if len(sys.argv) > 1 and "--diagnostic" in sys.argv:
        # Initialize session state
        initialize_session_state()
        
        # Create a session ID
        session_id = get_or_create_session_id()
        
        # Force authentication for testing
        st.session_state.authenticated = True
        
        print("\n" + "=" * 80)
        print("WHISPERFORGE DIAGNOSTIC REPORT")
        print("=" * 80)
        
        # Print session state
        print("\nSESSION STATE DUMP:")
        print("-" * 80)
        for key, value in st.session_state.items():
            # Truncate long strings
            if isinstance(value, str) and len(value) > 100:
                value = value[:100] + "... [truncated]"
            print(f"{key}: {value}")
        
        # Print UI rendering conditions
        print("\nUI RENDERING CONDITIONS:")
        print("-" * 80)
        print(f"User authenticated: {is_authenticated()}")
        print(f"Current page: {st.session_state.get('page', 'Not set')}")
        print(f"Transcription available: {bool(st.session_state.get('transcription', ''))}")
        print(f"Session ID: {session_id}")
        
        # Print potential issues
        print("\nPOTENTIAL ISSUES:")
        print("-" * 80)
        issues = []
        
        if not is_authenticated():
            issues.append("- User is not authenticated, will show login page instead of main pipeline")
        
        if not st.session_state.get('transcription', ''):
            issues.append("- No transcription in session state, content generation pipeline won't be displayed")
        
        if not st.session_state.get('api_keys', {}):
            issues.append("- No API keys in session state, will show warnings in UI")
        
        if not issues:
            issues.append("- No obvious issues detected in session state")
        
        for issue in issues:
            print(issue)
        
        print("\nRECOMMENDATIONS:")
        print("-" * 80)
        print("1. Ensure initialize_session_state() is called at the start of the application")
        print("2. Set st.session_state.authenticated = True to bypass login screen")
        print("3. Add sample transcription data with st.session_state.transcription = 'Sample text'")
        print("4. Check auth flow in main() function for potential redirect issues")
        
        print("\n" + "=" * 80)
        sys.exit(0)
    
    # Run the main application
    main()
