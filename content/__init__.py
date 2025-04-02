"""
Content generation package for WhisperForge.
"""

# Import all content generation functions
from content.wisdom import extract_wisdom
from content.outline import generate_outline
from content.blog import generate_blog_post
from content.social import generate_social_content
from content.image import generate_image_prompts
from content.summary import generate_summary

# Export all content generation functions
__all__ = [
    'extract_wisdom',
    'generate_outline',
    'generate_blog_post',
    'generate_social_content',
    'generate_image_prompts',
    'generate_summary'
]
