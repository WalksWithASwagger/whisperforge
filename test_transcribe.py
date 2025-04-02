#!/usr/bin/env python3
"""
Test script to verify OpenAI transcription works with the API key from the environment
"""

import requests
import sys
import os
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get API key from environment variable
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

def test_api_key():
    """Test the OpenAI API key with a direct API call"""
    print("Testing OpenAI API key...")
    
    if not OPENAI_API_KEY:
        print("ERROR: OPENAI_API_KEY environment variable is not set.")
        return False
    
    # Make a simple API call to check if the key is valid
    url = "https://api.openai.com/v1/models"
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}"
    }
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            print(f"API key is valid! Status code: {response.status_code}")
            models = response.json()
            print(f"Available models: {len(models['data'])}")
            # Print a few model IDs
            for model in models['data'][:3]:
                print(f"- {model['id']}")
            return True
        else:
            print(f"API key is invalid! Status code: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"Error testing API key: {str(e)}")
        return False

def create_test_audio():
    """Create a simple test audio file"""
    # Use ffmpeg to create a 3-second silent audio file
    print("Creating test audio file...")
    os.system("apt-get update && apt-get install -y ffmpeg")
    os.system("ffmpeg -f lavfi -i anullsrc=r=44100:cl=mono -t 3 -q:a 9 -acodec libmp3lame /app/test.mp3")
    return "/app/test.mp3"

def test_transcription(audio_file):
    """Test the transcription endpoint with the test audio file"""
    print(f"Testing transcription with {audio_file}...")
    
    url = "https://api.openai.com/v1/audio/transcriptions"
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}"
    }
    
    try:
        with open(audio_file, "rb") as f:
            files = {
                "file": (os.path.basename(audio_file), f, "audio/mpeg"),
                "model": (None, "whisper-1")
            }
            
            response = requests.post(url, headers=headers, files=files)
            print(f"API response status: {response.status_code}")
            print(f"API response: {response.text}")
            
            if response.status_code == 200:
                print("Transcription successful!")
                return True
            else:
                print("Transcription failed.")
                return False
    except Exception as e:
        print(f"Error during transcription: {str(e)}")
        return False

if __name__ == "__main__":
    if test_api_key():
        print("API key is valid! Now testing transcription...")
        
        # Create a test audio file
        test_file = create_test_audio()
        
        # Test transcription
        test_transcription(test_file)
    else:
        print("API key validation failed. Cannot proceed with transcription test.") 