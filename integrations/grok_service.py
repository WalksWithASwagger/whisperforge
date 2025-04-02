"""
This module provides integration with the Grok AI API.
"""

import os
import logging
import streamlit as st
import requests
import json

# Import from config
from config import GROK_API_KEY, logger
# Import from utils
from utils.helpers import get_api_key_for_service

def get_grok_api_key():
    """
    Get Grok API key with appropriate fallbacks.
    
    Returns:
        str: Grok API key, or None if not available
    """
    logger.debug("Getting Grok API key")
    
    # Get API key from user profile or environment
    api_key = get_api_key_for_service("grok")
    
    # Check if API key is valid
    if not api_key or len(api_key) < 10 or any(placeholder in api_key.lower() for placeholder in ["your_", "placeholder", "api_key"]):
        api_key = GROK_API_KEY
        logger.debug("Using API key from environment")
    
    # Final check
    if not api_key or len(api_key) < 10 or any(placeholder in api_key.lower() for placeholder in ["your_", "placeholder", "api_key"]):
        logger.error("Grok API key is not set or appears to be a placeholder")
        return None
    
    logger.debug(f"Got Grok API key (length: {len(api_key)})")
    return api_key

def generate_grok_completion(prompt, model="grok-1", max_tokens=1500, temperature=0.7):
    """
    Generate a completion using Grok AI.
    
    Args:
        prompt (str): The prompt to complete
        model (str): The model to use
        max_tokens (int): Maximum tokens to generate
        temperature (float): Temperature setting (0.0 to 1.0)
        
    Returns:
        str: Generated text
    """
    grok_api_key = get_grok_api_key()
    if not grok_api_key:
        return "Error: Grok API key is not configured"
    
    try:
        # Grok API endpoint
        url = "https://api.grok.x.ai/v1/chat/completions"
        
        # Headers
        headers = {
            "Authorization": f"Bearer {grok_api_key}",
            "Content-Type": "application/json"
        }
        
        # Payload
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": "You are a helpful AI assistant that generates high-quality content."},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": max_tokens,
            "temperature": temperature
        }
        
        # Make request
        response = requests.post(url, headers=headers, json=payload)
        
        # Check if request was successful
        if response.status_code == 200:
            result = response.json()
            return result["choices"][0]["message"]["content"]
        else:
            error_msg = f"Error from Grok API: {response.status_code} - {response.text}"
            logger.error(error_msg)
            return f"Error: {error_msg}"
    except Exception as e:
        error_msg = f"Error generating completion with Grok: {str(e)}"
        logger.error(error_msg)
        return f"Error: {error_msg}" 