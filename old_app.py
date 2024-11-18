"""
WhisperForge - AI-powered audio transcription and analysis tool.

This module contains the main Streamlit application code for WhisperForge,
integrating OpenAI's Whisper model with Notion for documentation.
"""

import streamlit as st
from streamlit.components.v1 import html
import tempfile
import os
from pathlib import Path
from openai import OpenAI
from datetime import datetime, timezone, timedelta
from notion_client import Client
import hashlib
import pickle
from dotenv import load_dotenv
import logging
import time
import requests

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('whisperforge.log')
    ]
)

# Load environment variables from .env file
load_dotenv()

# Initialize the OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Define a simple cache dictionary
cache = {}

def local_css():
    st.markdown("""
        <style>
        /* Main theme colors */
        :root {
            --main-bg-color: #000000;
            --text-color: #ffffff;
            --accent-color: #ff4d4d;
            --border-color: rgba(255,255,255,0.1);
            --secondary-bg: #1a1a1a;
            --hover-bg: #2a2a2a;
        }
        
        /* Global styles */
        .stApp {
            background-color: var(--main-bg-color);
            color: var(--text-color);
        }
        
        /* Sidebar styling */
        .css-1d391kg {  /* Sidebar */
            background-color: var(--main-bg-color);
        }
        
        /* Button styling */
        .stButton > button {
            width: 100%;
            background-color: var(--secondary-bg);
            color: var(--text-color);
            border: 1px solid var(--border-color);
            padding: 15px 20px;
            border-radius: 12px;
            font-size: 16px;
            font-weight: 500;
            transition: all 0.3s ease;
            margin: 5px 0;
            text-align: left;
        }
        
        .stButton > button:hover {
            background-color: var(--hover-bg);
            border-color: var(--accent-color);
        }
        
        /* Input fields */
        .stTextInput input {
            background-color: var(--secondary-bg);
            border: 1px solid var(--border-color);
            color: var(--text-color);
            border-radius: 12px;
            padding: 12px;
        }
        
        /* File uploader */
        .stFileUploader {
            background-color: var(--secondary-bg);
            border: 2px dashed var(--border-color);
            padding: 20px;
            border-radius: 12px;
            transition: all 0.3s ease;
        }
        
        .stFileUploader:hover {
            border-color: var(--accent-color);
        }
        
        /* Expander */
        .streamlit-expanderHeader {
            background-color: var(--secondary-bg);
            border-radius: 12px;
            border: 1px solid var(--border-color);
        }
        
        .streamlit-expanderHeader:hover {
            background-color: var(--hover-bg);
        }
        
        /* Text areas */
        .stTextArea textarea {
            background-color: var(--secondary-bg);
            color: var(--text-color);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 12px;
        }
        
        /* Select boxes */
        .stSelectbox > div > div {
            background-color: var(--secondary-bg);
            border: 1px solid var(--border-color);
            border-radius: 12px;
        }
        
        /* Progress bars */
        .stProgress > div > div {
            background-color: var(--accent-color);
        }
        
        /* Success/Info messages */
        .stSuccess, .stInfo {
            background-color: var(--secondary-bg);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 10px;
        }
        </style>
    """, unsafe_allow_html=True)

def render_header():
    st.markdown('<div class="brand-header"><h1 class="brand-name">WhisperForge</h1></div>', unsafe_allow_html=True)

def render_footer():
    st.markdown("""
        <div class="footer">
            <p>Created by Kris Krüg © 2024 | WhisperForge.ai v0.1 alpha</p>
        </div>
    """, unsafe_allow_html=True)

def split_audio(file_path, chunk_length_ms):
    filename = os.path.splitext(os.path.basename(file_path))[0]
    st.info(f"Loading audio file: {filename}")
    
    # Use ffmpeg directly instead of pydub
    import subprocess
    import math
    
    # Get duration using ffprobe
    duration_cmd = [
        'ffprobe', 
        '-v', 'error',
        '-show_entries', 'format=duration',
        '-of', 'default=noprint_wrappers=1:nokey=1',
        file_path
    ]
    
    duration = float(subprocess.check_output(duration_cmd).decode('utf-8').strip())
    num_chunks = math.ceil(duration / (chunk_length_ms / 1000))
    
    chunk_files = []
    for i in range(num_chunks):
        start_time = i * chunk_length_ms / 1000
        chunk_file = f"whisperforge_{filename}_chunk_{i}.mp3"
        
        # Use ffmpeg to extract chunk
        subprocess.run([
            'ffmpeg',
            '-y',  # Overwrite output files
            '-i', file_path,
            '-ss', str(start_time),
            '-t', str(chunk_length_ms / 1000),
            '-acodec', 'libmp3lame',
            chunk_file
        ], stderr=subprocess.DEVNULL)
        
        chunk_files.append(chunk_file)
        st.info(f"Created chunk {i+1} of {num_chunks}")
    
    return chunk_files

def transcribe_chunks(chunk_files):
    transcriptions = []
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i, chunk_file in enumerate(chunk_files):
        try:
            with open(chunk_file, "rb") as audio_file:
                # Update progress bar and status
                progress = (i + 1) / len(chunk_files)
                progress_bar.progress(progress)
                status_text.text(f"Transcribing: {i + 1}/{len(chunk_files)}")
                
                transcription = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file
                )
                transcriptions.append(transcription.text)
                
                # Clean up chunk file after processing
                os.remove(chunk_file)
        except Exception as e:
            st.error(f"Error transcribing chunk {i+1}: {str(e)}")
    
    progress_bar.empty()
    status_text.empty()
    return transcriptions

def chunk_text(text, max_tokens=6000):
    """Split text into chunks that fit within token limits."""
    # Rough estimate: 1 token ≈ 4 characters
    chunk_size = max_tokens * 4
    chunks = []
    
    # Split into paragraphs first
    paragraphs = text.split('\n')
    current_chunk = []
    current_length = 0
    
    for paragraph in paragraphs:
        if current_length + len(paragraph) > chunk_size:
            # Save current chunk and start new one
            chunks.append('\n'.join(current_chunk))
            current_chunk = [paragraph]
            current_length = len(paragraph)
        else:
            current_chunk.append(paragraph)
            current_length += len(paragraph)
    
    # Add the last chunk
    if current_chunk:
        chunks.append('\n'.join(current_chunk))
    
    return chunks

def setup_advanced_settings():
    """Setup advanced settings in sidebar."""
    with st.sidebar:
        with st.expander("Advanced Settings", expanded=False):
            chunk_size = st.slider(
                "Chunk Size (tokens)", 
                min_value=1000, 
                max_value=6000, 
                value=4000,
                help="Adjust the size of text chunks sent to GPT. Lower this if you get token limit errors."
            )
            
            show_chunks = st.checkbox(
                "Show Chunk Processing", 
                value=False,
                help="Show detailed progress of chunk processing"
            )
            
            return {
                "chunk_size": chunk_size,
                "show_chunks": show_chunks
            }

def process_with_gpt(text, mode, custom_prompt="", settings=None):
    """Process text with GPT, handling long content by chunking.
    
    Args:
        text (str): The input text to process
        mode (str): Processing mode ('summarize', 'extract insights', or 'custom instructions')
        custom_prompt (str, optional): Custom instructions for processing. Defaults to "".
        settings (dict, optional): Processing settings including:
            - chunk_size (int): Maximum tokens per chunk (default: 4000)
            - show_chunks (bool): Whether to show chunk processing progress (default: False)
    
    Returns:
        str: Processed text result, or None if processing fails
        
    Error Handling:
        - Displays warnings for large texts (>100k estimated tokens)
        - Provides actionable solutions for token limit errors
        - Shows detailed progress for chunk processing when enabled
    """
    if settings is None:
        settings = {"chunk_size": 4000, "show_chunks": False}
    
    try:
        chunks = chunk_text(text, max_tokens=settings["chunk_size"])
        
        # Add token size warning if text is very large
        total_chars = len(text)
        estimated_tokens = total_chars // 4  # Rough estimate
        if estimated_tokens > 100000:  # Arbitrary large number
            st.warning(f"⚠️ Large text detected (~{estimated_tokens:,} tokens). Processing may take longer.")
        
        all_results = []
        
        # Create a progress bar for chunks
        if settings["show_chunks"]:
            chunk_progress = st.progress(0)
            chunk_status = st.empty()
        
        for i, chunk in enumerate(chunks):
            try:
                if settings["show_chunks"]:
                    chunk_status.write(f"Processing chunk {i+1} of {len(chunks)}...")
                    chunk_progress.progress((i + 1) / len(chunks))
                
                # Handle custom instructions specially
                if mode == "custom instructions":
                    if custom_prompt.lower().strip() == "in spanish":
                        prompt = f"Translate the following text to Spanish:\n\n{chunk}"
                    else:
                        prompt = f"{custom_prompt}\n\n{chunk}"
                elif mode == "summarize":
                    prompt = f"Please summarize the following text. Focus on key points and main ideas:\n\n{chunk}"
                elif mode == "extract insights":
                    prompt = f"""Analyze the following text and provide:
                    **One-line Summary:**
                    **Key Themes:**
                    **Notable Points:**\n\n{chunk}"""
                
                response = client.chat.completions.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant skilled in analyzing and processing text."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=2000
                )
                
                result = response.choices[0].message.content
                all_results.append(result)
                
            except Exception as chunk_error:
                if "maximum context length" in str(chunk_error).lower():
                    st.error(f"""
                        🚫 Token limit exceeded in chunk {i+1}!
                        Try one of these solutions:
                        1. Reduce the chunk size in Advanced Settings
                        2. Use a shorter custom prompt
                        3. Process a smaller portion of the text
                        
                        Technical details: {str(chunk_error)}
                    """)
                else:
                    st.error(f"Error processing chunk {i+1}: {str(chunk_error)}")
                return None
        
        # Clear chunk progress indicators
        if settings["show_chunks"]:
            chunk_status.empty()
            chunk_progress.empty()
        
        # Combine results
        combined_result = "\n\n".join(all_results)
        
        # For translation, we don't need a final summary
        if mode == "custom instructions" and custom_prompt.lower().strip() == "in spanish":
            return combined_result
        
        # Final summary if multiple chunks
        if len(chunks) > 1:
            if settings["show_chunks"]:
                st.write("Creating final summary...")
            
            final_summary = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant skilled in synthesizing information."},
                    {"role": "user", "content": f"Please provide a cohesive summary combining these sections:\n\n{combined_result}"}
                ],
                max_tokens=2000
            )
            return final_summary.choices[0].message.content
        
        return combined_result
        
    except Exception as e:
        logging.error(f"Error processing with GPT: {str(e)}")
        st.error(f"Error processing with GPT: {str(e)}")
        return None

def generate_title_summary_tags(text):
    """Generate a title, one-line summary, and 5 relevant tags using GPT."""
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": """Generate:
                1. A compelling title that captures the essence (5-7 words)
                2. A one-line summary (max 15 words)
                3. Five relevant tags (single words or short phrases)

                Format as:
                TITLE: [title]
                SUMMARY: [one line]
                TAGS: [tag1], [tag2], [tag3], [tag4], [tag5]"""},
                {"role": "user", "content": text}
            ]
        )
        result = response.choices[0].message.content
        title = result.split("TITLE: ")[1].split("\n")[0].strip()
        summary = result.split("SUMMARY: ")[1].split("\n")[0].strip()
        tags = result.split("TAGS: ")[1].strip().split(", ")
        return title, summary, tags
    except Exception as e:
        st.error(f"Error generating title and summary: {str(e)}")
        return "Untitled Transcription", "[Summary generation failed]", ["transcription"]

def parse_processed_text(text):
    """Parse the processed text into sections."""
    sections = {
        "insights": [],
        "takeaways": [],
        "quotes": []
    }
    
    current_section = None
    for line in text.split('\n'):
        line = line.strip()
        if "1. Key Insights" in line:
            current_section = "insights"
        elif "2. Actionable Takeaways" in line:
            current_section = "takeaways"
        elif "3. Notable Quotes" in line:
            current_section = "quotes"
        elif line.startswith("- ") and current_section:
            sections[current_section].append(line[2:])  # Remove "- " prefix
            
    return sections

def send_to_notion(transcription: str, processed_text: str, notion_key: str, filename: str) -> tuple[bool, str, str]:
    """Send results to Notion via the storage service."""
    try:
        # Prepare the request to the storage service
        storage_url = "http://localhost:8002/store"  # Adjust port as needed
        headers = {
            "Authorization": f"Bearer {os.getenv('SERVICE_TOKEN')}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "transcription": transcription,
            "processed_text": processed_text,
            "filename": filename,
            "timestamp": datetime.now().isoformat(),
            "duration": None  # Add audio duration if available
        }
        
        # Send request to storage service
        response = requests.post(storage_url, json=payload, headers=headers)
        response.raise_for_status()
        
        result = response.json()
        return True, "Successfully exported to Notion", result["notion_url"]
        
    except Exception as e:
        logging.error(f"Notion export error: {str(e)}")
        return False, f"Failed to export to Notion: {str(e)}", ""

def split_transcription_into_blocks(transcription, max_length=1800):
    """Split transcription into Notion blocks."""
    chunks = []
    words = transcription.split()
    current_chunk = []
    current_length = 0
    
    for word in words:
        if current_length + len(word) + 1 > max_length:
            chunks.append(" ".join(current_chunk))
            current_chunk = [word]
            current_length = len(word)
        else:
            current_chunk.append(word)
            current_length += len(word) + 1
            
    if current_chunk:
        chunks.append(" ".join(current_chunk))
    
    return [
        {
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [{
                    "text": {"content": chunk}
                }]
            }
        }
        for chunk in chunks
    ]

def setup_notion_integration():
    st.sidebar.markdown("### Notion Integration")
    notion_key = st.sidebar.text_input(
        "Notion API Key", 
        value=os.getenv("NOTION_API_KEY", ""),
        type="password",
        help="Your Notion integration token"
    )
    return notion_key, "124c6f799a33806593b1c7afdc34ef94"

def cleanup_temp_files():
    """Clean up any temporary files created during processing."""
    try:
        for file in os.listdir():
            if file.startswith("whisperforge_") and file.endswith(".mp3"):
                os.remove(file)
    except Exception as e:
        st.error(f"Error cleaning up temporary files: {str(e)}")

def get_cache_key(file_path):
    """Generate a unique cache key based on the file content."""
    with open(file_path, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()

def load_cache():
    """Load cache from a file if it exists."""
    global cache
    if os.path.exists("cache.pkl"):
        with open("cache.pkl", "rb") as f:
            cache = pickle.load(f)
        logging.info("Cache loaded successfully.")
    else:
        logging.info("No cache file found. Starting with an empty cache.")

def save_cache():
    """Save cache to a file."""
    with open("cache.pkl", "wb") as f:
        pickle.dump(cache, f)
    logging.info(f"Cache saved successfully. Contains {len(cache)} items.")
    # Only rerun if explicitly requested
    if st.session_state.get('force_rerun', False):
        st.session_state.force_rerun = False
        st.rerun()

def transcribe_with_cache(file_path):
    """Transcribe audio with caching and verification."""
    cache_key = get_cache_key(file_path)
    
    logging.info(f"File: {os.path.basename(file_path)}")
    logging.info(f"Cache key: {cache_key}")
    logging.info(f"Current cache size: {len(cache)} items")
    
    if cache_key in cache:
        cached_text = cache[cache_key]
        logging.info(f"Cache HIT! Text length: {len(cached_text)}")
        st.success(f"🎯 Using cached transcription! (Cache key: {cache_key[:8]}...)")
        return cached_text
    
    logging.info("Cache MISS - Performing new transcription")
    transcription = transcribe_audio(file_path)
    cache[cache_key] = transcription
    save_cache()
    
    # Add logging to track flow
    logging.info("Transcription completed and cached, continuing with processing...")
    return transcription

def transcribe_audio(file_path):
    """Transcribe audio using OpenAI's Whisper model with progress updates."""
    logging.info(f"Starting transcription for file: {file_path}")
    
    # Get file size for progress estimation
    file_size = os.path.getsize(file_path)
    st.write(f"Processing {file_size/1024/1024:.1f}MB audio file...")
    
    # Create a progress placeholder
    progress_placeholder = st.empty()
    
    start_time = time.time()
    try:
        with open(file_path, "rb") as audio_file:
            # Show initial progress message
            progress_placeholder.info("Starting transcription... (this may take a few minutes)")
            
            response = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file
            )
            
            # Show completion time
            duration = time.time() - start_time
            progress_placeholder.success(f"Transcription completed in {duration:.1f} seconds!")
            
            logging.info(f"Completed transcription for file: {file_path}")
            return response.text
            
    except Exception as e:
        progress_placeholder.error(f"Transcription error: {str(e)}")
        raise e

def clear_cache():
    """Clear the cache file."""
    if os.path.exists("cache.pkl"):
        os.remove("cache.pkl")
        st.sidebar.success("Cache cleared!")
        global cache
        cache = {}

def setup_cache_display():
    """Setup cache display in sidebar"""
    # Move cache controls into an expander
    with st.sidebar.expander("🔧 Developer Tools", expanded=False):
        st.markdown("### 💾 Cache Status")
        
        # Force refresh cache status
        if os.path.exists("cache.pkl"):
            try:
                with open("cache.pkl", "rb") as f:
                    current_cache = pickle.load(f)
                    st.success(f"📦 Cache contains {len(current_cache)} items")
                    if st.checkbox("Show Cache Details"):
                        for key in current_cache.keys():
                            st.code(f"Cache Key: {key[:8]}...")
                    st.session_state.cache_initialized = True
            except Exception as e:
                st.warning(f"Error reading cache: {str(e)}")
        else:
            st.warning("🚫 No cache file exists")
            st.session_state.cache_initialized = False

        if st.button("🧹 Clear Cache"):
            if os.path.exists("cache.pkl"):
                os.remove("cache.pkl")
                st.success("Cache cleared!")
                st.session_state.cache_initialized = False
                st.rerun()

def create_download_button(text, filename, button_text):
    """Create a download button for text content."""
    try:
        # Create a temporary file with the content
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as tmp_file:
            tmp_file.write(text)
            tmp_file.flush()
            
            # Read the file in binary mode for download
            with open(tmp_file.name, 'rb') as f:
                return st.download_button(
                    label=button_text,
                    data=f.read(),
                    file_name=filename,
                    mime='text/plain'
                )
    except Exception as e:
        st.error(f"Error creating download button: {str(e)}")
        return None

def reset_processing_state():
    """Reset all processing-related state variables."""
    st.session_state.transcription_text = None
    st.session_state.processed_text = None
    st.session_state.notion_url = None
    st.session_state.processing_complete = False

def main():
    # Load cache at startup
    load_cache()
    
    # Setup cache display
    setup_cache_display()
    
    local_css()
    render_header()

    # Initialize session state variables if they don't exist
    if 'transcription_text' not in st.session_state:
        st.session_state.transcription_text = None
    if 'processed_text' not in st.session_state:
        st.session_state.processed_text = None
    if 'notion_url' not in st.session_state:
        st.session_state.notion_url = None
    if 'processing_complete' not in st.session_state:
        st.session_state.processing_complete = False

    # Sidebar configuration
    with st.sidebar:
        st.markdown("### Configuration")
        api_key = os.getenv("OPENAI_API_KEY")
        notion_key = None
        enable_notion = st.checkbox("Enable Notion Export")
        if enable_notion:
            notion_key = os.getenv("NOTION_API_KEY")

    # Main content area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        uploaded_file = st.file_uploader("Upload Audio File", type=['mp3', 'wav', 'm4a', 'ogg'])
        
    with col2:
        with st.expander("Advanced Settings"):
            chunk_length = st.slider("Chunk Length (min)", 1, 30, 5)
            language = st.selectbox("Language", ["Auto-detect", "English", "Spanish", "French", "German"])
    
    # Processing Mode Selection
    processing_mode = st.selectbox(
        "Processing Mode",
        ["Extract Insights", "Summarize", "Custom Instructions"],
        format_func=lambda x: x.title()
    )
    
    custom_prompt = ""
    if processing_mode == "Custom Instructions":
        custom_prompt = st.text_area("Custom Instructions", height=100)

    # Process button
    if uploaded_file:
        if st.button("Process Audio"):
            try:
                with st.status("Processing audio file...") as status:
                    # Step 1: Load File
                    status.update(label="Loading audio file...")
                    with tempfile.NamedTemporaryFile(delete=False, suffix=Path(uploaded_file.name).suffix) as tmp_file:
                        tmp_file.write(uploaded_file.getvalue())
                        audio_path = tmp_file.name
                    
                    # Step 2: Transcribe
                    status.update(label="Transcribing audio...")
                    logging.info("Starting transcription step...")
                    transcription = transcribe_with_cache(audio_path)
                    if not transcription:
                        raise Exception("Transcription failed")
                    logging.info("Transcription successful, length: %d", len(transcription))
                    st.session_state.transcription_text = transcription
                    
                    # Step 3: Process with GPT
                    status.update(label="Processing with GPT...")
                    logging.info(f"Starting GPT processing with mode: {processing_mode}")
                    if processing_mode == "Custom Instructions":
                        advanced_settings = setup_advanced_settings()
                        processed_text = process_with_gpt(
                            transcription, 
                            processing_mode.lower(), 
                            custom_prompt,
                            settings=advanced_settings
                        )
                    else:
                        processed_text = process_with_gpt(transcription, processing_mode.lower())
                    
                    if not processed_text:
                        raise Exception("GPT processing failed")
                    logging.info("GPT processing completed successfully")
                    st.session_state.processed_text = processed_text
                    
                    # Step 4: Export to Notion
                    if enable_notion and notion_key:
                        status.update(label="Exporting to Notion...")
                        success, message, url = send_to_notion(
                            transcription,
                            processed_text,
                            notion_key,
                            uploaded_file.name
                        )
                        if success:
                            st.session_state.notion_url = url
                            
                    status.update(label="Complete!", state="complete")
                    st.session_state.processing_complete = True
                    
            except Exception as e:
                st.error(f"Error during processing: {str(e)}")
                logging.error(f"Processing error: {str(e)}")
                reset_processing_state()
            finally:
                cleanup_temp_files()

    # Show results if they exist in session state
    if st.session_state.transcription_text:
        col1, col2 = st.columns([6, 1])
        with col1:
            st.text_area("Full Transcription", st.session_state.transcription_text, height=300)
        with col2:
            create_download_button(
                st.session_state.transcription_text,
                "transcription.txt",
                "⬇️ Download Transcription"
            )
        
    if st.session_state.processed_text:
        col1, col2 = st.columns([6, 1])
        with col1:
            st.text_area("Processed Result", st.session_state.processed_text, height=300)
        with col2:
            create_download_button(
                st.session_state.processed_text,
                "processed_result.txt",
                "⬇️ Download Results"
            )

    # After processing is complete
    if st.session_state.processing_complete:
        with st.expander("Processing Results", expanded=True):
            if st.session_state.transcription_text:
                st.text_area("Transcription", st.session_state.transcription_text, height=200)
                
            if st.session_state.processed_text:
                st.text_area("Processed Text", st.session_state.processed_text, height=200)
                
            if st.session_state.notion_url:
                st.markdown(f"""
                ### Notion Export
                ✅ Successfully exported to Notion  
                [View Document]({st.session_state.notion_url})
                """)

    render_footer()

if __name__ == "__main__":
    main()


