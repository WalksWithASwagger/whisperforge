"""
Content Generation Module for WhisperForge
Handles AI-powered content creation including transcription, wisdom extraction, and content generation
"""

import logging
import os
from typing import Dict, Optional

from .utils import get_openai_client, get_prompt, DEFAULT_PROMPTS, get_enhanced_prompt

logger = logging.getLogger(__name__)

AI_MODEL = os.getenv("GPT_MODEL", "gpt-4o")
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "whisper-1")


class ContentGenerationError(Exception):
    """Raised when content generation fails"""
    pass


def _get_client():
    """Get OpenAI client or raise if not configured"""
    client = get_openai_client()
    if not client:
        raise ContentGenerationError("OpenAI API key is not configured.")
    return client


def generate_wisdom(transcript: str, custom_prompt: str = None, knowledge_base: Dict[str, str] = None) -> str:
    """Extract key insights and wisdom from a transcript"""
    system_prompt = custom_prompt or get_enhanced_prompt(
        "wisdom_extraction", knowledge_base)

    client = _get_client()
    response = client.chat.completions.create(
        model=AI_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Here's the transcription to analyze:\n\n{transcript}"}
        ],
        max_tokens=1500
    )

    return response.choices[0].message.content


def generate_outline(transcript: str, wisdom: str, custom_prompt: str = None,
                     knowledge_base: Dict[str, str] = None) -> str:
    """Create a structured outline based on transcript and wisdom"""
    system_prompt = custom_prompt or get_enhanced_prompt(
        "outline_creation", knowledge_base)

    content = f"TRANSCRIPT:\n{transcript}\n\nWISDOM:\n{wisdom}"

    client = _get_client()
    response = client.chat.completions.create(
        model=AI_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": content}
        ],
        max_tokens=1500
    )

    return response.choices[0].message.content


def generate_article(transcript: str, wisdom: str, outline: str, custom_prompt: str = None,
                     knowledge_base: Dict[str, str] = None) -> str:
    """Generate a comprehensive article based on transcript, wisdom, and outline"""
    system_prompt = custom_prompt or get_enhanced_prompt(
        "article_writing", knowledge_base)

    transcript_excerpt = transcript[:2000] if len(
        transcript) > 2000 else transcript
    content = f"TRANSCRIPT:\n{transcript_excerpt}\n\nWISDOM:\n{wisdom}\n\nOUTLINE:\n{outline}"

    client = _get_client()
    response = client.chat.completions.create(
        model=AI_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": content}
        ],
        max_tokens=2000
    )

    return response.choices[0].message.content


def generate_social_content(wisdom: str, outline: str, article: str,
                            custom_prompt: str = None, knowledge_base: Dict[str, str] = None) -> str:
    """Generate 5 distinct social media posts"""
    system_prompt = custom_prompt or get_enhanced_prompt(
        "social_media", knowledge_base)

    article_excerpt = article[:1500] if len(article) > 1500 else article
    content = f"WISDOM:\n{wisdom}\n\nOUTLINE:\n{outline}\n\nARTICLE:\n{article_excerpt}"

    client = _get_client()
    response = client.chat.completions.create(
        model=AI_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": content}
        ],
        max_tokens=1500
    )

    return response.choices[0].message.content


def transcribe_audio(audio_file) -> str:
    """Transcribe audio using OpenAI Whisper - handles both file paths and file objects"""
    client = _get_client()

    if isinstance(audio_file, str):
        with open(audio_file, 'rb') as f:
            response = client.audio.transcriptions.create(
                model=WHISPER_MODEL,
                file=f
            )
    else:
        audio_file.seek(0)
        response = client.audio.transcriptions.create(
            model=WHISPER_MODEL,
            file=audio_file
        )

    return response.text
