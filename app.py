import streamlit as st
from openai import OpenAI
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
# Remove the problematic import completely
import streamlit.components.v1 as components

# Custom OpenAI Wrapper
class OpenAIWrapper:
    """A simple wrapper for the OpenAI API that avoids proxy issues"""
    
    def __init__(self, api_key=None):
        """Initialize with API key"""
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("API key is required. Either pass it directly or set OPENAI_API_KEY environment variable.")
        
        self.base_url = "https://api.openai.com/v1"
    
    class ChatCompletion:
        """Emulate OpenAI's ChatCompletion functionality"""
        
        @staticmethod
        def create(api_key, model="gpt-3.5-turbo", messages=None, max_tokens=1500):
            """Create a chat completion using the OpenAI API"""
            url = "https://api.openai.com/v1/chat/completions"
            
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": model,
                "messages": messages,
                "max_tokens": max_tokens
            }
            
            try:
                response = requests.post(url, headers=headers, json=data)
                response.raise_for_status()  # Raise exception for HTTP errors
                
                result = response.json()
                
                # Create a structure similar to what the OpenAI client returns
                class Choice:
                    def __init__(self, choice_data):
                        self.message = type('Message', (), {'content': choice_data['message']['content']})
                
                class Response:
                    def __init__(self, data):
                        self.choices = [Choice(choice) for choice in data['choices']]
                
                return Response(result)
            except requests.exceptions.RequestException as e:
                print(f"Error making request to OpenAI API: {str(e)}")
                if hasattr(e, 'response') and e.response:
                    print(f"Response status code: {e.response.status_code}")
                    print(f"Response body: {e.response.text}")
                raise
    
    class Models:
        """Emulate OpenAI's Models functionality"""
        
        @staticmethod
        def list(api_key):
            """List available models using the OpenAI API"""
            url = "https://api.openai.com/v1/models"
            
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            try:
                response = requests.get(url, headers=headers)
                response.raise_for_status()  # Raise exception for HTTP errors
                
                result = response.json()
                
                # Create a structure similar to what the OpenAI client returns
                models = []
                for model_data in result['data']:
                    model = type('Model', (), {'id': model_data['id']})
                    models.append(model)
                
                return models
            except requests.exceptions.RequestException as e:
                print(f"Error listing OpenAI models: {str(e)}")
                if hasattr(e, 'response') and e.response:
                    print(f"Response status code: {e.response.status_code}")
                    print(f"Response body: {e.response.text}")
                
                # Return default models as fallback
                default_models = ["gpt-4", "gpt-4-turbo-preview", "gpt-3.5-turbo"]
                return [type('Model', (), {'id': model_id}) for model_id in default_models]

# Load environment variables
load_dotenv()

# Utility function to handle proxy environment variables
def check_proxy_environment():
    """Check for proxy environment variables and warn if found"""
    proxy_vars = {}
    for env_var in list(os.environ.keys()):
        if 'PROXY' in env_var.upper() or 'HTTP_PROXY' in env_var.upper() or 'HTTPS_PROXY' in env_var.upper():
            proxy_vars[env_var] = os.environ[env_var]
    
    if proxy_vars:
        st.warning(f"Found proxy environment variables: {', '.join(proxy_vars.keys())}. These may cause issues with API clients.")
    
    return proxy_vars

def clean_proxy_environment(func):
    """Decorator to temporarily remove proxy environment variables when calling API clients"""
    def wrapper(*args, **kwargs):
        # Save the current proxy environment variables
        proxy_vars = check_proxy_environment()
        
        # Remove proxy environment variables
        for env_var in proxy_vars:
            if env_var in os.environ:
                del os.environ[env_var]
        
        try:
            # Call the original function
            result = func(*args, **kwargs)
        finally:
            # Restore proxy environment variables
            for env_var, value in proxy_vars.items():
                os.environ[env_var] = value
        
        return result
    return wrapper

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
@clean_proxy_environment
def get_openai_client():
    api_key = get_api_key_for_service("openai")
    if not api_key:
        return None
        
    try:
        # Use our wrapper instead of the OpenAI client
        return OpenAIWrapper()
    except Exception as e:
        st.error(f"Error initializing OpenAI client: {str(e)}")
        return None

@clean_proxy_environment
def get_anthropic_client():
    api_key = get_api_key_for_service("anthropic")
    if not api_key:
        st.error("Anthropic API key is not set. Please add your API key in the settings.")
        return None
    
    # Create Anthropic client with only supported parameters for current version
    try:
        # Basic initialization with just the API key
        return Anthropic(api_key=api_key)
    except Exception as e:
        st.error(f"Error initializing Anthropic client: {str(e)}")
        return None

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
    
    .section-divider {
        width: 100%;
        height: 1px;
        background: linear-gradient(90deg, transparent, rgba(121, 40, 202, 0.5), transparent);
        margin: 30px 0;
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
    """Apply a prompt to analyze text using the specified AI provider and model"""
    try:
        # Prepare the system prompt with user knowledge base if available
        if user_knowledge:
            system_prompt = f"{prompt_content}\n\nUSER KNOWLEDGE BASE:\n{user_knowledge}"
        else:
            system_prompt = prompt_content

        if provider == "OpenAI":
            client = get_openai_client()
            if client is None:
                return "Error: OpenAI API key is not configured. Please set up your API key in the API Keys page."
                
            api_key = get_api_key_for_service("openai")
            response = client.ChatCompletion.create(
                api_key=api_key,
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Here's the transcription to analyze:\n\n{text}"}
                ],
                max_tokens=1500
            )
            return response.choices[0].message.content

        elif provider == "Anthropic":
            client = get_anthropic_client()
            if client is None:
                return "Error: Anthropic API key is not configured. Please set up your API key in the API Keys page."
                
            response = client.messages.create(
                model=model,
                max_tokens=1500,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": f"Here's the transcription to analyze:\n\n{text}"}
                ]
            )
            return response.content[0].text

        elif provider == "Grok":
            # Get Grok API key
            grok_api_key = get_grok_api_key()
            if not grok_api_key:
                return "Error: Grok API key is not configured. Please set up your API key in the API Keys page."
                
            # Grok API endpoint (you'll need to adjust this based on actual Grok API documentation)
            headers = {
                "Authorization": f"Bearer {grok_api_key}",
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
        total_chunks = math.ceil(file_size / (target_size_mb * 1024 * 1024))
        
        # Ensure minimum chunk length (5 seconds) and maximum chunks (20)
        MIN_CHUNK_LENGTH_MS = 5000
        MAX_CHUNKS = 20
        
        if total_chunks > MAX_CHUNKS:
            target_size_mb = math.ceil(file_size / (MAX_CHUNKS * 1024 * 1024))
            total_chunks = MAX_CHUNKS
        
        chunk_length_ms = max(len(audio) // total_chunks, MIN_CHUNK_LENGTH_MS)
        
        # Create temporary directory for chunks
        temp_dir = tempfile.mkdtemp(prefix='whisperforge_chunks_')
        chunks = []
        
        # Show chunking progress
        progress_text = st.empty()
        progress_bar = st.progress(0)
        
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
        
        return chunks, temp_dir
    except Exception as e:
        st.error(f"Error chunking audio: {str(e)}")
        return [], None

def transcribe_chunk(chunk_path, i, total_chunks):
    """Transcribe a single chunk with error handling and progress tracking"""
    try:
        client = get_openai_client()
        if not client:
            return "Error: OpenAI API key is not configured."
            
        with open(chunk_path, "rb") as audio:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio
            )
            return transcript.text
    except Exception as e:
        st.warning(f"Warning: Failed to transcribe part {i+1} of {total_chunks}: {str(e)}")
        return ""

def generate_title(transcript):
    """Generate a descriptive 5-7 word title based on the transcript"""
    try:
        client = get_openai_client()
        if not client:
            return "Untitled Audio Transcription"
            
        prompt = f"""Create a clear, descriptive title (5-7 words) that captures the main topic of this transcript:
        Transcript: {transcript[:1000]}...
        
        Return only the title, no quotes or additional text."""
        
        response = client.chat.completions.create(
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
        client = get_openai_client()
        if not client:
            return "Summary of audio content"
            
        prompt = f"""Create a single, insightful sentence that summarizes the key message or main insight from this transcript:
        Transcript: {transcript[:1000]}...
        
        Return only the summary sentence, no additional text."""
        
        response = client.chat.completions.create(
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

def generate_short_title(text, ai_provider=None, ai_model=None):
    """Generate a 5-7 word descriptive title from the transcript"""
    try:
        client = get_openai_client()
        if not client:
            return "Untitled Audio Transcription"
            
        api_key = get_api_key_for_service("openai")
        response = client.ChatCompletion.create(
            api_key=api_key,
            model="gpt-4-turbo-preview",  # Always use the best model for titles regardless of user settings
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
        client = get_openai_client()
        if not client:
            return ["audio", "transcription", "content", "notes", "whisperforge"]
            
        # Use OpenAI to generate relevant tags
        prompt = f"""Based on this content:
        Transcript: {transcript[:500]}...
        Wisdom: {wisdom[:500] if wisdom else ''}
        
        Generate 5 relevant one-word tags that describe the main topics and themes.
        Return only the tags separated by commas, lowercase. Examples: spiritual, history, technology, motivation, business"""
        
        response = client.chat.completions.create(
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
        client = get_openai_client()
        if client is None:
            return {
                "GPT-4 (Most Capable)": "gpt-4",
                "GPT-4 Turbo": "gpt-4-turbo-preview",
                "GPT-3.5 Turbo (Faster)": "gpt-3.5-turbo",
            }
        
        api_key = get_api_key_for_service("openai")
        models = client.Models.list(api_key)
        gpt_models = {
            model.id: model.id for model in models 
            if any(x in model.id for x in ['gpt-4', 'gpt-3.5'])
        }
        return gpt_models
    except Exception as e:
        st.error(f"Error fetching models from OpenAI: {str(e)}")
        # Return default models as fallback
        return {
            "GPT-4 (Most Capable)": "gpt-4",
            "GPT-4 Turbo": "gpt-4-turbo-preview",
            "GPT-3.5 Turbo (Faster)": "gpt-3.5-turbo",
        }

def get_available_anthropic_models():
    """Get current list of available Anthropic models"""
    # Current as of March 2024
    return {
        "Claude 3 Opus": "claude-3-opus-20240229",
        "Claude 3 Sonnet": "claude-3-sonnet-20240229",
        "Claude 3 Haiku": "claude-3-haiku-20240307",
        "Claude 2.1": "claude-2.1",
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
    """Return a simple list of models for the selected provider"""
        if provider == "OpenAI":
                return ["gpt-4", "gpt-3.5-turbo"]
        elif provider == "Anthropic":
        return ["claude-3-opus-20240229", "claude-3-sonnet-20240229", "claude-3-haiku-20240307"]
        elif provider == "Grok":
            return ["grok-1"]
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
    """Process a large audio file by chunking it and transcribing each chunk"""
    try:
    st.info("Processing large audio file in chunks...")
    
    # Split audio into chunks
        chunks, temp_dir = chunk_audio(file_path)
    if not chunks:
        st.error("Failed to chunk audio file.")
        return ""
    
        # Create progress indicators
        progress_text = st.empty()
        progress_bar = st.progress(0)
    
    # Process each chunk
    transcriptions = []
    for i, chunk_path in enumerate(chunks):
        # Update progress
        progress = (i + 1) / len(chunks)
        progress_bar.progress(progress)
            progress_text.text(f"Transcribing part {i+1} of {len(chunks)}...")
        
            # Transcribe chunk
        chunk_text = transcribe_chunk(chunk_path, i, len(chunks))
        transcriptions.append(chunk_text)
    
            # Clean up chunk file
            try:
                os.remove(chunk_path)
            except:
                pass
        
        # Clean up temporary directory
        if temp_dir:
            try:
                shutil.rmtree(temp_dir)
            except:
                pass
        
        # Combine all transcriptions with proper spacing
    full_transcript = " ".join(transcriptions)
    
        # Clear progress indicators
        progress_text.empty()
        progress_bar.empty()
    
    return full_transcript
        
    except Exception as e:
        st.error(f"Error processing large file: {str(e)}")
        return ""

def transcribe_audio(audio_file):
    """Transcribe an audio file with size-based handling"""
    # Start timing for usage tracking
    start_time = time.time()
    
    try:
        # Check if audio_file is a string (path) or an UploadedFile object
        if isinstance(audio_file, str):
            audio_path = audio_file
            file_size = os.path.getsize(audio_path)
        else:
            # Save uploaded file temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{audio_file.name.split('.')[-1]}") as tmp_file:
            tmp_file.write(audio_file.getvalue())
                audio_path = tmp_file.name
                file_size = os.path.getsize(audio_path)
        
        # Size threshold for chunking (20MB)
        CHUNK_THRESHOLD = 20 * 1024 * 1024
        
        # Get OpenAI client with user's API key
        client = get_openai_client()
        if not client:
            return "Error: OpenAI API key is not configured. Please set up your API key in the settings."
        
        if file_size > CHUNK_THRESHOLD:
            # Process large file in chunks
            transcript = transcribe_large_file(audio_path)
        else:
            # Process small file directly
            with open(audio_path, "rb") as audio:
                response = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio
            )
                transcript = response.text
        
        # Clean up temporary file if we created it
        if not isinstance(audio_file, str):
            try:
                os.remove(audio_path)
            except:
                pass
        
        # Update usage tracking
        end_time = time.time()
        duration = end_time - start_time
        update_usage_tracking(duration)
        
        return transcript
        
    except Exception as e:
        st.error(f"Transcription error: {str(e)}")
        return ""

def generate_wisdom(transcript, ai_provider, model, custom_prompt=None, knowledge_base=None):
    """Extract key insights and wisdom from a transcript"""
    try:
        prompt = custom_prompt or DEFAULT_PROMPTS["wisdom"]
        
        # Combine with knowledge base if available
        if knowledge_base:
            system_prompt = f"{prompt}\n\nUSER KNOWLEDGE BASE:\n{knowledge_base}"
        else:
            system_prompt = prompt
        
        # Use the selected AI provider and model
        if ai_provider == "OpenAI":
            client = get_openai_client()
            if not client:
                return "Error: OpenAI API key is not configured."
                
            api_key = get_api_key_for_service("openai")
            response = client.ChatCompletion.create(
                api_key=api_key,
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Here's the transcription to analyze:\n\n{transcript}"}
                ],
                max_tokens=1500
            )
            result = response.choices[0].message.content
            
        elif ai_provider == "Anthropic":
            client = get_anthropic_client()
            if not client:
                return "Error: Anthropic API key is not configured."
                
            response = client.messages.create(
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
                "https://api.grok.x.ai/v1/chat/completions",
                headers=headers,
                json=payload
            )
            result = response.json()["choices"][0]["message"]["content"]
            
        else:
            return "Error: Invalid AI provider selected."
        
        return result
    except Exception as e:
        st.error(f"Error extracting wisdom with {ai_provider} {model}: {str(e)}")
        return None

def generate_outline(transcript, wisdom, ai_provider, model, custom_prompt=None, knowledge_base=None):
    """Create a structured outline based on transcript and wisdom"""
    try:
        prompt = custom_prompt or DEFAULT_PROMPTS["outline"]
        
        # Combine with knowledge base if available
        if knowledge_base:
            system_prompt = f"{prompt}\n\nUSER KNOWLEDGE BASE:\n{knowledge_base}"
        else:
            system_prompt = prompt
        
        # Combine transcript and wisdom for context
        content = f"TRANSCRIPT EXCERPT:\n{transcript[:1000]}...\n\nWISDOM EXTRACTED:\n{wisdom}"
        
        # Use the selected AI provider and model
        if ai_provider == "OpenAI":
            client = get_openai_client()
            if not client:
                return "Error: OpenAI API key is not configured."
                
            api_key = get_api_key_for_service("openai")
            response = client.ChatCompletion.create(
                api_key=api_key,
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": content}
                ],
                max_tokens=1500
            )
            return response.choices[0].message.content
            
        elif ai_provider == "Anthropic":
            client = get_anthropic_client()
            if not client:
                return "Error: Anthropic API key is not configured."
                
            response = client.messages.create(
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
            
        else:
            return "Error: Invalid AI provider selected."
    except Exception as e:
        st.error(f"Error creating outline with {ai_provider} {model}: {str(e)}")
        return None

def generate_image_prompts(wisdom, outline, ai_provider, model, custom_prompt=None, knowledge_base=None):
    """Create image generation prompts based on the content"""
    try:
        prompt = custom_prompt or DEFAULT_PROMPTS["image_prompts"]
        
        # Combine with knowledge base if available
        if knowledge_base:
            system_prompt = f"{prompt}\n\nUSER KNOWLEDGE BASE:\n{knowledge_base}"
        else:
            system_prompt = prompt
        
        # Combine wisdom and outline for context
        content = f"WISDOM:\n{wisdom}\n\nOUTLINE:\n{outline}"
        
        # Use the selected AI provider and model
        if ai_provider == "OpenAI":
            client = get_openai_client()
            if client is None:
                return "Error: OpenAI API key is not configured. Please set up your API key in the API Keys page."
                
            api_key = get_api_key_for_service("openai")
            response = client.ChatCompletion.create(
                api_key=api_key,
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": content}
                ],
                max_tokens=1000
            )
            return response.choices[0].message.content
            
        elif ai_provider == "Anthropic":
            client = get_anthropic_client()
            if client is None:
                return "Error: Anthropic API key is not configured. Please set up your API key in the API Keys page."
                
            response = client.messages.create(
                model=model,
                max_tokens=1000,
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
        
        else:
            return "Error: Invalid AI provider selected."
    except Exception as e:
        st.error(f"Error creating image prompts with {ai_provider} {model}: {str(e)}")
        return None

def generate_article(transcript, wisdom, outline, ai_provider, model, custom_prompt=None, knowledge_base=None):
    """Write a full article based on the outline and content"""
    try:
        prompt = custom_prompt or DEFAULT_PROMPTS["article"]
        
        # Combine with knowledge base if available
        if knowledge_base:
            system_prompt = f"{prompt}\n\nUSER KNOWLEDGE BASE:\n{knowledge_base}"
        else:
            system_prompt = prompt
        
        # Combine all content for context
        content = f"TRANSCRIPT EXCERPT:\n{transcript[:1000]}...\n\nWISDOM:\n{wisdom}\n\nOUTLINE:\n{outline}"
        
        # Use the selected AI provider and model
        if ai_provider == "OpenAI":
            client = get_openai_client()
            if client is None:
                return "Error: OpenAI API key is not configured. Please set up your API key in the API Keys page."
                
            api_key = get_api_key_for_service("openai")
            response = client.ChatCompletion.create(
                api_key=api_key,
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": content}
                ],
                max_tokens=2500
            )
            return response.choices[0].message.content
            
        elif ai_provider == "Anthropic":
            client = get_anthropic_client()
            if client is None:
                return "Error: Anthropic API key is not configured. Please set up your API key in the API Keys page."
                
            response = client.messages.create(
                model=model,
                max_tokens=2500,
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
        
        else:
            return "Error: Invalid AI provider selected."
    except Exception as e:
        st.error(f"Error writing article with {ai_provider} {model}: {str(e)}")
        return None

def generate_seo_metadata(content, title):
    """Generate SEO metadata for the content"""
    try:
        client = get_openai_client()
        if client is None:
            return {}
            
        api_key = get_api_key_for_service("openai")
        prompt = """Create SEO metadata for the given content. Return the metadata in a structured format including:
        - A list of 5-8 keywords or phrases
        - A meta description (155 characters max)
        - A suggested URL slug
        - Three possible alternate titles for A/B testing
        """
        
        content_sample = content[:1500] if content else ""
        
        response = client.ChatCompletion.create(
            api_key=api_key,
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": f"Title: {title}\n\nContent sample: {content_sample}..."}
            ],
            max_tokens=500
        )
        
        metadata_text = response.choices[0].message.content
        
        # Parse the response to extract metadata
        metadata = {}
        sections = metadata_text.split("\n\n")
        for section in sections:
            if "keywords" in section.lower():
                metadata["keywords"] = [k.strip() for k in section.split("\n")[1:] if k.strip()]
            elif "meta description" in section.lower():
                desc_line = [line for line in section.split("\n") if line.strip() and "meta description" not in line.lower()]
                if desc_line:
                    metadata["description"] = desc_line[0].strip()
            elif "slug" in section.lower():
                slug_line = [line for line in section.split("\n") if line.strip() and "slug" not in line.lower()]
                if slug_line:
                    metadata["slug"] = slug_line[0].strip()
            elif "alternate titles" in section.lower():
                metadata["alt_titles"] = [t.strip() for t in section.split("\n")[1:] if t.strip()]
        
        return metadata
        
    except Exception as e:
        st.error(f"Error generating SEO metadata: {str(e)}")
        return {}

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
        try:
            results['social_posts'] = generate_social_content(results['wisdom'], results['outline'], ai_provider, model, knowledge_base=knowledge_base)
            if results['social_posts'] is None:
                results['social_posts'] = "Error generating social content. Please check your API configuration."
        except Exception as e:
            st.error(f"Error generating social content: {str(e)}")
            results['social_posts'] = "Error generating social content. Please check your API configuration."
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
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'user_id' not in st.session_state:
        st.session_state.user_id = None
    if 'page' not in st.session_state:
        st.session_state.page = 'main'
    if 'show_cookie_banner' not in st.session_state:
        st.session_state.show_cookie_banner = True
    if 'transcription' not in st.session_state:
        st.session_state.transcription = ""
    if 'input_text' not in st.session_state:
        st.session_state.input_text = ""
    if 'wisdom' not in st.session_state:
        st.session_state.wisdom = ""
    if 'outline' not in st.session_state:
        st.session_state.outline = ""
    if 'social_posts' not in st.session_state:
        st.session_state.social_posts = ""
    if 'article' not in st.session_state:
        st.session_state.article = ""
    if 'image_prompts' not in st.session_state:
        st.session_state.image_prompts = ""
    if 'title' not in st.session_state:
        st.session_state.title = ""
    if 'audio_file' not in st.session_state:
        st.session_state.audio_file = None
    if 'ai_provider' not in st.session_state:
        st.session_state.ai_provider = "OpenAI"
    if 'ai_model' not in st.session_state:
        st.session_state.ai_model = None
    
    # Add debugging for proxy environment
    if os.getenv("DEBUG", "false").lower() == "true":
        st.sidebar.expander("Debug Info", expanded=False).write(
            f"""
            ## Environment Variables
            - OPENAI_API_KEY: {'Set' if os.getenv('OPENAI_API_KEY') else 'Not Set'}
            - ANTHROPIC_API_KEY: {'Set' if os.getenv('ANTHROPIC_API_KEY') else 'Not Set'}
            - NOTION_API_KEY: {'Set' if os.getenv('NOTION_API_KEY') else 'Not Set'}
            - GROK_API_KEY: {'Set' if os.getenv('GROK_API_KEY') else 'Not Set'}
            
            ## Proxy Settings
            {', '.join([f"{k}: {v}" for k, v in check_proxy_environment().items()]) or "No proxy settings found"}
            
            ## Package Versions
            - OpenAI: {OpenAI.__version__ if hasattr(OpenAI, '__version__') else 'Unknown'}
            - Anthropic: {Anthropic.__version__ if hasattr(Anthropic, '__version__') else 'Unknown'}
            - Requests: {requests.__version__ if hasattr(requests, '__version__') else 'Unknown'}
            """
        )
    
    # Apply CSS styles
    local_css()
    
    # Authentication handling
    if not st.session_state.authenticated:
        show_login_page()
        return
    
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
    if anthropic_key:
        providers.append("Anthropic")
    if api_keys.get("grok"):
        providers.append("Grok")
    
        ai_provider = st.selectbox(
            "AI Provider", 
        options=providers,
        key="ai_provider_select"
        )
        st.session_state.ai_provider = ai_provider
        
    # Simple model selection based on provider
    if ai_provider == "OpenAI":
        model_options = ["gpt-3.5-turbo", "gpt-4"]
        default_model = "gpt-4"
    elif ai_provider == "Anthropic":
        model_options = ["claude-3-haiku-20240307", "claude-3-sonnet-20240229", "claude-3-opus-20240229"]
        default_model = "claude-3-opus-20240229"
    elif ai_provider == "Grok":
        model_options = ["grok-1"]
        default_model = "grok-1"
    else:
        model_options = ["gpt-4"]
        default_model = "gpt-4"
    
    # AI Model selection in sidebar
        model_descriptions = {
            "gpt-4": "Most capable OpenAI model",
            "gpt-3.5-turbo": "Faster, cost-effective OpenAI model",
            "claude-3-opus-20240229": "Most capable Anthropic model",
            "claude-3-sonnet-20240229": "Balanced Anthropic model",
            "claude-3-haiku-20240307": "Fast, efficient Anthropic model",
            "grok-1": "Grok's base model"
        }
        
        selected_model = st.selectbox(
            "AI Model",
        options=model_options,
            format_func=lambda x: f"{x}" + (f" ({model_descriptions[x]})" if x in model_descriptions else ""),
        index=model_options.index(default_model) if default_model in model_options else 0,
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
            help="Files up to 500MB are supported. Large files will be automatically chunked for processing."
        )
        
        # Display custom message about automatic chunking for large files
        st.info("Large files are automatically chunked for optimal processing.")
        
        # Show buttons and audio player if file is uploaded
    if uploaded_file is not None:
            # Display audio player
        st.audio(uploaded_file)
        
            # Create columns for buttons
            col1, col2 = st.columns(2)
        
            # Add the Transcribe Audio button
            if col1.button("Transcribe Audio", key="transcribe_button"):
            with st.spinner("Transcribing audio..."):
                    st.session_state.transcription = transcribe_audio(uploaded_file)
                    st.session_state.audio_file = uploaded_file
                    st.success("Transcription complete!")
            
            # Add the "I'm Feeling Lucky" button
            if col2.button("I'm Feeling Lucky", key="lucky_button"):
                with st.spinner("Processing audio with default settings..."):
                    # Transcribe the audio
                    st.session_state.transcription = transcribe_audio(uploaded_file)
                    st.session_state.audio_file = uploaded_file
                    
                    # Process with AI to extract wisdom, etc.
    if st.session_state.transcription:
                        # Generate additional content
                        with st.spinner("Generating content..."):
                            result = process_all_content(
                                st.session_state.transcription,
                                st.session_state.ai_provider,
                                st.session_state.ai_model
                            )
                            if result:
                                # Update session state with results
                                st.session_state.wisdom = result['wisdom']
                                st.session_state.outline = result['outline']
                                st.session_state.social_posts = result['social_posts']
                                st.session_state.image_prompts = result['image_prompts']
                                st.session_state.article = result['article']
                        
                        st.success("Processing complete!")
    
    # Tab 2: Text Input
    with input_tabs[1]:
        st.markdown('<div class="section-header">Text Input</div>', unsafe_allow_html=True)
        
        # Text area for direct input
        text_input = st.text_area(
            "Enter your text", 
            value=st.session_state.input_text,
            height=250,
            placeholder="Paste your transcript or text to analyze here...",
            help="Enter the text you want to process with AI.",
            key="text_input_area"
        )
        # Store the input text in session state
        st.session_state.input_text = text_input
        
        # Create columns for buttons
        col1, col2 = st.columns(2)
        
        # Add the Process Text button
        if col1.button("Process Text", key="process_text_button"):
            if text_input.strip():
                with st.spinner("Processing text..."):
                    st.session_state.transcription = text_input
                    # Store in input_text for consistency
                    st.session_state.input_text = text_input
                        st.session_state.wisdom = generate_wisdom(
                        text_input,
                            st.session_state.ai_provider, 
                        st.session_state.ai_model
                    )
                    st.success("Processing complete!")
            else:
                st.warning("Please enter some text to process.")
        
        # Add the Full Content Generation button
        if col2.button("Generate Full Content", key="generate_content_button"):
            if text_input.strip():
                with st.spinner("Generating comprehensive content..."):
                    st.session_state.transcription = text_input
                    # Store in input_text for consistency
                    st.session_state.input_text = text_input
                    # Process with AI to extract wisdom, outline, etc.
                    result = process_all_content(
                        text_input,
                        st.session_state.ai_provider,
                        st.session_state.ai_model
                    )
                    if result:
                        # Update session state with results
                        st.session_state.wisdom = result['wisdom']
                        st.session_state.outline = result['outline']
                        st.session_state.social_posts = result['social_posts']
                        st.session_state.image_prompts = result['image_prompts']
                        st.session_state.article = result['article']
                    st.success("Content generation complete!")
            else:
                st.warning("Please enter some text to process.")

    # Add a section divider
    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
    
    # Display Results Section (shown after either audio transcription or text input is processed)
    if st.session_state.transcription or st.session_state.input_text:
        st.markdown('<div class="section-header">Results</div>', unsafe_allow_html=True)
        
        # Create tabs for different result sections
        result_tabs = st.tabs(["Transcription", "Wisdom", "Outline", "Social Content", "Article", "Image Prompts"])
        
        # Tab 1: Transcription
        with result_tabs[0]:
            st.markdown("### Transcription")
            if st.session_state.transcription:
                st.markdown(st.session_state.transcription)
            elif st.session_state.input_text:
                st.markdown(st.session_state.input_text)
        
        # Tab 2: Wisdom
        with result_tabs[1]:
            st.markdown("### Extracted Wisdom & Insights")
            if 'wisdom' in st.session_state and st.session_state.wisdom:
                st.markdown(st.session_state.wisdom)
            else:
                st.info("Process the content to extract wisdom and insights.")
                if st.button("Extract Wisdom"):
                    with st.spinner("Extracting wisdom..."):
                        input_content = st.session_state.transcription if st.session_state.transcription else st.session_state.input_text
                        st.session_state.wisdom = generate_wisdom(
                            input_content,
                            st.session_state.ai_provider,
                            st.session_state.ai_model
                        )
                    st.success("Wisdom extracted!")
                    st.rerun()
        
        # Tab 3: Outline
        with result_tabs[2]:
            st.markdown("### Content Outline")
            if 'outline' in st.session_state and st.session_state.outline:
                st.markdown(st.session_state.outline)
            else:
                st.info("Generate an outline based on the transcription.")
                if st.button("Generate Outline"):
                    if 'wisdom' not in st.session_state or not st.session_state.wisdom:
                        with st.spinner("Extracting wisdom first..."):
                            input_content = st.session_state.transcription if st.session_state.transcription else st.session_state.input_text
                            st.session_state.wisdom = generate_wisdom(
                                input_content,
                                st.session_state.ai_provider,
                                st.session_state.ai_model
                            )
                        
                        with st.spinner("Creating outline..."):
                        input_content = st.session_state.transcription if st.session_state.transcription else st.session_state.input_text
                            st.session_state.outline = generate_outline(
                            input_content,
                                st.session_state.wisdom,
                                st.session_state.ai_provider,
                            st.session_state.ai_model
                        )
                    st.success("Outline created!")
                    st.rerun()
        
        # Tab 4: Social Content
        with result_tabs[3]:
            st.markdown("### Social Media Content")
            if 'social_posts' in st.session_state and st.session_state.social_posts:
                st.markdown(st.session_state.social_posts)
            else:
                st.info("Generate social media posts based on the content.")
                    if st.button("Generate Social Posts"):
                    # Ensure we have wisdom and outline first
                    if 'wisdom' not in st.session_state or not st.session_state.wisdom:
                        with st.spinner("Extracting wisdom first..."):
                            input_content = st.session_state.transcription if st.session_state.transcription else st.session_state.input_text
                            st.session_state.wisdom = generate_wisdom(
                                input_content,
                                st.session_state.ai_provider,
                                st.session_state.ai_model
                            )
                    
                    if 'outline' not in st.session_state or not st.session_state.outline:
                        with st.spinner("Creating outline..."):
                            input_content = st.session_state.transcription if st.session_state.transcription else st.session_state.input_text
                            st.session_state.outline = generate_outline(
                                input_content,
                                st.session_state.wisdom,
                                st.session_state.ai_provider,
                                st.session_state.ai_model
                            )
                    
                    with st.spinner("Generating social media content..."):
                                st.session_state.social_posts = generate_social_content(
                                    st.session_state.wisdom,
                                    st.session_state.outline,
                                    st.session_state.ai_provider,
                            st.session_state.ai_model
                        )
                    st.success("Social posts created!")
                    st.rerun()
        
        # Tab 5: Article
        with result_tabs[4]:
            st.markdown("### Full Article")
            if 'article' in st.session_state and st.session_state.article:
                st.markdown(st.session_state.article)
            else:
                st.info("Generate a complete article based on the transcription and outline.")
                if st.button("Generate Article"):
                    # Ensure we have wisdom and outline first
                    if 'wisdom' not in st.session_state or not st.session_state.wisdom:
                        with st.spinner("Extracting wisdom first..."):
                            input_content = st.session_state.transcription if st.session_state.transcription else st.session_state.input_text
                            st.session_state.wisdom = generate_wisdom(
                                input_content,
                                st.session_state.ai_provider,
                                st.session_state.ai_model
                            )
                    
                    if 'outline' not in st.session_state or not st.session_state.outline:
                        with st.spinner("Creating outline..."):
                            input_content = st.session_state.transcription if st.session_state.transcription else st.session_state.input_text
                            st.session_state.outline = generate_outline(
                                input_content,
                                st.session_state.wisdom,
                                st.session_state.ai_provider,
                                st.session_state.ai_model
                            )
                    
                    with st.spinner("Writing article..."):
                        input_content = st.session_state.transcription if st.session_state.transcription else st.session_state.input_text
                        st.session_state.article = generate_article(
                            input_content,
                                    st.session_state.wisdom,
                                    st.session_state.outline,
                                    st.session_state.ai_provider,
                            st.session_state.ai_model
                        )
                    st.success("Article created!")
                    st.rerun()
        
        # Tab 6: Image Prompts
        with result_tabs[5]:
            st.markdown("### Image Generation Prompts")
            if 'image_prompts' in st.session_state and st.session_state.image_prompts:
                st.markdown(st.session_state.image_prompts)
            else:
                st.info("Generate prompts for image creation based on the content.")
                if st.button("Generate Image Prompts"):
                    # Ensure we have wisdom and outline first
                    if 'wisdom' not in st.session_state or not st.session_state.wisdom:
                        with st.spinner("Extracting wisdom first..."):
                            input_content = st.session_state.transcription if st.session_state.transcription else st.session_state.input_text
                            st.session_state.wisdom = generate_wisdom(
                                input_content,
                                st.session_state.ai_provider,
                                st.session_state.ai_model
                            )
                    
                    if 'outline' not in st.session_state or not st.session_state.outline:
                        with st.spinner("Creating outline..."):
                            input_content = st.session_state.transcription if st.session_state.transcription else st.session_state.input_text
                            st.session_state.outline = generate_outline(
                                input_content,
                                st.session_state.wisdom,
                                st.session_state.ai_provider,
                                st.session_state.ai_model
                            )
                    
                    with st.spinner("Creating image prompts..."):
                        st.session_state.image_prompts = generate_image_prompts(
                                    st.session_state.wisdom,
                                    st.session_state.outline,
                                    st.session_state.ai_provider,
                            st.session_state.ai_model
                        )
                    st.success("Image prompts created!")
                    st.rerun()
        
        # Notion Export Option
        st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
        notion_col1, notion_col2 = st.columns([3, 1])
        
        with notion_col1:
            st.markdown("### Export to Notion")
            st.markdown("Save all your processed content directly to your Notion database.")
        
        with notion_col2:
            if st.button("Export to Notion"):
                # Check if Notion API key is configured
                api_keys = get_user_api_keys()
                notion_key = api_keys.get("notion")
                notion_db_id = api_keys.get("notion_database_id")
                
                if not notion_key or not notion_db_id:
                    st.error("Notion API key or database ID not configured. Please set it up in the API Keys page.")
                else:
                    with st.spinner("Exporting to Notion..."):
                        # Generate a title if not already done
                        if 'title' not in st.session_state or not st.session_state.title:
                            input_content = st.session_state.transcription if st.session_state.transcription else st.session_state.input_text
                            st.session_state.title = generate_short_title(
                                input_content,
                                st.session_state.ai_provider,
                                st.session_state.ai_model
                            )
                        
                        # Export to Notion
                        input_content = st.session_state.transcription if st.session_state.transcription else st.session_state.input_text
                        
                        # Get title from session state
                        title = st.session_state.title if 'title' in st.session_state else ""
                        
                        # Call the Notion export function with all parameters
                        page_url = create_content_notion_entry(
                        title,
                            input_content,
                            wisdom=st.session_state.wisdom if 'wisdom' in st.session_state else "",
                            outline=st.session_state.outline if 'outline' in st.session_state else "",
                            social_content=st.session_state.social_posts if 'social_posts' in st.session_state else "",
                            image_prompts=st.session_state.image_prompts if 'image_prompts' in st.session_state else "",
                            article=st.session_state.article if 'article' in st.session_state else ""
                        )
                        
                        if page_url:
                            st.success(f"Content exported to Notion successfully!")
                            st.markdown(f"[View in Notion]({page_url})")
                    else:
                            st.error("Failed to export to Notion. Please check your API key and database ID.")

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
    
    "wisdom": """Extract key insights, lessons, and wisdom from the transcript. Focus on actionable takeaways and profound realizations.""",
    
    "summary": """## Summary
Create a concise summary of the main points and key messages in the transcript.
Capture the essence of the content in a few paragraphs.""",
    
    "outline_creation": """Create a detailed outline for an article or blog post based on the transcript and extracted wisdom. Include major sections and subsections.""",
    
    "outline": """Create a detailed outline for an article or blog post based on the transcript and extracted wisdom. Include major sections and subsections.""",
    
    "social_media": """Generate engaging social media posts for different platforms (Twitter, LinkedIn, Instagram) based on the key insights.""",
    
    "image_prompts": """Create detailed image generation prompts that visualize the key concepts and metaphors from the content.""",
    
    "article_writing": """Write a comprehensive article based on the provided outline and wisdom. Maintain a clear narrative flow and engaging style.""",
    
    "article": """Write a comprehensive article based on the provided outline and wisdom. Maintain a clear narrative flow and engaging style.""",
    
    "seo_analysis": """Analyze the content from an SEO perspective and provide optimization recommendations for better search visibility while maintaining content quality."""
}

# Set up security headers (disabled for local testing)
def add_security_headers(app):
    """Skip security headers for local development"""
    # This is a stub function that will be implemented for production
    return app

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

def generate_social_content(wisdom, outline, ai_provider, model, custom_prompt=None, knowledge_base=None):
    """Generate social media content based on wisdom and outline"""
    try:
        prompt = custom_prompt or DEFAULT_PROMPTS["social_media"]
        
        # Combine with knowledge base if available
        if knowledge_base:
            system_prompt = f"{prompt}\n\nUSER KNOWLEDGE BASE:\n{knowledge_base}"
        else:
            system_prompt = prompt
        
        # Combine wisdom and outline for context
        content = f"WISDOM:\n{wisdom}\n\nOUTLINE:\n{outline}"
        
        # Use the selected AI provider and model
        if ai_provider == "OpenAI":
            client = get_openai_client()
            if client is None:
                return "Error: OpenAI API key is not configured. Please set up your API key in the API Keys page."
                
            api_key = get_api_key_for_service("openai")
            response = client.ChatCompletion.create(
                api_key=api_key,
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": content}
                ],
                max_tokens=1200
            )
            return response.choices[0].message.content
            
        elif ai_provider == "Anthropic":
            client = get_anthropic_client()
            if client is None:
                return "Error: Anthropic API key is not configured. Please set up your API key in the API Keys page."
                
            response = client.messages.create(
                model=model,
                max_tokens=1200,
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
        
        else:
            return "Error: Invalid AI provider selected."
    except Exception as e:
        st.error(f"Error generating social content with {ai_provider} {model}: {str(e)}")
        return None

if __name__ == "__main__":
    main() 