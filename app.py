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

# Load environment variables
load_dotenv()

# Initialize clients with proper error handling
openai_client = None
anthropic_client = None
notion_client = None

# Initialize OpenAI client
try:
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if openai_api_key:
        openai_client = OpenAI(api_key=openai_api_key)
except Exception as e:
    pass  # Silently fail and handle later with user-friendly messages

# Initialize Anthropic client
try:
    anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
    if anthropic_api_key:
        anthropic_client = Anthropic(api_key=anthropic_api_key)
except Exception as e:
    pass

# Initialize Notion client
try:
    notion_api_key = os.getenv("NOTION_API_KEY")
    if notion_api_key:
        notion_client = Client(auth=notion_api_key)
except Exception as e:
    pass

NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID")

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
    }
    # Remove Grok section
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
        if openai_client is None:
            return "Untitled Content (OpenAI API not configured)"
            
        response = openai_client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[
                {"role": "system", "content": "Create a concise, descriptive 5-7 word title that captures the main topic or theme of this content. Make it clear and engaging. Return ONLY the title words, nothing else."},
                {"role": "user", "content": f"Generate a 5-7 word title for this transcript:\n\n{text[:2000]}..."} # First 2000 chars for context
            ]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return "Untitled Content"

def chunk_text_for_notion(text, chunk_size=1900):
    """Split text into chunks that respect Notion's character limit"""
    if not text:
        return []
    return [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]

def create_content_notion_entry(title, transcript, wisdom=None, outline=None, social_content=None, image_prompts=None, article=None):
    """Create a new entry in the Notion database with all content sections"""
    if notion_client is None or not NOTION_DATABASE_ID:
        st.error("Notion API key or database ID not configured. Please check your .env file.")
        return False
        
    try:
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
        if openai_client is None:
            # Return a default dictionary of models if client isn't available
            return {
                "gpt-4": "gpt-4",
                "gpt-4-turbo-preview": "gpt-4-turbo-preview",
                "gpt-3.5-turbo": "gpt-3.5-turbo"
            }
        
        models = openai_client.models.list()
        gpt_models = {
            model.id: model.id for model in models 
            if any(x in model.id for x in ['gpt-4', 'gpt-3.5'])
        }
        return gpt_models
    except Exception as e:
        st.warning(f"Error fetching OpenAI models: {str(e)}")
        # Return default models if API fails
        return {
            "gpt-4": "gpt-4",
            "gpt-4-turbo-preview": "gpt-4-turbo-preview",
            "gpt-3.5-turbo": "gpt-3.5-turbo"
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
    """Fetch available models from the selected AI provider"""
    # Default models to return if API is unavailable
    default_openai_models = ["gpt-4", "gpt-4-turbo-preview", "gpt-3.5-turbo"]
    default_anthropic_models = ["claude-3-opus-20240229", "claude-3-sonnet-20240229", "claude-3-haiku-20240307"]
    
    try:
        if provider == "OpenAI":
            if openai_client is None:
                return default_openai_models
                
            models = openai_client.models.list()
            # Filter for chat-capable models
            available_models = [
                model.id for model in models 
                if any(name in model.id.lower() for name in ["gpt-4", "gpt-3.5"])
            ]
            # Sort to put GPT-4 models first
            available_models.sort(key=lambda x: "gpt-4" in x.lower(), reverse=True)
            return available_models if available_models else default_openai_models
            
        elif provider == "Anthropic":
            return default_anthropic_models
            
        # Remove Grok case
            
        return []
    except Exception as e:
        # Return default models without showing an error
        if provider == "OpenAI":
            return default_openai_models
        elif provider == "Anthropic":
            return default_anthropic_models
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
    if openai_client is None:
        st.error("Please configure your OpenAI API key in the .env file to enable transcription.")
        return ""
        
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
        
        if file_size > CHUNK_THRESHOLD:
            # Process large file in chunks
            transcript = transcribe_large_file(audio_path)
        else:
            # Process small file directly
            with open(audio_path, "rb") as audio:
                response = openai_client.audio.transcriptions.create(
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
        
        return transcript
        
    except Exception as e:
        st.error(f"Transcription error: {str(e)}")
        return ""

def generate_wisdom(transcript, ai_provider, model, custom_prompt=None, knowledge_base=None):
    """Extract key insights and wisdom from a transcript"""
    try:
        # Check if the selected provider is available
        if ai_provider == "OpenAI" and openai_client is None:
            return "OpenAI API key not configured. Please add your API key to the .env file."
        if ai_provider == "Anthropic" and anthropic_client is None:
            return "Anthropic API key not configured. Please add your API key to the .env file."
        
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
            response = openai_client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Here's the transcription to analyze:\n\n{transcript}"}
                ],
                max_tokens=1500
            )
            return response.choices[0].message.content
            
        elif ai_provider == "Anthropic":
            response = anthropic_client.messages.create(
                model=model,
                max_tokens=1500,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": f"Here's the transcription to analyze:\n\n{transcript}"}
                ]
            )
            return response.content[0].text
            
        # Remove Grok case
        
    except Exception as e:
        return f"Analysis error with {ai_provider} {model}: {str(e)}"

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
            response = anthropic_client.messages.create(
                model=model,
                max_tokens=1500,
                system=system_prompt,
                messages=[{"role": "user", "content": content}]
            )
            return response.content[0].text
            
    except Exception as e:
        st.error(f"Error creating outline with {ai_provider} {model}: {str(e)}")
        return None

def generate_social_content(wisdom, outline, ai_provider, model, custom_prompt=None, knowledge_base=None):
    """Create social media posts based on the content"""
    try:
        prompt = custom_prompt or DEFAULT_PROMPTS["social_media"]
        
        # Combine wisdom and outline for context
        content = f"WISDOM:\n{wisdom}\n\nOUTLINE:\n{outline}"
        
        # Use the selected AI provider and model
        if ai_provider == "OpenAI":
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
            response = anthropic_client.messages.create(
                model=model,
                max_tokens=1000,
                system=prompt,
                messages=[{"role": "user", "content": content}]
            )
            return response.content[0].text
            
    except Exception as e:
        st.error(f"Error creating social content with {ai_provider} {model}: {str(e)}")
        return None

def generate_image_prompts(wisdom, outline, ai_provider, model, custom_prompt=None, knowledge_base=None):
    """Create image generation prompts based on the content"""
    try:
        prompt = custom_prompt or DEFAULT_PROMPTS["image_prompts"]
        
        # Combine wisdom and outline for context
        content = f"WISDOM:\n{wisdom}\n\nOUTLINE:\n{outline}"
        
        # Use the selected AI provider and model
        if ai_provider == "OpenAI":
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
            response = anthropic_client.messages.create(
                model=model,
                max_tokens=1000,
                system=prompt,
                messages=[{"role": "user", "content": content}]
            )
            return response.content[0].text
            
    except Exception as e:
        st.error(f"Error creating image prompts with {ai_provider} {model}: {str(e)}")
        return None

def generate_article(transcript, wisdom, outline, ai_provider, model, custom_prompt=None, knowledge_base=None):
    """Write a full article based on the outline and content"""
    try:
        prompt = custom_prompt or """Write a comprehensive, engaging article based on the provided outline and wisdom.
        Include an introduction, developed sections following the outline, and a conclusion.
        Maintain a conversational yet authoritative tone."""
        
        # Combine all content for context
        content = f"TRANSCRIPT EXCERPT:\n{transcript[:1000]}...\n\nWISDOM:\n{wisdom}\n\nOUTLINE:\n{outline}"
        
        # Use the selected AI provider and model
        if ai_provider == "OpenAI":
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
            response = anthropic_client.messages.create(
                model=model,
                max_tokens=2500,
                system=prompt,
                messages=[{"role": "user", "content": content}]
            )
            return response.content[0].text
            
    except Exception as e:
        st.error(f"Error writing article with {ai_provider} {model}: {str(e)}")
        return None

def generate_seo_metadata(content, title):
    """Generate SEO metadata for the content"""
    try:
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
    # Initialize session state variables first to avoid errors
    if 'transcription' not in st.session_state:
        st.session_state.transcription = ""
    if 'wisdom' not in st.session_state:
        st.session_state.wisdom = ""
    if 'audio_file' not in st.session_state:
        st.session_state.audio_file = None
    if 'ai_provider' not in st.session_state:
        st.session_state.ai_provider = "OpenAI"
    if 'ai_model' not in st.session_state:
        st.session_state.ai_model = None
    
    # Apply the improved cyberpunk theme
    local_css()
    
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
        
        # Get available users
        selected_user = st.selectbox("User Profile", options=get_available_users(), key="user_profile")
        
        # Load knowledge base for selected user
        knowledge_base = load_user_knowledge_base(selected_user)
        
        # AI Provider selection in sidebar with clean UI
        ai_provider = st.selectbox(
            "AI Provider", 
            options=["OpenAI", "Anthropic"],
            key="ai_provider_select",
            on_change=lambda: setattr(st.session_state, 'ai_model', None)  # Reset model when provider changes
        )
        st.session_state.ai_provider = ai_provider
        
        # Fetch and display available models based on provider
        available_models = get_available_models(ai_provider)
        
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
        
        # Move system status to sidebar and clean up UI
        st.markdown('<div class="section-header">System Status</div>', unsafe_allow_html=True)
        st.markdown("""
        <div class="status-container">
            <div class="status-card">
                <h3>AI Provider</h3>
                <div class="status-value" id="ai-provider-value">OpenAI</div>
            </div>
            <div class="status-card">
                <h3>Security</h3>
                <div class="status-value" id="security-status">Encrypted</div>
            </div>
            <div class="status-card">
                <h3>Status</h3>
                <div class="status-value" id="content-status">Ready</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Update the status card with JavaScript
        st.markdown(f"""
        <script>
            document.getElementById('ai-provider-value').innerText = '{ai_provider}';
        </script>
        """, unsafe_allow_html=True)
        
        # Configure custom prompts in a cleaner way
        with st.expander("Custom Prompts", expanded=False):
            users_prompts = {}  # Initialize empty prompts dict
            configure_prompts(selected_user, users_prompts)
    
        # Knowledge Base Management
        with st.expander("Knowledge Base", expanded=False):
            st.markdown("### Knowledge Base Files")
            
            if knowledge_base:
                # Use selectbox instead of nested expanders
                selected_file = st.selectbox(
                    "Select file to view",
                    options=list(knowledge_base.keys()),
                    key="kb_file_selector"
                )
                if selected_file:
                    st.text_area(
                        "Content",
                        value=knowledge_base[selected_file],
                        height=100,
                        key=f"kb_{selected_file}",
                        disabled=True
                    )
            else:
                st.info("No knowledge base files found.")
            
            # Upload new knowledge base file
            st.markdown("### Add New Knowledge")
            
            uploaded_kb = st.file_uploader(
                "Add Knowledge Base File", 
                type=['txt', 'md'],
                key="kb_uploader"
            )
            
            if uploaded_kb:
                kb_name = st.text_input("File Name (without extension)", 
                                      value=os.path.splitext(uploaded_kb.name)[0])
                if st.button("Save to Knowledge Base"):
                    try:
                        kb_path = f'prompts/{selected_user}/knowledge_base'
                        os.makedirs(kb_path, exist_ok=True)
                        
                        with open(os.path.join(kb_path, f"{kb_name}.md"), "wb") as f:
                            f.write(uploaded_kb.getvalue())
                        st.success("Knowledge base file added successfully!")
                        st.experimental_rerun()
                    except Exception as e:
                        st.error(f"Error saving knowledge base file: {str(e)}")
    
        # Add this in the sidebar section:
        with st.sidebar:
            # ... existing sidebar code ...
            
            st.markdown('<div class="section-header">API Status</div>', unsafe_allow_html=True)
            
            # Check API keys
            openai_status = "Ready" if openai_client else "Not Configured"
            anthropic_status = "Ready" if anthropic_client else "Not Configured"
            notion_status = "Ready" if notion_client and NOTION_DATABASE_ID else "Not Configured"
            
            # Create colored status indicators
            st.markdown(f"""
            <div class="status-container">
                <div class="status-card">
                    <h3>OpenAI</h3>
                    <div class="status-value" style="color: {'var(--success)' if openai_client else 'var(--error)'}">
                        {openai_status}
                    </div>
                </div>
                <div class="status-card">
                    <h3>Anthropic</h3>
                    <div class="status-value" style="color: {'var(--success)' if anthropic_client else 'var(--error)'}">
                        {anthropic_status}
                    </div>
                </div>
                <div class="status-card">
                    <h3>Notion</h3>
                    <div class="status-value" style="color: {'var(--success)' if notion_client and NOTION_DATABASE_ID else 'var(--error)'}">
                        {notion_status}
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Show configuration help if APIs are missing
            missing_apis = []
            if not openai_client:
                missing_apis.append("OpenAI")
            if not anthropic_client:
                missing_apis.append("Anthropic")
            if not notion_client or not NOTION_DATABASE_ID:
                missing_apis.append("Notion")
            
            if missing_apis:
                with st.expander("Configuration Help"):
                    st.markdown(f"""
                    ### API Configuration
                    The following APIs need to be configured in your `.env` file:
                    
                    {', '.join(missing_apis)}
                    
                    Example `.env` file:
                    ```
                    OPENAI_API_KEY=sk-your-key-here
                    ANTHROPIC_API_KEY=sk-ant-your-key-here
                    NOTION_API_KEY=secret_your-key-here
                    NOTION_DATABASE_ID=your-database-id
                    ```
                    """)
    
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
        
        # Add custom message about large file support
        st.markdown("""
        <div style="font-size: 0.85rem; color: var(--text-secondary); margin-top: -15px; margin-bottom: 15px;">
            Large files (up to 500MB) are automatically chunked for optimal processing.
        </div>
        """, unsafe_allow_html=True)
        
        # Display the audio player if a file is uploaded
        if uploaded_file is not None:
            st.audio(uploaded_file, format='audio/wav')
        
        # Always display the buttons and disable if no file
        col1, col2 = st.columns(2)
        
        with col1:
            transcribe_disabled = uploaded_file is None
            transcribe_button = st.button(
                "Transcribe Audio", 
                key="transcribe_button", 
                use_container_width=True,
                disabled=transcribe_disabled
            )
        
        with col2:
            lucky_disabled = uploaded_file is None
            lucky_button = st.button(
                "I'm Feeling Lucky", 
                key="lucky_button", 
                use_container_width=True,
                disabled=lucky_disabled
            )
        
        # Display a helpful message when no file is uploaded
        if uploaded_file is None:
            st.info("👆 Upload an audio file to begin transcription and processing")
        
        # Process based on which button was clicked
        if uploaded_file is not None:
            if transcribe_button:
                try:
                    with st.spinner("Transcribing..."):
                        # Process the audio file
                        transcription = transcribe_audio(uploaded_file)
                        st.session_state.transcription = transcription
                        st.session_state.audio_file = uploaded_file
                        
                        # Show transcription
                        st.text_area("Transcription", transcription, height=200)
                        
                        # Add a process content button after transcription
                        process_button = st.button("Process Content", key="process_after_transcribe", use_container_width=True)
                        if process_button:
                            with st.spinner("Processing content with AI..."):
                                results = process_all_content(
                                    transcription, 
                                    st.session_state.ai_provider, 
                                    st.session_state.ai_model,
                                    knowledge_base
                                )
                                for key, value in results.items():
                                    st.session_state[key] = value
                except Exception as e:
                    st.error(f"Transcription error: {str(e)}")
                    st.error("Please make sure your audio file is in a supported format and not corrupted.")
            
            elif lucky_button:
                try:
                    with st.spinner("Working magic - transcribing and processing audio..."):
                        # First transcribe
                        transcription = transcribe_audio(uploaded_file)
                        st.session_state.transcription = transcription
                        st.session_state.audio_file = uploaded_file
                        
                        # Show transcription
                        st.text_area("Transcription", transcription, height=200)
                        
                        # Now process everything and post to Notion in one go
                        with st.spinner("Generating content..."):
                            results = process_all_content(
                                transcription, 
                            st.session_state.ai_provider, 
                            st.session_state.ai_model,
                                knowledge_base
                            )
                            
                            if results:
                                for key, value in results.items():
                                    st.session_state[key] = value
                                
                                # Generate title for Notion
                                title = generate_short_title(transcription)
                                
                                # Post to Notion if credentials are available
                                notion_api_key = os.environ.get('NOTION_API_KEY', '')
                                notion_database_id = os.environ.get('NOTION_DATABASE_ID', '')
                                
                                if notion_api_key and notion_database_id:
                                    with st.spinner("Exporting to Notion..."):
                                        create_content_notion_entry(
                                            title,
                                            transcription,
                                            results.get('wisdom'),
                                            results.get('outline'),
                                            results.get('social_posts'),
                                            results.get('image_prompts'),
                                            results.get('article')
                                        )
                                        st.success("Everything processed and saved to Notion!")
                                else:
                                    st.success("Everything processed!")
                                    st.info("To export to Notion, configure NOTION_API_KEY and NOTION_DATABASE_ID environment variables.")
                except Exception as e:
                    st.error(f"Processing error: {str(e)}")
                    st.error("Please make sure your audio file is in a supported format and not corrupted.")
    
    # Tab 2: Text Input
    with input_tabs[1]:
        st.markdown('<div class="section-header">Text Processing</div>', unsafe_allow_html=True)
        
        text_input = st.text_area("Enter your text", height=200, key="text_input_area")
        
        if text_input:
            if st.button("I'm Feeling Lucky", key="text_lucky_button", use_container_width=True):
                # Create placeholder elements for streaming updates
                progress_placeholder = st.empty()
                wisdom_placeholder = st.empty()
                outline_placeholder = st.empty()
                social_placeholder = st.empty()
                image_placeholder = st.empty()
                article_placeholder = st.empty()
                export_placeholder = st.empty()
                
                # Store the text input as transcription
                st.session_state.transcription = text_input
                
                # Generate wisdom with streaming feedback
                with progress_placeholder.container():
                    st.info("Step 1/6: Extracting key insights...")
                
                wisdom = generate_wisdom(
                    text_input, 
                                st.session_state.ai_provider,
                                st.session_state.ai_model,
                    knowledge_base=knowledge_base
                )
                st.session_state.wisdom = wisdom
                
                # Update wisdom placeholder
                with wisdom_placeholder.container():
                    st.subheader("Key Insights")
                    st.markdown(wisdom)
                
                # Create outline with streaming updates
                with progress_placeholder.container():
                    st.info("Step 2/6: Creating content outline...")
                
                outline = generate_outline(
                    text_input, 
                    wisdom,
                                    st.session_state.ai_provider,
                                    st.session_state.ai_model,
                    knowledge_base=knowledge_base
                )
                st.session_state.outline = outline
                
                # Update outline placeholder
                with outline_placeholder.container():
                    st.subheader("Content Outline")
                    st.markdown(outline)
                
                # Social content
                with progress_placeholder.container():
                    st.info("Step 3/6: Generating social media posts...")
                
                social_content = generate_social_content(
                    wisdom,
                    outline,
                                    st.session_state.ai_provider,
                                    st.session_state.ai_model,
                    knowledge_base=knowledge_base
                )
                st.session_state.social_posts = social_content
                
                # Update social placeholder
                with social_placeholder.container():
                    st.subheader("Social Media Posts")
                    st.markdown(social_content)
                
                # Image prompts
                with progress_placeholder.container():
                    st.info("Step 4/6: Creating image prompts...")
                
                image_prompts = generate_image_prompts(
                    wisdom,
                    outline,
                                    st.session_state.ai_provider,
                                    st.session_state.ai_model,
                    knowledge_base=knowledge_base
                )
                st.session_state.image_prompts = image_prompts
                
                # Update image placeholder
                with image_placeholder.container():
                    st.subheader("Image Prompts")
                    st.markdown(image_prompts)
                
                # Article
                with progress_placeholder.container():
                    st.info("Step 5/6: Writing full article...")
                
                article = generate_article(
                    text_input,
                    wisdom,
                    outline,
                    st.session_state.ai_provider, 
                    st.session_state.ai_model,
                    knowledge_base=knowledge_base
                )
                st.session_state.article = article
                
                # Update article placeholder
                with article_placeholder.container():
                    st.subheader("Full Article")
                    st.markdown(article)
                
                # Generate title for Notion
                title = generate_short_title(text_input)
                
                # Post to Notion if credentials are available
                notion_api_key = os.environ.get('NOTION_API_KEY', '')
                notion_database_id = os.environ.get('NOTION_DATABASE_ID', '')
                
                if notion_api_key and notion_database_id:
                    with progress_placeholder.container():
                        st.info("Step 6/6: Exporting to Notion...")
                    
                    try:
                        notion_url = create_content_notion_entry(
                            title,
                            text_input,
                            wisdom,
                            outline,
                            social_content,
                            image_prompts,
                            article
                        )
                        
                        with export_placeholder.container():
                            st.success("Everything processed and saved to Notion!")
                            if notion_url:
                                st.markdown(f"[Open in Notion]({notion_url})")
                    except Exception as e:
                        with export_placeholder.container():
                            st.error(f"Error exporting to Notion: {str(e)}")
                else:
                    with progress_placeholder.container():
                        st.success("All content processed!")
                        st.info("To export to Notion, configure NOTION_API_KEY and NOTION_DATABASE_ID environment variables.")
                    
                # Final progress update
                with progress_placeholder.container():
                    st.success("Content generation complete!")
    
    # Display generated content in the main area, below the input tabs
    if st.session_state.transcription:
        if 'wisdom' in st.session_state and st.session_state.wisdom:
            st.markdown('<div class="section-header">Generated Content</div>', unsafe_allow_html=True)
            
            # Key Insights section
            st.markdown("### Key Insights")
            st.markdown(st.session_state.wisdom)
            
            # Display other generated content if available
            if 'outline' in st.session_state and st.session_state.outline:
                st.markdown("### Content Outline")
                st.markdown(st.session_state.outline)
            
            if 'social_content' in st.session_state and st.session_state.social_content:
                st.markdown("### Social Media Posts")
                st.markdown(st.session_state.social_content)
            
            if 'image_prompts' in st.session_state and st.session_state.image_prompts:
                st.markdown("### Image Generation Prompts")
                st.markdown(st.session_state.image_prompts)
            
            if 'article' in st.session_state and st.session_state.article:
                st.markdown("### Full Article")
                st.markdown(st.session_state.article)
            
            # Export to Notion section
            st.markdown('<div class="section-header">Export Options</div>', unsafe_allow_html=True)
            
            notion_api_key = os.environ.get('NOTION_API_KEY', '')
            notion_database_id = os.environ.get('NOTION_DATABASE_ID', '')
            
            if notion_api_key and notion_database_id:
                if st.button("Export to Notion"):
                    with st.spinner("Exporting to Notion..."):
                        try:
                            title = generate_short_title(st.session_state.transcription)
                            create_content_notion_entry(
                                title,
                                st.session_state.transcription,
                                st.session_state.wisdom if 'wisdom' in st.session_state else None,
                                st.session_state.outline if 'outline' in st.session_state else None,
                                st.session_state.social_content if 'social_content' in st.session_state else None,
                                st.session_state.image_prompts if 'image_prompts' in st.session_state else None,
                                st.session_state.article if 'article' in st.session_state else None
                            )
                            st.success("Successfully exported to Notion!")
                        except Exception as e:
                            st.error(f"Error exporting to Notion: {str(e)}")
            else:
                st.info("To export to Notion, please configure the NOTION_API_KEY and NOTION_DATABASE_ID environment variables.")
    
    # Add the footer
    st.markdown("""
    <div class="app-footer">
        <div class="footer-content">
            <div>WhisperForge Control Center v1.0</div>
            <div class="footer-status">
                <span class="status-secure"><span class="footer-status-dot"></span>Encrypted</span>
                <span class="status-sovereignty"><span class="footer-status-dot"></span>Knowledge Sovereignty</span>
                <span class="status-offline"><span class="footer-status-dot"></span>Offline Capable</span>
            </div>
            <div>© 2025 CypherMedia Group</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

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

if __name__ == "__main__":
    main() 