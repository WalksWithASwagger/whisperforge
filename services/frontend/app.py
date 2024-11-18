"""
WhisperForge - AI-powered audio transcription and analysis tool.

This module contains the main Streamlit application code for WhisperForge,
integrating OpenAI's Whisper model with Notion for documentation.
"""

import streamlit as st
import requests
import logging
import time
import os
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Enhanced logging
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def create_retrying_session(
    retries=3, backoff_factor=0.3, status_forcelist=(500, 502, 504)
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


def check_services():
    """Check if all required services are available"""
    services = {
        "transcription": "http://transcription:8000/health",
        "processing": "http://processing:8000/health",
    }

    status = {}
    for service, url in services.items():
        try:
            response = requests.get(url, timeout=5)
            status[service] = response.ok
            logger.info(f"Service {service} status: {response.ok}")
        except Exception as e:
            status[service] = False
            logger.error(f"Service {service} error: {str(e)}")
    return status


def get_api_key():
    """Get API key from environment variable"""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        st.error("OpenAI API key not found in environment variables")
        logger.error("OpenAI API key missing")
    return api_key


def main():
    st.title("WhisperForge")
    st.subheader("🎙️ Audio Transcription & Analysis")

    # Create a session with retry logic
    session = create_retrying_session()

    # Initialize session state
    if "widget_keys" not in st.session_state:
        st.session_state.widget_keys = {
            "uploader": f"uploader_{time.time_ns()}",
            "mode": f"mode_{time.time_ns()}",
            "language": f"lang_{time.time_ns()}",
            "process": f"process_{time.time_ns()}",
        }

    # File uploader
    uploaded_file = st.file_uploader(
        "Upload Audio File",
        type=["mp3", "wav", "m4a", "ogg"],
        key=st.session_state.widget_keys["uploader"],
    )

    # Processing options
    col1, col2 = st.columns(2)
    with col1:
        mode = st.selectbox(
            "Processing Mode",
            ["summarize", "extract insights", "custom"],
            key=st.session_state.widget_keys["mode"],
        )
    with col2:
        language = st.selectbox(
            "Output Language",
            ["english", "spanish", "french"],
            key=st.session_state.widget_keys["language"],
        )

    # Process button
    if st.button(
        "Process Audio",
        key=st.session_state.widget_keys["process"],
        disabled=not uploaded_file,
    ):
        if uploaded_file:
            try:
                # Get API key once
                api_key = get_api_key()
                if not api_key:
                    return

                # Different headers for file upload vs JSON
                file_headers = {"X-API-Key": api_key}

                json_headers = {
                    "X-API-Key": api_key,
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                }

                # Show progress
                progress_bar = st.progress(0)
                status_text = st.empty()

                # Step 1: Transcription
                status_text.text("Transcribing audio...")
                progress_bar.progress(25)

                logger.debug("Sending request to transcription service")
                response = session.post(
                    "http://transcription:8000/transcribe",
                    files={"file": uploaded_file},
                    headers=file_headers,
                    timeout=30,
                )
                logger.debug(f"Transcription response status: {response.status_code}")

                if not response.ok:
                    st.error(f"Transcription failed: {response.text}")
                    logger.error(f"Transcription error: {response.text}")
                    return

                transcription = response.json()["text"]
                progress_bar.progress(50)

                # Step 2: Processing
                status_text.text("Processing transcription...")
                logger.debug("Sending request to processing service")
                response = session.post(
                    "http://processing:8000/process",
                    json={
                        "text": transcription,
                        "mode": mode.lower(),
                        "language": language,
                        "custom_prompt": "",
                    },
                    headers=json_headers,
                )

                logger.debug(f"Processing response status: {response.status_code}")
                result = response.json()
                processed_text = result["result"]
                progress_bar.progress(100)
                status_text.text("Done!")

                # Show results
                with st.expander("Original Transcription", expanded=False):
                    st.text(transcription)

                st.subheader("Processed Result")
                st.write(processed_text)

                # Download buttons
                col1, col2 = st.columns(2)
                with col1:
                    st.download_button(
                        "Download Transcription",
                        transcription.encode(),
                        f"transcription_{uploaded_file.name}.txt",
                        "text/plain",
                    )
                with col2:
                    st.download_button(
                        "Download Processed Result",
                        processed_text.encode(),
                        f"processed_{uploaded_file.name}.txt",
                        "text/plain",
                    )

            except Exception as e:
                logger.exception("Error during processing")
                st.error(f"Processing error: {str(e)}")
                st.error(f"Processing error: {str(e)}")
                st.error(f"Processing error: {str(e)}")


if __name__ == "__main__":
    main()
