"""
Shared utilities for WhisperForge
Contains functions that are shared between the original app and Supabase version
"""

import hashlib
import logging
import os
import re
from pathlib import Path

import bcrypt

logger = logging.getLogger(__name__)

# --- Path safety ---

# Only allow alphanumeric, hyphens, underscores, and single dots (no ..)
_SAFE_FILENAME_RE = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9._-]*$")


def safe_path(root: str, untrusted_name: str) -> Path:
    """Build a file path that is guaranteed to stay within *root*.

    Raises ValueError if the resulting path escapes the root directory
    or if the filename contains disallowed characters.
    """
    if not _SAFE_FILENAME_RE.match(untrusted_name):
        raise ValueError(
            f"Invalid filename: {untrusted_name!r}. "
            "Only alphanumeric characters, hyphens, underscores, and dots are allowed."
        )
    if ".." in untrusted_name:
        raise ValueError("Path traversal sequences are not allowed.")

    root_resolved = Path(root).resolve()
    target = (root_resolved / untrusted_name).resolve()

    if not target.is_relative_to(root_resolved):
        raise ValueError(f"Path escapes allowed directory: {target} is not under {root_resolved}")
    return target


def hash_password(password: str) -> str:
    """Hash a password using bcrypt with salt"""
    # Generate salt and hash password
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(password: str, hashed: str) -> bool:
    """Verify a password against its hash"""
    try:
        return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))
    except Exception as e:
        logger.error(f"Password verification error: {e}")
        return False


# Legacy SHA-256 hash function for migration purposes


def legacy_hash_password(password: str) -> str:
    """Legacy SHA-256 hash - DEPRECATED, use for migration only"""
    return hashlib.sha256(password.encode()).hexdigest()


# Default prompts for content generation (DEPRECATED - use load_prompt_from_file)
DEFAULT_PROMPTS = {
    "wisdom_extraction": """Extract key insights, lessons, and wisdom from the transcript. Focus on actionable takeaways and profound realizations.""",
    "summary": """## Summary
Create a concise summary of the main points and key messages in the transcript.
Capture the essence of the content in a few paragraphs.""",
    "outline_creation": """Create a detailed outline for an article or blog post based on the transcript and extracted wisdom. Include major sections and subsections.""",
    "social_media": """Generate engaging social media posts for different platforms (Twitter, LinkedIn, Instagram) based on the key insights.""",
    "image_prompts": """Create detailed image generation prompts that visualize the key concepts and metaphors from the content.""",
    "article_writing": """Write a comprehensive article based on the provided outline and wisdom. Maintain a clear narrative flow and engaging style.""",
    "seo_analysis": """Analyze the content from an SEO perspective and provide optimization recommendations for better search visibility while maintaining content quality.""",
    "editor_persona": """You are a professional content editor. Provide constructive feedback to improve the content quality.""",
}


def load_prompt_from_file(prompt_type: str, user_id: str = None) -> str:
    """Load prompt from markdown file with user override support"""
    try:
        # Check for user-specific prompt first (for paid tiers)
        if user_id:
            user_dir = str(safe_path("prompts/users", user_id))
            user_prompt_path = safe_path(user_dir, f"{prompt_type}.md")
            if user_prompt_path.exists():
                return user_prompt_path.read_text(encoding="utf-8").strip()

        # Load default prompt
        default_prompt_path = safe_path("prompts/default", f"{prompt_type}.md")
        if default_prompt_path.exists():
            return default_prompt_path.read_text(encoding="utf-8").strip()

        # Fallback to hardcoded prompts
        fallback = DEFAULT_PROMPTS.get(prompt_type, "")
        if fallback:
            logger.warning(f"Using fallback prompt for {prompt_type} - consider creating markdown file")
            return fallback

        logger.error(f"No prompt found for type: {prompt_type}")
        return f"Please provide content for {prompt_type.replace('_', ' ')}."

    except Exception as e:
        logger.error(f"Error loading prompt {prompt_type}: {e}")
        return DEFAULT_PROMPTS.get(prompt_type, f"Error loading {prompt_type} prompt.")


def format_knowledge_base_context(knowledge_base: dict[str, str]) -> str:
    """Format knowledge base content for auto-concatenation to prompts"""
    if not knowledge_base:
        return ""

    context_parts = ["## Knowledge Base Context\n"]
    context_parts.append(
        "Use the following knowledge base to inform your analysis and maintain consistency with established perspectives:\n"
    )

    for name, content in knowledge_base.items():
        context_parts.append(f"### {name}")
        context_parts.append(content)
        context_parts.append("")  # Empty line for separation

    context_parts.append("---\n")
    context_parts.append("## Your Task\n")

    return "\n".join(context_parts)


def get_enhanced_prompt(prompt_type: str, knowledge_base: dict[str, str] = None, user_id: str = None) -> str:
    """Get prompt with automatic knowledge base concatenation"""
    base_prompt = load_prompt_from_file(prompt_type, user_id)

    if knowledge_base:
        kb_context = format_knowledge_base_context(knowledge_base)
        return f"{kb_context}{base_prompt}"

    return base_prompt


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


def get_prompt(prompt_type: str, prompts: dict[str, str], default_prompts: dict[str, str]) -> str:
    """Get prompt from user prompts or defaults (DEPRECATED - use get_enhanced_prompt)"""
    return prompts.get(prompt_type, default_prompts.get(prompt_type, ""))
