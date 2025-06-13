"""
Content Generation Module for WhisperForge
Handles AI-powered content creation including transcription, wisdom extraction, and content generation
"""

import logging
import os
from typing import Dict, Optional

from .utils import get_openai_client, get_prompt, DEFAULT_PROMPTS, get_enhanced_prompt

# Configure logging
logger = logging.getLogger(__name__)

def generate_wisdom(transcript: str, custom_prompt: str = None, knowledge_base: Dict[str, str] = None) -> str:
    """Extract key insights and wisdom from a transcript"""
    try:
        # Use enhanced prompt system with automatic KB concatenation
        system_prompt = custom_prompt or get_enhanced_prompt("wisdom_extraction", knowledge_base)
        
        openai_client = get_openai_client()
        if not openai_client:
            return "Error: OpenAI API key is not configured."
            
        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Here's the transcription to analyze:\n\n{transcript}"}
            ],
            max_tokens=1500
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        logger.exception("Error in wisdom generation:")
        return f"Error generating wisdom: {str(e)}"

def generate_outline(transcript: str, wisdom: str, custom_prompt: str = None, knowledge_base: Dict[str, str] = None) -> str:
    """Create a structured outline based on transcript and wisdom"""
    try:
        # Use enhanced prompt system with automatic KB concatenation
        system_prompt = custom_prompt or get_enhanced_prompt("outline_creation", knowledge_base)
        
        content = f"TRANSCRIPT:\n{transcript}\n\nWISDOM:\n{wisdom}"
        
        openai_client = get_openai_client()
        if not openai_client:
            return "Error: OpenAI API key is not configured."
            
        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": content}
            ],
            max_tokens=1500
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        logger.exception("Error in outline generation:")
        return f"Error generating outline: {str(e)}"

def generate_article(transcript: str, wisdom: str, outline: str, custom_prompt: str = None, knowledge_base: Dict[str, str] = None) -> str:
    """Generate a comprehensive article based on transcript, wisdom, and outline"""
    try:
        # Use enhanced prompt system with automatic KB concatenation
        system_prompt = custom_prompt or get_enhanced_prompt("article_writing", knowledge_base)
        
        # Limit transcript length to avoid token limits
        transcript_excerpt = transcript[:2000] if len(transcript) > 2000 else transcript
        content = f"TRANSCRIPT:\n{transcript_excerpt}\n\nWISDOM:\n{wisdom}\n\nOUTLINE:\n{outline}"
        
        openai_client = get_openai_client()
        if not openai_client:
            return "Error: OpenAI API key is not configured."
            
        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": content}
            ],
            max_tokens=2000
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        logger.exception("Error in article generation:")
        return f"Error generating article: {str(e)}"

def generate_social_content(wisdom: str, outline: str, article: str, custom_prompt: str = None, knowledge_base: Dict[str, str] = None) -> str:
    """Generate 5 distinct social media posts"""
    try:
        # Use enhanced prompt system with automatic KB concatenation
        system_prompt = custom_prompt or get_enhanced_prompt("social_media", knowledge_base)
        
        # Include article in content for richer context
        article_excerpt = article[:1500] if len(article) > 1500 else article
        content = f"WISDOM:\n{wisdom}\n\nOUTLINE:\n{outline}\n\nARTICLE:\n{article_excerpt}"
        
        openai_client = get_openai_client()
        if not openai_client:
            return "Error: OpenAI API key is not configured."
            
        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": content}
            ],
            max_tokens=1500
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        logger.exception("Error in social content generation:")
        return f"Error generating social content: {str(e)}"

def transcribe_audio(audio_file) -> str:
    """Transcribe audio using OpenAI Whisper"""
    try:
        openai_client = get_openai_client()
        if not openai_client:
            return "Error: OpenAI API key is not configured."
        
        # Reset file pointer to beginning
        audio_file.seek(0)
        
        response = openai_client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file
        )
        
        return response.text
        
    except Exception as e:
        logger.exception("Error in audio transcription:")
        return f"Error transcribing audio: {str(e)}" 