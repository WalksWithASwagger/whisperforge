"""
Shared utilities for WhisperForge
Contains functions that are shared between the original app and Supabase version
"""

import hashlib
import bcrypt
import os
import time
import logging
import requests
from typing import Dict, Optional, Any

logger = logging.getLogger(__name__)

def hash_password(password: str) -> str:
    """Hash a password using bcrypt with salt"""
    # Generate salt and hash password
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    """Verify a password against its hash"""
    try:
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    except Exception as e:
        logger.error(f"Password verification error: {e}")
        return False

# Legacy SHA-256 hash function for migration purposes
def legacy_hash_password(password: str) -> str:
    """Legacy SHA-256 hash - DEPRECATED, use for migration only"""
    return hashlib.sha256(password.encode()).hexdigest()

# Default prompts for content generation
DEFAULT_PROMPTS = {
    "wisdom_extraction": """Extract key insights, lessons, and wisdom from the transcript. Focus on actionable takeaways and profound realizations.""",
    "summary": """## Summary
Create a concise summary of the main points and key messages in the transcript.
Capture the essence of the content in a few paragraphs.""",
    "outline_creation": """Create a detailed outline for an article or blog post based on the transcript and extracted wisdom. Include major sections and subsections.""",
    "social_media": """Generate engaging social media posts for different platforms (Twitter, LinkedIn, Instagram) based on the key insights.""",
    "image_prompts": """Create detailed image generation prompts that visualize the key concepts and metaphors from the content.""",
    "article_writing": """Write a comprehensive article based on the provided outline and wisdom. Maintain a clear narrative flow and engaging style.""",
    "seo_analysis": """Analyze the content from an SEO perspective and provide optimization recommendations for better search visibility while maintaining content quality."""
}

def get_openai_client():
    """Get OpenAI client with API key"""
    try:
        import openai
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            return None
        
        client = openai.OpenAI(api_key=api_key)
        return client
    except ImportError:
        logger.error("OpenAI package not installed")
        return None
    except Exception as e:
        logger.error(f"Error initializing OpenAI client: {e}")
        return None

def get_anthropic_client():
    """Get Anthropic client with API key"""
    try:
        import anthropic
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            return None
        
        client = anthropic.Anthropic(api_key=api_key)
        return client
    except ImportError:
        logger.error("Anthropic package not installed")
        return None
    except Exception as e:
        logger.error(f"Error initializing Anthropic client: {e}")
        return None

def get_grok_api_key():
    """Get Grok API key"""
    return os.getenv("GROK_API_KEY")

def update_usage_tracking(duration_seconds: float):
    """Placeholder for usage tracking - implement as needed"""
    logger.info(f"Usage tracked: {duration_seconds} seconds")

def get_prompt(prompt_type: str, prompts: Dict[str, str], default_prompts: Dict[str, str]) -> str:
    """Get prompt from user prompts or defaults"""
    return prompts.get(prompt_type, default_prompts.get(prompt_type, "")) 