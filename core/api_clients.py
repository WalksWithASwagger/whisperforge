"""API client factory functions for WhisperForge.

Provides lazy-initialised clients for OpenAI, Anthropic, and Grok APIs.
Each factory returns ``None`` when the required API key is missing or the
underlying package is not installed, allowing callers to degrade
gracefully.
"""

import logging
import os

logger = logging.getLogger(__name__)


def get_openai_client():
    """Get OpenAI client with API key.

    Returns None only when the key is missing or the package isn't installed.
    Other errors (e.g. network, auth) propagate so callers can react.
    """
    try:
        import openai
    except ImportError:
        logger.error("OpenAI package not installed")
        return None

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None

    return openai.OpenAI(api_key=api_key)


def get_anthropic_client():
    """Get Anthropic client with API key.

    Returns None only when the key is missing or the package isn't installed.
    Other errors propagate so callers can react.
    """
    try:
        import anthropic
    except ImportError:
        logger.error("Anthropic package not installed")
        return None

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        return None

    return anthropic.Anthropic(api_key=api_key)


def get_grok_api_key():
    """Get Grok API key"""
    return os.getenv("GROK_API_KEY")


def get_grok_client():
    """Get a Grok client via the OpenAI-compatible API.

    Returns an ``openai.OpenAI`` instance pointed at the Grok endpoint,
    or ``None`` when the API key is missing or the ``openai`` package is
    not installed.
    """
    try:
        import openai
    except ImportError:
        logger.error("OpenAI package not installed (required for Grok client)")
        return None

    api_key = get_grok_api_key()
    if not api_key:
        return None

    return openai.OpenAI(api_key=api_key, base_url="https://api.x.ai/v1")
