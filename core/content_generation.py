"""
Content Generation Module for WhisperForge
Handles AI-powered content creation including transcription, wisdom extraction, and content generation
"""

import logging
import os
import requests
import time
from typing import Dict, Optional, Any

from .utils import get_openai_client, get_anthropic_client, get_grok_api_key, get_prompt, DEFAULT_PROMPTS, get_enhanced_prompt

# Configure logging
logger = logging.getLogger(__name__)

def generate_wisdom(transcript: str, ai_provider: str, model: str, custom_prompt: str = None, knowledge_base: Dict[str, str] = None) -> str:
    """Extract key insights and wisdom from a transcript"""
    try:
        # Use enhanced prompt system with automatic KB concatenation
        system_prompt = custom_prompt or get_enhanced_prompt("wisdom_extraction", knowledge_base)
        
        # Use the selected AI provider and model
        if ai_provider == "OpenAI":
            openai_client = get_openai_client()
            if not openai_client:
                return "Error: OpenAI API key is not configured."
                
            response = openai_client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Here's the transcription to analyze:\n\n{transcript}"}
                ],
                max_tokens=1500
            )
            
            return response.choices[0].message.content
            
        elif ai_provider == "Anthropic":
            anthropic_client = get_anthropic_client()
            if not anthropic_client:
                return "Error: Anthropic API key is not configured."
                
            response = anthropic_client.messages.create(
                model=model,
                max_tokens=1500,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": f"Here's the transcription to analyze:\n\n{transcript}"}
                ]
            )
            
            return response.content[0].text
            
        elif ai_provider == "Grok":
            grok_api_key = get_grok_api_key()
            if not grok_api_key:
                return "Error: Grok API key is not configured."

            headers = {
                "Authorization": f"Bearer {grok_api_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Here's the transcription to analyze:\n\n{transcript}"}
                ]
            }
            
            response = requests.post(
                "https://api.grok.x.ai/v1/chat/completions",
                headers=headers,
                json=payload
            )
            return response.json()["choices"][0]["message"]["content"]
        
        return "Error: Unsupported AI provider"
        
    except Exception as e:
        logger.exception("Error in wisdom generation:")
        return f"Error generating wisdom: {str(e)}"

def generate_outline(transcript: str, wisdom: str, ai_provider: str, model: str, custom_prompt: str = None, knowledge_base: Dict[str, str] = None) -> str:
    """Create a structured outline based on transcript and wisdom"""
    try:
        # Use enhanced prompt system with automatic KB concatenation
        system_prompt = custom_prompt or get_enhanced_prompt("outline_creation", knowledge_base)
        
        content = f"TRANSCRIPT:\n{transcript}\n\nWISDOM:\n{wisdom}"
        
        if ai_provider == "OpenAI":
            openai_client = get_openai_client()
            if not openai_client:
                return "Error: OpenAI API key is not configured."
                
            response = openai_client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": content}
                ],
                max_tokens=1500
            )
            
            return response.choices[0].message.content
            
        elif ai_provider == "Anthropic":
            anthropic_client = get_anthropic_client()
            if not anthropic_client:
                return "Error: Anthropic API key is not configured."
                
            response = anthropic_client.messages.create(
                model=model,
                max_tokens=1500,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": content}
                ]
            )
            
            return response.content[0].text
            
        elif ai_provider == "Grok":
            grok_api_key = get_grok_api_key()
            if not grok_api_key:
                return "Error: Grok API key is not configured."

            headers = {
                "Authorization": f"Bearer {grok_api_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": content}
                ]
            }
            
            response = requests.post(
                "https://api.grok.x.ai/v1/chat/completions",
                headers=headers,
                json=payload
            )
            return response.json()["choices"][0]["message"]["content"]
        
        return "Error: Unsupported AI provider"
        
    except Exception as e:
        logger.exception("Error in outline generation:")
        return f"Error generating outline: {str(e)}"

def generate_article(transcript: str, wisdom: str, outline: str, ai_provider: str, model: str, custom_prompt: str = None, knowledge_base: Dict[str, str] = None) -> str:
    """Generate a comprehensive article based on transcript, wisdom, and outline"""
    try:
        # Use enhanced prompt system with automatic KB concatenation
        system_prompt = custom_prompt or get_enhanced_prompt("article_writing", knowledge_base)
        
        # Limit transcript length to avoid token limits
        transcript_excerpt = transcript[:2000] if len(transcript) > 2000 else transcript
        content = f"TRANSCRIPT:\n{transcript_excerpt}\n\nWISDOM:\n{wisdom}\n\nOUTLINE:\n{outline}"
        
        if ai_provider == "OpenAI":
            openai_client = get_openai_client()
            if not openai_client:
                return "Error: OpenAI API key is not configured."
                
            response = openai_client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": content}
                ],
                max_tokens=2000
            )
            
            return response.choices[0].message.content
            
        elif ai_provider == "Anthropic":
            anthropic_client = get_anthropic_client()
            if not anthropic_client:
                return "Error: Anthropic API key is not configured."
                
            response = anthropic_client.messages.create(
                model=model,
                max_tokens=2000,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": content}
                ]
            )
            
            return response.content[0].text
            
        elif ai_provider == "Grok":
            grok_api_key = get_grok_api_key()
            if not grok_api_key:
                return "Error: Grok API key is not configured."

            headers = {
                "Authorization": f"Bearer {grok_api_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": content}
                ]
            }
            
            response = requests.post(
                "https://api.grok.x.ai/v1/chat/completions",
                headers=headers,
                json=payload
            )
            return response.json()["choices"][0]["message"]["content"]
        
        return "Error: Unsupported AI provider"
        
    except Exception as e:
        logger.exception("Error in article generation:")
        return f"Error generating article: {str(e)}"

def generate_social_content(wisdom: str, outline: str, article: str, ai_provider: str, model: str, custom_prompt: str = None, knowledge_base: Dict[str, str] = None) -> str:
    """Generate 5 distinct social media posts"""
    try:
        # Use enhanced prompt system with automatic KB concatenation
        system_prompt = custom_prompt or get_enhanced_prompt("social_media", knowledge_base)
        
        # Include article in content for richer context
        article_excerpt = article[:1500] if len(article) > 1500 else article
        content = f"WISDOM:\n{wisdom}\n\nOUTLINE:\n{outline}\n\nARTICLE:\n{article_excerpt}"
        
        if ai_provider == "OpenAI":
            openai_client = get_openai_client()
            if not openai_client:
                return "Error: OpenAI API key is not configured."
                
            response = openai_client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": content}
                ],
                max_tokens=1500
            )
            
            return response.choices[0].message.content
            
        elif ai_provider == "Anthropic":
            anthropic_client = get_anthropic_client()
            if not anthropic_client:
                return "Error: Anthropic API key is not configured."
                
            response = anthropic_client.messages.create(
                model=model,
                max_tokens=1500,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": content}
                ]
            )
            
            return response.content[0].text
            
        elif ai_provider == "Grok":
            grok_api_key = get_grok_api_key()
            if not grok_api_key:
                return "Error: Grok API key is not configured."

            headers = {
                "Authorization": f"Bearer {grok_api_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": content}
                ]
            }
            
            response = requests.post(
                "https://api.grok.x.ai/v1/chat/completions",
                headers=headers,
                json=payload
            )
            return response.json()["choices"][0]["message"]["content"]
        
        return "Error: Unsupported AI provider"
        
    except Exception as e:
        logger.exception("Error in social content generation:")
        return f"Error generating social content: {str(e)}"

def generate_image_prompts(wisdom: str, outline: str, ai_provider: str, model: str, custom_prompt: str = None, knowledge_base: Dict[str, str] = None) -> str:
    """Generate image generation prompts"""
    try:
        # Use enhanced prompt system with automatic KB concatenation
        system_prompt = custom_prompt or get_enhanced_prompt("image_prompts", knowledge_base)
        
        content = f"WISDOM:\n{wisdom}\n\nOUTLINE:\n{outline}"
        
        if ai_provider == "OpenAI":
            openai_client = get_openai_client()
            if not openai_client:
                return "Error: OpenAI API key is not configured."
                
            response = openai_client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": content}
                ],
                max_tokens=1500
            )
            
            return response.choices[0].message.content
            
        elif ai_provider == "Anthropic":
            anthropic_client = get_anthropic_client()
            if not anthropic_client:
                return "Error: Anthropic API key is not configured."
                
            response = anthropic_client.messages.create(
                model=model,
                max_tokens=1500,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": content}
                ]
            )
            
            return response.content[0].text
            
        elif ai_provider == "Grok":
            grok_api_key = get_grok_api_key()
            if not grok_api_key:
                return "Error: Grok API key is not configured."

            headers = {
                "Authorization": f"Bearer {grok_api_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": content}
                ]
            }
            
            response = requests.post(
                "https://api.grok.x.ai/v1/chat/completions",
                headers=headers,
                json=payload
            )
            return response.json()["choices"][0]["message"]["content"]
        
        return "Error: Unsupported AI provider"
        
    except Exception as e:
        logger.exception("Error in image prompt generation:")
        return f"Error generating image prompts: {str(e)}"

def editor_critique(content: str, content_type: str, ai_provider: str, model: str, knowledge_base: Dict[str, str] = None) -> str:
    """Generate editorial feedback using editor persona"""
    try:
        # Use enhanced prompt system with automatic KB concatenation
        system_prompt = get_enhanced_prompt("editor_persona", knowledge_base)
        
        user_content = f"Content Type: {content_type}\n\nContent to Review:\n{content}"
        
        if ai_provider == "OpenAI":
            openai_client = get_openai_client()
            if not openai_client:
                return "Error: OpenAI API key is not configured."
                
            response = openai_client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content}
                ],
                max_tokens=1500
            )
            
            return response.choices[0].message.content
            
        elif ai_provider == "Anthropic":
            anthropic_client = get_anthropic_client()
            if not anthropic_client:
                return "Error: Anthropic API key is not configured."
                
            response = anthropic_client.messages.create(
                model=model,
                max_tokens=1500,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": user_content}
                ]
            )
            
            return response.content[0].text
            
        elif ai_provider == "Grok":
            grok_api_key = get_grok_api_key()
            if not grok_api_key:
                return "Error: Grok API key is not configured."

            headers = {
                "Authorization": f"Bearer {grok_api_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content}
                ]
            }
            
            response = requests.post(
                "https://api.grok.x.ai/v1/chat/completions",
                headers=headers,
                json=payload
            )
            return response.json()["choices"][0]["message"]["content"]
        
        return "Error: Unsupported AI provider"
        
    except Exception as e:
        logger.exception("Error in editor critique:")
        return f"Error generating editorial feedback: {str(e)}"

def transcribe_audio(audio_file) -> str:
    """Transcribe audio file using OpenAI Whisper"""
    try:
        openai_client = get_openai_client()
        if not openai_client:
            return "Error: OpenAI API key is not configured for transcription."
        
        # Get the original file extension to preserve format
        import tempfile
        import os
        
        # Get file extension from the uploaded file name
        file_extension = ""
        if hasattr(audio_file, 'name') and audio_file.name:
            file_extension = os.path.splitext(audio_file.name)[1]
        
        # If no extension, default to common audio format
        if not file_extension:
            file_extension = ".m4a"
        
        # Save uploaded file temporarily with correct extension
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as temp_file:
            # Reset file pointer to beginning
            audio_file.seek(0)
            temp_file.write(audio_file.read())
            temp_file_path = temp_file.name
        
        # Transcribe using OpenAI Whisper with correct file
        with open(temp_file_path, "rb") as audio:
            transcript = openai_client.audio.transcriptions.create(
                model="whisper-1",
                file=audio
            )
        
        # Clean up temporary file
        os.unlink(temp_file_path)
        
        return transcript.text
        
    except Exception as e:
        logger.exception("Error in audio transcription:")
        return f"Error transcribing audio: {str(e)}" 