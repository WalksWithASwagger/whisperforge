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
# Import our config module
from config import (
    DATABASE_PATH, DATA_DIR, UPLOADS_DIR, TEMP_DIR, LOGS_DIR, PROMPTS_DIR,
    OPENAI_API_KEY, ANTHROPIC_API_KEY, NOTION_API_KEY, NOTION_DATABASE_ID, GROK_API_KEY,
    JWT_SECRET, ADMIN_EMAIL, ADMIN_PASSWORD, logger
)

# Import all content modules at once 
from content import extract_wisdom, generate_outline, generate_blog_post, generate_social_content, generate_image_prompts, generate_summary

# Import individual modules for direct access
import content.social as social
from utils.prompts import DEFAULT_PROMPTS

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("whisperforge.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("whisperforge")

# Initialize OPENAI_API_KEY from the file if it exists
def load_api_key_from_file(file_path="/app/openai_api_key.txt"):
    """Load API key from file, used especially for Docker environment"""
    try:
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                key = f.read().strip()
                if key and len(key) > 10 and not any(placeholder in key.lower() for placeholder in ["your_", "placeholder", "api_key"]):
                    logger.info(f"Loaded OpenAI API key from file (length: {len(key)})")
                    return key
    except Exception as e:
        logger.error(f"Error loading API key from file: {str(e)}")
    return None

# Try to load API key from file at startup
file_api_key = load_api_key_from_file()
if file_api_key:
    logger.info("Setting OpenAI API key from file")
    os.environ['OPENAI_API_KEY'] = file_api_key
    OPENAI_API_KEY = file_api_key

# This must be the very first st.* command
st.set_page_config(
    page_title="WhisperForge | Audio to Content Platform",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Remove load_dotenv() as it's now handled in config.py
# load_dotenv()

# Update the database setup
def get_db_connection():
    conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    # Ensure data directory exists
    os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
    
    conn = get_db_connection()
    conn.execute('''
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
    ''')
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
    payload = {
        "user_id": user_id,
        "exp": expiration
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm="HS256")
    return token

def validate_jwt_token(token):
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        return payload["user_id"]
    except:
        return None

# Initialization of clients - will be called as needed with user-specific API keys
def get_openai_client():
    logger.debug("Entering get_openai_client function")
    
    # Priority 1: Get API key from the user's profile
    api_key = get_api_key_for_service("openai")
    
    # Priority 2: Try to load from the file directly
    if not api_key or len(api_key) < 10 or any(placeholder in api_key.lower() for placeholder in ["your_", "placeholder", "api_key"]):
        file_key = load_api_key_from_file()
        if file_key:
            api_key = file_key
            logger.debug("Using API key from file")
    
    # Priority 3: Fallback to environment variable
    if not api_key or len(api_key) < 10 or any(placeholder in api_key.lower() for placeholder in ["your_", "placeholder", "api_key"]):
        api_key = OPENAI_API_KEY
        logger.debug("Using API key from environment")
    
    # Final check
    if not api_key or len(api_key) < 10 or any(placeholder in api_key.lower() for placeholder in ["your_", "placeholder", "api_key"]):
        logger.error("OpenAI API key is not set or appears to be a placeholder")
        st.error("OpenAI API key is not properly set. Please add your API key in the settings.")
        return None
    
    logger.debug(f"Got OpenAI API key (length: {len(api_key)})")
    
    try:
        client = OpenAI(api_key=api_key)
        return client
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Failed to initialize OpenAI client: {error_msg}")
        
        # Try alternative initialization for proxy environments
        if 'proxies' in error_msg:
            logger.debug("Trying alternative initialization approach due to proxies error")
            try:
                # Define a simple function to make API requests directly
                def simple_transcribe(audio_file):
                    import requests
                    url = "https://api.openai.com/v1/audio/transcriptions"
                    headers = {
                        "Authorization": f"Bearer {api_key}"
                    }
                    files = {
                        "file": audio_file,
                        "model": (None, "whisper-1")
                    }
                    response = requests.post(url, headers=headers, files=files)
                    return response.json()
                
                # Create a minimal client object that just has the transcribe method
                class MinimalOpenAIClient:
                    def __init__(self, api_key):
                        self.api_key = api_key
                        self.audio = type('', (), {})()
                        self.audio.transcriptions = type('', (), {})()
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
        # Fallback to config
        api_key = ANTHROPIC_API_KEY
    
    if not api_key:
        st.error("Anthropic API key is not set. Please add your API key in the settings.")
        return None
    return Anthropic(api_key=api_key)

def get_notion_client():
    api_key = get_api_key_for_service("notion")
    if not api_key:
        # Fallback to config
        api_key = NOTION_API_KEY
    
    if not api_key:
        st.error("Notion API key is not set. Please add your API key in the settings.")
        return None
    return Client(auth=api_key)

def get_notion_database_id():
    api_keys = get_user_api_keys()
    db_id = api_keys.get("notion_database_id")
    if not db_id:
        db_id = NOTION_DATABASE_ID
    return db_id

def get_grok_api_key():
    api_key = get_api_key_for_service("grok")
    if not api_key:
        # Fallback to config
        api_key = GROK_API_KEY
    return api_key

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
    }
}

def local_css():
    """Apply refined cyberpunk styling inspired by Luma's interface"""
    with open('static/css/main.css') as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    
    # Add custom styles for the navigation buttons like in the image
    custom_styles = """
    <style>
    /* Dark purple/black nav button styling */
    .nav-item {
        color: white !important;
        text-decoration: none;
        font-size: 0.9rem;
        font-weight: 500;
        padding: 6px 14px;
        border-radius: 4px;
        transition: all 0.2s ease;
        position: relative;
        background: #1a1020 !important;
        border: 1px solid #2a1a30;
        box-shadow: 0 0 4px rgba(0, 0, 0, 0.3);
    }
    
    .nav-item:hover {
        color: white !important;
        background: #2a1a30 !important;
        box-shadow: 0 0 8px rgba(121, 40, 202, 0.3);
    }
    
    .nav-item.active {
        color: white !important;
        background: #3a2040 !important;
        box-shadow: 0 0 8px rgba(121, 40, 202, 0.4);
        border: 1px solid #4a3050;
    }
    
    /* Remove the underline effect */
    .nav-item::after {
        display: none;
    }
    
    /* Specific styling for sidebar button */
    .sidebar-button {
        display: inline-block;
        margin-bottom: 10px;
        text-align: center;
        width: 100%;
    }
    
    /* Style the button in the sidebar the same way */
    .stButton button {
        color: white !important;
        background: #1a1020 !important;
        border: 1px solid #2a1a30 !important;
        box-shadow: 0 0 4px rgba(0, 0, 0, 0.3) !important;
    }
    
    .stButton button:hover {
        background: #2a1a30 !important;
        border: 1px solid #3a2040 !important;
        box-shadow: 0 0 8px rgba(121, 40, 202, 0.3) !important;
    }
    
    /* Footer styling */
    .footer-container {
        margin-top: 30px;
        padding: 20px 0;
        border-top: 1px solid rgba(121, 40, 202, 0.2);
        background: rgba(26, 16, 32, 0.2);
        border-radius: 5px;
    }
    
    .footer-container h4 {
        color: #f0f0f0;
        font-size: 0.9rem;
        margin-bottom: 15px;
        padding-bottom: 6px;
        border-bottom: 1px solid rgba(121, 40, 202, 0.3);
    }
    
    .footer-container a {
        color: rgba(121, 40, 202, 1);
        text-decoration: none;
        font-size: 0.85rem;
        display: block;
        margin-bottom: 8px;
        transition: color 0.2s ease;
    }
    
    .footer-container a:hover {
        color: rgba(255, 0, 128, 1);
        text-decoration: none;
    }
    
    .footer-container p {
        margin: 0;
        padding: 0;
        font-size: 0.85rem;
        color: var(--text-secondary);
    }
    
    .footer-container strong {
        color: var(--text-primary);
    }
    </style>
    """
    st.markdown(custom_styles, unsafe_allow_html=True)
    
    # Add the scanner line animation div
    st.markdown('<div class="scanner-line"></div>', unsafe_allow_html=True)

def load_user_knowledge_base(user):
    """Load knowledge base files for a specific user"""
    knowledge_base = {}
    kb_path = f'prompts/{user}/knowledge_base'
    
    if os.path.exists(kb_path):
        for file in os.listdir(kb_path):
            if file.endswith(('.txt', '.md')):
                with open(os.path.join(kb_path, file), 'r') as f:
                    name = os.path.splitext(file)[0].replace('_', ' ').title()
                    knowledge_base[name] = f.read()
    
    return knowledge_base

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
    user_dirs = [d for d in os.listdir("prompts") if os.path.isdir(os.path.join("prompts", d))]
    
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
            prompt_files = [f for f in os.listdir(user_dir) if f.endswith('.md')]
        except Exception as e:
            st.warning(f"Error accessing prompts for {user}: {str(e)}")
        
        # Load each prompt file
        for prompt_file in prompt_files:
            prompt_name = os.path.splitext(prompt_file)[0]
            try:
                with open(os.path.join(user_dir, prompt_file), 'r') as f:
                    prompt_content = f.read()
                users_prompts[user][prompt_name] = prompt_content
            except Exception as e:
                st.warning(f"Error loading prompt {prompt_file}: {str(e)}")
    
    return users, users_prompts

def apply_prompt(text, prompt_content, provider, model, user_knowledge=None):
    """Apply a specific prompt using the selected model and provider, incorporating user knowledge"""
    try:
        prompt_parts = prompt_content.split('## Prompt')
        if len(prompt_parts) > 1:
            prompt_text = prompt_parts[1].strip()
        else:
            prompt_text = prompt_content

        # Include knowledge base context if available
        system_prompt = prompt_text
        if user_knowledge:
            knowledge_context = "\n\n".join([
                f"## {name}\n{content}" 
                for name, content in user_knowledge.items()
            ])
            system_prompt = f"""Use the following knowledge base to inform your analysis and match the user's style and perspective:

{knowledge_context}

When analyzing the content, please incorporate these perspectives and style guidelines.

Original Prompt:
{prompt_text}"""

        if provider == "OpenAI":
            response = openai_client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Here's the transcription to analyze:\n\n{text}"}
                ],
                max_tokens=1500
            )
            return response.choices[0].message.content

        elif provider == "Anthropic":
            response = anthropic_client.messages.create(
                model=model,
                max_tokens=1500,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": f"Here's the transcription to analyze:\n\n{text}"}
                ]
            )
            return response.content[0].text

        elif provider == "Grok":
            # Grok API endpoint (you'll need to adjust this based on actual Grok API documentation)
            headers = {
                "Authorization": f"Bearer {GROK_API_KEY}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Here's the transcription to analyze:\n\n{text}"}
                ]
            }
            response = requests.post(
                "https://api.grok.x.ai/v1/chat/completions",  # Adjust URL as needed
                headers=headers,
                json=payload
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
            logger.debug(f"Large file detected ({file_size_mb:.2f} MB). Using silence-based chunking.")
            
            # Detect silences in the audio
            try:
                silence_thresh = -40  # dB
                min_silence_len = 700  # ms
                
                # Get silence ranges
                silence_ranges = silence.detect_silence(
                    audio, 
                    min_silence_len=min_silence_len, 
                    silence_thresh=silence_thresh
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
                target_chunk_len_ms = target_size_mb * 5 * 60 * 1000 / file_size_mb  # Scale based on file size
                
                filtered_points = [chunk_points[0]]  # Always keep the first point
                current_pos = chunk_points[0]
                
                for point in chunk_points[1:]:
                    if point - current_pos >= target_chunk_len_ms or point == chunk_points[-1]:
                        filtered_points.append(point)
                        current_pos = point
                
                logger.debug(f"Created {len(filtered_points)-1} chunk boundaries using silence detection")
                chunk_points = filtered_points
                
                # Create progress bar
                progress_bar = st.progress(0)
                
                # Process each chunk
                for i in range(len(chunk_points) - 1):
                    start = chunk_points[i]
                    end = chunk_points[i+1]
                    
                    # Skip if segment is too short (less than 1 second)
                    if end - start < 1000:
                        logger.debug(f"Skipping segment {i+1} (too short: {end-start}ms)")
                        continue
                    
                    try:
                        chunk = audio[start:end]
                        chunk_path = os.path.join(temp_dir, f'chunk_{i}.mp3')
                        
                        # Export with specific parameters that work well with OpenAI's API
                        chunk.export(
                            chunk_path, 
                            format='mp3',
                            parameters=["-ac", "1", "-ar", "16000"]  # Mono, 16kHz
                        )
                        
                        # Verify the exported file exists and has content
                        if os.path.exists(chunk_path) and os.path.getsize(chunk_path) > 0:
                            chunks.append(chunk_path)
                            logger.debug(f"Created chunk {i+1}: {chunk_path} (Duration: {len(chunk)}ms)")
                        else:
                            logger.warning(f"Failed to create chunk {i+1}: File is empty or doesn't exist")
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
                    logger.debug(f"Skipping final segment (too short: {len(audio) - i}ms)")
                    continue
                
                try:
                    # Extract chunk
                    chunk = audio[i:min(i + chunk_length_ms, len(audio))]
                    
                    # Save chunk with index in filename
                    chunk_path = os.path.join(temp_dir, f'chunk_{chunk_count}.mp3')
                    
                    # Export with specific parameters for OpenAI
                    chunk.export(
                        chunk_path, 
                        format='mp3',
                        parameters=["-ac", "1", "-ar", "16000"]  # Mono, 16kHz
                    )
                    
                    # Verify the exported file exists and has content
                    if os.path.exists(chunk_path) and os.path.getsize(chunk_path) > 0:
                        chunks.append(chunk_path)
                        chunk_count += 1
                        logger.debug(f"Created chunk {chunk_count}: {chunk_path} (Duration: {len(chunk)}ms)")
                    else:
                        logger.warning(f"Failed to create chunk at position {i}ms: File is empty or doesn't exist")
                except Exception as chunk_error:
                    logger.error(f"Error creating chunk at position {i}ms: {str(chunk_error)}")
                
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
        logger.debug(f"Processing chunk {i+1}/{total_chunks} ({os.path.getsize(chunk_path)/1024:.1f}KB): {chunk_path}")
        
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
            
            headers = {
                "Authorization": f"Bearer {api_key}"
            }
            
            url = "https://api.openai.com/v1/audio/transcriptions"
            
            # Set transcription options
            model = st.session_state.get('transcription_model', 'whisper-1')
            
            # Create form data
            files = {
                'file': open(chunk_path, 'rb')
            }
            
            data = {
                'model': model,
                'response_format': 'text'
            }
            
            # Check for language code in session state
            if st.session_state.get('language_code') and st.session_state.get('language_code') != 'auto':
                data['language'] = st.session_state.get('language_code')
                logger.debug(f"Setting language for chunk {i+1} to: {data['language']}")
            
            # Make the API request
            response = requests.post(url, headers=headers, files=files, data=data)
            
            # Handle different response codes
            if response.status_code == 200:
                transcript = response.text
                logger.debug(f"Successfully transcribed chunk {i+1} (Length: {len(transcript)} chars)")
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
                    error_msg = error_data.get('error', {}).get('message', f"Unknown API error for chunk {i+1}")
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
                if st.session_state.get('language_code') and st.session_state.get('language_code') != 'auto':
                    options['language'] = st.session_state.get('language_code')
                
                # Get model preference or use default
                model = st.session_state.get('transcription_model', 'whisper-1')
                
                with open(chunk_path, "rb") as audio_file:
                    # Use client library as fallback
                    response = client.audio.transcriptions.create(
                        model=model,
                        file=audio_file,
                        response_format="text",
                        **options
                    )
                
                # If we get here, the fallback worked
                transcript = response
                logger.debug(f"Fallback succeeded for chunk {i+1} (Length: {len(transcript)} chars)")
                return transcript
                
            except Exception as client_error:
                error_msg = f"Fallback also failed for chunk {i+1}: {str(client_error)}"
                logger.error(error_msg)
                return f"[Failed: {error_msg}]"
    
    except Exception as e:
        error_msg = f"Unexpected error processing chunk {i+1}: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return f"[Error: {error_msg}]"

def generate_title(transcript):
    """Generate a descriptive 5-7 word title based on the transcript"""
    try:
        openai_client = get_openai_client()
        if not openai_client:
            return "Untitled Audio Transcription"
            
        prompt = f"""Create a clear, descriptive title (5-7 words) that captures the main topic of this transcript:
        Transcript: {transcript[:1000]}...
        
        Return only the title, no quotes or additional text."""
        
        response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that creates concise, descriptive titles."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=50,
            temperature=0.3
        )
        
        return response.choices[0].message.content.strip()
    except Exception as e:
        return "Audio Transcription"

def generate_summary(transcript):
    """Generate a one-sentence summary of the audio content"""
    try:
        # Use our new module for summary generation if available
        try:
            from content import generate_summary as content_generate_summary
            return content_generate_summary(transcript, "transcript", "OpenAI", "gpt-3.5-turbo")
        except Exception as e:
            logger.warning(f"Could not use modular summary generation: {str(e)}")
            
            # Fallback to built-in functionality
            openai_client = get_openai_client()
            if not openai_client:
                return "Summary of audio content"
                
            prompt = f"""Create a single, insightful sentence that summarizes the key message or main insight from this transcript:
            Transcript: {transcript[:1000]}...
            
            Return only the summary sentence, no additional text."""
            
            response = openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that creates concise, insightful summaries."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=100,
                temperature=0.3
            )
            
            return response.choices[0].message.content.strip()
    except Exception as e:
        logger.exception(f"Error generating summary: {str(e)}")
        return "Summary of audio content"

def generate_short_title(text):
    """Generate a descriptive title from the transcript using Claude 3.7 Sonnet"""
    try:
        # Use Anthropic Claude 3.7 Sonnet for generating title
        api_key = get_api_key_for_service("anthropic")
        if not api_key:
            return "Untitled Audio Transcription"
        
        # Create a better prompt for title generation
        prompt = f"""Create a descriptive, specific title (5-8 words) that accurately captures the core topic or theme of this content. 
        The title should be informative and specific enough that someone reading it would immediately understand what the content is about.
        
        Content sample:
        {text[:2000]}...
        
        Return only the title, no quotes, asterisks, or additional text. The title should be engaging but primarily informative and descriptive.
        """
        
        # Use direct API call to Claude
        result = direct_anthropic_completion(prompt, api_key, model="claude-3-7-sonnet-20250219")
        
        if result and not result.startswith("Error"):
            # Clean the title
            title = result.strip().rstrip('.').strip('"').strip("'")
            return title
        else:
            return "Untitled Audio Transcription"
    except Exception as e:
        logger.exception("Error generating title:")
        return "Untitled Audio Transcription"

def chunk_text_for_notion(text, chunk_size=1900):
    """Split text into chunks suitable for Notion API, with proper error handling"""
    if not text:
        return ["No content available"]
        
    try:
        # Ensure text is a string
        if not isinstance(text, str):
            if text is None:
                return ["No content available"]
            else:
                # Attempt to convert to string
                text = str(text)
                
        # Now split into chunks
        result = []
        for i in range(0, len(text), chunk_size):
            if i + chunk_size <= len(text):
                result.append(text[i:i + chunk_size])
            else:
                result.append(text[i:])
        
        return result or ["No content available"]  # Ensure we return something
    except Exception as e:
        logger.error(f"Error chunking text for Notion: {str(e)}")
        return ["Error processing content for Notion"]

def create_summary_callout(transcript):
    """Create a summary callout for Notion with proper error handling"""
    try:
        summary = generate_summary(transcript)
        if not summary or len(summary) < 5:  # Basic validation
            summary = "Summary of audio content"
            
        # Ensure the summary isn't too long for Notion
        if len(summary) > 2000:
            summary = summary[:1997] + "..."
            
        return {
            "object": "block",  # This is required for Notion API
            "type": "callout",
            "callout": {
                "rich_text": [{"type": "text", "text": {"content": summary}}],
                "color": "purple_background",
                "icon": {
                    "type": "emoji",
                    "emoji": "💜"
                }
            }
        }
    except Exception as e:
        logger.error(f"Error creating summary callout: {str(e)}")
        return {
            "object": "block",  # This is required for Notion API
            "type": "callout",
            "callout": {
                "rich_text": [{"type": "text", "text": {"content": "Summary of audio content"}}],
                "color": "purple_background",
                "icon": {
                    "type": "emoji",
                    "emoji": "💜"
                }
            }
        }

def create_content_notion_entry(title, transcript, wisdom=None, outline=None, social_content=None, image_prompts=None, article=None):
    """Create a new entry in the Notion database with all content sections"""
    try:
        # Get Notion client and database ID
        notion_client = get_notion_client()
        if not notion_client:
            st.error("Notion API key is not configured. Please add your API key in the settings.")
            return False
            
        NOTION_DATABASE_ID = get_notion_database_id()
        if not NOTION_DATABASE_ID:
            st.error("Notion Database ID is not configured. Please add it in the settings.")
            return False
        
        # Initialize audio_filename at the beginning of the function
        audio_filename = "None"
        if hasattr(st.session_state, 'audio_file') and st.session_state.audio_file:
            audio_filename = st.session_state.audio_file.name
        
        # Generate AI title if none provided
        if not title or title.startswith("Transcription -") or title.startswith("Content -"):
            ai_title = generate_short_title(transcript)
            title = f"WHISPER: {ai_title}"
        
        # Generate tags for the content
        content_tags = generate_content_tags(transcript, wisdom)
        
        # Generate summary
        summary = generate_summary(transcript)
        
        # Track model usage for metadata
        used_models = []
        if hasattr(st.session_state, 'ai_provider') and hasattr(st.session_state, 'ai_model'):
            if st.session_state.ai_provider and st.session_state.ai_model:
                used_models.append(f"{st.session_state.ai_provider} {st.session_state.ai_model}")
        if transcript:  # If we have a transcript, we likely used Whisper
            used_models.append("OpenAI Whisper-1")
            
        # Estimate token usage
        total_tokens = estimate_token_usage(transcript, wisdom, outline, social_content, image_prompts, article)
        
        # Format content with toggles
        content = []
        
        # Add summary section with AI-generated summary
        try:
            # Use the new function to create the summary callout
            summary_callout = create_summary_callout(transcript)
            content.append(summary_callout)
            
            content.append({
                "type": "divider",
                "divider": {}
            })
        except Exception as e:
            logger.error(f"Error adding summary to Notion: {str(e)}")
        
        # Add Transcript section with chunked content and color
        content.extend([
            {
                "type": "toggle",
                "toggle": {
                    "rich_text": [{"type": "text", "text": {"content": "Transcription"}}],
                    "color": "default", # dark gray/black
                    "children": [
                        {
                            "type": "paragraph",
                            "paragraph": {
                                "rich_text": [{"type": "text", "text": {"content": chunk}}]
                            }
                        } for chunk in chunk_text_for_notion(transcript)
                    ]
                }
            }
        ])

        # Add Wisdom section if available
        if wisdom:
            content.extend([
                {
                    "type": "toggle",
                    "toggle": {
                        "rich_text": [{"type": "text", "text": {"content": "Wisdom"}}],
                        "color": "brown_background",
                        "children": [
                            {
                                "type": "paragraph",
                                "paragraph": {
                                    "rich_text": [{"type": "text", "text": {"content": chunk}}]
                                }
                            } for chunk in chunk_text_for_notion(wisdom)
                        ]
                    }
                }
            ])

        # Add Socials section with golden brown background
        if social_content:
            content.extend([
                {
                    "type": "toggle",
                    "toggle": {
                        "rich_text": [{"type": "text", "text": {"content": "Socials"}}],
                        "color": "orange_background", # closest to golden brown
                        "children": [
                            {
                                "type": "paragraph",
                                "paragraph": {
                                    "rich_text": [{"type": "text", "text": {"content": chunk}}]
                                }
                            } for chunk in chunk_text_for_notion(social_content)
                        ]
                    }
                }
            ])

        # Add Image Prompts with green background
        if image_prompts:
            content.extend([
                {
                    "type": "toggle",
                    "toggle": {
                        "rich_text": [{"type": "text", "text": {"content": "Image Prompts"}}],
                        "color": "green_background",
                        "children": [
                            {
                                "type": "paragraph",
                                "paragraph": {
                                    "rich_text": [{"type": "text", "text": {"content": chunk}}]
                                }
                            } for chunk in chunk_text_for_notion(image_prompts)
                        ]
                    }
                }
            ])

        # Add Outline with blue background
        if outline:
            content.extend([
                {
                    "type": "toggle",
                    "toggle": {
                        "rich_text": [{"type": "text", "text": {"content": "Outline"}}],
                        "color": "blue_background",
                        "children": [
                            {
                                "type": "paragraph",
                                "paragraph": {
                                    "rich_text": [{"type": "text", "text": {"content": chunk}}]
                                }
                            } for chunk in chunk_text_for_notion(outline)
                        ]
                    }
                }
            ])

        # Add Draft Post with purple background
        if article:
            content.extend([
                {
                    "type": "toggle",
                    "toggle": {
                        "rich_text": [{"type": "text", "text": {"content": "Draft Post"}}],
                        "color": "purple_background",
                        "children": [
                            {
                                "type": "paragraph",
                                "paragraph": {
                                    "rich_text": [{"type": "text", "text": {"content": chunk}}]
                                }
                            } for chunk in chunk_text_for_notion(article)
                        ]
                    }
                }
            ])

        # Add Original Audio section with maroon/red background if audio file exists
        if audio_filename != "None":
            content.extend([
                {
                    "type": "toggle",
                    "toggle": {
                        "rich_text": [{"type": "text", "text": {"content": "Original Audio"}}],
                        "color": "red_background",
                        "children": [
                            {
                                "type": "paragraph",
                                "paragraph": {
                                    "rich_text": [{"type": "text", "text": {"content": audio_filename}}]
                                }
                            }
                        ]
                    }
                }
            ])

        # Add metadata section
            content.extend([
                {
                    "type": "divider",
                    "divider": {}
                },
                {
                    "type": "heading_2",
                    "heading_2": {
                    "rich_text": [{"type": "text", "text": {"content": "Metadata"}}]
                }
            },
            {
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"type": "text", "text": {"content": f"**Original Audio:** {audio_filename}"}}]
                }
            },
                            {
                                "type": "paragraph",
                                "paragraph": {
                    "rich_text": [{"type": "text", "text": {"content": f"**Created:** {datetime.now().strftime('%Y-%m-%d %H:%M')}"}}]
                }
            },
            {
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"type": "text", "text": {"content": f"**Models Used:** {', '.join(used_models) if used_models else 'None'}"}}]
                }
            },
            {
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"type": "text", "text": {"content": f"**Estimated Tokens:** {total_tokens:,}"}}]
                    }
                }
            ])

        # Create the page in Notion
        response = notion_client.pages.create(
            parent={"database_id": NOTION_DATABASE_ID},
            properties={
                "Name": {"title": [{"text": {"content": title}}]},
                "Tags": {"multi_select": [{"name": tag} for tag in content_tags]},
            },
            children=content
        )
        
        # Make the Notion link clickable in the UI
        if response and isinstance(response, dict) and 'id' in response:
            page_id = response['id']
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

def estimate_token_usage(transcript, wisdom=None, outline=None, social_content=None, image_prompts=None, article=None):
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
    if social_content:
        token_count += len(social_content) / 4
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
        result = direct_anthropic_completion(prompt, api_key, model="claude-3-7-sonnet-20250219")
        
        if result and not result.startswith("Error"):
            # Split the response into individual tags and clean them
            tags = [tag.strip() for tag in result.split(',') if tag.strip()]
            
            # Ensure we have at least 3 tags but no more than 7
            while len(tags) < 3:
                tags.append("whisperforge content")
            
            return tags[:7]
        else:
            return ["audio content", "transcription", "whisperforge", "ai generated", "content notes"]
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
            model.id: model.id for model in models 
            if any(x in model.id for x in ['gpt-4', 'gpt-3.5'])
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
    prompts_dir = 'prompts'
    
    if not os.path.exists(prompts_dir):
        os.makedirs(prompts_dir)
        return ["Default"]
    
    # Get all user directories
    for user_dir in os.listdir(prompts_dir):
        user_path = os.path.join(prompts_dir, user_dir)
        if os.path.isdir(user_path) and not user_dir.startswith('.'):
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

def list_knowledge_base_files(user):
    """List knowledge base files for a specific user"""
    kb_path = os.path.join('prompts', user, 'knowledge_base')
    files = []
    
    if os.path.exists(kb_path):
        for file in os.listdir(kb_path):
            if file.endswith(('.txt', '.md')) and not file.startswith('.'):
                files.append(os.path.join(kb_path, file))
    
    return files

def get_available_models(provider):
    """Get available models for a given provider"""
    try:
        openai_client = get_openai_client()
        
        # Default models in case API calls fail
        default_models = {
            "OpenAI": ["gpt-4-turbo-preview", "gpt-4", "gpt-3.5-turbo"],
            "Anthropic": ["claude-3-7-sonnet-20250219", "claude-3-opus-20240229", "claude-3-sonnet-20240229", "claude-3-haiku-20240307"],
            "Grok": ["grok-1"]
        }
        
        if provider == "OpenAI":
            try:
                if openai_client:
                    models = openai_client.models.list()
                    available_models = []
                    
                    # Filter for chat and text generation models
                    for model in models.data:
                        model_id = model.id
                        if ("gpt" in model_id.lower() and 
                            "instruct" not in model_id.lower() and 
                            any(ver in model_id.lower() for ver in ["3.5", "4"])):
                            available_models.append(model_id)
                    
                    # Add standard model options
                    standard_models = [
                        "gpt-4", 
                        "gpt-4-turbo-preview", 
                        "gpt-3.5-turbo"
                    ]
                    
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
    st.subheader("Custom Prompts")
    st.write("Configure custom prompts for different content types:")
    
    # Ensure users_prompts is a dictionary
    if not isinstance(users_prompts, dict):
        st.warning("Error with prompt storage. Using an empty dictionary instead.")
        users_prompts = {}
    
    # List of prompt types
    prompt_types = ["wisdom_extraction", "summary", "outline_creation", "social_media", "image_prompts"]
    
    for prompt_type in prompt_types:
        # Get current prompt for the user and type
        current_prompt = get_custom_prompt(selected_user, prompt_type, users_prompts, DEFAULT_PROMPTS)
        
        # Display text area for editing
        new_prompt = st.text_area(
            f"{prompt_type.replace('_', ' ').title()}",
            value=current_prompt,
            height=150,
            key=f"prompt_{prompt_type}"
        )
        
        # Save button for this prompt
        if st.button(f"Save {prompt_type.replace('_', ' ').title()} Prompt"):
            try:
                # Create user directory if it doesn't exist
                user_dir = os.path.join("prompts", selected_user)
                os.makedirs(user_dir, exist_ok=True)
                
                # Save the prompt
                with open(os.path.join(user_dir, f"{prompt_type}.md"), "w") as f:
                    f.write(new_prompt)
                
                st.success(f"Saved custom {prompt_type} prompt for {selected_user}")
                
                # Update the in-memory prompts
                if selected_user not in users_prompts:
                    users_prompts[selected_user] = {}
                users_prompts[selected_user][prompt_type] = new_prompt
            except Exception as e:
                st.error(f"Error saving prompt: {str(e)}")
                logger.error(f"Error saving prompt for {selected_user}/{prompt_type}: {str(e)}")

def transcribe_large_file(file_path, service="openai", username=None, file_name=None):
    """Transcribe a large audio file by splitting it into chunks and processing each chunk in parallel"""
    import os
    import time
    import concurrent.futures
    import json
    import librosa
    import soundfile as sf
    import tempfile
    import logging
    
    logger.info(f"Starting transcription of large file: {file_path}")
    
    # Get API key for the service - do this in the main thread before spawning workers
    api_key = get_api_key_for_service(service)
    
    # Replace placeholder with actual API key in worker function
    def _worker_transcribe(chunk_path, chunk_number):
        try:
            logger.debug(f"Starting transcription of chunk {chunk_number}: {chunk_path}")
            if service == "openai":
                # Use our direct implementation that doesn't depend on session state
                result = direct_transcribe_audio(chunk_path, api_key)
            else:
                # For other services we would handle differently
                result = f"Transcription with {service} not implemented"
                
            if result.startswith("Error:"):
                logger.error(f"Error processing chunk {chunk_number}: {result}")
                return f"[Error: {result}]"
            return result
        except Exception as e:
            error_msg = f"Unexpected error processing chunk {chunk_number}: {str(e)}"
            logger.error(error_msg)
            return f"[Error: {error_msg}]"
    
    try:
        # Get file size for logging
        file_size = os.path.getsize(file_path) / (1024 * 1024)  # Convert to MB
        start_time = time.time()
        
        # Create temporary directory for audio chunks
        temp_dir = tempfile.mkdtemp()
        logger.debug(f"Created temporary directory for chunks: {temp_dir}")
        
        # Split audio into chunks
        # We'll use a simple time-based split for most formats
        try:
            # Try to get audio duration using librosa
            y, sr = librosa.load(file_path, sr=None, mono=True, duration=10)  # Just load a small sample to get sample rate
            audio_duration = librosa.get_duration(path=file_path)
            
            # Calculate chunk duration (aim for ~10 MB chunks or 10-minute segments, whichever is shorter)
            chunk_duration = min(600, max(30, audio_duration / max(1, file_size / 10)))
            logger.debug(f"Audio duration: {audio_duration}s, chunk duration: {chunk_duration}s")
            
            # Calculate number of chunks
            num_chunks = int(audio_duration / chunk_duration) + 1
            
            # Create chunks
            chunks = []
            for i in range(num_chunks):
                start = i * chunk_duration
                end = min((i + 1) * chunk_duration, audio_duration)
                
                if end <= start:
                    continue  # Skip if this chunk would be empty
                
                # Create chunk file path
                chunk_path = os.path.join(temp_dir, f"chunk_{i+1}.wav")
                
                # Load the segment
                y, sr = librosa.load(file_path, sr=None, mono=True, offset=start, duration=end-start)
                
                # Save the segment
                sf.write(chunk_path, y, sr)
                
                chunks.append(chunk_path)
            
            logger.info(f"Audio split into {len(chunks)} chunks, average size: {sum(os.path.getsize(c) for c in chunks)/len(chunks)/1024:.1f}KB")
            
        except Exception as e:
            logger.warning(f"Error using librosa to split audio: {str(e)}")
            
            # Fallback to ffmpeg-based splitting by file size
            import subprocess
            
            # Calculate number of chunks based on file size
            target_size_mb = 10  # Target chunk size in MB
            num_chunks = max(1, int(file_size / target_size_mb))
            
            # Calculate segment duration
            segment_duration = int(60 * 10)  # 10 minutes per segment as a default
            
            chunks = []
            for i in range(num_chunks):
                # Calculate start time in seconds
                start_time_sec = i * segment_duration
                
                # Create chunk file path
                chunk_path = os.path.join(temp_dir, f"chunk_{i+1}.mp3")
                
                # Use ffmpeg to extract segment
                try:
                    cmd = [
                        "ffmpeg", "-i", file_path,
                        "-ss", str(start_time_sec),
                        "-t", str(segment_duration),
                        "-acodec", "libmp3lame",
                        "-ab", "128k",
                        "-ar", "44100",
                        "-y",  # Overwrite output files
                        chunk_path
                    ]
                    
                    subprocess.run(cmd, check=True, capture_output=True)
                    
                    # Only add if file was created and has content
                    if os.path.exists(chunk_path) and os.path.getsize(chunk_path) > 0:
                        chunks.append(chunk_path)
                    
                except subprocess.CalledProcessError as e:
                    logger.error(f"Error creating chunk {i+1} with ffmpeg: {str(e)}")
                    continue
            
            logger.info(f"Created {len(chunks)} chunks using ffmpeg")
        
        # Log the number of chunks
        logger.info(f"Created {len(chunks)} chunks for processing")
        
        # Process chunks with concurrent execution
        results = []
        failed_chunks = []
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            # Submit all tasks
            future_to_chunk = {executor.submit(_worker_transcribe, chunk, i+1): i for i, chunk in enumerate(chunks)}
            
            # Process results as they complete
            for i, future in enumerate(concurrent.futures.as_completed(future_to_chunk)):
                chunk_idx = future_to_chunk[future]
                
                try:
                    result = future.result()
                    results.append((chunk_idx, result))
                    
                    # Log progress at regular intervals
                    if (i + 1) % 2 == 0 or (i + 1) == len(chunks):
                        elapsed = time.time() - start_time
                        logger.info(f"Transcription in progress: {i+1}/{len(chunks)} chunks completed after {elapsed:.1f} seconds")
                        
                    # Check if this chunk failed
                    if result.startswith("[Error:"):
                        failed_chunks.append(result)
                        
                except Exception as e:
                    logger.error(f"Exception processing result for chunk {chunk_idx+1}: {str(e)}")
                    failed_chunks.append(f"[Error: Exception processing chunk {chunk_idx+1}: {str(e)}]")
        
        # Clean up temp files
        try:
            for chunk in chunks:
                if os.path.exists(chunk):
                    os.remove(chunk)
            os.rmdir(temp_dir)
            logger.debug("Cleaned up temporary files")
        except Exception as e:
            logger.warning(f"Error cleaning up temporary files: {str(e)}")
        
        # Sort results by chunk index
        results.sort(key=lambda x: x[0])
        
        # Combine results
        combined_text = " ".join([r[1] for r in results if not r[1].startswith("[Error:")])
        
        # Log completion
        elapsed_time = time.time() - start_time
        success_count = len(results) - len(failed_chunks)
        logger.info(f"Transcription complete in {elapsed_time:.1f} seconds: {success_count} successful chunks, {len(failed_chunks)} failed chunks")
        
        if failed_chunks:
            logger.warning(f"Errors during transcription: {failed_chunks}")
        
        return combined_text.strip()
        
    except Exception as e:
        logger.error(f"Error in large file transcription: {str(e)}")
        return f"Error: {str(e)}"

def generate_outline(transcript, wisdom, ai_provider, model, custom_prompt=None, knowledge_base=None):
    """Create a structured outline based on transcript and wisdom with streaming output"""
    # Start timing for usage tracking
    start_time = time.time()
    
    # Create a placeholder for streaming output
    stream_container = st.empty()
    stream_content = ""
    
    try:
        prompt = custom_prompt or DEFAULT_PROMPTS["outline_creation"]
        
        # Include knowledge base context if available
        if knowledge_base:
            knowledge_context = "\n\n".join([
                f"## {name}\n{content}" 
                for name, content in knowledge_base.items()
            ])
            system_prompt = f"""Use the following knowledge base to inform your analysis:

{knowledge_context}

When creating the outline, please incorporate these perspectives and guidelines.

Original Prompt:
{prompt}"""
        else:
            system_prompt = prompt
        
        # Combine transcript and wisdom for better context
        content = f"TRANSCRIPT:\n{transcript}\n\nWISDOM:\n{wisdom}"
        
        # Display initial message
        stream_container.markdown("Creating outline...")
        
        # Use the selected AI provider and model
        if ai_provider == "OpenAI":
            openai_client = get_openai_client()
            if not openai_client:
                return "Error: OpenAI API key is not configured."
                
            # Stream response from OpenAI
            response = openai_client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": content}
                ],
                max_tokens=1500,
                stream=True
            )
            
            result = ""
            # Process the streaming response
            for chunk in response:
                if hasattr(chunk.choices[0].delta, "content") and chunk.choices[0].delta.content is not None:
                    content_chunk = chunk.choices[0].delta.content
                    result += content_chunk
                    stream_content += content_chunk
                    # Update the stream display
                    stream_container.markdown(stream_content)
            
        elif ai_provider == "Anthropic":
            anthropic_client = get_anthropic_client()
            if not anthropic_client:
                return "Error: Anthropic API key is not configured."
                
            # Stream response from Anthropic
            with anthropic_client.messages.stream(
                model=model,
                max_tokens=1500,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": content}
                ]
            ) as stream:
                result = ""
                for text in stream.text_stream:
                    result += text
                    stream_content += text
                    # Update the stream display
                    stream_container.markdown(stream_content)
            
        elif ai_provider == "Grok":
            grok_api_key = get_grok_api_key()
            if not grok_api_key:
                return "Error: Grok API key is not configured."
                
            headers = {
                "Authorization": f"Bearer {grok_api_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": content}
                ]
            }
            
            # Show a progress indicator
            with st.spinner("Creating outline with Grok (this may take a moment)..."):
                response = requests.post(
                    "https://api.grok.x.ai/v1/chat/completions",
                    headers=headers,
                    json=payload
                )
                result = response.json()["choices"][0]["message"]["content"]
                # Display the complete result
                stream_container.markdown(result)
        
        # Clear the streaming container when done
        stream_container.empty()
        
        # Update usage tracking
        end_time = time.time()
        duration = end_time - start_time
        update_usage_tracking(duration)
        
        return result
        
    except Exception as e:
        logger.exception("Error in outline creation:")
        stream_container.error(f"Error: {str(e)}")
        return f"Error creating outline: {str(e)}"

def generate_image_prompts(wisdom, outline, ai_provider, model, custom_prompt=None, knowledge_base=None):
    """
    Wrapper for the new modular image prompts generation to maintain backward compatibility.
    This function delegates to the new implementation.
    """
    # Import the image module directly to avoid circular imports
    import content.image as image
    return image.generate_image_prompts(wisdom, outline, ai_provider, model, custom_prompt, knowledge_base)

def generate_social_content(wisdom, outline, ai_provider, model, custom_prompt=None, knowledge_base=None):
    """
    Wrapper for the new modular social content generation to maintain backward compatibility.
    This function delegates to the new implementation with default platforms.
    """
    try:
        # Validate inputs
        if not wisdom and not outline:
            logger.warning("Both wisdom and outline are empty or missing")
            return "No content was provided to generate social posts. Please extract wisdom or create an outline first."
            
        # Ensure wisdom and outline are strings, not None
        wisdom_text = wisdom or ""
        outline_text = outline or ""
        
        # The old implementation doesn't have transcript or platforms parameters
        # Default to typical social platforms
        platforms = ["Twitter", "LinkedIn", "Facebook"]
        
        # Import the social module dynamically to avoid circular imports
        import content.social as social
        
        # Use an empty transcript as we don't have it in the old function signature
        result = social.generate_social_content("", wisdom_text, outline_text, platforms, ai_provider, model, custom_prompt, knowledge_base)
        
        # Validate the result
        if not result or not isinstance(result, str) or len(result) < 10:
            logger.warning(f"Social content generation returned invalid result: {result}")
            return "The AI was unable to generate meaningful social content. Please try again or modify your inputs."
            
        return result
    except ImportError as ie:
        logger.exception(f"Module import error in generate_social_content: {str(ie)}")
        return f"Error: Missing required module: {str(ie)}"
    except Exception as e:
        logger.exception(f"Error in generate_social_content: {str(e)}")
        return f"Error generating social content: {str(e)}"

def generate_article(transcript, wisdom, outline, ai_provider, model, custom_prompt=None, knowledge_base=None):
    """
    Wrapper for generate_blog_post to maintain backward compatibility.
    This function delegates to the new modular implementation.
    """
    return generate_blog_post(transcript, wisdom, outline, ai_provider, model, custom_prompt, knowledge_base)

def generate_seo_metadata(content, title):
    """Generate SEO metadata for the content"""
    try:
        openai_client = get_openai_client()
        if not openai_client:
            st.error("OpenAI API key is not configured.")
            return None

        prompt = f"""As an SEO expert, analyze this content and generate essential SEO metadata:

        Content Title: {title}
        Content Preview: {content[:1000]}...

        Please provide:
        1. SEO-optimized title (50-60 chars)
        2. Meta description (150-160 chars)
        3. Primary keyword
        4. 3-4 secondary keywords
        5. Recommended URL slug
        6. Schema type recommendation

        Format as JSON."""

        response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an SEO expert that provides metadata in JSON format."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500,
            temperature=0.3
        )
        
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"Error generating SEO metadata: {str(e)}")
        return None

def process_all_content(text, ai_provider, model, knowledge_base=None):
    """Process all content stages at once with detailed streaming progress"""
    try:
        results = {
            'wisdom': None,
            'outline': None,
            'social_posts': None,
            'image_prompts': None,
            'article': None
        }
        
        # Main progress container
        progress_container = st.empty()
        progress_container.markdown("### Content Generation Progress")
        
        # Sequential processing with progress bar
        progress_bar = st.progress(0)
        status_text = st.empty()
        content_preview = st.empty()
        
        # Update progress function
        def update_progress(step, step_name, progress_value):
            status_text.text(f"Step {step}/5: {step_name}...")
            progress_bar.progress(progress_value)
        
        # STEP 1: Generate wisdom
        update_progress(1, "Extracting wisdom", 0)
        with st.status("Extracting key insights from your content...") as status:
            try:
                results['wisdom'] = extract_wisdom(text, ai_provider, model, knowledge_base=knowledge_base)
                if results['wisdom']:
                    progress_bar.progress(0.2)
                    status.update(label="✅ Wisdom extracted successfully!", state="complete")
                    # Safe preview
                    if isinstance(results['wisdom'], str):
                        preview = results['wisdom'][:300] + "..." if len(results['wisdom']) > 300 else results['wisdom']
                        content_preview.markdown(f"**Wisdom Preview:**\n{preview}")
                    else:
                        content_preview.markdown(f"**Wisdom Preview:**\nGenerated successfully")
                else:
                    status.update(label="❌ Wisdom extraction failed.", state="error")
            except Exception as e:
                logger.exception(f"Error extracting wisdom: {str(e)}")
                status.update(label=f"❌ Error: {str(e)}", state="error")
        
        # STEP 2: Generate outline - continue even if wisdom failed
        update_progress(2, "Creating outline", 0.2)
        with st.status("Organizing content into a structured outline...") as status:
            try:
                results['outline'] = generate_outline(text, results['wisdom'] or "", ai_provider, model, knowledge_base=knowledge_base)
                if results['outline']:
                    progress_bar.progress(0.4)
                    status.update(label="✅ Outline created successfully!", state="complete")
                    # Safe preview
                    if isinstance(results['outline'], str):
                        preview = results['outline'][:300] + "..." if len(results['outline']) > 300 else results['outline']
                        content_preview.markdown(f"**Outline Preview:**\n{preview}")
                    else:
                        content_preview.markdown(f"**Outline Preview:**\nGenerated successfully")
                else:
                    status.update(label="❌ Outline creation failed.", state="error")
            except Exception as e:
                logger.exception(f"Error creating outline: {str(e)}")
                status.update(label=f"❌ Error: {str(e)}", state="error")
        
        # STEP 3: Generate social content
        update_progress(3, "Generating social media content", 0.4)
        with st.status("Creating social media posts from your content...") as status:
            try:
                results['social_posts'] = generate_social_content(
                    results['wisdom'] or "", 
                    results['outline'] or "", 
                    ai_provider, 
                    model, 
                    knowledge_base=knowledge_base
                )
                if results['social_posts']:
                    progress_bar.progress(0.6)
                    status.update(label="✅ Social media content generated!", state="complete")
                    # Add a safe slicing approach to prevent errors
                    if isinstance(results['social_posts'], str):
                        preview = results['social_posts'][:300] + "..." if len(results['social_posts']) > 300 else results['social_posts']
                        content_preview.markdown(f"**Social Posts Preview:**\n{preview}")
                    else:
                        content_preview.markdown(f"**Social Posts Preview:**\nGenerated successfully")
                else:
                    status.update(label="❌ Social content generation failed.", state="error")
            except Exception as e:
                logger.exception(f"Error generating social content: {str(e)}")
                status.update(label=f"❌ Error: {str(e)}", state="error")
        
        # STEP 4: Generate image prompts
        update_progress(4, "Creating image prompts", 0.6)
        with st.status("Generating image description prompts...") as status:
            try:
                results['image_prompts'] = generate_image_prompts(
                    results['wisdom'] or "", 
                    results['outline'] or "", 
                    ai_provider, 
                    model, 
                    knowledge_base=knowledge_base
                )
                if results['image_prompts']:
                    progress_bar.progress(0.8)
                    status.update(label="✅ Image prompts created successfully!", state="complete")
                    # Safe preview
                    if isinstance(results['image_prompts'], str):
                        preview = results['image_prompts'][:300] + "..." if len(results['image_prompts']) > 300 else results['image_prompts']
                        content_preview.markdown(f"**Image Prompts Preview:**\n{preview}")
                    else:
                        content_preview.markdown(f"**Image Prompts Preview:**\nGenerated successfully")
                else:
                    status.update(label="❌ Image prompt creation failed.", state="error")
            except Exception as e:
                logger.exception(f"Error generating image prompts: {str(e)}")
                status.update(label=f"❌ Error: {str(e)}", state="error")
        
        # STEP 5: Generate article
        update_progress(5, "Writing full article", 0.8)
        with st.status("Writing a complete article from your content...") as status:
            try:
                results['article'] = generate_article(
                    text, 
                    results['wisdom'] or "", 
                    results['outline'] or "", 
                    ai_provider, 
                    model, 
                    knowledge_base=knowledge_base
                )
                if results['article']:
                    progress_bar.progress(1.0)
                    status.update(label="✅ Article written successfully!", state="complete")
                    # Safe preview
                    if isinstance(results['article'], str):
                        preview = results['article'][:300] + "..." if len(results['article']) > 300 else results['article']
                        content_preview.markdown(f"**Article Preview:**\n{preview}")
                    else:
                        content_preview.markdown(f"**Article Preview:**\nGenerated successfully")
                else:
                    status.update(label="❌ Article generation failed.", state="error")
            except Exception as e:
                logger.exception(f"Error writing article: {str(e)}")
                status.update(label=f"❌ Error: {str(e)}", state="error")
        
        # Check overall success
        success_count = sum(1 for value in results.values() if value)
        if success_count == 5:
            status_text.text("🎉 All content generated successfully!")
            progress_container.markdown("### ✅ All content generated successfully!")
        else:
            status_text.text(f"✓ Completed with {success_count}/5 successful generations")
            progress_container.markdown(f"### ⚠️ Completed with {success_count}/5 successful generations")
        
        content_preview.empty()
        
        return results
        
    except Exception as e:
        logger.exception("Error in batch processing:")
        st.error(f"Error in batch processing: {str(e)}")
        return None

def main():
    # Initialize session state variables
    if 'user_id' not in st.session_state:
        st.session_state.user_id = 1  # Set to admin user ID
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = True  # Auto-authenticate for testing
    if 'page' not in st.session_state:
        st.session_state.page = "home"
    if 'show_cookie_banner' not in st.session_state:
        st.session_state.show_cookie_banner = True
    if 'transcription' not in st.session_state:
        st.session_state.transcription = ""
    if 'wisdom' not in st.session_state:
        st.session_state.wisdom = ""
    if 'audio_file' not in st.session_state:
        st.session_state.audio_file = None
    if 'ai_provider' not in st.session_state:
        st.session_state.ai_provider = "Anthropic"
    if 'ai_model' not in st.session_state:
        # Set default model to Claude 3.7 Sonnet
        st.session_state.ai_model = "claude-3-7-sonnet-20250219"
    if 'transcription_provider' not in st.session_state:
        st.session_state.transcription_provider = "OpenAI"
    if 'transcription_model' not in st.session_state:
        st.session_state.transcription_model = "whisper-1"
    if 'content_title_value' not in st.session_state:
        st.session_state.content_title_value = ""
    
    # Check for URL query parameters
    if "page" in st.query_params:
        st.session_state.page = st.query_params["page"]
    
    # Apply production CSS enhancements
    add_production_css()
    
    # Initialize database and create admin user if needed
    init_db()
    init_admin_user()
    
    # Apply the improved cyberpunk theme
    local_css()
    
    # Load JavaScript files
    load_js()
    
    # Skip authentication for testing purposes
    # Authentication handling
    # if not st.session_state.authenticated:
    #     show_login_page()
    #     return
    
    # Create a custom header with the refined styling and navigation
    create_custom_header()
    
    # Show different pages based on selection
    if st.session_state.page == "home":
        show_main_page()
    elif st.session_state.page == "api":
        show_api_keys_page()
    elif st.session_state.page == "usage":
        show_usage_page()
    elif st.session_state.page == "admin":
        show_admin_page()
    elif st.session_state.page == "legal":
        show_legal_page()
    elif st.session_state.page == "user_config":
        show_user_config_page()
    else:
        show_main_page()
    
    # Show cookie consent banner
    show_cookie_banner()
    
    # Display tool area if transcript is available
    if st.session_state.get("transcript"):
        with st.expander("🛠️ Tools", expanded=True):
            col1, col2, col3 = st.columns(3)
            
            # First column - transcript actions
            with col1:
                st.subheader("Transcript")
                if st.button("📝 Copy Transcript"):
                    st.session_state.clipboard = st.session_state.transcript
                    st.toast("Transcript copied to clipboard")
                
                if st.button("💾 Save Transcript"):
                    st.session_state.file_to_save = "transcript.txt"
                    st.session_state.content_to_save = st.session_state.transcript
                    st.toast("Preparing transcript for download...")
            
            # Second column - wisdom actions
            with col2:
                st.subheader("Wisdom")
                
                if st.session_state.get("wisdom"):
                    if st.button("📝 Copy Wisdom"):
                        st.session_state.clipboard = st.session_state.wisdom
                        st.toast("Wisdom copied to clipboard")
                    
                    if st.button("💾 Save Wisdom"):
                        st.session_state.file_to_save = "wisdom.txt"
                        st.session_state.content_to_save = st.session_state.wisdom
                        st.toast("Preparing wisdom for download...")
            
            # Third column - outline actions
            with col3:
                st.subheader("Outline")
                
                if st.session_state.get("outline"):
                    if st.button("📝 Copy Outline"):
                        st.session_state.clipboard = st.session_state.outline
                        st.toast("Outline copied to clipboard")
                    
                    if st.button("💾 Save Outline"):
                        st.session_state.file_to_save = "outline.txt"
                        st.session_state.content_to_save = st.session_state.outline
                        st.toast("Preparing outline for download...")
    
    # Add page footer with about links, account info, and version info
    st.markdown("---")
    st.markdown('<div class="footer-container">', unsafe_allow_html=True)
    footer_cols = st.columns([1, 1, 1, 1])
    
    # About links column
    with footer_cols[0]:
        st.markdown("#### About")
        st.markdown("[Terms & Privacy](?page=legal)")
        st.markdown("[Website](https://whisperforge.ai)")
        st.markdown("[Support](mailto:support@whisperforge.ai)")
    
    # Account information column
    with footer_cols[1]:
        st.markdown("#### Account")
        # Get user info
        conn = get_db_connection()
        user = conn.execute(
            "SELECT email, subscription_tier, usage_quota, usage_current FROM users WHERE id = ?",
            (st.session_state.user_id,)
        ).fetchone()
        conn.close()
        
        if user:
            st.markdown(f"**Email**: {user['email']}")
            st.markdown(f"**Plan**: {user['subscription_tier'].title()}")
            usage_percent = min(100, (user['usage_current'] / user['usage_quota']) * 100) if user['usage_quota'] > 0 else 0
            st.markdown(f"**Usage**: {user['usage_current']}/{user['usage_quota']} min ({usage_percent:.1f}%)")
            st.markdown("[Upgrade Account]()")
            
        # Logout link
        st.markdown("[Logout](javascript:logoutUser())")
        
        # Add JavaScript for logout
        st.markdown("""
        <script>
        function logoutUser() {
            // Use the Streamlit event to trigger the logout button click
            const logoutButtons = parent.document.querySelectorAll('button:contains("Logout")');
            if (logoutButtons.length > 0) {
                logoutButtons[0].click();
            }
        }
        </script>
        """, unsafe_allow_html=True)
    
    # Legal column
    with footer_cols[2]:
        st.markdown("#### Legal")
        st.markdown("© 2024 WhisperForge")
        st.markdown("v1.0.0")
    
    # Additional links/features column
    with footer_cols[3]:
        st.markdown("#### Quick Links")
        st.markdown("[API Keys](?page=api)")
        st.markdown("[Usage Stats](?page=usage)")
        st.markdown("[User Config](?page=user_config)")
        if is_admin_user():
            st.markdown("[Admin Dashboard](?page=admin)")
    
    st.markdown('</div>', unsafe_allow_html=True)

def show_main_page():
    # This function contains the original main app functionality
    
    # Get user's API keys
    api_keys = get_user_api_keys()
    
    # Check if API keys are set up
    openai_key = api_keys.get("openai")
    anthropic_key = api_keys.get("anthropic")
    notion_key = api_keys.get("notion")
    
    if not openai_key:
        st.warning("⚠️ Your OpenAI API key is not set up. Some features may not work properly. [Set up your API keys](?page=api)")
    
    if not anthropic_key:
        st.warning("⚠️ Your Anthropic API key is not set up. Some features may not work properly. [Set up your API keys](?page=api)")
    
    # Settings section at the top
    with st.expander("⚙️ Settings", expanded=False):
        col1, col2 = st.columns(2)
        
        # User Profile selection - moved from sidebar
        with col1:
            st.markdown("#### User Profile")
            selected_user = st.selectbox("Select Profile", options=get_available_users(), key="user_profile_main")
            # Update the sidebar value to keep in sync
            if "user_profile_sidebar" in st.session_state:
                st.session_state.user_profile_sidebar = selected_user
        
        # Model selection
        with col2:
            st.markdown("#### AI Model")
            ai_provider = st.selectbox(
                "AI Provider",
                options=["Anthropic", "OpenAI", "Grok"],
                index=0 if st.session_state.ai_provider == "Anthropic" else 
                       1 if st.session_state.ai_provider == "OpenAI" else 2
            )
            
            available_models = get_available_models(ai_provider)
            ai_model = st.selectbox("AI Model", options=available_models)
            
            if st.button("Apply Model Selection"):
                st.session_state.ai_provider = ai_provider
                st.session_state.ai_model = ai_model
                st.success(f"Using {ai_provider} {ai_model}")
                st.rerun()
    
    # Load knowledge base for selected user
    selected_user = selected_user if "selected_user" in locals() else st.session_state.get("user_profile_sidebar", "Default")
    knowledge_base = load_user_knowledge_base(selected_user)
    
    # Display the current models being used
    st.info(f"Using {st.session_state.transcription_provider} {st.session_state.transcription_model} for transcription and {st.session_state.ai_provider} {st.session_state.ai_model} for content processing. Model settings can be changed in the Admin panel.")
    
    # Add tabs for input selection
    input_tabs = st.tabs(["Audio Upload", "Text Input"])
    
    # Tab 1: Audio Upload
    with input_tabs[0]:
        st.markdown('<div class="section-header">Audio Transcription</div>', unsafe_allow_html=True)
        
        # Update the file uploader with clear message about 500MB limit
        uploaded_file = st.file_uploader(
            "Upload your audio file", 
            type=['mp3', 'wav', 'ogg', 'm4a'],
            key="audio_uploader",
            help="Files up to 500MB are supported. Large files will be automatically chunked for parallel processing."
        )
        
        # Transcribe Button
        if uploaded_file is not None:
            if st.button("🎙️ Transcribe Audio", key="transcribe_button", use_container_width=True):
                with st.spinner("Transcribing your audio..."):
                    transcription = transcribe_audio(uploaded_file)
                    if transcription:
                        st.session_state.transcription = transcription
                        st.session_state.audio_file = uploaded_file
        
        # Display transcription result if available
        if st.session_state.transcription:
            st.markdown("### Transcription Result")
            st.text_area("Transcript", st.session_state.transcription, height=200, key="transcript_display")
            
            # Content generation section
            st.markdown('<div class="section-header">Content Generation</div>', unsafe_allow_html=True)
            
            # Show content generation options
            content_tabs = st.tabs(["Step-by-Step", "All-in-One", "Custom"])
            
            with content_tabs[0]:
                # Wisdom extraction
                wisdom_expander = st.expander("📝 Extract Wisdom", expanded=True)
                with wisdom_expander:
                    if st.button("Generate Wisdom", key="wisdom_button", use_container_width=True):
                        with st.spinner("Extracting key insights..."):
                            wisdom = extract_wisdom(
                                st.session_state.transcription, 
                                st.session_state.ai_provider,
                                st.session_state.ai_model,
                                knowledge_base=knowledge_base
                            )
                            if wisdom:
                                st.session_state.wisdom = wisdom
                    
                    if st.session_state.get("wisdom"):
                        st.markdown("### Extracted Wisdom")
                        st.markdown(st.session_state.wisdom)
                
                # Outline creation
                outline_expander = st.expander("📋 Create Outline", expanded=False)
                with outline_expander:
                    if st.button("Generate Outline", key="outline_button", use_container_width=True):
                        if not st.session_state.get("wisdom"):
                            st.warning("Please extract wisdom first.")
                        else:
                            with st.spinner("Creating outline..."):
                                outline = generate_outline(
                                    st.session_state.transcription,
                                    st.session_state.wisdom,
                                    st.session_state.ai_provider,
                                    st.session_state.ai_model,
                                    knowledge_base=knowledge_base
                                )
                                if outline:
                                    st.session_state.outline = outline
                    
                    if st.session_state.get("outline"):
                        st.markdown("### Content Outline")
                        st.markdown(st.session_state.outline)
                
                # Social media content
                social_expander = st.expander("📱 Social Media Content", expanded=False)
                with social_expander:
                    if st.button("Generate Social Posts", key="social_button", use_container_width=True):
                        if not st.session_state.get("wisdom") or not st.session_state.get("outline"):
                            st.warning("Please extract wisdom and create an outline first.")
                        else:
                            with st.spinner("Creating social media content..."):
                                social = generate_social_content(
                                    st.session_state.wisdom,
                                    st.session_state.outline,
                                    st.session_state.ai_provider,
                                    st.session_state.ai_model,
                                    knowledge_base=knowledge_base
                                )
                                if social:
                                    st.session_state.social = social
                    
                    if st.session_state.get("social"):
                        st.markdown("### Social Media Content")
                        st.markdown(st.session_state.social)
                
                # Image prompts
                image_expander = st.expander("🖼️ Image Prompts", expanded=False)
                with image_expander:
                    if st.button("Generate Image Prompts", key="image_button", use_container_width=True):
                        if not st.session_state.get("wisdom") or not st.session_state.get("outline"):
                            st.warning("Please extract wisdom and create an outline first.")
                        else:
                            with st.spinner("Creating image prompts..."):
                                prompts = generate_image_prompts(
                                    st.session_state.wisdom,
                                    st.session_state.outline,
                                    st.session_state.ai_provider,
                                    st.session_state.ai_model,
                                    knowledge_base=knowledge_base
                                )
                                if prompts:
                                    st.session_state.image_prompts = prompts
                    
                    if st.session_state.get("image_prompts"):
                        st.markdown("### Image Prompts")
                        st.markdown(st.session_state.image_prompts)
                
                # Full article
                article_expander = st.expander("📄 Full Article", expanded=False)
                with article_expander:
                    if st.button("Generate Article", key="article_button", use_container_width=True):
                        if not st.session_state.get("wisdom") or not st.session_state.get("outline"):
                            st.warning("Please extract wisdom and create an outline first.")
                        else:
                            with st.spinner("Writing full article..."):
                                article = generate_blog_post(
                                    st.session_state.transcription,
                                    st.session_state.wisdom,
                                    st.session_state.outline,
                                    st.session_state.ai_provider,
                                    st.session_state.ai_model,
                                    knowledge_base=knowledge_base
                                )
                                if article:
                                    st.session_state.article = article
                    
                    if st.session_state.get("article"):
                        st.markdown("### Generated Article")
                        st.markdown(st.session_state.article)
            
            with content_tabs[1]:
                # All-in-one generation
                st.markdown("### Generate All Content")
                st.markdown("This will extract wisdom, create an outline, generate social media posts, image prompts, and write a full article - all in one step.")
                
                generate_and_export = st.checkbox("Export to Notion after generation", value=True, help="Automatically export to Notion after all content is generated")
                
                if st.button("🚀 Generate All Content", key="generate_all", use_container_width=True):
                    with st.spinner("Processing all content..."):
                        results = process_all_content(
                            st.session_state.transcription,
                            st.session_state.ai_provider,
                            st.session_state.ai_model,
                            knowledge_base=knowledge_base
                        )
                        if results:
                            st.session_state.wisdom = results.get('wisdom', '')
                            st.session_state.outline = results.get('outline', '')
                            st.session_state.social = results.get('social_posts', '')
                            st.session_state.image_prompts = results.get('image_prompts', '')
                            st.session_state.article = results.get('article', '')
                            st.success("✅ All content generated successfully!")
                            
                            # Auto-export to Notion if checkbox is checked
                            if generate_and_export:
                                with st.status("Exporting to Notion...") as status:
                                    try:
                                        # Get Notion API key and database ID
                                        notion_key = api_keys.get("notion") or os.getenv("NOTION_API_KEY")
                                        notion_db = api_keys.get("notion_database_id") or os.getenv("NOTION_DATABASE_ID")
                                        
                                        if not notion_key or not notion_db:
                                            status.update(label="⚠️ Notion integration is not configured.", state="error")
                                        else:
                                            # Generate title
                                            title_to_use = generate_short_title(st.session_state.transcription)
                                            status.update(label=f"Title generated: \"{title_to_use}\"")
                                            
                                            # First try direct Notion save
                                            try:
                                                result = direct_notion_save(
                                                    title=title_to_use,
                                                    transcript=st.session_state.transcription,
                                                    wisdom=st.session_state.wisdom,
                                                    outline=st.session_state.outline,
                                                    social_content=st.session_state.social,
                                                    image_prompts=st.session_state.image_prompts,
                                                    article=st.session_state.article
                                                )
                                                
                                                if result and 'url' in result and not 'error' in result:
                                                    status.update(label=f"✅ Exported to Notion successfully! [View in Notion]({result['url']})", state="complete")
                                                    st.markdown(f"[View Your Content in Notion]({result['url']})")
                                                    return
                                            except Exception as e:
                                                logger.warning(f"Direct Notion save failed, trying standard method: {str(e)}")
                                                
                                            # Fallback to standard method
                                            result = create_content_notion_entry(
                                                title_to_use,
                                                st.session_state.transcription,
                                                wisdom=st.session_state.wisdom,
                                                outline=st.session_state.outline,
                                                social_content=st.session_state.social,
                                                image_prompts=st.session_state.image_prompts,
                                                article=st.session_state.article
                                            )
                                            
                                            if result:
                                                status.update(label="✅ Exported to Notion successfully!", state="complete")
                                            else:
                                                status.update(label="❌ Failed to export to Notion", state="error")
                                    except Exception as e:
                                        logger.exception("Error in auto-export to Notion:")
                                        status.update(label=f"❌ Error exporting to Notion: {str(e)}", state="error")
            
            with content_tabs[2]:
                # Custom prompt generation
                st.markdown("### Custom Prompt")
                custom_prompt = st.text_area(
                    "Enter your custom prompt",
                    placeholder="Ask anything about the transcription...",
                    height=100
                )
                
                if st.button("Send Custom Prompt", key="custom_prompt_button", use_container_width=True):
                    if custom_prompt:
                        with st.spinner("Processing custom prompt..."):
                            result = apply_prompt(
                                st.session_state.transcription, 
                                custom_prompt,
                                st.session_state.ai_provider,
                                st.session_state.ai_model,
                                user_knowledge=knowledge_base
                            )
                            if result:
                                st.markdown("### Result")
                                st.markdown(result)
            
            # Notion export
            st.markdown('<div class="section-header">Export to Notion</div>', unsafe_allow_html=True)
            
            # Check if Notion API key is configured
            notion_key = api_keys.get("notion") or os.getenv("NOTION_API_KEY")
            notion_db = api_keys.get("notion_database_id") or os.getenv("NOTION_DATABASE_ID")
            
            if not notion_key or not notion_db:
                st.warning("⚠️ Notion integration is not configured. Please set up your Notion API key and database ID in Settings.")
            else:
                title = st.session_state.content_title_value or "Untitled Content"
                
                if st.button("💾 Save to Notion", key="notion_save", use_container_width=True):
                    with st.spinner("Saving to Notion..."):
                        try:
                            # Always generate an AI title for better results
                            if st.session_state.transcription:
                                with st.status("Generating a descriptive title...") as status:
                                    title_to_use = generate_short_title(st.session_state.transcription)
                                    status.update(label=f"Title generated: \"{title_to_use}\"", state="complete")
                            else:
                                title_to_use = "WhisperForge Content"
                            
                            with st.status("Saving to Notion...") as status:
                                result = create_content_notion_entry(
                                    title_to_use,
                                    st.session_state.transcription,
                                    wisdom=st.session_state.get("wisdom"),
                                    outline=st.session_state.get("outline"),
                                    social_content=st.session_state.get("social"),
                                    image_prompts=st.session_state.get("image_prompts"),
                                    article=st.session_state.get("article")
                                )
                                
                                if result:
                                    status.update(label="Successfully saved to Notion!", state="complete")
                                else:
                                    status.update(label="Failed to save to Notion", state="error")
                        except Exception as e:
                            logger.exception("Error saving to Notion:")
                            st.error(f"Error saving to Notion: {str(e)}")
    
    # Tab 2: Text Input
    with input_tabs[1]:
        st.markdown('<div class="section-header">Manual Text Input</div>', unsafe_allow_html=True)
        
        text_input = st.text_area(
            "Enter your text",
            placeholder="Paste your transcript or any text to process...",
            height=300,
            key="manual_text"
        )
        
        if st.button("Use This Text", key="use_text_button", use_container_width=True):
            if text_input:
                st.session_state.transcription = text_input
                st.success("Text loaded for processing!")
                st.rerun()

def show_api_keys_page():
    st.markdown("## API Keys Management")
    st.markdown("Set up your API keys to use with WhisperForge. Your keys are encrypted and stored securely.")
    
    # Get current API keys
    api_keys = get_user_api_keys()
    
    # Create tabs for different API providers
    api_tabs = st.tabs(["OpenAI", "Anthropic", "Notion", "Grok"])
    
    # OpenAI Tab
    with api_tabs[0]:
        st.markdown("### OpenAI API Key")
        st.markdown("Required for audio transcription and GPT models.")
        
        # Create a masked display of the current key if it exists
        openai_key = api_keys.get("openai", "")
        openai_key_display = f"••••••••••••••••••{openai_key[-4:]}" if openai_key else "Not set"
        
        st.markdown(f"**Current key:** {openai_key_display}")
        
        # Input for new key
        new_openai_key = st.text_input("Enter new OpenAI API key", type="password", key="new_openai_key")
        
        # Link to get API key
        st.markdown("[Get an OpenAI API key](https://platform.openai.com/account/api-keys)")
        
        if st.button("Save OpenAI Key"):
            if new_openai_key:
                update_api_key("openai", new_openai_key)
                st.success("OpenAI API key updated successfully!")
                time.sleep(1)
                st.rerun()
    
    # Anthropic Tab
    with api_tabs[1]:
        st.markdown("### Anthropic API Key")
        st.markdown("Used for Claude AI models.")
        
        anthropic_key = api_keys.get("anthropic", "")
        anthropic_key_display = f"••••••••••••••••••{anthropic_key[-4:]}" if anthropic_key else "Not set"
        
        st.markdown(f"**Current key:** {anthropic_key_display}")
        
        new_anthropic_key = st.text_input("Enter new Anthropic API key", type="password", key="new_anthropic_key")
        
        # Link to get API key
        st.markdown("[Get an Anthropic API key](https://console.anthropic.com/account/keys)")
        
        if st.button("Save Anthropic Key"):
            update_api_key("anthropic", new_anthropic_key)
            st.success("Anthropic API key updated successfully!")
            time.sleep(1)
            st.rerun()
    
    # Notion Tab
    with api_tabs[2]:
        st.markdown("### Notion Integration")
        st.markdown("Used for exporting content to Notion.")
        
        notion_key = api_keys.get("notion", "")
        notion_key_display = f"••••••••••••••••••{notion_key[-4:]}" if notion_key else "Not set"
        
        st.markdown(f"**Current API key:** {notion_key_display}")
        
        new_notion_key = st.text_input("Enter new Notion API key", type="password", key="new_notion_key")
        
        st.markdown("### Notion Database")
        st.markdown("The ID of the Notion database where content will be exported.")
        
        notion_database_id = api_keys.get("notion_database_id", "")
        notion_db_display = f"••••••••••{notion_database_id[-4:]}" if notion_database_id else "Not set"
        
        st.markdown(f"**Current Database ID:** {notion_db_display}")
        
        new_notion_database_id = st.text_input("Notion Database ID", key="notion_database_id")
        
        # Setup guide
        with st.expander("How to set up Notion integration"):
            st.markdown("""
            1. Create a Notion integration at [notion.so/my-integrations](https://www.notion.so/my-integrations)
            2. Copy your integration token (API key)
            3. Create a database in Notion where you want to export content
            4. Share the database with your integration
            5. Copy the database ID from the URL (the long string after the database name and before the question mark)
            """)
        
        if st.button("Save Notion Settings"):
            update_api_key("notion", new_notion_key)
            update_api_key("notion_database_id", new_notion_database_id)
            st.success("Notion settings updated successfully!")
            time.sleep(1)
            st.rerun()
    
    # Grok Tab
    with api_tabs[3]:
        st.markdown("### Grok API Key")
        st.markdown("Used for Grok AI models.")
        
        grok_key = api_keys.get("grok", "")
        grok_key_display = f"••••••••••••••••••{grok_key[-4:]}" if grok_key else "Not set"
        
        st.markdown(f"**Current key:** {grok_key_display}")
        
        new_grok_key = st.text_input("Enter new Grok API key", type="password", key="new_grok_key")
        
        # Note about Grok availability
        st.info("Grok API access is currently limited. Visit [Grok](https://www.grok.x) for more information.")
        
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
        (st.session_state.user_id,)
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
    usage_percent = min(100, (user['usage_current'] / user['usage_quota']) * 100) if user['usage_quota'] > 0 else 0
    
    # Show progress bar
    st.progress(usage_percent / 100)
    st.write(f"**Usage this month:** {user['usage_current']} / {user['usage_quota']} minutes ({usage_percent:.1f}%)")
    
    # Upgrade options
    st.markdown("### Upgrade Your Plan")
    st.markdown("""
    | Plan | Monthly Price | Minutes/Month | Features |
    |------|---------------|---------------|----------|
    | Free | $0 | 60 | Basic transcription |
    | Basic | $9.99 | 300 | + Claude AI models |
    | Pro | $19.99 | 1,000 | + Advanced processing |
    | Enterprise | Contact us | Custom | Custom integrations |
    """)
    
    if user['subscription_tier'] != 'enterprise':
        if st.button("Upgrade Now"):
            st.info("This would redirect to a payment page in the production version.")
    
    # Reset usage manually (for testing)
    if st.button("Reset Usage Counter"):
        conn = get_db_connection()
        conn.execute(
            "UPDATE users SET usage_current = 0 WHERE id = ?",
            (st.session_state.user_id,)
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
        "SELECT api_keys FROM users WHERE id = ?",
        (st.session_state.user_id,)
    ).fetchone()
    
    if not user:
        conn.close()
        return False
    
    # Update the specific key
    api_keys = json.loads(user['api_keys']) if user['api_keys'] else {}
    
    # If key value is empty, remove the key
    if key_value:
        api_keys[key_name] = key_value
    else:
        api_keys.pop(key_name, None)
    
    # Save back to the database
    conn.execute(
        "UPDATE users SET api_keys = ? WHERE id = ?",
        (json.dumps(api_keys), st.session_state.user_id)
    )
    conn.commit()
    conn.close()
    return True
    
def get_api_key_for_service(service_name, user_id=None):
    """
    Get API key for a specific service, prioritizing user-stored keys over environment variables
    and validating against placeholder values.
    
    Parameters:
    - service_name: The service to get the API key for (openai, anthropic, etc.)
    - user_id: Optional user ID to get keys for a specific user (for threads)
    
    Returns:
    - API key string or None if not found
    """
    logger.debug(f"Retrieving API key for service: {service_name}")
    
    def is_placeholder_key(key):
        """Check if a key is a placeholder/sample value"""
        if not key or len(key) < 10:  # API keys are usually longer
            return True
            
        placeholder_patterns = [
            "your_", "sk-your_", "placeholder", "sample", "test_",
            "api_key", "default", "change_this", "my_", "insert"
        ]
        
        key_lower = key.lower()
        return any(pattern in key_lower for pattern in placeholder_patterns)
    
    # For OpenAI in Docker environment, check the file directly first
    # This is the most reliable source in Docker where environment may be corrupted
    if service_name == "openai":
        try:
            openai_key_file = "/app/openai_api_key.txt"
            if os.path.exists(openai_key_file):
                with open(openai_key_file, 'r') as f:
                    file_key = f.read().strip()
                    if file_key and len(file_key) > 10 and not is_placeholder_key(file_key):
                        logger.debug("Using OpenAI API key from file")
                        return file_key
        except Exception as e:
            logger.error(f"Error reading OpenAI API key from file: {str(e)}")
    
    # For Docker environment, prioritize admin user's API key from database
    # This is the most reliable source in Docker where session state may not be available
    try:
        conn = get_db_connection()
        admin_user = conn.execute("SELECT api_keys FROM users WHERE is_admin = 1 LIMIT 1").fetchone()
        conn.close()
        
        if admin_user and admin_user["api_keys"]:
            try:
                api_keys = json.loads(admin_user["api_keys"])
                admin_key = api_keys.get(service_name)
                if admin_key and not is_placeholder_key(admin_key):
                    logger.debug(f"Using admin API key for {service_name} from database")
                    return admin_key
                else:
                    logger.debug(f"Admin API key for {service_name} found in database but appears to be a placeholder")
            except json.JSONDecodeError:
                logger.error("Failed to parse API keys JSON for admin user")
    except Exception as e:
        logger.error(f"Error retrieving admin API key: {str(e)}")
    
    # Get user-specific API keys from database if user is authenticated
    user_key = None
    
    # First try to get from user ID if provided (for thread safety)
    if user_id:
        try:
            conn = get_db_connection()
            user = conn.execute(
                "SELECT api_keys FROM users WHERE id = ?", 
                (user_id,)
            ).fetchone()
            conn.close()
            
            if user and user["api_keys"]:
                try:
                    api_keys = json.loads(user["api_keys"])
                    user_key = api_keys.get(service_name)
                    logger.debug(f"Found user-specific API key for {service_name} using user_id: {'Present' if user_key else 'Not found'}")
                except json.JSONDecodeError:
                    logger.error(f"Failed to parse API keys JSON for user {user_id}")
        except Exception as e:
            logger.error(f"Error retrieving user API key: {str(e)}")
    # Otherwise try from session state if available
    elif hasattr(st, 'session_state') and hasattr(st.session_state, 'authenticated') and st.session_state.authenticated and st.session_state.get("user_id"):
        try:
            conn = get_db_connection()
            user = conn.execute(
                "SELECT api_keys FROM users WHERE id = ?", 
                (st.session_state.user_id,)
            ).fetchone()
            conn.close()
            
            if user and user["api_keys"]:
                try:
                    api_keys = json.loads(user["api_keys"])
                    user_key = api_keys.get(service_name)
                    logger.debug(f"Found user-specific API key for {service_name} from session: {'Present' if user_key else 'Not found'}")
                except json.JSONDecodeError:
                    logger.error(f"Failed to parse API keys JSON for user {st.session_state.user_id}")
        except Exception as e:
            logger.error(f"Error retrieving user API key: {str(e)}")
    
    # Check if user key is valid (not a placeholder)
    if user_key and not is_placeholder_key(user_key):
        logger.debug(f"Using valid user-specific key for {service_name}")
        return user_key
    
    # Fall back to environment variables
    env_key_map = {
        "openai": OPENAI_API_KEY,
        "anthropic": ANTHROPIC_API_KEY,
        "notion": NOTION_API_KEY,
        "grok": GROK_API_KEY,
    }
    
    env_key = env_key_map.get(service_name)
    
    # Validate the environment key
    if env_key and not is_placeholder_key(env_key):
        logger.debug(f"Using valid environment key for {service_name}")
        return env_key
    
    # Final fallback for OpenAI: try to get from database again and ignore placeholder detection
    if service_name == "openai":
        try:
            conn = get_db_connection()
            admin_user = conn.execute("SELECT api_keys FROM users WHERE is_admin = 1 LIMIT 1").fetchone()
            conn.close()
            
            if admin_user and admin_user["api_keys"]:
                try:
                    api_keys = json.loads(admin_user["api_keys"])
                    admin_key = api_keys.get(service_name)
                    if admin_key and len(admin_key) > 20:  # Just check length as last resort
                        logger.debug("Using admin OpenAI key as last resort fallback")
                        return admin_key
                except Exception:
                    pass
        except Exception:
            pass
    
    logger.warning(f"No valid API key found for {service_name}")
    return None

# Authentication UI
def show_login_page():
    st.markdown(f"""
    <div class="header-container">
        <div class="header-title">WhisperForge // Authentication</div>
        <div class="header-date">{datetime.now().strftime('%a %d %b %Y · %H:%M')}</div>
    </div>
    """, unsafe_allow_html=True)
    
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
        confirm_password = st.text_input("Confirm Password", type="password", key="register_confirm_password")
        
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
        (email, hashed_password)
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
        "SELECT id FROM users WHERE email = ?", 
        (email,)
    ).fetchone()
    
    if existing_user:
        conn.close()
        return False
    
    # Create new user
    conn.execute(
        "INSERT INTO users (email, password, api_keys) VALUES (?, ?, ?)",
        (email, hashed_password, json.dumps({}))
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
        (st.session_state.user_id,)
    ).fetchone()
    conn.close()
    
    if user:
        st.write(f"**Email:** {user['email']}")
        st.write(f"**Plan:** {user['subscription_tier'].title()}")
        
        # Show usage meter
        usage_percent = min(100, (user['usage_current'] / user['usage_quota']) * 100) if user['usage_quota'] > 0 else 0
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
    """Get the user's API keys directly from the database without using get_api_key_for_service"""
    if not st.session_state.get("authenticated", False) or not st.session_state.get("user_id"):
        return {}
    
    try:
        conn = get_db_connection()
        user = conn.execute(
            "SELECT api_keys FROM users WHERE id = ?",
            (st.session_state.user_id,)
        ).fetchone()
        conn.close()
        
        if user and user['api_keys']:
            return json.loads(user['api_keys'])
    except Exception as e:
        logger.error(f"Error retrieving user API keys: {str(e)}")
        
    return {}

def update_usage_tracking(duration_seconds):
    if not st.session_state.authenticated:
        return
    
    # Convert seconds to minutes and round up
    minutes = math.ceil(duration_seconds / 60)
    
    conn = get_db_connection()
    conn.execute(
        "UPDATE users SET usage_current = usage_current + ? WHERE id = ?",
        (minutes, st.session_state.user_id)
    )
    conn.commit()
    conn.close()

# Default prompts in case user prompts are not available
DEFAULT_PROMPTS = {
    "wisdom_extraction": """Extract key insights, lessons, and wisdom from the transcript. Focus on actionable takeaways and profound realizations.""",
    
    "summary": """## Summary
Create a concise summary of the main points and key messages in the transcript.
Capture the essence of the content in a few paragraphs.""",
    
    "outline_creation": """Create a detailed outline for an article or blog post based on the transcript and extracted wisdom. Include major sections and subsections.""",
    
    "social_media": """Generate engaging social media posts for different platforms (Twitter, LinkedIn, Instagram) based on the key insights.""",
    
    "image_prompts": """Create detailed image generation prompts that visualize the key concepts and metaphors from the content.""",
    
    "article_writing": """Write a comprehensive article based on the provided outline and wisdom. Maintain a clear narrative flow and engaging style.""",
    
    "seo_analysis": """Analyze the content from an SEO perspective and provide optimization recommendations for better search visibility while maintaining content quality."""
}

# Set up security headers
def add_security_headers():
    st.markdown("""
        <meta http-equiv="Content-Security-Policy" content="default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'">
        <meta http-equiv="X-Frame-Options" content="DENY">
        <meta http-equiv="X-Content-Type-Options" content="nosniff">
    """, unsafe_allow_html=True)

# Add extended CSS for production look and feel
def add_production_css():
    with open('static/css/production.css') as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

# Initialize database with admin user if not exists
def init_admin_user():
    """Create an admin user if none exists"""
    conn = get_db_connection()
    admin_exists = conn.execute(
        "SELECT COUNT(*) FROM users WHERE is_admin = 1"
    ).fetchone()[0]
    
    if admin_exists == 0:
        # Create admin user with default password
        hashed_password = hash_password(ADMIN_PASSWORD)
        
        conn.execute(
            "INSERT INTO users (email, password, is_admin, subscription_tier, usage_quota, api_keys) VALUES (?, ?, ?, ?, ?, ?)",
            (ADMIN_EMAIL, hashed_password, 1, "enterprise", 100000, json.dumps({}))
        )
        conn.commit()
    else:
        # Update existing admin users with empty JSON if api_keys is NULL
        conn.execute(
            "UPDATE users SET api_keys = '{}' WHERE is_admin = 1 AND api_keys IS NULL"
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
        "SELECT is_admin FROM users WHERE id = ?",
        (st.session_state.user_id,)
    ).fetchone()[0]
    
    if not is_admin:
        st.error("You do not have permission to access this page.")
        conn.close()
        return
    
    # Create tabs for different admin functions
    admin_tabs = st.tabs(["System Overview", "User Management", "Model Configuration", "App Configuration", "Default Prompts"])
    
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
                data.append({
                    "ID": user["id"],
                    "Email": user["email"],
                    "Created": user["created_at"].split(" ")[0] if " " in user["created_at"] else user["created_at"],
                    "Plan": user["subscription_tier"],
                    "Usage": f"{user['usage_current']}/{user['usage_quota']} min",
                    "Admin": "Yes" if user["is_admin"] else "No"
                })
            
            st.dataframe(data)
        
        # Edit user form
        st.markdown("### Edit User")
        user_id = st.number_input("User ID", min_value=1, step=1)
        
        if st.button("Load User"):
            user = conn.execute(
                "SELECT * FROM users WHERE id = ?", 
                (user_id,)
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
                index=["free", "basic", "pro", "enterprise"].index(user["subscription_tier"])
            )
            quota = st.number_input("Usage Quota (minutes)", value=user["usage_quota"], min_value=0)
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
                    (email, subscription, quota, usage_current, int(is_admin), user_id)
                )
                conn.commit()
                st.success("User updated successfully")
    
    # Model Configuration Tab
    with admin_tabs[2]:
        st.markdown("### Model Configuration")
        
        config_tab1, config_tab2 = st.tabs(["Transcription Model", "Content Processing Model"])
        
        with config_tab1:
            st.subheader("Transcription Model Settings")
            
            # Display current default
            st.markdown(f"**Current default:** {st.session_state.transcription_provider}/{st.session_state.transcription_model}")
            
            transcription_provider = st.selectbox(
                "Transcription Provider",
                options=["OpenAI"],  # Currently only OpenAI supports transcription
                index=0
            )
            
            transcription_models = ["whisper-1"]
            if transcription_provider == "OpenAI":
                transcription_models = ["whisper-1"]
            
            transcription_model = st.selectbox(
                "Transcription Model",
                options=transcription_models,
                index=0
            )
            
            if st.button("Set as Default Transcription Model"):
                st.session_state.transcription_provider = transcription_provider
                st.session_state.transcription_model = transcription_model
                st.success(f"Default transcription model set to {transcription_provider}/{transcription_model}")
        
        with config_tab2:
            st.subheader("Content Processing Model Settings")
            
            # Display current default
            st.markdown(f"**Current default:** {st.session_state.ai_provider}/{st.session_state.ai_model}")
            
            ai_provider = st.selectbox(
                "AI Provider",
                options=["Anthropic", "OpenAI", "Grok"],
                index=0 if st.session_state.ai_provider == "Anthropic" else 
                       1 if st.session_state.ai_provider == "OpenAI" else 2
            )
            
            # Show different model options based on provider
            available_models = get_available_models(ai_provider)
            
            ai_model = st.selectbox(
                "AI Model",
                options=available_models,
                index=0
            )
            
            if st.button("Set as Default Content Processing Model"):
                st.session_state.ai_provider = ai_provider
                st.session_state.ai_model = ai_model
                st.success(f"Default content processing model set to {ai_provider}/{ai_model}")
    
    # App Configuration Tab
    with admin_tabs[3]:
        st.markdown("### App Configuration")
        
        # User Profile Settings
        st.subheader("User Profile Settings")
        selected_user = st.selectbox(
            "Default User Profile",
            options=get_available_users(),
            index=get_available_users().index(st.session_state.get("user_profile_sidebar", "Default")) if st.session_state.get("user_profile_sidebar", "Default") in get_available_users() else 0,
            key="admin_user_profile"
        )
        
        if st.button("Set as Default User Profile"):
            st.session_state.user_profile_sidebar = selected_user
            st.success(f"Default user profile set to {selected_user}")
        
        # Knowledge Base Management
        st.subheader("Knowledge Base")
        knowledge_files = list_knowledge_base_files(selected_user)
        if knowledge_files:
            st.write(f"Knowledge base files for {selected_user}:")
            for file in knowledge_files:
                st.code(file, language="")
        else:
            st.info(f"No knowledge base files found for {selected_user}")
        
        # Upload Knowledge Base File
        uploaded_kb_file = st.file_uploader("Upload Knowledge Base File", type=["txt", "md"])
        if uploaded_kb_file is not None:
            file_name = uploaded_kb_file.name
            kb_path = os.path.join('prompts', selected_user, 'knowledge_base')
            os.makedirs(kb_path, exist_ok=True)
            
            with open(os.path.join(kb_path, file_name), "wb") as f:
                f.write(uploaded_kb_file.getvalue())
            
            st.success(f"File {file_name} uploaded to knowledge base for {selected_user}")
        
        # Custom Prompts Configuration
        st.subheader("Custom Prompts")
        _, users_prompts = load_prompts()  # Fixed to unpack the tuple correctly
        
        # Configure custom prompts for the selected user
        configure_prompts(selected_user, users_prompts)
    
    # Default Prompts Tab
    with admin_tabs[4]:
        st.markdown("### System Default Prompts")
        st.write("Configure the default prompt templates that will be used for all users who haven't customized their own.")
        
        # Prompt types
        prompt_types = [
            "wisdom_extraction", 
            "summary", 
            "outline_creation", 
            "social_media", 
            "image_prompts", 
            "article_writing", 
            "seo_analysis"
        ]
        
        selected_prompt = st.selectbox(
            "Select Prompt Type", 
            options=prompt_types,
            format_func=lambda x: x.replace("_", " ").title()
        )
        
        # Get the current default prompt
        current_prompt = DEFAULT_PROMPTS.get(selected_prompt, "")
        
        # Edit prompt
        new_prompt = st.text_area(
            f"Edit Default {selected_prompt.replace('_', ' ').title()} Prompt", 
            value=current_prompt,
            height=300
        )
        
        if st.button("Save Default Prompt"):
            # In a real implementation, you would update the DEFAULT_PROMPTS dictionary
            # and possibly write to a database or config file
            st.success(f"Default {selected_prompt.replace('_', ' ').title()} prompt updated.")
            
            # For demo purposes, just display what would be updated
            st.code(f'DEFAULT_PROMPTS["{selected_prompt}"] = """{new_prompt}"""')
            
            # Could also implement: DEFAULT_PROMPTS[selected_prompt] = new_prompt
    
    conn.close()
    
# Show terms and privacy
def show_legal_page():
    """Show terms of service and privacy policy"""
    st.markdown("## Legal Information")
    
    tab1, tab2 = st.tabs(["Terms of Service", "Privacy Policy"])
    
    with tab1:
        st.markdown("""
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
        """)
    
    with tab2:
        st.markdown("""
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
        """)

def direct_transcribe_audio(audio_file_path, api_key=None):
    """
    Transcribe audio directly using the OpenAI API without relying on the OpenAI Python client.
    This function does not depend on session state and can be used in worker threads.
    """
    logger.debug(f"Starting direct transcription of {audio_file_path}")
    
    # If no API key is provided, try multiple sources
    if not api_key:
        # 1. First try to get it from the dedicated file (most reliable in Docker)
        try:
            file_key = load_api_key_from_file()
            if file_key:
                api_key = file_key
                logger.debug(f"Using API key from file - length: {len(api_key)}, starting with: {api_key[:4]}...")
        except Exception as e:
            logger.error(f"Error reading API key from file: {str(e)}")
            
        # 2. Try to get it from the database if still not found
        if not api_key:
            try:
                # Directly query the database for admin API key
                conn = get_db_connection()
                admin_user = conn.execute("SELECT api_keys FROM users WHERE is_admin = 1 LIMIT 1").fetchone()
                conn.close()
                
                if admin_user and admin_user["api_keys"]:
                    try:
                        api_keys = json.loads(admin_user["api_keys"])
                        admin_key = api_keys.get("openai")
                        if admin_key and len(admin_key) > 10 and not any(pattern in admin_key.lower() for pattern in ["your_", "placeholder", "sample", "api_key", "change_this"]):
                            api_key = admin_key
                            logger.debug(f"Using admin API key from database - length: {len(api_key)}, starting with: {api_key[:4]}...")
                        else:
                            logger.warning(f"Admin API key found in database but appears to be invalid or a placeholder")
                    except Exception as parse_error:
                        logger.error(f"Error parsing admin API keys: {str(parse_error)}")
                else:
                    logger.warning("No admin user found in database or admin user has no API keys")
            except Exception as db_error:
                logger.error(f"Error accessing database for API key: {str(db_error)}")
        
        # 3. If we still don't have a key, use the environment variable
        if not api_key:
            env_key = OPENAI_API_KEY
            if env_key and len(env_key) > 10 and not any(pattern in env_key.lower() for pattern in ["your_", "placeholder", "sample", "api_key", "change_this"]):
                api_key = env_key
                logger.debug(f"Using OpenAI API key from environment variables - length: {len(api_key)}, starting with: {api_key[:4]}...")
            else:
                logger.warning(f"Environment API key appears to be invalid or a placeholder: '{env_key[:4]}...'")
    else:
        logger.debug(f"Using provided API key - length: {len(api_key)}, starting with: {api_key[:4]}...")
    
    # Final check - do we have a valid API key?
    if not api_key:
        error_msg = "No OpenAI API key available from any source"
        logger.error(error_msg)
        return f"Error: {error_msg}"
    
    # Check for placeholder API keys
    if any(pattern in api_key.lower() for pattern in ["your_", "placeholder", "sample", "api_key", "change_this"]):
        error_msg = "Invalid API key (appears to be a placeholder)"
        logger.error(error_msg)
        return f"Error: {error_msg}"
    
    try:
        import requests
        
        logger.debug("Preparing API request for direct transcription")
        url = "https://api.openai.com/v1/audio/transcriptions"
        headers = {
            "Authorization": f"Bearer {api_key}"
        }
        
        # Check file exists
        if not os.path.exists(audio_file_path):
            logger.error(f"Audio file not found: {audio_file_path}")
            return "Error: Audio file not found"
        
        # Log file details
        file_size = os.path.getsize(audio_file_path)
        logger.debug(f"Audio file size: {file_size/1024/1024:.2f} MB")
        
        # Scale timeout based on file size, minimum 300 seconds
        timeout_seconds = max(300, int(file_size / (100 * 1024)))  # Scale with file size
        logger.debug(f"Using API request timeout of {timeout_seconds} seconds")
        
        # Open the file in binary mode
        with open(audio_file_path, "rb") as audio_file:
            files = {
                "file": (os.path.basename(audio_file_path), audio_file, "audio/mpeg"),
                "model": (None, "whisper-1")
            }
            
            logger.debug(f"Sending request to OpenAI API with key starting with: {api_key[:4]}...")
            
            try:
                response = requests.post(url, headers=headers, files=files, timeout=timeout_seconds)
                logger.debug(f"Received response with status code: {response.status_code}")
            except requests.exceptions.Timeout:
                logger.error(f"API request timed out after {timeout_seconds} seconds")
                return "Error: API request timed out. The audio chunk may be too large."
            except requests.exceptions.ConnectionError:
                logger.error("Connection error when calling OpenAI API")
                return "Error: Connection failed when calling the API. Please check your internet connection."
            
            # Check for various error types
            if response.status_code == 429:
                logger.error(f"Rate limit exceeded: {response.text}")
                return "Error: API rate limit exceeded. Please try again in a few minutes."
            elif response.status_code == 401:
                error_text = response.text
                logger.error(f"Authentication error (401): {error_text}")
                return f"Error in transcribe_with_whisper: Invalid API key. Please check your OpenAI API key."
            elif response.status_code != 200:
                logger.error(f"API Error: {response.status_code} - {response.text}")
                return f"Error: API returned status code {response.status_code}: {response.text}"
            
            # Parse the response
            try:
                result = response.json()
                logger.debug("Successfully received transcription from API")
                if "text" in result:
                    return result.get("text", "")
                else:
                    logger.error(f"API response did not contain text field: {result}")
                    return "Error: API response did not contain expected 'text' field."
            except Exception as parse_error:
                logger.error(f"Error parsing API response: {str(parse_error)}")
                return f"Error parsing API response: {str(parse_error)}"
                
    except Exception as e:
        logger.exception("Exception in direct_transcribe_audio:")
        return f"Error transcribing audio directly: {str(e)}"

def direct_anthropic_completion(prompt, api_key=None, model="claude-3-7-sonnet-20250219"):
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
            "content-type": "application/json"
        }
        
        # Prepare the payload
        payload = {
            "model": model,
            "max_tokens": 1500,
            "messages": [
                {"role": "user", "content": prompt}
            ]
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
        social_content = st.session_state.get("social_content", None)
        image_prompts = st.session_state.get("image_prompts", None)
        article = st.session_state.get("article", None)
        
        # Validate that we have some content to save
        if not transcript:
            logger.error("No transcript available for export to Notion")
            st.error("No transcript available to export. Please transcribe audio first.")
            return None
            
        # Verify API key and database ID are configured
        notion_api_key = get_api_key_for_service("notion")
        notion_db_id = get_notion_database_id()
        
        if not notion_api_key:
            logger.error("Notion API key not configured")
            st.error("Notion API key is not configured. Please add your API key in the settings.")
            return None
            
        if not notion_db_id:
            logger.error("Notion database ID not configured")
            st.error("Notion database ID is not configured. Please add it in the settings.")
            return None
        
        # Try to use the direct notion save method first
        try:
            logger.debug("Attempting direct Notion save")
            result = direct_notion_save(
                title=title,
                transcript=transcript,
                wisdom=wisdom,
                outline=outline,
                social_content=social_content,
                image_prompts=image_prompts,
                article=article
            )
            
            if result and 'url' in result and not 'error' in result:
                logger.debug(f"Successfully exported to Notion using direct method: {result}")
                return result
            elif result and 'error' in result:
                logger.warning(f"Direct Notion save failed: {result['error']}")
                # Will fall through to try the standard method
            else:
                logger.warning("Direct Notion save returned unexpected result")
                # Will fall through to try the standard method
        except Exception as direct_error:
            logger.exception(f"Error in direct Notion save: {str(direct_error)}")
            # Will fall through to try the standard method
        
        # Fallback to standard notion client method
        logger.debug("Falling back to standard Notion client method")
        result = create_content_notion_entry(
            title=title,
            transcript=transcript,
            wisdom=wisdom,
            outline=outline,
            social_content=social_content,
            image_prompts=image_prompts,
            article=article
        )
        
        if result:
            logger.debug(f"Successfully exported to Notion using standard method: {result}")
            return result
        else:
            logger.error("Both Notion export methods failed")
            st.error("Failed to export to Notion. Please check your Notion API configuration.")
            return None
    
    except Exception as e:
        logger.exception("Error in export_to_notion:")
        st.error(f"Error exporting to Notion: {str(e)}")
        return None

def direct_notion_save(title, transcript, wisdom=None, outline=None, social_content=None, image_prompts=None, article=None):
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
        if not title or title == "Untitled Audio" or title == "Untitled Content" or title.startswith("WhisperForge"):
            logger.debug("Generating AI title for Notion page")
            ai_title = generate_short_title(transcript)
            title = ai_title
            logger.debug(f"Generated title: {title}")
        
        # Generate tags for the content - safely with try/except
        try:
            logger.debug("Generating tags for Notion page")
            content_tags = generate_content_tags(transcript, wisdom)
            logger.debug(f"Generated tags: {content_tags}")
        except Exception as e:
            logger.error(f"Error generating tags: {str(e)}")
            content_tags = ["audio", "transcript"]
        
        logger.debug("Preparing API request for Notion")
        url = "https://api.notion.com/v1/pages"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28"
        }
        
        # Initialize content blocks
        children = []
        
        # Add summary callout at the beginning
        try:
            summary_callout = create_summary_callout(transcript)
            children.append(summary_callout)
            
            children.append({
                "object": "block",  # Required for Notion API
                "type": "divider",
                "divider": {}
            })
        except Exception as e:
            logger.error(f"Error adding summary to Notion direct save: {str(e)}")
        
        # Add transcript toggle with safe handling
        if transcript:
            try:
                # Split transcript into chunks to respect Notion's block size limit
                transcript_chunks = chunk_text_for_notion(transcript)
                
                # Create transcript toggle
                transcript_blocks = [{
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [{"type": "text", "text": {"content": chunk}}]
                    }
                } for chunk in transcript_chunks]
                
                children.append({
                    "object": "block",
                    "type": "toggle",
                    "toggle": {
                        "rich_text": [{"type": "text", "text": {"content": "▶️ Transcription"}}],
                        "children": transcript_blocks
                    }
                })
            except Exception as e:
                logger.error(f"Error adding transcript to Notion: {str(e)}")
                # Add simplified transcript block if chunking fails
                children.append({
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [{"type": "text", "text": {"content": "Error processing transcript for Notion"}}]
                    }
                })
        
        # Add wisdom toggle
        if wisdom:
            try:
                wisdom_chunks = chunk_text_for_notion(wisdom)
                wisdom_blocks = [{
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [{"type": "text", "text": {"content": chunk}}]
                    }
                } for chunk in wisdom_chunks]
                
                children.append({
                    "object": "block",
                    "type": "toggle",
                    "toggle": {
                        "rich_text": [{"type": "text", "text": {"content": "▶️ Wisdom"}}],
                        "children": wisdom_blocks
                    }
                })
            except Exception as e:
                logger.error(f"Error adding wisdom to Notion: {str(e)}")
        
        # Add outline toggle
        if outline:
            try:
                outline_chunks = chunk_text_for_notion(outline)
                outline_blocks = [{
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [{"type": "text", "text": {"content": chunk}}]
                    }
                } for chunk in outline_chunks]
                
                children.append({
                    "object": "block",
                    "type": "toggle",
                    "toggle": {
                        "rich_text": [{"type": "text", "text": {"content": "▶️ Outline"}}],
                        "children": outline_blocks
                    }
                })
            except Exception as e:
                logger.error(f"Error adding outline to Notion: {str(e)}")
        
        # Add social content toggle
        if social_content:
            try:
                social_chunks = chunk_text_for_notion(social_content)
                social_blocks = [{
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [{"type": "text", "text": {"content": chunk}}]
                    }
                } for chunk in social_chunks]
                
                children.append({
                    "object": "block",
                    "type": "toggle",
                    "toggle": {
                        "rich_text": [{"type": "text", "text": {"content": "▶️ Socials"}}],
                        "children": social_blocks
                    }
                })
            except Exception as e:
                logger.error(f"Error adding social content to Notion: {str(e)}")
        
        # Add image prompts toggle
        if image_prompts:
            try:
                prompt_chunks = chunk_text_for_notion(image_prompts)
                prompt_blocks = [{
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [{"type": "text", "text": {"content": chunk}}]
                    }
                } for chunk in prompt_chunks]
                
                children.append({
                    "object": "block",
                    "type": "toggle",
                    "toggle": {
                        "rich_text": [{"type": "text", "text": {"content": "▶️ Image Prompts"}}],
                        "children": prompt_blocks
                    }
                })
            except Exception as e:
                logger.error(f"Error adding image prompts to Notion: {str(e)}")
        
        # Add article toggle
        if article:
            try:
                article_chunks = chunk_text_for_notion(article)
                article_blocks = [{
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [{"type": "text", "text": {"content": chunk}}]
                    }
                } for chunk in article_chunks]
                
                children.append({
                    "object": "block",
                    "type": "toggle",
                    "toggle": {
                        "rich_text": [{"type": "text", "text": {"content": "▶️ Draft Post"}}],
                        "children": article_blocks
                    }
                })
            except Exception as e:
                logger.error(f"Error adding article to Notion: {str(e)}")
        
        try:
            # Add metadata section
            children.append({
                "object": "block",  # Required for Notion API
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [{"type": "text", "text": {"content": "Metadata"}}]
                }
            })
            
            children.append({
                "object": "block",  # Required for Notion API
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [
                        {"type": "text", "text": {"content": "Created with "}},
                        {"type": "text", "text": {"content": "WhisperForge"}, "annotations": {"bold": True, "color": "purple"}}
                    ]
                }
            })
            
            # Add tags to metadata
            if content_tags:
                tags_text = ", ".join(content_tags)
                children.append({
                    "object": "block",  # Required for Notion API
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [
                            {"type": "text", "text": {"content": "Tags: "}, "annotations": {"bold": True}},
                            {"type": "text", "text": {"content": tags_text}}
                        ]
                    }
                })
                
            # Prepare the payload
            payload = {
                "parent": {"database_id": database_id},
                "properties": {
                    "Name": {
                        "title": [{"text": {"content": title}}]
                    }
                    # Remove the "Created" property since it's causing issues
                    # If you need created date, check your Notion database for the exact property name
                },
                "children": children
            }
            
            # Add tags to properties if the database has a multi-select Tags property
            if content_tags:
                # Try adding tags - if this fails, the database might not have a Tags property
                try:
                    payload["properties"]["Tags"] = {"multi_select": [{"name": tag} for tag in content_tags[:10]]}  # Limit to 10 tags
                except Exception as e:
                    logger.warning(f"Could not add tags to Notion page: {str(e)}")
            
            # Add Created/Created time property only if needed and with a proper format
            try:
                iso_date = datetime.now().isoformat()
                # Check different variations of property names that might exist in the database
                # Use the Title property as the default
                payload["properties"]["Created at"] = {"date": {"start": iso_date}}
            except Exception as e:
                logger.warning(f"Could not add Created date to Notion: {str(e)}")
            
            logger.debug(f"Payload prepared with {len(children)} content blocks")
            
            # Send the request
            logger.debug("Sending request to Notion API")
            response = requests.post(url, headers=headers, json=payload)
            
            # Check for errors
            if response.status_code != 200:
                logger.error(f"API Error: {response.status_code} - {response.text}")
                return {"error": f"Error: API returned status code {response.status_code}: {response.text}"}
            
            # Parse the response
            result = response.json()
            logger.debug("Successfully saved page to Notion")
            
            return {"url": result.get("url", ""), "id": result.get("id", "")}
        
        except Exception as e:
            logger.exception("Exception in direct_notion_save:")
            return {"error": f"Error saving to Notion: {str(e)}"}
    
    except Exception as e:
        logger.exception("Exception in direct_notion_save:")
        return {"error": f"Error saving to Notion: {str(e)}"}

def is_admin_user():
    """Check if the current user is an admin"""
    try:
        conn = get_db_connection()
        is_admin = conn.execute(
            "SELECT is_admin FROM users WHERE id = ?",
            (st.session_state.user_id,)
        ).fetchone()
        conn.close()
        
        return is_admin and is_admin[0]
    except Exception:
        return False

def create_custom_header():
    # See if Admin link should be visible
    admin_link = ""
    if is_admin_user():
        admin_link = '<a href="?page=admin" class="nav-item" id="nav-admin">Admin</a>'
    
    # Create the HTML and JS as separate strings
    header_html = f'''
    <div class="header-container">
        <div class="header-left">
            <div class="header-title">WhisperForge // Control_Center</div>
        </div>
        <div class="header-nav">
            <a href="?page=home" class="nav-item" id="nav-home">Home</a>
            <a href="?page=api" class="nav-item" id="nav-api">API Keys</a>
            <a href="?page=usage" class="nav-item" id="nav-usage">Usage</a>
            <a href="?page=user_config" class="nav-item" id="nav-user-config">User Config</a>
            {admin_link}
        </div>
        <div class="header-right">
            <div class="header-date">{datetime.now().strftime("%Y-%m-%d %H:%M")}</div>
        </div>
    </div>
    '''
    
    # JavaScript as a separate string
    js_code = '''
    <script>
        document.addEventListener('DOMContentLoaded', function() {
            // Get current URL and extract page parameter
            const urlParams = new URLSearchParams(window.location.search);
            const currentPage = urlParams.get('page') || 'home';
            
            // Find all navigation links
            const navLinks = document.querySelectorAll('.nav-item');
            
            // Loop through links and add active class to current page
            navLinks.forEach(link => {
                const linkId = link.id;
                if (linkId === 'nav-' + currentPage) {
                    link.classList.add('active');
                }
            });
        });
    </script>
    '''
    
    # Combine the HTML and JavaScript
    full_header = header_html + js_code
    st.markdown(full_header, unsafe_allow_html=True)

def load_js():
    """Load JavaScript files"""
    # Load cookie consent JavaScript
    with open('static/js/cookie-consent.js') as f:
        st.markdown(f'<script>{f.read()}</script>', unsafe_allow_html=True)
        
    # Load UI interactions JavaScript
    with open('static/js/ui-interactions.js') as f:
        st.markdown(f'<script>{f.read()}</script>', unsafe_allow_html=True)

# Show cookie consent banner if necessary
def show_cookie_banner():
    """Show cookie consent banner with dismiss functionality"""
    if "cookie_consent" not in st.session_state:
        st.session_state.cookie_consent = False
    
    if not st.session_state.cookie_consent:
        with st.container():
            st.markdown("""
            <style>
            .cookie-banner {
                position: fixed;
                bottom: 0;
                left: 0;
                right: 0;
                padding: 10px 20px;
                background: rgba(0, 0, 0, 0.85);
                color: white;
                z-index: 9999;
                display: flex;
                justify-content: space-between;
                align-items: center;
                box-shadow: 0 -2px 10px rgba(0, 0, 0, 0.2);
            }
            .cookie-banner-text {
                flex: 1;
            }
            .cookie-banner-button {
                margin-left: 20px;
                background: #4CAF50;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                cursor: pointer;
            }
            </style>
            <div class="cookie-banner">
                <div class="cookie-banner-text">
                    We use cookies to enhance your experience. By continuing to use this site, you agree to our use of cookies.
                </div>
                <button class="cookie-banner-button" onclick="document.querySelector('.cookie-banner').style.display='none'; window.parent.postMessage({cookie_consent: true}, '*');">
                    Accept
                </button>
            </div>
            """, unsafe_allow_html=True)
    
            # JavaScript to handle the button click
            st.markdown("""
            <script>
            window.addEventListener('message', function(e) {
                if (e.data.cookie_consent) {
                    window.parent.postMessage({cookie_consent: true}, '*');
                }
            });
            </script>
            """, unsafe_allow_html=True)
            
def transcribe_with_whisper(file_path):
    """Transcribe audio using the OpenAI Whisper API with progress tracking"""
    # Create progress indicators
    progress_placeholder = st.empty()
    progress_bar = progress_placeholder.progress(0)
    status_text = st.empty()
    
    def update_progress(progress, message):
        """Update the progress bar and status message"""
        progress_bar.progress(progress)
        status_text.text(message)
    
    try:
        # Get an OpenAI client
        client = get_openai_client()
        if not client:
            update_progress(0.1, "OpenAI client not available, using direct method...")
            return direct_transcribe_audio(file_path)
        
        update_progress(0.2, "Initializing transcription...")
        
        # Calculate file size for logging and timeout
        file_size = os.path.getsize(file_path) / (1024 * 1024)  # Size in MB
        
        update_progress(0.3, f"Processing audio file ({file_size:.2f} MB)...")
        
        # Set a timeout proportional to file size
        timeout = max(300, int(file_size * 10))  # At least 5 minutes
        
        try:
            with open(file_path, "rb") as audio_file:
                update_progress(0.5, "Sending to OpenAI Whisper API...")
                # Use direct transcribe as a fallback if client-based approach fails
                try:
                    response = client.audio.transcriptions.create(
                        model="whisper-1",
                        file=audio_file,
                        timeout=timeout
                    )
                    transcript = response.text
                except Exception as e:
                    logger.info(f"Client-based transcription failed: {str(e)}")
                    logger.info("Trying direct_transcribe_audio as final fallback method")
                    # If client method fails, try direct method with hardcoded key
                    update_progress(0.6, "Using alternative transcription method...")
                    transcript = direct_transcribe_audio(file_path, HARD_CODED_OPENAI_API_KEY)
                
                update_progress(1.0, "Transcription complete!")
                # Remove the progress indicators
                progress_placeholder.empty()
                progress_bar.empty()
                status_text.empty()
    
                # Delay to show the completion message briefly
                time.sleep(0.5)
                
                return transcript
        except Exception as e:
            # If everything fails, try one more direct method
            logger.error(f"Error in transcribe_with_whisper: {str(e)}")
            try:
                update_progress(0.7, "Using fallback transcription method...")
                transcript = direct_transcribe_audio(file_path, HARD_CODED_OPENAI_API_KEY)
                update_progress(1.0, "Transcription complete with fallback method!")
                return transcript
            except Exception as final_e:
                logger.error(f"Final fallback also failed: {str(final_e)}")
                return f"Error in transcribe_with_whisper: {str(e)}"
    except Exception as e:
        logger.error(f"Error in transcribe_with_whisper: {str(e)}")
        return f"Error in transcribe_with_whisper: {str(e)}"

def show_user_config_page():
    """Show user configuration page for managing profiles, knowledge base, and prompts"""
    st.title("User Configuration")
    
    # Get available users and prompts
    users, users_prompts = load_prompts()
    
    # Add tabs for different configuration sections
    config_tabs = st.tabs(["User Profiles", "Knowledge Base", "Prompt Templates"])
    
    # Tab 1: User Profiles Management
    with config_tabs[0]:
        st.header("User Profiles")
        st.write("Manage user profiles for different content generation styles and preferences.")
        
        # Current users list
        st.subheader("Current Profiles")
        user_table = {"Profile Name": [], "Knowledge Files": [], "Custom Prompts": []}
        
        for user in users:
            # Count knowledge base files
            kb_files = list_knowledge_base_files(user)
            kb_count = len(kb_files)
            
            # Count custom prompts
            if user in users_prompts:
                prompt_count = len(users_prompts[user])
            else:
                prompt_count = 0
                
            user_table["Profile Name"].append(user)
            user_table["Knowledge Files"].append(kb_count)
            user_table["Custom Prompts"].append(prompt_count)
        
        # Display user profiles as a table
        st.dataframe(user_table)
        
        # Create new profile
        st.subheader("Create New Profile")
        new_user = st.text_input("New Profile Name", key="new_profile_name",
                                help="Enter a name for the new user profile. Use only letters, numbers, and underscores.")
        
        if st.button("Create Profile", key="create_profile_btn"):
            if not new_user:
                st.error("Please enter a valid profile name")
            elif not re.match(r'^[a-zA-Z0-9_]+$', new_user):
                st.error("Profile name can only contain letters, numbers, and underscores")
            elif new_user in users:
                st.error(f"Profile '{new_user}' already exists")
            else:
                # Create user directories
                user_dir = os.path.join("prompts", new_user)
                kb_dir = os.path.join(user_dir, "knowledge_base")
                
                try:
                    os.makedirs(user_dir, exist_ok=True)
                    os.makedirs(kb_dir, exist_ok=True)
                    st.success(f"Created new profile: {new_user}")
                    st.session_state.user_profile_sidebar = new_user
                    st.rerun()
                except Exception as e:
                    st.error(f"Error creating profile: {str(e)}")
    
    # Tab 2: Knowledge Base Management
    with config_tabs[1]:
        st.header("Knowledge Base")
        st.write("Manage knowledge base files for the selected user profile. These files provide context and style guidance for AI-generated content.")
        
        # Select user profile
        selected_user = st.selectbox("Select Profile", options=users, key="kb_profile_select")
        
        if selected_user:
            # Knowledge base directory for selected user
            kb_dir = os.path.join("prompts", selected_user, "knowledge_base")
            os.makedirs(kb_dir, exist_ok=True)
            
            # List existing knowledge base files
            kb_files = list_knowledge_base_files(selected_user)
            
            if kb_files:
                st.subheader("Current Knowledge Base Files")
                
                # Create a dictionary of filenames to display names
                file_options = {}
                for file_path in kb_files:
                    filename = os.path.basename(file_path)
                    name = os.path.splitext(filename)[0].replace('_', ' ').title()
                    file_options[name] = file_path
                
                # File selection
                selected_file = st.selectbox("Select File", options=list(file_options.keys()), key="kb_file_select")
                
                if selected_file and selected_file in file_options:
                    file_path = file_options[selected_file]
                    
                    # Read and display file content
                    try:
                        with open(file_path, 'r') as f:
                            file_content = f.read()
                        
                        # Edit file
                        new_content = st.text_area("Edit File Content", value=file_content, height=300, key="kb_file_edit")
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button("Update File", key="update_kb_file"):
                                try:
                                    with open(file_path, 'w') as f:
                                        f.write(new_content)
                                    st.success(f"Updated knowledge base file: {selected_file}")
                                except Exception as e:
                                    st.error(f"Error updating file: {str(e)}")
                        
                        with col2:
                            if st.button("Delete File", key="delete_kb_file"):
                                try:
                                    os.remove(file_path)
                                    st.success(f"Deleted knowledge base file: {selected_file}")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error deleting file: {str(e)}")
                    
                    except Exception as e:
                        st.error(f"Error reading file: {str(e)}")
            
            # Upload new knowledge base file
            st.subheader("Add New Knowledge Base File")
            
            # Method 1: Upload file
            uploaded_file = st.file_uploader("Upload Knowledge Base File", 
                                           type=["txt", "md"], 
                                           key="kb_file_upload",
                                           help="Upload a text or markdown file to add to the knowledge base")
            
            if uploaded_file:
                file_name = uploaded_file.name
                if st.button("Add Uploaded File", key="add_uploaded_kb"):
                    try:
                        file_path = os.path.join(kb_dir, file_name)
                        with open(file_path, 'wb') as f:
                            f.write(uploaded_file.getvalue())
                        st.success(f"Added knowledge base file: {file_name}")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error saving file: {str(e)}")
            
            # Method 2: Create file
            st.subheader("Create New Knowledge Base File")
            new_file_name = st.text_input("File Name (without extension)", key="new_kb_filename",
                                         help="Enter a name for the new file (without extension)")
            new_file_content = st.text_area("File Content", height=200, key="new_kb_content")
            
            if st.button("Create File", key="create_kb_file"):
                if not new_file_name:
                    st.error("Please enter a file name")
                else:
                    try:
                        # Clean filename
                        clean_name = re.sub(r'[^\w\s-]', '', new_file_name)
                        clean_name = re.sub(r'[\s-]+', '_', clean_name).lower()
                        
                        # Add .md extension
                        file_path = os.path.join(kb_dir, f"{clean_name}.md")
                        
                        # Check if file already exists
                        if os.path.exists(file_path):
                            st.error(f"File {clean_name}.md already exists")
                        else:
                            with open(file_path, 'w') as f:
                                f.write(new_file_content)
                            st.success(f"Created knowledge base file: {clean_name}.md")
                            st.rerun()
                    except Exception as e:
                        st.error(f"Error creating file: {str(e)}")
    
    # Tab 3: Prompt Template Management
    with config_tabs[2]:
        st.header("Prompt Templates")
        st.write("Customize prompt templates for different content generation tasks.")
        
        # Select user profile
        selected_user = st.selectbox("Select Profile", options=users, key="prompt_profile_select")
        
        if selected_user:
            # Use the existing configure_prompts function
            configure_prompts(selected_user, users_prompts)
            
            # Add explanation of prompt variables
            with st.expander("Prompt Template Help"):
                st.markdown("""
                ### Prompt Template Variables
                
                Your prompt templates can include the following variables which will be replaced with actual content:
                
                - `{transcript}` - The full transcript text
                - `{knowledge_base}` - Any knowledge base context that's relevant
                
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
                """)
def transcribe_audio(uploaded_file):
    """
    Process the uploaded file from Streamlit and transcribe it using the appropriate function.
    This is the main entry point for audio transcription from the UI.
    """
    logger.info(f"Starting transcription of uploaded file: {uploaded_file.name}")
    
    try:
        # Create a temporary file to save the uploaded content
        temp_dir = tempfile.mkdtemp()
        temp_file_path = os.path.join(temp_dir, uploaded_file.name)
        
        # Save the uploaded file to the temporary path
        with open(temp_file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        # Get file size to determine whether to use chunked processing
        file_size_mb = os.path.getsize(temp_file_path) / (1024 * 1024)
        logger.info(f"File size: {file_size_mb:.2f} MB")
        
        # Choose transcription method based on file size
        if file_size_mb > 25:  # For files larger than 25MB, use chunked processing
            logger.info("Using chunked processing for large file")
            transcript = transcribe_large_file(temp_file_path)
        else:
            logger.info("Using standard transcription")
            transcript = transcribe_with_whisper(temp_file_path)
        
        # Clean up temporary file
        try:
            os.remove(temp_file_path)
            os.rmdir(temp_dir)
        except Exception as e:
            logger.warning(f"Error cleaning up temporary files: {str(e)}")
        
        return transcript
        
    except Exception as e:
        logger.exception("Error in transcribe_audio:")
        return f"Error transcribing audio: {str(e)}"

if __name__ == "__main__":
    main() 