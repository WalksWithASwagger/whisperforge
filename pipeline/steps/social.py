"""
WhisperForge Social Media Module

This module generates social media content based on transcripts, wisdom, and blogs.
"""

import logging
import json
import re
from typing import Dict, Any, List, Optional, Union

# Configure logging
logger = logging.getLogger("whisperforge.pipeline.social")

async def generate_social_content(context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate social media content based on transcript, wisdom, and blog content.
    
    Args:
        context: Dictionary containing:
            - transcript: The transcript text
            - wisdom: Optional wisdom notes extracted from transcript
            - blog_post: Optional blog post content
            - blog_title: Optional blog post title
            - config: Step configuration with social media parameters
            
    Returns:
        Dictionary containing the generated social media content and metadata
    """
    # At least one of transcript, wisdom, or blog_post must be provided
    transcript = context.get("transcript", "")
    wisdom = context.get("wisdom", "")
    blog_post = context.get("blog_post", "")
    blog_title = context.get("blog_title", "")
    
    if not any([transcript, wisdom, blog_post]):
        raise ValueError("At least one of transcript, wisdom, or blog_post must be provided")
    
    config = context.get("config", {})
    params = config.get("params", {})
    
    # Get social platforms from config
    platforms = params.get("platforms", ["twitter", "linkedin", "facebook"])
    
    # Get number of posts per platform
    post_count = params.get("post_count", 2)
    
    # Get AI provider and model from config or use defaults
    provider = params.get("ai_provider", "anthropic")
    model = params.get("ai_model")
    
    # Get knowledge documents if available
    knowledge_docs = config.get("knowledge_docs", [])
    
    # Construct the social content prompt
    prompt, system_prompt = construct_social_prompt(
        transcript=transcript,
        wisdom=wisdom,
        blog_post=blog_post,
        blog_title=blog_title,
        platforms=platforms,
        post_count=post_count,
        knowledge_docs=knowledge_docs
    )
    
    # Generate social content using the specified provider
    if provider == "anthropic":
        response = await generate_with_anthropic(prompt, system_prompt, model, params)
    elif provider == "openai":
        response = await generate_with_openai(prompt, system_prompt, model, params)
    else:
        raise ValueError(f"Unsupported AI provider: {provider}")
    
    # Parse the response to extract individual posts
    parsed_content = parse_social_response(response, platforms)
    
    return {
        "social_content": response,
        "parsed_social_content": parsed_content,
        "metadata": {
            "provider": provider,
            "model": model,
            "platforms": platforms,
            "post_count": post_count,
            "posts_generated": sum(len(posts) for platform, posts in parsed_content.items())
        }
    }

def construct_social_prompt(
    transcript: str = "",
    wisdom: str = "",
    blog_post: str = "",
    blog_title: str = "",
    platforms: List[str] = None,
    post_count: int = 2,
    knowledge_docs: List[str] = None
) -> tuple:
    """
    Construct a prompt for social media content generation.
    
    Args:
        transcript: The transcript text (optional)
        wisdom: Wisdom notes extracted from transcript (optional)
        blog_post: Blog post content (optional)
        blog_title: Blog post title (optional)
        platforms: List of social media platforms to generate content for
        post_count: Number of posts to generate per platform
        knowledge_docs: Optional list of knowledge documents for style matching
        
    Returns:
        Tuple of (user_prompt, system_prompt)
    """
    if not platforms:
        platforms = ["twitter", "linkedin", "facebook"]
    
    # Format platforms for prompt
    platform_descriptions = []
    for platform in platforms:
        if platform.lower() in ["twitter", "x"]:
            platform_descriptions.append(f"Twitter/X ({post_count} posts, 280 characters max)")
        elif platform.lower() == "linkedin":
            platform_descriptions.append(f"LinkedIn ({post_count} posts, professional tone)")
        elif platform.lower() == "facebook":
            platform_descriptions.append(f"Facebook ({post_count} posts, conversational tone)")
        elif platform.lower() == "instagram":
            platform_descriptions.append(f"Instagram ({post_count} posts, visual focus with caption)")
        else:
            platform_descriptions.append(f"{platform.capitalize()} ({post_count} posts)")
    
    platforms_text = "\n".join([f"- {desc}" for desc in platform_descriptions])
    
    # System prompt
    system_prompt = """You are an expert social media content creator who crafts engaging, platform-appropriate posts.
Your content should be optimized for each platform's specific format, audience expectations, and character limits.
Focus on creating posts that drive engagement through questions, insights, and compelling hooks while maintaining brand voice."""
    
    # User prompt
    user_prompt = f"""Create social media content based on the provided material.

Generate posts for the following platforms:
{platforms_text}

For each platform:
1. Create {post_count} unique posts that capture key insights
2. Make each post stand alone but cohesive with the others
3. Include relevant hashtags where appropriate
4. Format the posts exactly as they would appear on each platform
5. Organize by platform with clear headings (## Twitter, ## LinkedIn, etc.)

"""
    
    # Add available content sources
    if blog_post and blog_title:
        user_prompt += f"""
BLOG TITLE:
{blog_title}

BLOG CONTENT:
{blog_post}
"""
    
    if wisdom:
        user_prompt += f"""
WISDOM NOTES:
{wisdom}
"""
        
    if transcript:
        # If transcript is very long, include just the beginning
        if len(transcript) > 2000:
            truncated = transcript[:2000] + "... [transcript truncated]"
            user_prompt += f"""
TRANSCRIPT EXCERPT:
{truncated}
"""
        else:
            user_prompt += f"""
TRANSCRIPT:
{transcript}
"""
    
    # Add knowledge documents if available
    if knowledge_docs and len(knowledge_docs) > 0:
        knowledge_context = "\n\n".join(knowledge_docs)
        user_prompt += f"""
        
Reference materials for voice and style matching:
{knowledge_context}
"""
    
    return user_prompt, system_prompt

async def generate_with_anthropic(
    prompt: str, 
    system_prompt: str,
    model: Optional[str] = None, 
    params: Dict[str, Any] = None
) -> str:
    """
    Generate social media content using Anthropic's Claude API.
    
    Args:
        prompt: The formatted prompt
        system_prompt: System instructions for the model
        model: Specific Claude model to use (or None for default)
        params: Additional parameters for the API call
        
    Returns:
        Generated social media content
    """
    try:
        # Lazy import to avoid dependencies if not using Anthropic
        from anthropic import Anthropic
        
        # Get API key
        from config import load_api_key_for_service
        api_key = load_api_key_for_service("anthropic")
        
        if not api_key:
            raise ValueError("Anthropic API key not configured")
        
        client = Anthropic(api_key=api_key)
        
        # Use default model if not specified
        if not model:
            model = "claude-3-haiku-20240307"  # Smaller model fine for social content
        
        # Default parameters
        max_tokens = params.get("max_tokens", 2000)
        temperature = params.get("temperature", 0.7)
        
        logger.info(f"Generating social media content with Anthropic model: {model}")
        
        response = await client.messages.create(
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system_prompt,
            messages=[{"role": "user", "content": prompt}]
        )
        
        return response.content[0].text
    
    except Exception as e:
        logger.error(f"Error in Anthropic generation: {str(e)}", exc_info=True)
        raise

async def generate_with_openai(
    prompt: str, 
    system_prompt: str,
    model: Optional[str] = None, 
    params: Dict[str, Any] = None
) -> str:
    """
    Generate social media content using OpenAI's API.
    
    Args:
        prompt: The formatted prompt
        system_prompt: System instructions for the model
        model: Specific OpenAI model to use (or None for default)
        params: Additional parameters for the API call
        
    Returns:
        Generated social media content
    """
    try:
        # Lazy import to avoid dependencies if not using OpenAI
        from openai import OpenAI
        
        # Get API key
        from config import load_api_key_for_service
        api_key = load_api_key_for_service("openai")
        
        if not api_key:
            raise ValueError("OpenAI API key not configured")
        
        client = OpenAI(api_key=api_key)
        
        # Use default model if not specified
        if not model:
            model = "gpt-3.5-turbo"  # Smaller model fine for social content
        
        # Default parameters
        max_tokens = params.get("max_tokens", 2000)
        temperature = params.get("temperature", 0.7)
        
        logger.info(f"Generating social media content with OpenAI model: {model}")
        
        response = await client.chat.completions.create(
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ]
        )
        
        return response.choices[0].message.content
    
    except Exception as e:
        logger.error(f"Error in OpenAI generation: {str(e)}", exc_info=True)
        raise

def parse_social_response(response: str, platforms: List[str]) -> Dict[str, List[str]]:
    """
    Parse the social media content response to extract individual posts by platform.
    
    Args:
        response: Raw response from the LLM
        platforms: List of platforms to extract content for
        
    Returns:
        Dictionary mapping platform names to lists of posts
    """
    result = {}
    
    # Normalize platform names for matching
    normalized_platforms = []
    for platform in platforms:
        if platform.lower() in ["twitter", "x"]:
            normalized_platforms.append(("twitter", ["twitter", "x"]))
        else:
            normalized_platforms.append((platform.lower(), [platform.lower()]))
    
    # Look for content sections by platform
    for platform_key, platform_aliases in normalized_platforms:
        # Create patterns to match section headers for this platform
        header_patterns = []
        for alias in platform_aliases:
            header_patterns.extend([
                rf"(?:^|\n)#+\s*{alias}(?:\s+posts)?(?:\s*:|\s*\n)",  # Markdown headers: ## Twitter, ## Twitter:, etc.
                rf"(?:^|\n){alias}(?:\s+posts)?(?:\s*:|\s*\n)",       # Plain text headers: Twitter, Twitter:, etc.
                rf"(?:^|\n)For\s+{alias}(?:\s*:|\s*\n)",              # "For Twitter:" style headers
            ])
        
        # Combine patterns with OR
        combined_pattern = "|".join(header_patterns)
        combined_pattern = f"({combined_pattern})"
        
        # Find all instances of headers for this platform
        matches = list(re.finditer(combined_pattern, response, re.IGNORECASE))
        
        if matches:
            # Get content after the header until the next platform header or end of text
            posts = []
            for i, match in enumerate(matches):
                start = match.end()
                # If this is the last match, get content until the end
                if i == len(matches) - 1:
                    # Look for next platform header from any platform
                    next_platform_patterns = []
                    for next_platform_key, next_platform_aliases in normalized_platforms:
                        if next_platform_key != platform_key:  # Skip current platform
                            for alias in next_platform_aliases:
                                next_platform_patterns.extend([
                                    rf"(?:^|\n)#+\s*{alias}(?:\s+posts)?(?:\s*:|\s*\n)",
                                    rf"(?:^|\n){alias}(?:\s+posts)?(?:\s*:|\s*\n)",
                                    rf"(?:^|\n)For\s+{alias}(?:\s*:|\s*\n)",
                                ])
                    
                    if next_platform_patterns:
                        combined_next_pattern = "|".join(next_platform_patterns)
                        next_match = re.search(combined_next_pattern, response[start:], re.IGNORECASE)
                        if next_match:
                            end = start + next_match.start()
                        else:
                            end = len(response)
                    else:
                        end = len(response)
                else:
                    end = matches[i+1].start()
                
                # Extract content between markers
                content = response[start:end].strip()
                
                # Split content into individual posts
                if content:
                    # Try to split by numbered or bulleted list items
                    post_splits = re.split(r"\n(?:(?:\d+[\.\)]\s*)|(?:[•\-\*]\s+))", content)
                    if len(post_splits) > 1:
                        # First element might be empty or intro text, skip if empty
                        if post_splits[0].strip():
                            posts.append(post_splits[0].strip())
                        
                        # Add the rest with the bullet/number markers re-added for clarity
                        for i, post in enumerate(post_splits[1:], 1):
                            if post.strip():
                                posts.append(f"{i}. {post.strip()}")
                    else:
                        # If no clear list markers, just add the whole content
                        posts.append(content)
            
            # Store posts for this platform
            normalized_name = platform_key.capitalize()
            if platform_key == "linkedin":
                normalized_name = "LinkedIn"
            elif platform_key == "twitter":
                normalized_name = "Twitter"
            elif platform_key == "facebook":
                normalized_name = "Facebook"
            elif platform_key == "instagram":
                normalized_name = "Instagram"
                
            result[normalized_name] = posts
    
    # For any platforms we didn't find, add empty lists
    for platform_key, _ in normalized_platforms:
        normalized_name = platform_key.capitalize()
        if platform_key == "linkedin":
            normalized_name = "LinkedIn"
        elif platform_key == "twitter":
            normalized_name = "Twitter"
        elif platform_key == "facebook":
            normalized_name = "Facebook"
        elif platform_key == "instagram":
            normalized_name = "Instagram"
            
        if normalized_name not in result:
            result[normalized_name] = []
    
    return result 