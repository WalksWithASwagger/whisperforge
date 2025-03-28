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
from streamlit.middleware.app_middleware import AppMiddleware
import streamlit.components.v1 as components

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
    api_key = get_api_key_for_service("openai")
    if not api_key:
        st.error("OpenAI API key is not set. Please add your API key in the settings.")
        return None
    return OpenAI(api_key=api_key)

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
        openai_client = get_openai_client()
        if not openai_client:
            return "Error: OpenAI API key is not configured."
            
        with open(chunk_path, "rb") as audio:
            transcript = openai_client.audio.transcriptions.create(
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
        
