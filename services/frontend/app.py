"""
WhisperForge - AI-powered audio transcription and analysis tool.
"""

import streamlit as st
import logging
import sys
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
import time
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

# Modified logging setup
logging.basicConfig(
    level=logging.INFO,
    format='\033[92m%(asctime)s [%(levelname)s]\033[0m %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger('whisperforge')

# Load environment variables
load_dotenv()

# Replace environment debug with simple service check
def check_environment():
    logger.info("Checking environment configuration...")
    required_vars = ['OPENAI_API_KEY', 'NOTION_API_KEY', 'SERVICE_TOKEN']
    missing = [var for var in required_vars if not os.getenv(var)]
    if missing:
        logger.error(f"Missing required environment variables: {', '.join(missing)}")
        return False
    return True

# Service URLs
TRANSCRIPTION_URL = "http://transcription:8000"
PROCESSING_URL = "http://processing:8000"
STORAGE_URL = "http://storage:8000"

# Your CSS styles here...
st.markdown("""
<style>
    /* Base theme */
    .stApp {
        background-color: #0A0404;
    }
    
    /* Terminal-style typography */
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&display=swap');
    
    * {
        font-family: 'JetBrains Mono', monospace !important;
    }
    
    /* Header styling */
    .header {
        color: #FF3B3B;
        border-bottom: 1px solid #FF3B3B33;
        padding: 1rem 0;
        margin-bottom: 2rem;
    }
    
    .header h1 {
        font-size: 1.8rem;
        font-weight: 700;
    }
    
    /* Terminal sections */
    .terminal-section {
        background: #1A0808;
        border: 1px solid #FF3B3B33;
        border-radius: 4px;
        padding: 1.5rem;
        margin: 1rem 0;
    }
    
    .section-header {
        color: #FF3B3B;
        font-size: 1.2rem;
        margin-bottom: 1rem;
    }
    
    /* Upload area */
    .upload-area {
        border: 2px dashed #FF3B3B33;
        border-radius: 4px;
        padding: 2rem;
        text-align: center;
        color: #FF3B3B;
    }
    
    /* Buttons */
    .stButton>button {
        background-color: #2A0808 !important;
        color: #FF3B3B !important;
        border: 1px solid #FF3B3B !important;
        border-radius: 2px;
        padding: 0.5rem 1rem;
        font-size: 0.9rem;
        transition: all 0.3s ease;
    }
    
    .stButton>button:hover {
        background-color: #FF3B3B22 !important;
    }
    
    /* Selectbox */
    .stSelectbox > div > div {
        background-color: #2A0808 !important;
        color: #FF3B3B !important;
        border: 1px solid #FF3B3B33 !important;
    }
    
    /* Progress/Status */
    .stProgress > div > div {
        background-color: #FF3B3B !important;
    }
    
    /* Text areas */
    .output-text {
        background: #0A0404;
        color: #FF3B3B;
        border: 1px solid #FF3B3B33;
        padding: 1rem;
        font-family: 'JetBrains Mono', monospace;
    }
    
    /* Custom decrypt section */
    .decrypt-section {
        text-align: center;
        color: #FF3B3B;
        padding: 3rem;
        border: 2px dashed #FF3B3B33;
        border-radius: 8px;
        margin: 2rem 0;
    }
</style>
""", unsafe_allow_html=True)

def create_retrying_session(
    retries=3, 
    backoff_factor=0.3, 
    status_forcelist=(500, 502, 504)
):
    session = requests.Session()
    retry = Retry(
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session

# Your other functions here...

# Add function to check API keys
def check_api_keys():
    required_keys = {
        'OPENAI_API_KEY': os.getenv('OPENAI_API_KEY'),
        'NOTION_API_KEY': os.getenv('NOTION_API_KEY'),
        'SERVICE_TOKEN': os.getenv('SERVICE_TOKEN')
    }
    
    missing_keys = []
    for key, value in required_keys.items():
        if not value:
            missing_keys.append(key)
            logger.error(f"Missing {key}")
        else:
            logger.info(f"{key} is present (ends with: ...{value[-4:]})")
    
    if missing_keys:
        raise Exception(f"Missing required API keys: {', '.join(missing_keys)}")
    return True

def show_error(message):
    st.markdown(f"""
        <div class="output-stream error">
            > ERROR: {message}
        </div>
    """, unsafe_allow_html=True)

def cleanup_temp_files(file_path):
    try:
        if os.path.exists(file_path):
            os.unlink(file_path)
            logger.info(f"Cleaned up temporary file: {file_path}")
    except Exception as e:
        logger.error(f"Cleanup error: {str(e)}")

def check_service_health():
    services = {
        "transcription": TRANSCRIPTION_URL,
        "processing": PROCESSING_URL
    }
    
    for service, url in services.items():
        try:
            response = requests.get(f"{url}/health")
            if response.status_code != 200:
                return False, f"{service} service unavailable"
        except Exception as e:
            return False, f"Cannot connect to {service} service: {str(e)}"
    return True, "All services operational"

def update_status(status, message, progress=None):
    status.update(label=f"> {message}")
    if progress is not None:
        st.progress(progress)

def save_to_notion(transcription, processed_text, file_name):
    logger.info("Saving results to Notion...")
    
    notion = Client(auth=os.getenv('NOTION_API_KEY'))
    database_id = os.getenv('NOTION_DATABASE_ID')
    
    try:
        # Create the page in Notion
        new_page = notion.pages.create(
            parent={"database_id": database_id},
            properties={
                "Title": {
                    "title": [
                        {
                            "text": {
                                "content": f"Transcription: {file_name}"
                            }
                        }
                    ]
                },
                "Transcription": {
                    "rich_text": [
                        {
                            "text": {
                                "content": transcription[:2000] # Notion has a limit
                            }
                        }
                    ]
                },
                "Processed": {
                    "rich_text": [
                        {
                            "text": {
                                "content": processed_text[:2000] if processed_text else ""
                            }
                        }
                    ]
                },
                "Date": {
                    "date": {
                        "start": datetime.now().isoformat()
                    }
                }
            }
        )
        
        logger.info(f"Successfully saved to Notion. Page ID: {new_page.id}")
        return new_page.url
        
    except Exception as e:
        logger.error(f"Failed to save to Notion: {str(e)}")
        raise Exception(f"Notion save failed: {str(e)}")

def make_transcription_request(file_path, file_name, language):
    if not os.path.exists(file_path):
        raise Exception("Audio file not found")
        
    service_token = os.getenv('SERVICE_TOKEN')
    if not service_token:
        raise Exception("Service authentication not configured")
    
    headers = {'X-API-Key': service_token}
    
    try:
        with open(file_path, 'rb') as f:
            files = {'file': (file_name, f)}
            response = requests.post(
                f"{TRANSCRIPTION_URL}/transcribe",
                files=files,
                data={'language': language} if language and language != "AUTO" else {},
                headers=headers,
                timeout=300  # 5 minutes
            )
            
        if response.status_code != 200:
            logger.error(f"Transcription service error: {response.text}")
            raise Exception("Transcription service unavailable")
            
        return response
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed: {str(e)}")
        raise Exception("Failed to connect to transcription service")

def main():
    logger.info("Starting WhisperForge application")
    
    # Title
    st.markdown('<div class="title">WhisperForge//:_</div>', unsafe_allow_html=True)
    
    # Decrypt Audio Section
    st.markdown("""
        <div class="decrypt-section">
            <h2>[DECRYPT_AUDIO]</h2>
            <p>ACCEPTABLE_FORMATS: MP3/WAV/M4A/OGG :: MAX_SIZE: 200MB</p>
        </div>
    """, unsafe_allow_html=True)
    
    # File upload
    uploaded_file = st.file_uploader(
        "Upload Audio File",
        type=['mp3', 'wav', 'm4a', 'ogg'],
        key="main_audio_uploader"
    )
    
    if uploaded_file:
        logger.info(f"Processing file: {uploaded_file.name}")
        
        try:
            # System Config
            st.markdown('<div class="config-header">> SYSTEM_CONFIG</div>', unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            with col1:
                mode = st.selectbox(
                    "EXECUTE_STANDARD",
                    ["TRANSCRIBE", "EXTRACT_INSIGHTS", "FULL_ANALYSIS"],
                    key="execute_mode_select"
                )
            with col2:
                language = st.selectbox(
                    "AUTO_DETECT_LANG",
                    ["AUTO", "EN", "ES", "FR", "DE"],
                    key="language_select"
                )
            
            if st.button("> INITIATE_SEQUENCE", key="initiate_btn"):
                try:
                    # First check API keys
                    if not check_api_keys():
                        raise Exception("API keys not configured. Check .env file.")
                        
                    with st.status("INITIALIZING_SEQUENCE...", expanded=True) as status:
                        # Step 1: Load File
                        update_status(status, "LOADING_AUDIO_FILE...")
                        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(uploaded_file.name).suffix) as tmp_file:
                            tmp_file.write(uploaded_file.getvalue())
                            audio_path = tmp_file.name
                        
                        # Step 2: Transcribe
                        update_status(status, "TRANSCRIBING...")
                        logger.info("Starting transcription...")
                        
                        response = make_transcription_request(audio_path, uploaded_file.name, language)
                        
                        if response.status_code != 200:
                            logger.error(f"Transcription failed with status {response.status_code}: {response.text}")
                            raise Exception(f"Transcription failed: {response.text}")
                            
                        transcription = response.json()['text']
                        logger.info("Transcription complete")
                        
                        # Step 3: Process with selected mode
                        update_status(status, "PROCESSING_TEXT...")
                        logger.info(f"Processing with mode: {mode}")
                        
                        process_data = {
                            'text': transcription,
                            'mode': mode.lower()
                        }
                        
                        headers = {
                            'X-API-Key': os.getenv('SERVICE_TOKEN')
                        }
                        
                        logger.info("Making processing request...")
                        response = requests.post(
                            f"{PROCESSING_URL}/process",
                            json=process_data,
                            headers=headers
                        )
                        
                        if response.status_code != 200:
                            logger.error(f"Processing failed with status {response.status_code}: {response.text}")
                            raise Exception(f"Processing failed: {response.text}")
                            
                        processed_text = response.json()['result']
                        
                        # Step 4: Display results
                        update_status(status, "COMPLETE!", progress=1.0)
                        
                        # Show results
                        st.markdown("### TRANSCRIPTION_OUTPUT")
                        st.text_area("Raw Transcription", transcription, height=200)
                        
                        st.markdown("### PROCESSED_RESULT")
                        st.text_area("Processed Text", processed_text, height=200)
                        
                        # Add download buttons
                        col1, col2 = st.columns(2)
                        with col1:
                            st.download_button(
                                "DOWNLOAD_TRANSCRIPTION",
                                transcription,
                                file_name="transcription.txt",
                                key="download_trans"
                            )
                        with col2:
                            st.download_button(
                                "DOWNLOAD_PROCESSED",
                                processed_text,
                                file_name="processed_output.txt",
                                key="download_proc"
                            )
                        
                        # Save to Notion
                        notion_url = save_to_notion(
                            transcription,
                            processed_text,
                            uploaded_file.name
                        )
                        
                        # Show success message with Notion link
                        st.markdown(f"""
                            <div class="success-message">
                                > EXPORT_COMPLETE
                                > [VIEW_IN_NOTION]({notion_url})
                            </div>
                        """, unsafe_allow_html=True)
                        
                except Exception as e:
                    logger.error(f"Processing error: {str(e)}", exc_info=True)
                    st.error(f"ERROR: {str(e)}")
                finally:
                    # Cleanup
                    if 'audio_path' in locals():
                        try:
                            os.unlink(audio_path)
                        except Exception as e:
                            logger.error(f"Cleanup error: {str(e)}")
            
            # Output Stream
            st.markdown('<div class="config-header">> OUTPUT_STREAM</div>', unsafe_allow_html=True)
            st.markdown("""
                <div class="output-stream">
                    > AWAITING_INPUT...
                </div>
            """, unsafe_allow_html=True)
            
        except Exception as e:
            logger.error(f"Processing error: {str(e)}", exc_info=True)
            st.error(f"Error processing file: {str(e)}")

if __name__ == "__main__":
    main()
