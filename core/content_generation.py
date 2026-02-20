"""
Content Generation Module for WhisperForge
Handles AI-powered content creation including transcription, wisdom extraction, and content generation.
Supports multiple AI providers: OpenAI, Anthropic, and Grok (xAI).
"""

import logging
import os

from .api_clients import get_anthropic_client, get_grok_client, get_openai_client
from .constants import (
    ARTICLE_PREVIEW_LENGTH,
    MAX_TOKENS_ARTICLE,
    MAX_TOKENS_DEFAULT,
    TRANSCRIPT_PREVIEW_LENGTH,
)
from .exceptions import PipelineError
from .prompts import get_enhanced_prompt

logger = logging.getLogger(__name__)

WHISPER_MODEL = os.getenv("WHISPER_MODEL", "whisper-1")

DEFAULT_MODELS = {
    "openai": os.getenv("GPT_MODEL", "gpt-4o"),
    "anthropic": os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-20250514"),
    "grok": os.getenv("GROK_MODEL", "grok-3"),
}

# Provider priority for fallback ordering
_PROVIDER_PRIORITY = ("openai", "anthropic", "grok")

# Map provider names to their client factory functions
_CLIENT_FACTORIES = {
    "openai": get_openai_client,
    "anthropic": get_anthropic_client,
    "grok": get_grok_client,
}


class ContentGenerationError(PipelineError):
    """Raised when content generation fails"""

    pass


def _resolve_provider() -> str:
    """Determine the active AI provider.

    Checks ``st.session_state.ai_provider`` first (if Streamlit is running),
    then falls back to the first provider with a configured API key in
    priority order: openai > anthropic > grok.

    Raises ``ContentGenerationError`` if no provider is available.
    """
    # Try Streamlit session state first
    try:
        import streamlit as st

        preferred = st.session_state.get("ai_provider")
        if preferred and _CLIENT_FACTORIES.get(preferred):
            client = _CLIENT_FACTORIES[preferred]()
            if client is not None:
                return preferred
            logger.warning("Preferred provider '%s' is not configured (missing API key). Trying fallbacks.", preferred)
    except (ImportError, RuntimeError):
        # Not running in Streamlit context
        pass

    # Fallback: first available provider
    for provider in _PROVIDER_PRIORITY:
        client = _CLIENT_FACTORIES[provider]()
        if client is not None:
            return provider

    raise ContentGenerationError(
        "No AI provider is configured. Set at least one of: OPENAI_API_KEY, ANTHROPIC_API_KEY, or GROK_API_KEY."
    )


def _call_openai_compatible(provider: str, system_prompt: str, user_content: str, max_tokens: int, model: str) -> str:
    """Make a chat completion call using the OpenAI SDK shape.

    Works for both OpenAI and Grok (xAI), since Grok exposes an
    OpenAI-compatible API.
    """
    client = _CLIENT_FACTORIES[provider]()
    if not client:
        raise ContentGenerationError(f"{provider} client is not configured.")

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ],
        max_tokens=max_tokens,
    )
    return response.choices[0].message.content


def _call_anthropic(system_prompt: str, user_content: str, max_tokens: int, model: str) -> str:
    """Make a chat completion call using the Anthropic SDK."""
    client = get_anthropic_client()
    if not client:
        raise ContentGenerationError("Anthropic client is not configured.")

    response = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        system=system_prompt,
        messages=[{"role": "user", "content": user_content}],
    )
    return response.content[0].text


def _call_provider(provider: str, system_prompt: str, user_content: str, max_tokens: int) -> str:
    """Dispatch a chat completion call to the appropriate provider backend."""
    model = DEFAULT_MODELS[provider]

    # Check for a session-state model override
    try:
        import streamlit as st

        model_key = f"{provider}_model"
        override = st.session_state.get(model_key)
        if override:
            model = override
    except (ImportError, RuntimeError):
        pass

    if provider == "anthropic":
        return _call_anthropic(system_prompt, user_content, max_tokens, model)
    else:
        # Both OpenAI and Grok use OpenAI-compatible SDK
        return _call_openai_compatible(provider, system_prompt, user_content, max_tokens, model)


def _chat_completion(system_prompt: str, user_content: str, max_tokens: int = MAX_TOKENS_DEFAULT) -> str:
    """Run a chat completion with automatic provider resolution and fallback.

    Resolves the preferred provider, attempts the call, and on failure
    tries remaining providers in priority order before raising.
    """
    primary = _resolve_provider()

    # Build ordered list: primary first, then remaining providers
    providers_to_try = [primary] + [p for p in _PROVIDER_PRIORITY if p != primary]

    last_error = None
    for provider in providers_to_try:
        # Skip providers that aren't configured
        client = _CLIENT_FACTORIES[provider]()
        if client is None:
            continue

        try:
            return _call_provider(provider, system_prompt, user_content, max_tokens)
        except ContentGenerationError:
            raise
        except Exception as e:
            logger.warning("Provider '%s' failed: %s. Trying next provider.", provider, e)
            last_error = e

    raise ContentGenerationError(f"All AI providers failed. Last error: {last_error}")


# ---------------------------------------------------------------------------
# Whisper transcription (OpenAI-only)
# ---------------------------------------------------------------------------


def _get_whisper_client():
    """Get an OpenAI client for Whisper transcription.

    Whisper is only available through the OpenAI API, so this always
    returns an OpenAI client or raises.
    """
    client = get_openai_client()
    if not client:
        raise ContentGenerationError(
            "OpenAI API key is not configured. Whisper transcription requires an OpenAI API key."
        )
    return client


def transcribe_audio(audio_file) -> str:
    """Transcribe audio using OpenAI Whisper - handles both file paths and file objects"""
    client = _get_whisper_client()

    if isinstance(audio_file, str):
        with open(audio_file, "rb") as f:
            response = client.audio.transcriptions.create(model=WHISPER_MODEL, file=f)
    else:
        audio_file.seek(0)
        response = client.audio.transcriptions.create(model=WHISPER_MODEL, file=audio_file)

    return response.text


# ---------------------------------------------------------------------------
# Content generation functions
# ---------------------------------------------------------------------------


def generate_wisdom(transcript: str, custom_prompt: str = None, knowledge_base: dict[str, str] = None) -> str:
    """Extract key insights and wisdom from a transcript"""
    system_prompt = custom_prompt or get_enhanced_prompt("wisdom_extraction", knowledge_base)
    return _chat_completion(system_prompt, f"Here's the transcription to analyze:\n\n{transcript}")


def generate_outline(
    transcript: str, wisdom: str, custom_prompt: str = None, knowledge_base: dict[str, str] = None
) -> str:
    """Create a structured outline based on transcript and wisdom"""
    system_prompt = custom_prompt or get_enhanced_prompt("outline_creation", knowledge_base)
    return _chat_completion(system_prompt, f"TRANSCRIPT:\n{transcript}\n\nWISDOM:\n{wisdom}")


def generate_article(
    transcript: str, wisdom: str, outline: str, custom_prompt: str = None, knowledge_base: dict[str, str] = None
) -> str:
    """Generate a comprehensive article based on transcript, wisdom, and outline"""
    system_prompt = custom_prompt or get_enhanced_prompt("article_writing", knowledge_base)
    transcript_excerpt = (
        transcript[:TRANSCRIPT_PREVIEW_LENGTH] if len(transcript) > TRANSCRIPT_PREVIEW_LENGTH else transcript
    )
    return _chat_completion(
        system_prompt,
        f"TRANSCRIPT:\n{transcript_excerpt}\n\nWISDOM:\n{wisdom}\n\nOUTLINE:\n{outline}",
        max_tokens=MAX_TOKENS_ARTICLE,
    )


def generate_social_content(
    wisdom: str, outline: str, article: str, custom_prompt: str = None, knowledge_base: dict[str, str] = None
) -> str:
    """Generate 5 distinct social media posts"""
    system_prompt = custom_prompt or get_enhanced_prompt("social_media", knowledge_base)
    article_excerpt = article[:ARTICLE_PREVIEW_LENGTH] if len(article) > ARTICLE_PREVIEW_LENGTH else article
    return _chat_completion(
        system_prompt,
        f"WISDOM:\n{wisdom}\n\nOUTLINE:\n{outline}\n\nARTICLE:\n{article_excerpt}",
    )
