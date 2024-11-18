"""
WhisperForge - AI-powered audio transcription and analysis tool.

This module contains the main Streamlit application code for WhisperForge,
integrating OpenAI's Whisper model with Notion for documentation.
"""

import streamlit as st
import requests
import logging
import os
from pathlib import Path
import json
from typing import Optional
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Service URLs from environment/config
TRANSCRIPTION_URL = "http://transcription:8000"  # Use container name
PROCESSING_URL = "http://processing:8000"
STORAGE_URL = "http://storage:8000"
SERVICE_TOKEN = os.getenv("SERVICE_TOKEN")

class ServiceClient:
    def __init__(self):
        self.headers = {
            "X-API-Key": SERVICE_TOKEN
        }
    
    def check_services_health(self) -> dict:
        """Check health of all services"""
        health = {}
        services = {
            "transcription": f"{TRANSCRIPTION_URL}/health",
            "processing": f"{PROCESSING_URL}/health",
            "storage": f"{STORAGE_URL}/health"
        }
        
        for service, url in services.items():
            try:
                response = requests.get(url, timeout=2)  # Add timeout
                health[service] = "✅" if response.status_code == 200 else "❌"
            except requests.exceptions.RequestException as e:
                logger.error(f"Health check failed for {service}: {str(e)}")
                health[service] = "❌"
        
        return health
    
    def transcribe_audio(self, audio_file) -> Optional[str]:
        """Send audio file to transcription service"""
        try:
            files = {"file": audio_file}
            response = requests.post(
                f"{TRANSCRIPTION_URL}/transcribe",
                headers=self.headers,
                files=files
            )
            response.raise_for_status()
            return response.json()["text"]
        except Exception as e:
            logger.error(f"Transcription error: {str(e)}")
            st.error(f"Transcription failed: {str(e)}")
            return None
    
    def process_text(self, text: str, mode: str, custom_prompt: str = "", language: str = None) -> Optional[str]:
        """Send text to processing service"""
        try:
            data = {
                "text": text,
                "mode": mode.lower(),
                "custom_prompt": custom_prompt,
                "language": language
            }
            response = requests.post(
                f"{PROCESSING_URL}/process",
                headers=self.headers,
                json=data
            )
            response.raise_for_status()
            return response.json()["processed_text"]
        except Exception as e:
            logger.error(f"Processing error: {str(e)}")
            st.error(f"Processing failed: {str(e)}")
            return None
    
    def store_results(self, transcription: str, processed_text: str, filename: str) -> Optional[str]:
        """Send results to storage service"""
        try:
            data = {
                "transcription": transcription,
                "processed_text": processed_text,
                "file_name": filename,
                "timestamp": datetime.now().isoformat(),
                "metadata": {
                    "processing_mode": st.session_state.get("processing_mode", "default"),
                    "language": st.session_state.get("language", "en"),
                    "file_size": st.session_state.get("file_size", "unknown"),
                    "duration": st.session_state.get("duration", "unknown")
                }
            }
            
            response = requests.post(
                f"{STORAGE_URL}/store",
                headers=self.headers,
                json=data
            )
            response.raise_for_status()
            return response.json().get("url")  # Now returns the actual Notion URL
        except Exception as e:
            logger.error(f"Storage error: {str(e)}")
            st.error(f"Storage failed: {str(e)}")
            return None

def render_header():
    """Render the app header"""
    st.title("WhisperForge")
    st.markdown("🎙️ Audio Transcription & Analysis")

def render_sidebar(client: ServiceClient):
    """Render the sidebar with service status"""
    with st.sidebar:
        st.header("Service Status")
        health = client.check_services_health()
        for service, status in health.items():
            st.text(f"{service.title()}: {status}")

def call_service(service_url: str, method: str = "GET", data: dict = None, files: dict = None) -> dict:
    """Make authenticated call to service"""
    headers = {"Authorization": f"Bearer {os.getenv('SERVICE_TOKEN')}"}
    
    try:
        if method == "GET":
            response = requests.get(service_url, headers=headers)
        elif method == "POST":
            if files:
                response = requests.post(service_url, headers=headers, files=files)
            else:
                response = requests.post(service_url, headers=headers, json=data)
        
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Service call failed: {str(e)}")
        raise

def main():
    # Initialize session state
    if 'client' not in st.session_state:
        st.session_state.client = ServiceClient()
    
    if 'processing_complete' not in st.session_state:
        st.session_state.processing_complete = False
    
    # Render UI components
    render_header()
    render_sidebar(st.session_state.client)
    
    # File upload
    uploaded_file = st.file_uploader(
        "Upload Audio File",
        type=['mp3', 'wav', 'm4a', 'ogg'],
        help="Upload an audio file for transcription"
    )
    
    # Processing options
    col1, col2 = st.columns(2)
    with col1:
        processing_mode = st.selectbox(
            "Processing Mode",
            ["Summarize", "Extract Insights", "Custom"]
        )
    
    with col2:
        language = st.selectbox(
            "Output Language",
            ["English", "Spanish", "French", "German", None],
            index=0
        )
    
    if processing_mode == "Custom":
        custom_prompt = st.text_area(
            "Custom Instructions",
            help="Enter custom processing instructions"
        )
    else:
        custom_prompt = ""
    
    # Process button
    if uploaded_file and st.button("Process Audio", type="primary"):
        with st.status("Processing...", expanded=True) as status:
            try:
                # Step 1: Transcription
                status.update(label="Transcribing audio...")
                transcription = st.session_state.client.transcribe_audio(uploaded_file)
                
                if transcription:
                    # Step 2: Processing
                    status.update(label="Processing text...")
                    processed_text = st.session_state.client.process_text(
                        transcription,
                        processing_mode,
                        custom_prompt,
                        language
                    )
                    
                    if processed_text:
                        # Step 3: Storage
                        status.update(label="Storing results...")
                        notion_url = st.session_state.client.store_results(
                            transcription,
                            processed_text,
                            uploaded_file.name
                        )
                        
                        # Update session state
                        st.session_state.transcription = transcription
                        st.session_state.processed_text = processed_text
                        st.session_state.notion_url = notion_url
                        st.session_state.processing_complete = True
                        
                        status.update(label="Complete!", state="complete")
                
            except Exception as e:
                st.error(f"Processing failed: {str(e)}")
                logger.error(f"Processing error: {str(e)}")
    
    # Display results
    if st.session_state.processing_complete:
        st.header("Results")
        
        with st.expander("Original Transcription", expanded=False):
            col1, col2 = st.columns([6, 1])
            with col1:
                st.text_area(
                    "Transcribed Text",
                    st.session_state.transcription,
                    height=200
                )
            with col2:
                st.download_button(
                    "⬇️ Download",
                    st.session_state.transcription,
                    file_name="transcription.txt",
                    mime="text/plain"
                )
        
        st.subheader("Processed Result")
        col1, col2 = st.columns([6, 1])
        with col1:
            st.text_area(
                "Processed Text",
                st.session_state.processed_text,
                height=300
            )
        with col2:
            st.download_button(
                "⬇️ Download",
                st.session_state.processed_text,
                file_name="processed_result.txt",
                mime="text/plain"
            )
        
        if st.session_state.notion_url:
            st.success(f"✅ Results saved to Notion: [View Document]({st.session_state.notion_url})")

if __name__ == "__main__":
    main()


