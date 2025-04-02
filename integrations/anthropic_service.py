"""
This module provides integration with the Anthropic API for Claude models.
"""

import os
import logging
import streamlit as st
from anthropic import Anthropic

# Import from config
from config import ANTHROPIC_API_KEY, logger
# Import from utils
from utils.helpers import get_api_key_for_service

def get_anthropic_client():
    """
    Get an Anthropic client with proper API key.
    
    Returns:
        Anthropic: Initialized Anthropic client, or None on failure
    """
    logger.debug("Getting Anthropic client")
    
    # Get API key from user profile or environment
    api_key = get_api_key_for_service("anthropic")
    
    # Check if API key is valid
    if not api_key or len(api_key) < 10 or any(placeholder in api_key.lower() for placeholder in ["your_", "placeholder", "api_key"]):
        api_key = ANTHROPIC_API_KEY
        logger.debug("Using API key from environment")
    
    # Final check
    if not api_key or len(api_key) < 10 or any(placeholder in api_key.lower() for placeholder in ["your_", "placeholder", "api_key"]):
        logger.error("Anthropic API key is not set or appears to be a placeholder")
        st.error("Anthropic API key is not properly set. Please add your API key in the settings.")
        return None
    
    logger.debug(f"Got Anthropic API key (length: {len(api_key)})")
    
    try:
        client = Anthropic(api_key=api_key)
        return client
    except Exception as e:
        logger.error(f"Failed to initialize Anthropic client: {str(e)}")
        st.error(f"Error initializing Anthropic client: {str(e)}")
        return None

def generate_anthropic_completion(prompt, model="claude-3-5-sonnet-20240307", max_tokens=1500, temperature=0.7):
    """
    Generate a completion using Anthropic's Claude models.
    
    Args:
        prompt (str): The prompt to complete
        model (str): The model to use
        max_tokens (int): Maximum tokens to generate
        temperature (float): Temperature setting (0.0 to 1.0)
        
    Returns:
        str: Generated text
    """
    client = get_anthropic_client()
    if not client:
        return "Error: Could not initialize Anthropic client"
    
    try:
        response = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            system="You are a helpful AI assistant that generates high-quality content.",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text
    except Exception as e:
        error_msg = f"Error generating completion with Anthropic: {str(e)}"
        logger.error(error_msg)
        return f"Error: {error_msg}"

def stream_anthropic_completion(prompt, model="claude-3-5-sonnet-20240307", max_tokens=1500, temperature=0.7):
    """
    Stream a completion from Anthropic's Claude models.
    
    Args:
        prompt (str): The prompt to complete
        model (str): The model to use
        max_tokens (int): Maximum tokens to generate
        temperature (float): Temperature setting (0.0 to 1.0)
        
    Returns:
        generator: Generator yielding pieces of text as they are generated
    """
    client = get_anthropic_client()
    if not client:
        yield "Error: Could not initialize Anthropic client"
        return
    
    try:
        with client.messages.stream(
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            system="You are a helpful AI assistant that generates high-quality content.",
            messages=[{"role": "user", "content": prompt}]
        ) as stream:
            for text in stream.text_stream:
                yield text
    except Exception as e:
        error_msg = f"Error streaming completion from Anthropic: {str(e)}"
        logger.error(error_msg)
        yield f"Error: {error_msg}" 