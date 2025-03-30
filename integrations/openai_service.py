import os
import requests
import json
import logging
import streamlit as st
from openai import OpenAI
import time

# Import from config
from config import OPENAI_API_KEY, logger
# Import from utils
from utils.helpers import get_api_key_for_service, load_api_key_from_file

# Hard-coded API key for fallback scenarios (set to None initially)
HARD_CODED_OPENAI_API_KEY = None

def get_openai_client():
    """
    Get an OpenAI client with proper API key.
    
    Returns:
        OpenAI: Initialized OpenAI client, or None on failure
    """
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

def direct_transcribe_audio(audio_file_path, api_key=None):
    """
    Transcribe audio directly using the OpenAI API without relying on the client.
    
    Args:
        audio_file_path (str): Path to the audio file
        api_key (str): OpenAI API key, or None to use default
        
    Returns:
        str: Transcription text
    """
    logger.info(f"Direct transcribing audio with file path: {audio_file_path}")
    
    # Get API key if not provided
    if not api_key:
        api_key = get_api_key_for_service("openai")
    
    # Check if file exists
    if not os.path.exists(audio_file_path):
        error_msg = f"Audio file does not exist: {audio_file_path}"
        logger.error(error_msg)
        return f"Error: {error_msg}"
    
    try:
        with open(audio_file_path, "rb") as audio_file:
            url = "https://api.openai.com/v1/audio/transcriptions"
            headers = {
                "Authorization": f"Bearer {api_key}"
            }
            files = {
                "file": (os.path.basename(audio_file_path), audio_file, "audio/mpeg"),
                "model": (None, "whisper-1")
            }
            
            logger.info("Sending audio file to OpenAI API for transcription")
            response = requests.post(url, headers=headers, files=files)
            
            if response.status_code == 200:
                result = response.json()
                logger.info("Successfully transcribed audio file")
                return result.get("text", "")
            else:
                error_msg = f"Error transcribing audio: {response.status_code} {response.text}"
                logger.error(error_msg)
                return f"Error: {error_msg}"
    except Exception as e:
        error_msg = f"Exception during direct transcription: {str(e)}"
        logger.error(error_msg)
        return f"Error: {error_msg}"

def get_available_openai_models():
    """
    Get current list of available OpenAI models.
    
    Returns:
        list: List of model IDs
    """
    client = get_openai_client()
    if not client:
        return []
    
    try:
        models = client.models.list()
        # Extract model IDs
        model_ids = [model.id for model in models.data]
        return model_ids
    except Exception as e:
        logger.error(f"Error fetching OpenAI models: {str(e)}")
        return []

def generate_completion(prompt, model="gpt-4", temperature=0.7, max_tokens=1000):
    """
    Generate a completion using OpenAI models.
    
    Args:
        prompt (str): The prompt to complete
        model (str): The model to use
        temperature (float): Temperature setting (0.0 to 1.0)
        max_tokens (int): Maximum tokens to generate
        
    Returns:
        str: Generated text
    """
    client = get_openai_client()
    if not client:
        return "Error: Could not initialize OpenAI client"
    
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=max_tokens
        )
        return response.choices[0].message.content
    except Exception as e:
        error_msg = f"Error generating completion: {str(e)}"
        logger.error(error_msg)
        return f"Error: {error_msg}" 