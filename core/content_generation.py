"""
Content Generation Module for WhisperForge
Handles AI-powered content generation without Streamlit dependencies
"""

import os
import time
import logging
import requests
from typing import Dict, Optional, Any
from .utils import get_openai_client, get_anthropic_client, get_grok_api_key, get_prompt, DEFAULT_PROMPTS

logger = logging.getLogger(__name__)

def generate_wisdom(transcript: str, ai_provider: str, model: str, custom_prompt: str = None, knowledge_base: Dict[str, str] = None) -> str:
    """Extract key insights and wisdom from a transcript"""
    try:
        # Use the custom prompt if provided, otherwise get from defaults
        prompt = custom_prompt or DEFAULT_PROMPTS.get("wisdom_extraction", "")
        
        # Include knowledge base context if available
        if knowledge_base:
            knowledge_context = "\n\n".join([
                f"## {name}\n{content}" 
                for name, content in knowledge_base.items()
            ])
            system_prompt = f"""Use the following knowledge base to inform your analysis:

{knowledge_context}

When analyzing the content, please incorporate these perspectives and guidelines.

Original Prompt:
{prompt}"""
        else:
            system_prompt = prompt
        
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
        prompt = custom_prompt or DEFAULT_PROMPTS.get("outline_creation", "")
        
        if knowledge_base:
            knowledge_context = "\n\n".join([
                f"## {name}\n{content}" 
                for name, content in knowledge_base.items()
            ])
            system_prompt = f"""Use the following knowledge base to inform your analysis:

{knowledge_context}

When creating the outline, please incorporate these perspectives and guidelines.

Original Prompt:
{prompt}"""
        else:
            system_prompt = prompt
        
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

def generate_social_content(wisdom: str, outline: str, ai_provider: str, model: str, custom_prompt: str = None, knowledge_base: Dict[str, str] = None) -> str:
    """Generate social media content"""
    try:
        prompt = custom_prompt or DEFAULT_PROMPTS.get("social_media", "")
        
        if knowledge_base:
            knowledge_context = "\n\n".join([
                f"## {name}\n{content}" 
                for name, content in knowledge_base.items()
            ])
            system_prompt = f"""Use the following knowledge base to inform your analysis:

{knowledge_context}

When creating social content, please incorporate these perspectives and guidelines.

Original Prompt:
{prompt}"""
        else:
            system_prompt = prompt
        
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
        logger.exception("Error in social content generation:")
        return f"Error generating social content: {str(e)}"

def generate_image_prompts(wisdom: str, outline: str, ai_provider: str, model: str, custom_prompt: str = None, knowledge_base: Dict[str, str] = None) -> str:
    """Generate image generation prompts"""
    try:
        prompt = custom_prompt or DEFAULT_PROMPTS.get("image_prompts", "")
        
        if knowledge_base:
            knowledge_context = "\n\n".join([
                f"## {name}\n{content}" 
                for name, content in knowledge_base.items()
            ])
            system_prompt = f"""Use the following knowledge base to inform your analysis:

{knowledge_context}

When creating image prompts, please incorporate these perspectives and guidelines.

Original Prompt:
{prompt}"""
        else:
            system_prompt = prompt
        
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

def transcribe_audio(audio_file) -> str:
    """Transcribe audio file using OpenAI Whisper"""
    try:
        openai_client = get_openai_client()
        if not openai_client:
            return "Error: OpenAI API key is not configured for transcription."
        
        # Save uploaded file temporarily
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
            temp_file.write(audio_file.read())
            temp_file_path = temp_file.name
        
        # Transcribe using OpenAI Whisper
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