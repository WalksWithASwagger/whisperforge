"""
WhisperForge Outline Module

This module generates structured content outlines based on transcripts and extracted wisdom.
"""

import logging
import json
from typing import Dict, Any, List, Optional, Union

# Configure logging
logger = logging.getLogger("whisperforge.pipeline.outline")

async def generate_outline(context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate a structured content outline based on transcript and wisdom.
    
    Args:
        context: Dictionary containing:
            - transcript: The transcript text
            - wisdom: Optional wisdom notes extracted from transcript
            - config: Step configuration with outline parameters
            
    Returns:
        Dictionary containing the generated outline and metadata
    """
    transcript = context.get("transcript")
    if not transcript:
        raise ValueError("No transcript provided for outline generation")
    
    # Get wisdom notes if available
    wisdom = context.get("wisdom", "")
    
    config = context.get("config", {})
    params = config.get("params", {})
    
    # Get content type from config
    content_type = params.get("content_type", "blog")
    
    # Get outline style from config
    outline_style = params.get("outline_style", "standard")
    
    # Get AI provider and model from config or use defaults
    provider = params.get("ai_provider", "anthropic")
    model = params.get("ai_model")
    
    # Get knowledge documents if available
    knowledge_docs = config.get("knowledge_docs", [])
    
    # Construct the outline prompt
    prompt, system_prompt = construct_outline_prompt(
        transcript=transcript,
        wisdom=wisdom,
        content_type=content_type,
        outline_style=outline_style,
        knowledge_docs=knowledge_docs
    )
    
    # Generate outline using the specified provider
    if provider == "anthropic":
        response = await generate_with_anthropic(prompt, system_prompt, model, params)
    elif provider == "openai":
        response = await generate_with_openai(prompt, system_prompt, model, params)
    else:
        raise ValueError(f"Unsupported AI provider: {provider}")
    
    return {
        "outline": response,
        "metadata": {
            "provider": provider,
            "model": model,
            "content_type": content_type,
            "outline_style": outline_style,
            "knowledge_docs_used": len(knowledge_docs)
        }
    }

def construct_outline_prompt(
    transcript: str,
    wisdom: str = "",
    content_type: str = "blog",
    outline_style: str = "standard",
    knowledge_docs: List[str] = None
) -> tuple:
    """
    Construct a prompt for outline generation.
    
    Args:
        transcript: The transcript text
        wisdom: Optional wisdom notes extracted from transcript
        content_type: Type of content to outline (blog, newsletter, etc.)
        outline_style: Style of outline to generate
        knowledge_docs: Optional list of knowledge documents for style matching
        
    Returns:
        Tuple of (user_prompt, system_prompt)
    """
    # Get appropriate outline template
    template = OUTLINE_TEMPLATES.get(
        f"{content_type}_{outline_style}",
        OUTLINE_TEMPLATES.get(f"{content_type}_standard", 
        OUTLINE_TEMPLATES["blog_standard"])  # Default to blog_standard
    )
    
    # Basic system prompt
    system_prompt = template["system_prompt"]
    
    # User instruction prompt
    instruction_template = template["instruction_template"]
    user_prompt = instruction_template.format(
        transcript=transcript,
        wisdom=wisdom if wisdom else "No wisdom notes provided."
    )
    
    # Add knowledge documents if available
    if knowledge_docs and len(knowledge_docs) > 0:
        knowledge_context = "\n\n".join(knowledge_docs)
        user_prompt += f"""
        
        Reference materials for style matching:
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
    Generate outline using Anthropic's Claude API.
    
    Args:
        prompt: The formatted prompt
        system_prompt: System instructions for the model
        model: Specific Claude model to use (or None for default)
        params: Additional parameters for the API call
        
    Returns:
        Generated outline text
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
            model = "claude-3-haiku-20240307"  # Reasonable default for outline generation
        
        # Default parameters
        max_tokens = params.get("max_tokens", 4000)
        temperature = params.get("temperature", 0.7)
        
        logger.info(f"Generating outline with Anthropic model: {model}")
        
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
    Generate outline using OpenAI's API.
    
    Args:
        prompt: The formatted prompt
        system_prompt: System instructions for the model
        model: Specific OpenAI model to use (or None for default)
        params: Additional parameters for the API call
        
    Returns:
        Generated outline text
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
            model = "gpt-3.5-turbo"  # Reasonable default for outline generation
        
        # Default parameters
        max_tokens = params.get("max_tokens", 2000)
        temperature = params.get("temperature", 0.7)
        
        logger.info(f"Generating outline with OpenAI model: {model}")
        
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

# Template library for different content types and styles
OUTLINE_TEMPLATES = {
    "blog_standard": {
        "name": "Standard Blog Outline",
        "system_prompt": """You are an expert content strategist who creates well-structured blog outlines.
Your outlines should be comprehensive, logical, and engaging, following best practices for digital content.
Focus on creating outlines that have clear sections, cover key points from the transcript and wisdom notes,
and maintain a natural flow that will engage readers.""",

        "instruction_template": """Create a detailed blog post outline based on the provided transcript and wisdom notes.

Include:
1. An engaging headline
2. A compelling introduction
3. 4-6 main sections with subpoints
4. A strong conclusion
5. Any key quotes or statistics to highlight

Make the outline comprehensive enough to guide a writer but not excessively detailed.
Ensure the structure flows logically and covers the most important insights.

TRANSCRIPT:
{transcript}

WISDOM NOTES:
{wisdom}
"""
    },
    
    "blog_listicle": {
        "name": "Listicle Blog Outline",
        "system_prompt": """You are an expert content strategist who creates engaging listicle-style blog outlines.
Your outlines should organize content into a numbered list format that is easy to scan and digest.
Focus on creating outlines with clear, consistent list items that are substantive and valuable to readers.""",

        "instruction_template": """Create a listicle-style blog post outline based on the provided transcript and wisdom notes.

Include:
1. A numbered-list headline (e.g., "7 Ways to..." or "10 Strategies for...")
2. A brief introduction explaining the value of the list
3. 5-10 numbered list items with brief descriptions
4. A conclusion that ties the list items together

Make each list item substantive and consistent in structure.
Ensure the outline captures the most important insights from the material.

TRANSCRIPT:
{transcript}

WISDOM NOTES:
{wisdom}
"""
    },
    
    "blog_howto": {
        "name": "How-To Blog Outline",
        "system_prompt": """You are an expert content strategist who creates clear, instructional how-to blog outlines.
Your outlines should provide step-by-step guidance that is easy to follow and actionable.
Focus on creating outlines that break complex processes into manageable steps with clear explanations.""",

        "instruction_template": """Create a how-to blog post outline based on the provided transcript and wisdom notes.

Include:
1. A clear "How to" headline
2. An introduction explaining the value of learning this skill/process
3. A materials/prerequisites section if applicable
4. 5-10 sequential steps with brief descriptions
5. Troubleshooting tips or common mistakes section
6. A conclusion highlighting benefits of mastering this skill/process

Ensure steps are in logical order and provide a complete guide to the process.

TRANSCRIPT:
{transcript}

WISDOM NOTES:
{wisdom}
"""
    },
    
    "newsletter_standard": {
        "name": "Standard Newsletter Outline",
        "system_prompt": """You are an expert content strategist who creates engaging newsletter outlines.
Your outlines should be concise, varied, and designed to maintain reader interest through multiple segments.
Focus on creating outlines that have a mix of content types, clear sections, and a consistent voice.""",

        "instruction_template": """Create a newsletter outline based on the provided transcript and wisdom notes.

Include:
1. An attention-grabbing subject line
2. A brief personal/branded introduction
3. 3-5 content sections (main story, quick tips, news items, etc.)
4. A call-to-action section
5. A brief sign-off

Keep sections brief but substantive, with varied content to maintain interest.
Ensure the outline captures the most valuable insights for the audience.

TRANSCRIPT:
{transcript}

WISDOM NOTES:
{wisdom}
"""
    },
    
    "social_content": {
        "name": "Social Media Content Outline",
        "system_prompt": """You are an expert social media strategist who creates effective social content outlines.
Your outlines should provide varied social posts that work across different platforms while maintaining key messages.
Focus on creating outlines that are attention-grabbing, shareable, and aligned with platform best practices.""",

        "instruction_template": """Create a social media content outline based on the provided transcript and wisdom notes.

Include:
1. 3 Twitter/X post ideas (280 characters max each)
2. 2 LinkedIn post ideas (text-focused, professional tone)
3. 2 Facebook post ideas (community-focused)
4. 1-2 key quotes to highlight
5. 2-3 hashtag suggestions

Ensure posts are platform-appropriate and capture key insights.
Focus on elements most likely to generate engagement.

TRANSCRIPT:
{transcript}

WISDOM NOTES:
{wisdom}
"""
    },
    
    "executive_summary": {
        "name": "Executive Summary Outline",
        "system_prompt": """You are an expert business communicator who creates concise, high-impact executive summary outlines.
Your outlines should focus on key strategic insights, business implications, and actionable takeaways.
Focus on creating outlines that are brief but comprehensive, highlighting what executives need to know.""",

        "instruction_template": """Create an executive summary outline based on the provided transcript and wisdom notes.

Include:
1. A clear, business-focused title
2. Overview section (1-2 sentences)
3. 3-5 key findings or insights
4. Business implications section
5. Recommended actions section
6. Brief conclusion

Keep the outline concise, strategic, and focused on business value.
Highlight metrics, ROI, or strategic advantages where possible.

TRANSCRIPT:
{transcript}

WISDOM NOTES:
{wisdom}
"""
    },
    
    "video_script": {
        "name": "Video Script Outline",
        "system_prompt": """You are an expert video content producer who creates effective video script outlines.
Your outlines should have clear segments timed appropriately for video, with visual and audio guidance.
Focus on creating outlines that will translate well to visual storytelling with proper pacing.""",

        "instruction_template": """Create a video script outline based on the provided transcript and wisdom notes.

Include:
1. Video title and target duration
2. Intro hook (15-30 seconds)
3. 3-6 main segments with approximate timing
4. Visual/graphic suggestions for key points
5. Call-to-action conclusion

Structure the outline for visual storytelling with good pacing.
Include notes on tone, visual elements, and key points to emphasize.

TRANSCRIPT:
{transcript}

WISDOM NOTES:
{wisdom}
"""
    }
} 