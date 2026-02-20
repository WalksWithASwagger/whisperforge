"""Prompt management for WhisperForge content generation.

Handles loading, formatting, and enhancing prompts from markdown files
with support for per-user overrides and automatic knowledge-base
concatenation.
"""

import logging

from .exceptions import FileProcessingError
from .path_safety import safe_path

logger = logging.getLogger(__name__)

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

    except (FileProcessingError, OSError) as e:
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
