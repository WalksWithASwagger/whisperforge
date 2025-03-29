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

# This must be the very first st.* command
st.set_page_config(
    page_title="WhisperForge",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load environment variables
load_dotenv()

# Database setup
def get_db_connection():
    conn = sqlite3.connect('whisperforge.db', check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
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
    logger.debug("Checking environment variables that might affect client initialization:")
    for env_var in os.environ:
        if 'proxy' in env_var.lower() or 'http_' in env_var.lower() or 'openai' in env_var.lower():
            logger.debug(f"  Found environment variable: {env_var}")
    
    # Create client with just the API key, no extra parameters
    try:
        logger.debug("Attempting to initialize OpenAI client with ONLY api_key parameter")
        
        # Create a completely clean approach - don't use any environment variables
        client_kwargs = {'api_key': api_key}
        
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
        if 'proxies' in error_msg:
            logger.debug("Trying alternative initialization approach due to proxies error")
            try:
                # Alternative approach - don't use OpenAI client class directly
                # Instead use a simple function-based approach
                
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
        st.error("Anthropic API key is not set. Please add your API key in the settings.")
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
    }
}

def local_css():
    """Apply refined cyberpunk styling inspired by Luma's interface"""
    st.markdown("""
    <style>
    /* Refined Cyberpunk Theme - WhisperForge Command Center */
    
    /* Base variables for limited color palette */
    :root {
        --bg-primary: #121218;
        --bg-secondary: #1a1a24;
        --bg-tertiary: #222230;
        --accent-primary: #7928CA;
        --accent-secondary: #FF0080;
        --text-primary: #f0f0f0;
        --text-secondary: #a0a0a0;
        --text-muted: #707070;
        --success: #36D399;
        --warning: #FBBD23;
        --error: #F87272;
        --info: #3ABFF8;
        --border-radius: 6px;
        --card-radius: 10px;
        --glow-intensity: 4px;
        --terminal-font: 'JetBrains Mono', 'Courier New', monospace;
        --system-font: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
    }
    
    /* Global styles */
    .stApp {
        background: linear-gradient(160deg, var(--bg-primary) 0%, #0f0f17 100%);
        color: var(--text-primary);
        font-family: var(--system-font);
    }
    
    /* Clean, compact header */
    .header-container {
        border-radius: var(--card-radius);
        background: linear-gradient(110deg, rgba(121, 40, 202, 0.10) 0%, rgba(0, 0, 0, 0) 80%);
        border: 1px solid rgba(121, 40, 202, 0.25);
        padding: 12px 20px;
        margin-bottom: 20px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        position: relative;
        overflow: hidden;
    }
    
    .header-container::before {
        content: "";
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 1px;
        background: linear-gradient(90deg, transparent, rgba(121, 40, 202, 0.5), transparent);
        animation: header-shine 3s ease-in-out infinite;
    }
    
    @keyframes header-shine {
        0% { transform: translateX(-100%); }
        50% { transform: translateX(100%); }
        100% { transform: translateX(-100%); }
    }
    
    .header-title {
        font-family: var(--terminal-font);
        font-size: 1.4rem;
        font-weight: 500;
        background: linear-gradient(90deg, #7928CA, #FF0080);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        letter-spacing: 0.02em;
    }
    
    .header-date {
        font-family: var(--terminal-font);
        color: var(--text-secondary);
        font-size: 0.85rem;
        opacity: 0.8;
    }
    
    /* Compact status cards */
    .status-container {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 8px;
        margin: 12px 0 18px 0;
    }
    
    .status-card {
        background: linear-gradient(120deg, var(--bg-secondary) 0%, var(--bg-tertiary) 100%);
        border-radius: var(--card-radius);
        padding: 12px;
        transition: all 0.2s ease;
        border: 1px solid rgba(255, 255, 255, 0.05);
        position: relative;
        overflow: hidden;
    }
    
    .status-card:hover {
        border: 1px solid rgba(121, 40, 202, 0.3);
        box-shadow: 0 0 10px rgba(121, 40, 202, 0.15);
    }
    
    .status-card::after {
        content: "";
        position: absolute;
        bottom: 0;
        left: 0;
        right: 0;
        height: 1.5px;
        background: linear-gradient(90deg, transparent, var(--accent-primary), transparent);
        opacity: 0;
        transition: opacity 0.3s ease;
    }
    
    .status-card:hover::after {
        opacity: 1;
    }
    
    .status-card h3 {
        margin: 0;
        color: var(--text-secondary);
        font-size: 0.8rem;
        margin-bottom: 4px;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        font-weight: 500;
    }
    
    .status-value {
        font-size: 1.15rem;
        font-weight: 600;
        text-align: center;
        color: var(--text-primary);
        font-family: var(--terminal-font);
    }
    
    /* Quick access buttons */
    .quick-access {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 8px;
        margin: 12px 0;
    }
    
    .quick-button {
        background: rgba(121, 40, 202, 0.1);
        border-radius: var(--card-radius);
        padding: 10px;
        text-align: center;
        color: var(--text-primary);
        transition: all 0.2s ease;
        cursor: pointer;
        border: 1px solid rgba(121, 40, 202, 0.1);
        font-size: 0.85rem;
        backdrop-filter: blur(4px);
        -webkit-backdrop-filter: blur(4px);
    }
    
    .quick-button:hover {
        background: rgba(121, 40, 202, 0.15);
        border-color: rgba(121, 40, 202, 0.3);
        transform: translateY(-2px);
    }
    
    /* Section headers with subtle underline */
    .section-header {
        color: var(--text-primary);
        font-size: 0.9rem;
        font-weight: 600;
        margin: 20px 0 8px 0;
        padding-bottom: 6px;
        position: relative;
        text-transform: uppercase;
        letter-spacing: 0.1em;
    }
    
    .section-header::after {
        content: "";
        position: absolute;
        left: 0;
        bottom: 0;
        height: 1px;
        width: 100%;
        background: linear-gradient(90deg, var(--accent-primary), transparent);
    }
    
    /* Tabs styling */
    .stTabs [data-baseweb="tab-list"] {
        background-color: var(--bg-secondary);
        border-radius: var(--border-radius);
        padding: 4px;
        border: 1px solid rgba(255, 255, 255, 0.05);
        gap: 2px;
    }
    
    .stTabs [data-baseweb="tab"] {
        border-radius: var(--border-radius);
        color: var(--text-secondary);
        background-color: transparent;
        transition: all 0.2s ease;
        font-size: 0.85rem;
        font-weight: 500;
        padding: 8px 16px;
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        color: var(--text-primary);
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(110deg, rgba(121, 40, 202, 0.15) 0%, rgba(255, 0, 128, 0.05) 100%);
        color: var(--text-primary) !important;
        border: 1px solid rgba(121, 40, 202, 0.25) !important;
    }
    
    /* File uploader styling */
    [data-testid="stFileUploader"] {
        background: linear-gradient(120deg, var(--bg-secondary) 0%, var(--bg-tertiary) 100%);
        border: 1px dashed rgba(121, 40, 202, 0.3);
        border-radius: var(--card-radius);
        padding: 15px;
        transition: all 0.2s ease;
    }
    
    [data-testid="stFileUploader"]:hover {
        border-color: rgba(121, 40, 202, 0.5);
        box-shadow: 0 0 15px rgba(121, 40, 202, 0.15);
    }
    
    /* Button styling */
    .stButton > button {
        background: linear-gradient(110deg, rgba(121, 40, 202, 0.08) 0%, rgba(255, 0, 128, 0.05) 100%);
        border: 1px solid rgba(121, 40, 202, 0.25);
        color: var(--text-primary);
        border-radius: var(--border-radius);
        padding: 8px 16px;
        font-family: var(--system-font);
        transition: all 0.2s ease;
        font-weight: 500;
        font-size: 0.85rem;
    }
    
    .stButton > button:hover {
        background: linear-gradient(110deg, rgba(121, 40, 202, 0.15) 0%, rgba(255, 0, 128, 0.08) 100%);
        border-color: rgba(121, 40, 202, 0.4);
        transform: translateY(-1px);
        box-shadow: 0 3px 10px rgba(0, 0, 0, 0.15);
    }
    
    .stButton > button:active {
        transform: translateY(0px);
    }
    
    /* "I'm Feeling Lucky" special button */
    .lucky-button {
        background: linear-gradient(110deg, rgba(54, 211, 153, 0.1) 0%, rgba(255, 0, 128, 0.05) 100%) !important;
        border: 1px solid rgba(54, 211, 153, 0.3) !important;
    }
    
    .lucky-button:hover {
        background: linear-gradient(110deg, rgba(54, 211, 153, 0.15) 0%, rgba(255, 0, 128, 0.08) 100%) !important;
        border-color: rgba(54, 211, 153, 0.5) !important;
    }
    
    /* Audio player styling */
    audio {
        width: 100%;
        border-radius: var(--border-radius);
        background: var(--bg-secondary);
        margin: 10px 0;
        height: 32px;
    }
    
    /* Text area styling */
    .stTextArea > div > div > textarea {
        background-color: var(--bg-secondary);
        color: var(--text-primary);
        border: 1px solid rgba(121, 40, 202, 0.2);
        border-radius: var(--border-radius);
        padding: 10px;
        font-family: var(--system-font);
    }
    
    .stTextArea > div > div > textarea:focus {
        border: 1px solid rgba(121, 40, 202, 0.4);
        box-shadow: 0 0 0 1px rgba(121, 40, 202, 0.2);
    }
    
    /* Text input styling */
    .stTextInput > div > div > input {
        background-color: var(--bg-secondary);
        color: var(--text-primary);
        border: 1px solid rgba(121, 40, 202, 0.2);
        border-radius: var(--border-radius);
        padding: 8px 12px;
        font-family: var(--system-font);
        height: 36px;
    }
    
    .stTextInput > div > div > input:focus {
        border: 1px solid rgba(121, 40, 202, 0.4);
        box-shadow: 0 0 0 1px rgba(121, 40, 202, 0.2);
    }
    
    /* Selectbox styling */
    .stSelectbox > div {
        background-color: var(--bg-secondary);
    }
    
    .stSelectbox > div > div {
        background-color: var(--bg-secondary);
        color: var(--text-primary);
        border: 1px solid rgba(121, 40, 202, 0.2);
        border-radius: var(--border-radius);
    }
    
    /* Progress bar styling */
    .stProgress > div > div > div {
        background: linear-gradient(90deg, var(--accent-primary), var(--accent-secondary));
        border-radius: var(--border-radius);
    }
    
    /* Expander styling */
    .streamlit-expanderHeader {
        background-color: var(--bg-secondary);
        border-radius: var(--border-radius);
        border: 1px solid rgba(121, 40, 202, 0.1);
        font-size: 0.85rem;
        padding: 8px 12px;
    }
    
    .streamlit-expanderHeader:hover {
        border-color: rgba(121, 40, 202, 0.25);
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background-color: var(--bg-primary);
        border-right: 1px solid rgba(121, 40, 202, 0.15);
    }
    
    [data-testid="stSidebar"] [data-testid="stMarkdown"] h1,
    [data-testid="stSidebar"] [data-testid="stMarkdown"] h2,
    [data-testid="stSidebar"] [data-testid="stMarkdown"] h3 {
        color: var(--accent-primary);
        font-size: 1rem;
    }
    
    /* Content section styling */
    .content-section {
        background: linear-gradient(120deg, var(--bg-secondary) 0%, var(--bg-tertiary) 100%);
        border-radius: var(--card-radius);
        padding: 15px;
        margin: 12px 0;
        border: 1px solid rgba(255, 255, 255, 0.05);
    }
    
    .content-section h3 {
        color: var(--text-primary);
        margin-top: 0;
        margin-bottom: 10px;
        font-weight: 500;
        font-size: 1rem;
        padding-bottom: 8px;
        border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    /* Terminal-style output */
    .terminal-output {
        background-color: rgba(0, 0, 0, 0.2);
        border-left: 2px solid var(--accent-primary);
        border-radius: var(--border-radius);
        padding: 10px 15px;
        font-family: var(--terminal-font);
        color: var(--text-primary);
        font-size: 0.85rem;
        margin: 10px 0;
    }
    
    /* Process indicator */
    .process-indicator {
        display: flex;
        align-items: center;
        justify-content: space-between;
        background: var(--bg-secondary);
        padding: 10px;
        border-radius: var(--border-radius);
        margin: 15px 0;
        border: 1px solid rgba(255, 255, 255, 0.05);
    }
    
    .process-indicator .dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: var(--accent-primary);
        margin-right: 10px;
        animation: pulse 1.5s infinite;
    }
    
    @keyframes pulse {
        0% { opacity: 0.4; }
        50% { opacity: 1; }
        100% { opacity: 0.4; }
    }
    
    .process-status {
        flex-grow: 1;
        font-size: 0.85rem;
    }
    
    /* Notion button styling */
    .notion-button {
        display: inline-block;
        background: linear-gradient(110deg, rgba(121, 40, 202, 0.1) 0%, rgba(255, 0, 128, 0.05) 100%);
        border: 1px solid rgba(121, 40, 202, 0.25);
        border-radius: var(--border-radius);
        padding: 8px 15px;
        color: var(--text-primary);
        text-decoration: none;
        font-family: var(--system-font);
        transition: all 0.2s ease;
        font-size: 0.85rem;
        font-weight: 500;
        margin-top: 10px;
    }
    
    .notion-button:hover {
        background: linear-gradient(110deg, rgba(121, 40, 202, 0.15) 0%, rgba(255, 0, 128, 0.08) 100%);
        border-color: rgba(121, 40, 202, 0.4);
        transform: translateY(-1px);
    }
    
    /* Footer styling */
    .app-footer {
        margin-top: 30px;
        padding-top: 20px;
        border-top: 1px solid rgba(121, 40, 202, 0.15);
        font-size: 0.8rem;
        text-align: center;
        color: var(--text-muted);
    }
    
    .footer-content {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 10px;
    }
    
    .footer-status {
        display: flex;
        justify-content: center;
        gap: 20px;
        margin: 10px 0;
    }
    
    .footer-status span {
        display: flex;
        align-items: center;
        gap: 5px;
    }
    
    .footer-status-dot {
        width: 6px;
        height: 6px;
        border-radius: 50%;
        display: inline-block;
    }
    
    .status-secure .footer-status-dot {
        background-color: var(--success);
        box-shadow: 0 0 5px var(--success);
    }
    
    .status-sovereignty .footer-status-dot {
        background-color: var(--accent-primary);
        box-shadow: 0 0 5px var(--accent-primary);
    }
    
    .status-offline .footer-status-dot {
        background-color: var(--info);
        box-shadow: 0 0 5px var(--info);
    }
    
    /* Animations and effects */
    .scanner-line {
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        height: 1px;
        background: linear-gradient(90deg, transparent, var(--accent-primary), transparent);
        opacity: 0.4;
        z-index: 1000;
        animation: scanner-move 8s linear infinite;
    }
    
    @keyframes scanner-move {
        0% { top: 0; }
        100% { top: 100%; }
    }
    
    /* Toast notifications */
    .toast-notification {
        position: fixed;
        bottom: 20px;
        right: 20px;
        background: var(--bg-secondary);
        border-radius: var(--border-radius);
        padding: 10px 15px;
        border-left: 3px solid var(--success);
        color: var(--text-primary);
        box-shadow: 0 5px 15px rgba(0, 0, 0, 0.3);
        z-index: 1000;
        font-size: 0.85rem;
        animation: toast-in 0.3s ease forwards;
    }
    
    @keyframes toast-in {
        from { transform: translateX(100%); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    </style>
    
    <!-- Add the scanner line animation -->
    <div class="scanner-line"></div>
    """, unsafe_allow_html=True)

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
        audio = AudioSegment.from_file(audio_path)
        
        # Calculate optimal chunk size based on file size
        file_size = os.path.getsize(audio_path)
        file_size_mb = file_size / (1024 * 1024)
        
        # Adjust target chunk size based on file size for better handling of very large files
        if file_size_mb > 300:  # For files larger than 300MB
            target_size_mb = 30  # Larger chunks for very large files
        elif file_size_mb > 100:  # For files between 100-300MB
            target_size_mb = 25  # Medium chunks
        else:
            target_size_mb = 20  # Smaller chunks for better accuracy on smaller files
        
        total_chunks = math.ceil(file_size / (target_size_mb * 1024 * 1024))
        
        # Ensure we have reasonable chunking
        MIN_CHUNK_LENGTH_MS = 5000  # 5 seconds minimum
        MAX_CHUNKS = 30  # Increased from 20 to handle larger files
        
        if total_chunks > MAX_CHUNKS:
            target_size_mb = math.ceil(file_size / (MAX_CHUNKS * 1024 * 1024))
            total_chunks = MAX_CHUNKS
        
        # Adjust chunk size based on audio length rather than just file size
        # This ensures more even chunks with complete sentences
        chunk_length_ms = max(len(audio) // total_chunks, MIN_CHUNK_LENGTH_MS)
        
        # Create temporary directory for chunks
        temp_dir = tempfile.mkdtemp(prefix='whisperforge_chunks_')
        chunks = []
        
        # Show chunking progress
        progress_text = st.empty()
        progress_bar = st.progress(0)
        
        # Try to detect silences to make better chunk boundaries when possible
        try:
            from pydub.silence import detect_silence
            silences = detect_silence(audio, min_silence_len=500, silence_thresh=-40)
            has_silence_data = len(silences) > 0
        except:
            has_silence_data = False
        
        # Process and save chunks
        if has_silence_data and len(silences) > total_chunks:
            # Use silences as natural chunk boundaries
            chunk_points = []
            silence_step = max(1, len(silences) // (total_chunks + 1))
            for i in range(0, len(silences), silence_step):
                if len(chunk_points) < total_chunks - 1:  # Leave room for the last chunk
                    chunk_points.append(silences[i][1])  # End of silence
            
            # Add start and end points
            chunk_points = [0] + chunk_points + [len(audio)]
            
            # Create chunks based on silence points
            for i in range(len(chunk_points) - 1):
                start = chunk_points[i]
                end = chunk_points[i + 1]
                
                if end - start < MIN_CHUNK_LENGTH_MS:
                    continue
                
                chunk = audio[start:end]
                chunk_path = os.path.join(temp_dir, f'chunk_{i}.mp3')
                chunk.export(chunk_path, format='mp3')
                chunks.append(chunk_path)
                
                # Update progress
                progress = (i + 1) / (len(chunk_points) - 1)
                progress_bar.progress(min(progress, 1.0))
                progress_text.text(f"Chunking audio: {min(int(progress * 100), 100)}%")
        else:
            # Standard time-based chunking if silence detection failed
            for i in range(0, len(audio), chunk_length_ms):
                chunk = audio[i:i + chunk_length_ms]
                if len(chunk) < MIN_CHUNK_LENGTH_MS:
                    continue
                    
                # Save chunk with index in filename
                chunk_path = os.path.join(temp_dir, f'chunk_{i//chunk_length_ms}.mp3')
                chunk.export(chunk_path, format='mp3')
                chunks.append(chunk_path)
                
                # Update progress
                progress = (i + chunk_length_ms) / len(audio)
                progress_bar.progress(min(progress, 1.0))
                progress_text.text(f"Chunking audio: {min(int(progress * 100), 100)}%")
        
        progress_text.empty()
        progress_bar.empty()
        
        # Display chunking summary
        st.info(f"Audio split into {len(chunks)} chunks for processing. Total file size: {file_size_mb:.1f} MB")
        
        return chunks, temp_dir
    except Exception as e:
        st.error(f"Error chunking audio: {str(e)}")
        return [], None

def transcribe_chunk(chunk_path, i, total_chunks):
    """Transcribe a single chunk with error handling and progress tracking"""
    try:
        # Get the API key directly
        api_key = get_api_key_for_service("openai")
        if not api_key:
            return f"[Error in chunk {i+1}: OpenAI API key is not configured]"
        
        # Create a fresh client instance with just the API key
        try:
            client = OpenAI(api_key=api_key)
            
            with open(chunk_path, "rb") as audio:
                try:
                    transcript = client.audio.transcriptions.create(
                        model="whisper-1",
                        file=audio
                    )
                    return transcript.text
                except Exception as api_error:
                    error_msg = str(api_error)
                    # Handle specific API errors
                    if "rate limit" in error_msg.lower():
                        return f"[Error in chunk {i+1}: API rate limit exceeded]"
                    elif "api key" in error_msg.lower():
                        return f"[Error in chunk {i+1}: Invalid API key]"
                    elif "proxies" in error_msg.lower() or "client.init" in error_msg.lower():
                        return f"[Error in chunk {i+1}: OpenAI client configuration issue]"
                    else:
                        return f"[Error in chunk {i+1}: {error_msg}]"
        except Exception as client_error:
            return f"[Error initializing OpenAI client for chunk {i+1}: {str(client_error)}]"
    except Exception as e:
        return f"[Error processing chunk {i+1} of {total_chunks}: {str(e)}]"

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
        return "Summary of audio content"

def generate_short_title(text):
    """Generate a 5-7 word descriptive title from the transcript"""
    try:
        openai_client = get_openai_client()
        if not openai_client:
            return "Untitled Audio Transcription"
            
        response = openai_client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[
                {"role": "system", "content": "Create a concise, descriptive 5-7 word title that captures the main topic or theme of this content. Make it clear and engaging. Return ONLY the title words, nothing else."},
                {"role": "user", "content": f"Generate a 5-7 word title for this transcript:\n\n{text[:2000]}..."} # First 2000 chars for context
            ]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        st.error(f"Title generation error: {str(e)}")
        return "Untitled Audio Transcription"

def chunk_text_for_notion(text, chunk_size=1900):
    """Split text into chunks that respect Notion's character limit"""
    if not text:
        return []
    return [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]

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
        content.extend([
            {
                "type": "callout",
                "callout": {
                    "rich_text": [{"type": "text", "text": {"content": summary}}],
                    "color": "purple_background",
                    "icon": {
                        "type": "emoji",
                        "emoji": "💜"
                    }
                }
            },
            {
                "type": "divider",
                "divider": {}
            }
        ])
        
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
        openai_client = get_openai_client()
        if not openai_client:
            return ["audio", "transcription", "content", "notes", "whisperforge"]
            
        # Use OpenAI to generate relevant tags
        prompt = f"""Based on this content:
        Transcript: {transcript[:500]}...
        Wisdom: {wisdom[:500] if wisdom else ''}
        
        Generate 5 relevant one-word tags that describe the main topics and themes.
        Return only the tags separated by commas, lowercase. Examples: spiritual, history, technology, motivation, business"""
        
        response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that generates relevant content tags."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=50,
            temperature=0.3
        )
        
        # Split the response into individual tags and clean them
        tags = [tag.strip().lower() for tag in response.choices[0].message.content.split(',')]
        
        # Ensure we have exactly 5 tags
        while len(tags) < 5:
            tags.append("general")
        return tags[:5]
    except Exception as e:
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
    # Current as of March 2024
    return {
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
            "OpenAI": ["gpt-3.5-turbo", "gpt-4-turbo-preview"],
            "Anthropic": ["claude-3-haiku-20240307", "claude-3-sonnet-20240229", "claude-3-opus-20240229"],
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

def transcribe_large_file(file_path):
    """Process a large audio file by chunking it and transcribing each chunk with concurrent processing"""
    try:
        st.info("Processing large audio file in chunks...")
        
        # Split audio into chunks
        chunks, temp_dir = chunk_audio(file_path)
        if not chunks:
            st.error("Failed to chunk audio file.")
            return ""
        
        # Create progress indicators
        progress_text = st.empty()
        overall_status = st.empty()
        progress_bar = st.progress(0)
        
        overall_status.info(f"Beginning transcription of {len(chunks)} audio segments...")
        
        # Determine optimal number of concurrent processes
        # For very large files (many chunks), we'll use more concurrency
        import os
        import concurrent.futures
        
        # Adjust concurrency based on number of chunks
        if len(chunks) > 20:
            max_workers = min(8, len(chunks))  # Up to 8 workers for very large files
        elif len(chunks) > 10:
            max_workers = min(5, len(chunks))  # Up to 5 workers for medium files
        else:
            max_workers = min(3, len(chunks))  # Up to 3 workers for smaller files
        
        # Set up shared variables for progress tracking
        import threading
        lock = threading.Lock()
        progress_tracker = {
            'completed': 0,
            'success': 0,
            'failed': 0,
            'results': [None] * len(chunks)
        }
        
        # Function for processing a single chunk with progress tracking
        def process_chunk(args):
            chunk_path, idx, total = args
            try:
                # Process the chunk
                chunk_text = transcribe_chunk(chunk_path, idx, total)
                
                # Update progress tracker
                with lock:
                    progress_tracker['completed'] += 1
                    if chunk_text and not any(error_marker in chunk_text for error_marker in ["[Error", "[Failed", "[Rate limit"]):
                        progress_tracker['success'] += 1
                    else:
                        progress_tracker['failed'] += 1
                    
                    progress_tracker['results'][idx] = chunk_text
                    
                    # Update progress display
                    completed = progress_tracker['completed']
                    success = progress_tracker['success']
                    failed = progress_tracker['failed']
                    progress = completed / total
                    
                    # Update UI from the main thread
                    progress_bar.progress(progress)
                    progress_text.text(f"Transcribing: {completed}/{total} chunks processed...")
                    overall_status.info(f"Progress: {completed}/{total} chunks ({success} successful, {failed} failed)")
                
                # Clean up chunk file
                try:
                    os.remove(chunk_path)
                except:
                    pass
                
                return chunk_text
            except Exception as e:
                with lock:
                    progress_tracker['completed'] += 1
                    progress_tracker['failed'] += 1
                    progress_tracker['results'][idx] = f"[Error processing chunk {idx+1}: {str(e)}]"
                    
                    # Update progress
                    progress = progress_tracker['completed'] / total
                    progress_bar.progress(progress)
                return f"[Error processing chunk {idx+1}: {str(e)}]"
        
        # Process chunks with concurrent execution
        chunk_args = [(chunk_path, i, len(chunks)) for i, chunk_path in enumerate(chunks)]
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Start all tasks
            future_to_chunk = {executor.submit(process_chunk, arg): arg for arg in chunk_args}
            
            # Wait for all tasks to complete
            concurrent.futures.wait(future_to_chunk)
        
        # Collect results in correct order
        transcriptions = progress_tracker['results']
        
        # Clean up temporary directory
        if temp_dir:
            try:
                shutil.rmtree(temp_dir)
            except:
                pass
        
        # Combine all transcriptions with proper spacing
        full_transcript = " ".join([t for t in transcriptions if t])
        
        # Clear progress indicators
        progress_text.empty()
        progress_bar.empty()
        
        # Final status message
        if progress_tracker['failed'] > 0:
            overall_status.warning(f"⚠️ Transcription partially complete. Processed {progress_tracker['success']} of {len(chunks)} chunks successfully. {progress_tracker['failed']} chunks had errors.")
        else:
            overall_status.success(f"✅ Transcription complete! Successfully processed all {len(chunks)} audio segments.")
        
        return full_transcript
        
    except Exception as e:
        st.error(f"Error processing large file: {str(e)}")
        if "ffmpeg" in str(e).lower():
            st.error("FFmpeg error. Please ensure FFmpeg is properly installed on your system.")
        elif "memory" in str(e).lower():
            st.error("Memory error. File may be too large for processing.")
        return ""

def transcribe_audio(audio_file):
    """Transcribe an audio file with size-based handling for files up to 500MB"""
    # Start timing for usage tracking
    start_time = time.time()
    
    try:
        logger.debug(f"Starting transcription of audio file: {getattr(audio_file, 'name', str(audio_file))}")
        
        # Check if audio_file is a string (path) or an UploadedFile object
        if isinstance(audio_file, str):
            audio_path = audio_file
            file_size = os.path.getsize(audio_path)
            file_name = os.path.basename(audio_path)
        else:
            # Save uploaded file temporarily
            file_name = audio_file.name
            file_extension = file_name.split('.')[-1].lower()
            
            logger.debug(f"Processing uploaded file: {file_name} (extension: {file_extension})")
            
            # Validate file extension
            valid_extensions = ['mp3', 'wav', 'ogg', 'm4a', 'mp4', 'mpeg', 'mpga', 'webm']
            if file_extension not in valid_extensions:
                logger.error(f"Invalid file extension: {file_extension}")
                return f"Error: Unsupported file format '{file_extension}'. Please upload an audio file in one of these formats: {', '.join(valid_extensions)}"
            
            # Create temp file with proper extension
            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_extension}") as tmp_file:
                logger.debug(f"Created temporary file: {tmp_file.name}")
                tmp_file.write(audio_file.getvalue())
                audio_path = tmp_file.name
                file_size = os.path.getsize(audio_path)
        
        # Check for maximum file size (500MB)
        MAX_FILE_SIZE = 500 * 1024 * 1024  # 500MB
        if file_size > MAX_FILE_SIZE:
            error_msg = f"File size ({file_size/(1024*1024):.1f} MB) exceeds the maximum allowed size of 500MB."
            logger.error(error_msg)
            st.error(error_msg)
            return f"Error: {error_msg}"
        
        # Display file information to user
        file_size_mb = file_size / (1024 * 1024)
        logger.debug(f"File size: {file_size_mb:.2f} MB")
        st.info(f"Processing '{file_name}' ({file_size_mb:.1f} MB)")
        
        # Size threshold for chunking - adjusted for different file sizes
        if file_size_mb > 100:
            # For larger files, use a higher threshold to reduce the number of chunks
            CHUNK_THRESHOLD = 40 * 1024 * 1024  # 40MB threshold for larger files
        else:
            # For smaller files, use a lower threshold for better accuracy
            CHUNK_THRESHOLD = 25 * 1024 * 1024  # 25MB threshold for smaller files
            
        logger.debug(f"Chunk threshold: {CHUNK_THRESHOLD/(1024*1024):.2f} MB")
        
        # Process based on file size
        if file_size > CHUNK_THRESHOLD:
            logger.debug("Large file detected. Processing in chunks.")
            st.info(f"Large file detected ({file_size_mb:.1f} MB). Processing in chunks for better reliability.")
            # Process large file in chunks
            transcript = transcribe_large_file(audio_path)
        else:
            # Process small file directly - try multiple methods if needed
            logger.debug("Processing small file directly.")
            with st.spinner(f"Transcribing audio file ({file_size_mb:.1f} MB)..."):
                try:
                    # METHOD 1: Try using standard OpenAI client first
                    logger.debug("Attempt 1: Using standard OpenAI client")
                    api_key = get_api_key_for_service("openai")
                    if not api_key:
                        logger.error("Missing OpenAI API key")
                        return "Error: OpenAI API key is not configured. Please set up your API key in the settings."
                    
                    # Try to initialize with only API key
                    try:
                        logger.debug("Initializing OpenAI client")
                        client = OpenAI(api_key=api_key)
                        
                        logger.debug("Sending transcription request")
                        with open(audio_path, "rb") as audio:
                            response = client.audio.transcriptions.create(
                                model="whisper-1",
                                file=audio
                            )
                            transcript = response.text
                            logger.debug(f"Transcription successful. Length: {len(transcript)} characters")
                    except Exception as client_error:
                        error_msg = str(client_error)
                        logger.error(f"OpenAI client error: {error_msg}")
                        
                        # METHOD 2: Try direct API call if client fails
                        if "proxies" in error_msg or "Client.init" in error_msg:
                            logger.debug("Attempt 2: Using direct API call due to client error")
                            transcript = direct_transcribe_audio(audio_path, api_key)
                            if transcript and not transcript.startswith("Error:"):
                                logger.debug("Direct transcription successful")
                            else:
                                logger.error(f"Direct transcription failed: {transcript}")
                                raise Exception(transcript)
                        else:
                            raise client_error
                    
                except Exception as api_error:
                    error_msg = str(api_error)
                    logger.error(f"API Error: {error_msg}")
                    st.error(f"API Error: {error_msg}")
                    
                    # Try to provide more helpful error messages for common issues
                    if "rate limit" in error_msg.lower():
                        logger.error("Rate limit exceeded")
                        return "Error: OpenAI API rate limit reached. Please try again in a few minutes."
                    elif "api key" in error_msg.lower():
                        logger.error("Invalid API key")
                        return "Error: Invalid OpenAI API key. Please check your API key configuration."
                    elif "file size" in error_msg.lower() or "too large" in error_msg.lower():
                        # If direct upload fails due to size, try chunking as fallback
                        logger.warning("File size error. Attempting chunking as fallback.")
                        st.warning("File size error from API. Attempting to process in chunks as a fallback...")
                        transcript = transcribe_large_file(audio_path)
                    elif "proxies" in error_msg.lower() or "client.init" in error_msg.lower():
                        logger.error("OpenAI client configuration issue")
                        return "Error: OpenAI client configuration issue. Restarting the application should fix this."
                    else:
                        return f"Error transcribing audio: {error_msg}"
        
        # Clean up temporary file if we created it
        if not isinstance(audio_file, str):
            try:
                logger.debug(f"Cleaning up temporary file: {audio_path}")
                os.remove(audio_path)
            except Exception as cleanup_error:
                logger.warning(f"Failed to clean up temporary file: {str(cleanup_error)}")
        
        # Update usage tracking
        end_time = time.time()
        duration = end_time - start_time
        update_usage_tracking(duration)
        
        if transcript:
            logger.debug(f"Transcription complete. Result length: {len(transcript)} characters")
            st.success(f"✅ Transcription complete! ({len(transcript)} characters)")
            
        return transcript
        
    except Exception as e:
        logger.exception("Unhandled exception in transcribe_audio")
        st.error(f"Transcription error: {str(e)}")
        # Provide more specific error messages for common issues
        if "ffmpeg" in str(e).lower():
            st.error("Audio processing error. Please ensure the file is a valid audio format.")
        elif "permission" in str(e).lower():
            st.error("File permission error. Please try uploading the file again.")
        elif "memory" in str(e).lower():
            st.error("Memory error. The file may be too large to process with available system resources.")
        return ""

def generate_wisdom(transcript, ai_provider, model, custom_prompt=None, knowledge_base=None):
    """Extract key insights and wisdom from a transcript"""
    # Start timing for usage tracking
    start_time = time.time()
    
    try:
        prompt = custom_prompt or DEFAULT_PROMPTS["wisdom_extraction"]
        
        # Include knowledge base context if available
        if knowledge_base:
            knowledge_context = "\n\n".join([
                f"## {name}\n{content}" 
                for name, content in knowledge_base.items()
            ])
            system_prompt = f"""Use the following knowledge base to inform your analysis:

{knowledge_context}

When analyzing the content, please incorporate these perspectives and guidelines.

Original Prompt:
{prompt}"""
        else:
            system_prompt = prompt
        
        # Use the selected AI provider and model
        if ai_provider == "OpenAI":
            openai_client = get_openai_client()
            if not openai_client:
                return "Error: OpenAI API key is not configured."
                
            response = openai_client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Here's the transcription to analyze:\n\n{transcript}"}
                ],
                max_tokens=1500
            )
            result = response.choices[0].message.content
            
        elif ai_provider == "Anthropic":
            anthropic_client = get_anthropic_client()
            if not anthropic_client:
                return "Error: Anthropic API key is not configured."
                
            response = anthropic_client.messages.create(
                model=model,
                max_tokens=1500,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": f"Here's the transcription to analyze:\n\n{transcript}"}
                ]
            )
            result = response.content[0].text
            
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
                    {"role": "user", "content": f"Here's the transcription to analyze:\n\n{transcript}"}
                ]
            }
            response = requests.post(
                "https://api.grok.x.ai/v1/chat/completions",  # Adjust URL as needed
                headers=headers,
                json=payload
            )
            result = response.json()["choices"][0]["message"]["content"]
        
        # Update usage tracking
        end_time = time.time()
        duration = end_time - start_time
        update_usage_tracking(duration)
        
        return result
        
    except Exception as e:
        st.error(f"Analysis error with {ai_provider} {model}: {str(e)}")
        return None

def generate_outline(transcript, wisdom, ai_provider, model, custom_prompt=None, knowledge_base=None):
    """Create a structured outline based on transcript and wisdom"""
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
        
        # Use the selected AI provider and model
        if ai_provider == "OpenAI":
            openai_client = get_openai_client()
            if not openai_client:
                return "Error: OpenAI API key is not configured."
                
            response = openai_client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": content}
                ],
                max_tokens=1500
            )
            return response.choices[0].message.content
            
        elif ai_provider == "Anthropic":
            anthropic_client = get_anthropic_client()
            if not anthropic_client:
                return "Error: Anthropic API key is not configured."
                
            response = anthropic_client.messages.create(
                model=model,
                max_tokens=1500,
                system=system_prompt,
                messages=[{"role": "user", "content": content}]
            )
            return response.content[0].text
            
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
            response = requests.post(
                "https://api.grok.x.ai/v1/chat/completions",
                headers=headers,
                json=payload
            )
            return response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        st.error(f"Error creating outline with {ai_provider} {model}: {str(e)}")
        return None

def generate_image_prompts(wisdom, outline, ai_provider, model, custom_prompt=None, knowledge_base=None):
    """Create descriptive image prompts based on wisdom and outline"""
    try:
        prompt = custom_prompt or DEFAULT_PROMPTS["image_prompts"]
        
        # Combine content for context
        content = f"WISDOM:\n{wisdom}\n\nOUTLINE:\n{outline}"
        
        if ai_provider == "OpenAI":
            openai_client = get_openai_client()
            if not openai_client:
                st.error("OpenAI API key is not configured.")
                return None

            response = openai_client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": content}
                ],
                max_tokens=1000
            )
            return response.choices[0].message.content
            
        elif ai_provider == "Anthropic":
            anthropic_client = get_anthropic_client()
            if not anthropic_client:
                st.error("Anthropic API key is not configured.")
                return None

            response = anthropic_client.messages.create(
                model=model,
                max_tokens=1000,
                system=prompt,
                messages=[{"role": "user", "content": content}]
            )
            return response.content[0].text
            
        elif ai_provider == "Grok":
            grok_api_key = get_grok_api_key()
            if not grok_api_key:
                st.error("Grok API key is not configured.")
                return None

            headers = {
                "Authorization": f"Bearer {grok_api_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": model,
                "messages": [
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": content}
                ]
            }
            response = requests.post(
                "https://api.grok.x.ai/v1/chat/completions",
                headers=headers,
                json=payload
            )
            return response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        st.error(f"Error generating image prompts with {ai_provider} {model}: {str(e)}")
        return None

def generate_social_content(wisdom, outline, ai_provider, model, custom_prompt=None, knowledge_base=None):
    """Generate social media content based on wisdom and outline"""
    try:
        prompt = custom_prompt or DEFAULT_PROMPTS["social_media"]
        
        # Combine content for context
        content = f"WISDOM:\n{wisdom}\n\nOUTLINE:\n{outline}"
        
        if ai_provider == "OpenAI":
            openai_client = get_openai_client()
            if not openai_client:
                st.error("OpenAI API key is not configured.")
                return None

            response = openai_client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": content}
                ],
                max_tokens=1000
            )
            return response.choices[0].message.content
            
        elif ai_provider == "Anthropic":
            anthropic_client = get_anthropic_client()
            if not anthropic_client:
                st.error("Anthropic API key is not configured.")
                return None

            response = anthropic_client.messages.create(
                model=model,
                max_tokens=1000,
                system=prompt,
                messages=[{"role": "user", "content": content}]
            )
            return response.content[0].text
            
        elif ai_provider == "Grok":
            grok_api_key = get_grok_api_key()
            if not grok_api_key:
                st.error("Grok API key is not configured.")
                return None

            headers = {
                "Authorization": f"Bearer {grok_api_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": model,
                "messages": [
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": content}
                ]
            }
            response = requests.post(
                "https://api.grok.x.ai/v1/chat/completions",
                headers=headers,
                json=payload
            )
            return response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        st.error(f"Error generating social media content with {ai_provider} {model}: {str(e)}")
        return None

def generate_article(transcript, wisdom, outline, ai_provider, model, custom_prompt=None, knowledge_base=None):
    """Write a full article based on the outline and content"""
    try:
        prompt = custom_prompt or """Write a comprehensive, engaging article based on the provided outline and wisdom.
        Include an introduction, developed sections following the outline, and a conclusion.
        Maintain a conversational yet authoritative tone."""
        
        # Combine all content for context
        content = f"TRANSCRIPT EXCERPT:\n{transcript[:1000]}...\n\nWISDOM:\n{wisdom}\n\nOUTLINE:\n{outline}"
        
        if ai_provider == "OpenAI":
            openai_client = get_openai_client()
            if not openai_client:
                st.error("OpenAI API key is not configured.")
                return None

            response = openai_client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": content}
                ],
                max_tokens=2500
            )
            return response.choices[0].message.content
            
        elif ai_provider == "Anthropic":
            anthropic_client = get_anthropic_client()
            if not anthropic_client:
                st.error("Anthropic API key is not configured.")
                return None

            response = anthropic_client.messages.create(
                model=model,
                max_tokens=2500,
                system=prompt,
                messages=[{"role": "user", "content": content}]
            )
            return response.content[0].text
            
        elif ai_provider == "Grok":
            grok_api_key = get_grok_api_key()
            if not grok_api_key:
                st.error("Grok API key is not configured.")
                return None

            headers = {
                "Authorization": f"Bearer {grok_api_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": model,
                "messages": [
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": content}
                ]
            }
            response = requests.post(
                "https://api.grok.x.ai/v1/chat/completions",
                headers=headers,
                json=payload
            )
            return response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        st.error(f"Error writing article with {ai_provider} {model}: {str(e)}")
        return None

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
    """Process all content stages at once"""
    try:
        results = {
            'wisdom': None,
            'outline': None,
            'social_posts': None,
            'image_prompts': None,
            'article': None
        }
        
        # Sequential processing with progress bar
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Generate wisdom
        status_text.text("Extracting wisdom...")
        results['wisdom'] = generate_wisdom(text, ai_provider, model, knowledge_base=knowledge_base)
        progress_bar.progress(0.2)
        
        # Generate outline
        status_text.text("Creating outline...")
        results['outline'] = generate_outline(text, results['wisdom'], ai_provider, model, knowledge_base=knowledge_base)
        progress_bar.progress(0.4)
        
        # Generate social content
        status_text.text("Generating social media content...")
        results['social_posts'] = generate_social_content(results['wisdom'], results['outline'], ai_provider, model, knowledge_base=knowledge_base)
        progress_bar.progress(0.6)
        
        # Generate image prompts
        status_text.text("Creating image prompts...")
        results['image_prompts'] = generate_image_prompts(results['wisdom'], results['outline'], ai_provider, model, knowledge_base=knowledge_base)
        progress_bar.progress(0.8)
        
        # Generate article
        status_text.text("Writing full article...")
        results['article'] = generate_article(text, results['wisdom'], results['outline'], ai_provider, model, knowledge_base=knowledge_base)
        progress_bar.progress(1.0)
        
        status_text.text("Content generation complete!")
        return results
        
    except Exception as e:
        st.error(f"Error in batch processing: {str(e)}")
        return None

def main():
    # Initialize session state variables
    if 'user_id' not in st.session_state:
        st.session_state.user_id = 1  # Set to admin user ID
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = True  # Auto-authenticate for testing
    if 'page' not in st.session_state:
        st.session_state.page = "main"
    if 'show_cookie_banner' not in st.session_state:
        st.session_state.show_cookie_banner = True
    if 'transcription' not in st.session_state:
        st.session_state.transcription = ""
    if 'wisdom' not in st.session_state:
        st.session_state.wisdom = ""
    if 'audio_file' not in st.session_state:
        st.session_state.audio_file = None
    if 'ai_provider' not in st.session_state:
        st.session_state.ai_provider = "OpenAI"
    if 'ai_model' not in st.session_state:
        # Set default model
        st.session_state.ai_model = "gpt-3.5-turbo"
    if 'content_title_value' not in st.session_state:
        st.session_state.content_title_value = ""
    
    # Apply production CSS enhancements
    add_production_css()
    
    # Initialize database and create admin user if needed
    init_db()
    init_admin_user()
    
    # Apply the improved cyberpunk theme
    local_css()
    
    # Skip authentication for testing purposes
    # Authentication handling
    # if not st.session_state.authenticated:
    #     show_login_page()
    #     return
    
    # Create a custom header with the refined styling
    st.markdown(f"""
    <div class="header-container">
        <div class="header-title">WhisperForge // Control_Center</div>
        <div class="header-date">{datetime.now().strftime('%a %d %b %Y · %H:%M')}</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar configuration
    with st.sidebar:
        st.markdown('<div class="section-header">Configuration</div>', unsafe_allow_html=True)
        
        # Account section with logout
        show_account_sidebar()
        
        # Navigation
        st.markdown("### Navigation")
        if st.button("🏠 Home"):
            st.session_state.page = "main"
            st.rerun()
        if st.button("🔑 API Keys"):
            st.session_state.page = "api_keys"
            st.rerun()
        if st.button("📊 Usage"):
            st.session_state.page = "usage"
            st.rerun()
        
        # Check if user is admin
        conn = get_db_connection()
        is_admin = conn.execute(
            "SELECT is_admin FROM users WHERE id = ?",
            (st.session_state.user_id,)
        ).fetchone()
        conn.close()
        
        # Show admin button if user is admin
        if is_admin and is_admin[0]:
            if st.button("⚙️ Admin"):
                st.session_state.page = "admin"
                st.rerun()
        
        # Footer links
        st.markdown("---")
        st.markdown("### About")
        if st.button("📜 Terms & Privacy"):
            st.session_state.page = "legal"
            st.rerun()
        st.markdown("[🌐 Website](https://whisperforge.ai)")
        st.markdown("[📧 Support](mailto:support@whisperforge.ai)")
        
        # Version info
        st.markdown("---")
        st.markdown("WhisperForge v1.0.0")
    
    # Show different pages based on selection
    if st.session_state.page == "main":
        show_main_page()
    elif st.session_state.page == "api_keys":
        show_api_keys_page()
    elif st.session_state.page == "usage":
        show_usage_page()
    elif st.session_state.page == "admin":
        show_admin_page()
    elif st.session_state.page == "legal":
        show_legal_page()
    
    # Show cookie consent banner if necessary
    if st.session_state.show_cookie_banner:
        cookie_banner_html = """
        <div class="cookie-banner">
            <div>
                We use cookies to improve your experience. By continuing, you consent to our use of cookies.
                <a href="/?page=legal">Learn more</a>
            </div>
            <div class="cookie-banner-buttons">
                <button onclick="document.querySelector('.cookie-banner').style.display='none'; localStorage.setItem('cookies_accepted', 'true');">
                    Accept
                </button>
            </div>
        </div>
        <script>
            if (localStorage.getItem('cookies_accepted') === 'true') {
                document.querySelector('.cookie-banner').style.display = 'none';
            }
        </script>
        """
        st.markdown(cookie_banner_html, unsafe_allow_html=True)
    
    # Display tool area if transcript is available
    if st.session_state.get("transcript"):
        with st.expander("🛠️ Tools", expanded=True):
            col1, col2, col3, col4 = st.columns(4)
            
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
                
                direct_wisdom_button = st.button("🧠 Direct Wisdom")
                if direct_wisdom_button:
                    with st.spinner("Generating wisdom directly..."):
                        try:
                            transcript = st.session_state.get("transcript", "")
                            if transcript:
                                wisdom = direct_anthropic_completion(
                                    transcript, 
                                    "Extract the key insights, lessons, and wisdom from this transcript. Format as bullet points."
                                )
                                if not wisdom.startswith("Error:"):
                                    st.session_state.wisdom = wisdom
                                    st.toast("Wisdom extracted successfully!")
                                    st.experimental_rerun()
                                else:
                                    st.error(wisdom)
                            else:
                                st.error("No transcript available")
                        except Exception as e:
                            logger.exception("Error in direct wisdom generation:")
                            st.error(f"Error generating wisdom: {str(e)}")
                
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
                
                direct_outline_button = st.button("📋 Direct Outline")
                if direct_outline_button:
                    with st.spinner("Generating outline directly..."):
                        try:
                            transcript = st.session_state.get("transcript", "")
                            if transcript:
                                outline = direct_anthropic_completion(
                                    transcript, 
                                    "Create a detailed outline of this content, with hierarchical sections and subsections."
                                )
                                if not outline.startswith("Error:"):
                                    st.session_state.outline = outline
                                    st.toast("Outline created successfully!")
                                    st.experimental_rerun()
                                else:
                                    st.error(outline)
                            else:
                                st.error("No transcript available")
                        except Exception as e:
                            logger.exception("Error in direct outline generation:")
                            st.error(f"Error generating outline: {str(e)}")
                
                if st.session_state.get("outline"):
                    if st.button("📝 Copy Outline"):
                        st.session_state.clipboard = st.session_state.outline
                        st.toast("Outline copied to clipboard")
                    
                    if st.button("💾 Save Outline"):
                        st.session_state.file_to_save = "outline.txt"
                        st.session_state.content_to_save = st.session_state.outline
                        st.toast("Preparing outline for download...")
            
            # Fourth column - export actions
            with col4:
                st.subheader("Export")
                
                # Add Direct Save to Notion button
                direct_notion_button = st.button("📕 Direct Notion Save")
                if direct_notion_button:
                    with st.spinner("Saving to Notion directly..."):
                        try:
                            title = st.session_state.get("file_name", "Untitled Audio")
                            transcript = st.session_state.get("transcript", "")
                            wisdom = st.session_state.get("wisdom", None)
                            outline = st.session_state.get("outline", None)
                            
                            if transcript:
                                result = direct_notion_save(
                                    title=title,
                                    transcript=transcript,
                                    wisdom=wisdom,
                                    outline=outline
                                )
                                
                                if "error" not in result:
                                    st.toast("Successfully saved to Notion!")
                                    st.markdown(f"[Open in Notion]({result['url']})")
                                else:
                                    st.error(result["error"])
                            else:
                                st.error("No transcript available to save")
                        except Exception as e:
                            logger.exception("Error in direct Notion save:")
                            st.error(f"Error saving to Notion: {str(e)}")
                
                # Normal Notion export button
                if os.environ.get("NOTION_API_KEY") or st.session_state.get("NOTION_API_KEY"):
                    if st.button("📘 Export to Notion"):
                        with st.spinner("Exporting to Notion..."):
                            try:
                                export_to_notion()
                            except Exception as e:
                                logger.exception("Error exporting to Notion:")
                                st.error(f"Error exporting to Notion: {str(e)}")
    
    # ... existing code ...

def show_main_page():
    # This function contains the original main app functionality
    
    # Get user's API keys
    api_keys = get_user_api_keys()
    
    # Check if API keys are set up
    openai_key = api_keys.get("openai")
    anthropic_key = api_keys.get("anthropic")
    notion_key = api_keys.get("notion")
    
    if not openai_key:
        st.warning("⚠️ Your OpenAI API key is not set up. Some features may not work properly. [Set up your API keys](/?page=api_keys)")
    
    # Get available users for the current authenticated user
    selected_user = st.selectbox("User Profile", options=get_available_users(), key="user_profile")
    
    # Load knowledge base for selected user
    knowledge_base = load_user_knowledge_base(selected_user)
    
    # AI Provider selection in sidebar with clean UI
    providers = ["OpenAI"]
    
    # Only add providers if API keys are available
    if os.getenv("ANTHROPIC_API_KEY") or api_keys.get("anthropic"):
        providers.append("Anthropic")
    if os.getenv("GROK_API_KEY") or api_keys.get("grok"):
        providers.append("Grok")
    
    ai_provider = st.selectbox(
        "AI Provider", 
        options=providers,
        index=providers.index(st.session_state.ai_provider) if st.session_state.ai_provider in providers else 0,
        key="ai_provider_select"
    )
    st.session_state.ai_provider = ai_provider
    
    # Fetch and display available models based on provider
    available_models = get_available_models(ai_provider)
    
    # Safety check - ensure we have models
    if not available_models:
        if ai_provider == "OpenAI":
            available_models = ["gpt-3.5-turbo", "gpt-4"]
        elif ai_provider == "Anthropic":
            available_models = ["claude-3-haiku-20240307", "claude-3-sonnet-20240229"]
        else:
            available_models = ["gpt-3.5-turbo"]  # Fallback to OpenAI
    
    # Model descriptions for helpful UI
    model_descriptions = {
        "gpt-4": "Most capable OpenAI model",
        "gpt-3.5-turbo": "Faster, cost-effective OpenAI model",
        "claude-3-opus-20240229": "Most capable Anthropic model",
        "claude-3-sonnet-20240229": "Balanced Anthropic model",
        "claude-3-haiku-20240307": "Fast, efficient Anthropic model",
        "grok-1": "Grok's base model"
    }
    
    # If no model is selected or previous model isn't in new provider's list, select first
    if not st.session_state.ai_model or st.session_state.ai_model not in available_models:
        if available_models:
            st.session_state.ai_model = available_models[0]
    
    # AI Model selection in sidebar
    selected_model = st.selectbox(
        "AI Model",
        options=available_models,
        format_func=lambda x: f"{x}" + (f" ({model_descriptions[x]})" if x in model_descriptions else ""),
        key="ai_model_select"
    )
    st.session_state.ai_model = selected_model
    
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
        
        # Add a title input for better organization
        if 'content_title_value' not in st.session_state:
            st.session_state.content_title_value = ""
            
        content_title = st.text_input("Content Title (Optional)", 
                                     value=st.session_state.content_title_value,
                                     placeholder="Enter a title, or leave blank to auto-generate",
                                     key="content_title")
        
        # Store the value in session state
        st.session_state.content_title_value = content_title
        
        # Transcribe Button
        if uploaded_file is not None:
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("🎙️ Transcribe Audio", key="transcribe_button", use_container_width=True):
                    with st.spinner("Transcribing your audio..."):
                        transcription = transcribe_audio(uploaded_file)
                        if transcription:
                            st.session_state.transcription = transcription
                            st.session_state.audio_file = uploaded_file
                            
                            # Generate a title if none provided
                            if not content_title and transcription:
                                with st.spinner("Generating title..."):
                                    generated_title = generate_title(transcription)
                                    if generated_title:
                                        # Update the value, not the widget state directly
                                        st.session_state.content_title_value = generated_title
                                        st.rerun()  # Rerun to update the UI with the new title
            
            with col2:
                if st.button("🎙️ Direct Transcribe (Fallback)", key="direct_transcribe_button", use_container_width=True):
                    with st.spinner("Directly transcribing audio (bypassing client)..."):
                        # Save the file to a temporary location
                        file_name = uploaded_file.name
                        file_extension = file_name.split('.')[-1].lower()
                        
                        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_extension}") as tmp_file:
                            tmp_file.write(uploaded_file.getvalue())
                            audio_path = tmp_file.name
                        
                        # Use direct transcription
                        api_key = get_api_key_for_service("openai") 
                        if not api_key:
                            st.error("OpenAI API key is required for transcription")
                        else:
                            transcription = direct_transcribe_audio(audio_path, api_key)
                            
                            # Clean up temp file
                            try:
                                os.remove(audio_path)
                            except:
                                pass
                                
                            if transcription and not transcription.startswith("Error:"):
                                st.session_state.transcription = transcription
                                st.session_state.audio_file = uploaded_file
                                st.success("Direct transcription successful!")
                                
                                # Generate a title if none provided
                                if not content_title and transcription:
                                    with st.spinner("Generating title..."):
                                        try:
                                            # Simple direct title generation
                                            prompt = f"Create a concise title (5-7 words) for this transcript: {transcription[:1000]}..."
                                            generated_title = direct_anthropic_completion(prompt, api_key=get_api_key_for_service("anthropic"))
                                            if generated_title and not generated_title.startswith("Error:"):
                                                st.session_state.content_title_value = generated_title
                                                st.rerun()
                                        except:
                                            pass
        
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
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        if st.button("Generate Wisdom", key="wisdom_button", use_container_width=True):
                            with st.spinner("Extracting key insights..."):
                                wisdom = generate_wisdom(
                                    st.session_state.transcription, 
                                    st.session_state.ai_provider,
                                    st.session_state.ai_model,
                                    knowledge_base=knowledge_base
                                )
                                if wisdom:
                                    st.session_state.wisdom = wisdom
                    
                    with col2:
                        if st.button("Direct API Wisdom (Fallback)", key="direct_wisdom_button", use_container_width=True):
                            with st.spinner("Extracting wisdom directly via API..."):
                                # Create a prompt for wisdom extraction
                                prompt = f"""Extract key insights, lessons, and wisdom from the transcript. Focus on actionable takeaways and profound realizations.

Transcript: {st.session_state.transcription[:2000]}...

Please provide a well-formatted, structured response with the main insights clearly outlined."""
                                
                                # Get API key
                                api_key = get_api_key_for_service("anthropic")
                                if api_key:
                                    try:
                                        # Use direct API call
                                        wisdom = direct_anthropic_completion(prompt, api_key)
                                        if wisdom and not wisdom.startswith("Error"):
                                            st.session_state.wisdom = wisdom
                                            st.success("Direct wisdom extraction successful!")
                                        else:
                                            st.error(f"Failed to extract wisdom: {wisdom}")
                                    except Exception as e:
                                        st.error(f"Error: {str(e)}")
                                else:
                                    st.error("Anthropic API key is required")
                    
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
                                article = generate_article(
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
                            # Get title, with fallbacks
                            title_to_use = title
                            if not title_to_use or title_to_use == "Untitled Content":
                                # Try to generate a title if we have transcription
                                if st.session_state.transcription:
                                    try:
                                        title_to_use = generate_short_title(st.session_state.transcription)
                                    except:
                                        title_to_use = "WhisperForge Content"
                                else:
                                    title_to_use = "WhisperForge Content"
                            
                            result = create_content_notion_entry(
                                title_to_use,
                                st.session_state.transcription,
                                wisdom=st.session_state.get("wisdom"),
                                outline=st.session_state.get("outline"),
                                social_content=st.session_state.get("social"),
                                image_prompts=st.session_state.get("image_prompts"),
                                article=st.session_state.get("article")
                            )
                            
                            if result and result.get("url"):
                                st.success(f"✅ Content saved to Notion! [View Page]({result['url']})")
                            else:
                                st.error("Failed to save to Notion. Please check your API keys and database ID.")
                        except Exception as e:
                            st.error(f"Notion export error: {str(e)}")
    
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
    
    # OpenAI API Key
    st.markdown("### OpenAI API Key")
    st.markdown("Required for audio transcription and most AI capabilities.")
    
    # Create a masked display of the current key if it exists
    openai_key = api_keys.get("openai", "")
    openai_key_display = f"••••••••••••••••••{openai_key[-4:]}" if openai_key else "Not set"
    
    st.markdown(f"**Current key:** {openai_key_display}")
    
    # Input for new key
    new_openai_key = st.text_input("Enter new OpenAI API key", type="password", key="new_openai_key")
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
    anthropic_key_display = f"••••••••••••••••••{anthropic_key[-4:]}" if anthropic_key else "Not set"
    
    st.markdown(f"**Current key:** {anthropic_key_display}")
    
    new_anthropic_key = st.text_input("Enter new Anthropic API key", type="password", key="new_anthropic_key")
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
    notion_key_display = f"••••••••••••••••••{notion_key[-4:]}" if notion_key else "Not set"
    
    st.markdown(f"**Current key:** {notion_key_display}")
    
    col1, col2 = st.columns(2)
    with col1:
        new_notion_key = st.text_input("Enter new Notion API key", type="password", key="new_notion_key")
    with col2:
        notion_database_id = st.text_input("Notion Database ID", value=api_keys.get("notion_database_id", ""), key="notion_database_id")
    
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
    
    new_grok_key = st.text_input("Enter new Grok API key", type="password", key="new_grok_key")
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
    if not st.session_state.authenticated:
        return {}
    
    conn = get_db_connection()
    user = conn.execute(
        "SELECT api_keys FROM users WHERE id = ?",
        (st.session_state.user_id,)
    ).fetchone()
    conn.close()
    
    if user and user['api_keys']:
        return json.loads(user['api_keys'])
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
    st.markdown("""
    <style>
    /* Production-specific styles */
    .pricing-table {
        width: 100%;
        border-collapse: collapse;
        margin: 20px 0;
    }
    
    .pricing-table th, .pricing-table td {
        padding: 12px 15px;
        border: 1px solid rgba(121, 40, 202, 0.2);
    }
    
    .pricing-table th {
        background: rgba(121, 40, 202, 0.1);
        color: var(--text-primary);
        text-align: left;
    }
    
    .pricing-table tr:nth-child(even) {
        background: rgba(121, 40, 202, 0.03);
    }
    
    .pricing-table tr:hover {
        background: rgba(121, 40, 202, 0.05);
    }
    
    .highlight-plan {
        background: rgba(121, 40, 202, 0.08) !important;
        border-left: 3px solid var(--accent-primary);
    }
    
    /* Responsive tables */
    @media (max-width: 768px) {
        .pricing-table {
            display: block;
            overflow-x: auto;
        }
    }
    
    /* Badge styles */
    .badge {
        display: inline-block;
        padding: 3px 7px;
        font-size: 0.75rem;
        border-radius: 12px;
        font-weight: 500;
    }
    
    .badge-pro {
        background: linear-gradient(135deg, #7928CA 0%, #FF0080 100%);
        color: white;
    }
    
    .badge-free {
        background: rgba(121, 40, 202, 0.1);
        color: var(--text-primary);
    }
    
    .badge-new {
        background: linear-gradient(135deg, #36D399 0%, #3ABFF8 100%);
        color: white;
    }
    
    /* Cookie consent banner */
    .cookie-banner {
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        background: var(--bg-secondary);
        padding: 15px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        border-top: 1px solid rgba(121, 40, 202, 0.2);
        z-index: 9999;
    }
    
    .cookie-banner-buttons {
        display: flex;
        gap: 10px;
    }
    
    .admin-dashboard-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
        gap: 15px;
        margin: 20px 0;
    }
    
    .admin-card {
        background: var(--bg-secondary);
        border-radius: var(--card-radius);
        padding: 20px;
        border: 1px solid rgba(121, 40, 202, 0.2);
    }
    
    .admin-card h3 {
        margin-top: 0;
        font-size: 1.1rem;
        color: var(--text-primary);
        border-bottom: 1px solid rgba(121, 40, 202, 0.1);
        padding-bottom: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

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
            (admin_email, hashed_password, 1, "enterprise", 100000)
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
    
    # System stats
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
    
    # User management
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
        
        # Open the file in binary mode
        with open(audio_file_path, "rb") as audio_file:
            files = {
                "file": (os.path.basename(audio_file_path), audio_file, "audio/mpeg"),
                "model": (None, "whisper-1")
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

def direct_anthropic_completion(prompt, api_key=None, model="claude-3-haiku-20240307"):
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
        
        # Create content in Notion
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
            logger.debug(f"Successfully exported to Notion: {result}")
            return result
        else:
            logger.error("Failed to export to Notion")
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
        
        logger.debug("Preparing API request for Notion")
        url = "https://api.notion.com/v1/pages"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28"
        }
        
        # Initialize content blocks
        children = []
        
        # Add summary if wisdom is available
        if wisdom:
            children.append({
                "object": "block",
                "type": "callout",
                "callout": {
                    "rich_text": [{"type": "text", "text": {"content": wisdom[:2000]}}],
                    "color": "purple_background",
                    "icon": {"type": "emoji", "emoji": "💜"}
                }
            })
        
        # Add transcript toggle
        if transcript:
            # Split transcript into chunks to respect Notion's block size limit
            transcript_chunks = [transcript[i:i+2000] for i in range(0, len(transcript), 2000)]
            
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
        
        # Add wisdom toggle
        if wisdom:
            children.append({
                "object": "block",
                "type": "toggle",
                "toggle": {
                    "rich_text": [{"type": "text", "text": {"content": "▶️ Wisdom"}}],
                    "children": [{
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": [{"type": "text", "text": {"content": wisdom[:2000]}}]
                        }
                    }]
                }
            })
        
        # Add outline toggle
        if outline:
            children.append({
                "object": "block",
                "type": "toggle",
                "toggle": {
                    "rich_text": [{"type": "text", "text": {"content": "▶️ Outline"}}],
                    "children": [{
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": [{"type": "text", "text": {"content": outline[:2000]}}]
                        }
                    }]
                }
            })
        
        # Add metadata section
        children.append({
            "object": "block",
            "type": "heading_2",
            "heading_2": {
                "rich_text": [{"type": "text", "text": {"content": "Metadata"}}]
            }
        })
        
        children.append({
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [
                    {"type": "text", "text": {"content": "Created with "}},
                    {"type": "text", "text": {"content": "WhisperForge"}, "annotations": {"bold": True, "color": "purple"}}
                ]
            }
        })
        
        # Prepare the payload
        payload = {
            "parent": {"database_id": database_id},
            "properties": {
                "Name": {
                    "title": [{"text": {"content": title}}]
                },
                "Created": {
                    "date": {"start": datetime.now().isoformat()}
                }
            },
            "children": children
        }
        
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

if __name__ == "__main__":
    main() 