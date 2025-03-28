#!/usr/bin/env python3
"""
A simple wrapper for the OpenAI API using requests instead of the OpenAI Python client
"""

import requests
import os
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class OpenAIWrapper:
    """A simple wrapper for the OpenAI API"""
    
    def __init__(self, api_key=None):
        """Initialize with API key"""
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("API key is required. Either pass it directly or set OPENAI_API_KEY environment variable.")
        
        self.base_url = "https://api.openai.com/v1"
        
    def chat_completion(self, messages, model="gpt-3.5-turbo", max_tokens=1500):
        """Create a chat completion using the OpenAI API"""
        url = f"{self.base_url}/chat/completions"
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
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
            return result
        except requests.exceptions.RequestException as e:
            print(f"Error making request to OpenAI API: {str(e)}")
            if hasattr(e, 'response') and e.response:
                print(f"Response status code: {e.response.status_code}")
                print(f"Response body: {e.response.text}")
            raise

def test_openai_wrapper():
    """Test the OpenAI wrapper"""
    try:
        # Create a wrapper instance
        wrapper = OpenAIWrapper()
        
        # Test with a simple completion
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello, can you hear me?"}
        ]
        
        response = wrapper.chat_completion(messages)
        
        # Extract and print the response
        content = response["choices"][0]["message"]["content"]
        print(f"Success! OpenAI API response: {content}")
        
        return True
    except Exception as e:
        print(f"Error testing OpenAI API: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # Test the wrapper
    success = test_openai_wrapper()
    
    if success:
        print("\nOpenAI API test completed successfully!")
    else:
        print("\nOpenAI API test failed. See error messages above.") 