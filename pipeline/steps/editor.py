"""
WhisperForge Editor Module

This module provides editorial pass functionality to improve content quality
while maintaining voice consistency.
"""

import logging
import re
from typing import Dict, Any, List, Optional, Tuple, Union

# Configure logging
logger = logging.getLogger("whisperforge.pipeline.editor")

async def apply_editor(context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Apply editorial pass to content for improvement.
    
    Args:
        context: Dictionary containing:
            - content: The content to edit
            - content_type: Type of content (outline, blog, social, etc.)
            - config: Step configuration with editor parameters
            
    Returns:
        Dictionary containing the edited content and feedback
    """
    content = context.get("content")
    if not content:
        raise ValueError("No content provided for editing")
    
    content_type = context.get("content_type", "text")
    
    config = context.get("config", {})
    params = config.get("params", {})
    
    # Get editor style from config
    editor_style = params.get("editor_style", "standard")
    
    # Get AI provider and model from config or use defaults
    provider = params.get("ai_provider", "anthropic")
    model = params.get("ai_model")
    
    # Get knowledge documents for voice consistency
    knowledge_docs = config.get("knowledge_docs", [])
    
    # Construct the editor prompt
    prompt, system_prompt = construct_editor_prompt(
        content=content, 
        content_type=content_type,
        editor_style=editor_style, 
        knowledge_docs=knowledge_docs
    )
    
    # Generate edited content using the specified provider
    if provider == "anthropic":
        response = await generate_with_anthropic(prompt, system_prompt, model, params)
    elif provider == "openai":
        response = await generate_with_openai(prompt, system_prompt, model, params)
    else:
        raise ValueError(f"Unsupported AI provider: {provider}")
    
    # Parse response to extract feedback and edited content
    feedback, edited_content = parse_editor_response(response)
    
    return {
        "edited_content": edited_content,
        "feedback": feedback,
        "metadata": {
            "provider": provider,
            "model": model,
            "editor_style": editor_style,
            "content_type": content_type,
            "knowledge_docs_used": len(knowledge_docs)
        }
    }

def construct_editor_prompt(
    content: str, 
    content_type: str = "text",
    editor_style: str = "standard",
    knowledge_docs: List[str] = None
) -> Tuple[str, str]:
    """
    Construct a prompt for the editor.
    
    Args:
        content: The content to be edited
        content_type: Type of content (outline, blog, social, etc.)
        editor_style: Editor style to use (standard, brevity, engagement)
        knowledge_docs: Optional list of knowledge documents for voice consistency
        
    Returns:
        Tuple of (user_prompt, system_prompt)
    """
    # Get appropriate editor template
    template = EDITOR_TEMPLATES.get(editor_style, EDITOR_TEMPLATES["standard"])
    
    # Basic system prompt
    system_prompt = template["system_prompt"]
    
    # User instruction prompt
    instruction_template = template["instruction_template"]
    user_prompt = instruction_template.format(
        content_type=content_type,
        content=content
    )
    
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
    Generate edited content using Anthropic's Claude API.
    
    Args:
        prompt: The formatted prompt
        system_prompt: System instructions for the model
        model: Specific Claude model to use (or None for default)
        params: Additional parameters for the API call
        
    Returns:
        Generated response with feedback and edited content
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
            model = "claude-3-opus-20240229"  # Use the most capable model for editing
        
        # Default parameters - higher quality for editing
        max_tokens = params.get("max_tokens", 4000)
        temperature = params.get("temperature", 0.5)
        
        logger.info(f"Generating edited content with Anthropic model: {model}")
        
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
    Generate edited content using OpenAI's API.
    
    Args:
        prompt: The formatted prompt
        system_prompt: System instructions for the model
        model: Specific OpenAI model to use (or None for default)
        params: Additional parameters for the API call
        
    Returns:
        Generated response with feedback and edited content
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
            model = "gpt-4"  # Use the most capable model for editing
        
        # Default parameters - higher quality for editing
        max_tokens = params.get("max_tokens", 4000)
        temperature = params.get("temperature", 0.5)
        
        logger.info(f"Generating edited content with OpenAI model: {model}")
        
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

def parse_editor_response(response: str) -> Tuple[str, str]:
    """
    Parse the editor response to separate feedback from revised content.
    
    Args:
        response: Raw response from the LLM
        
    Returns:
        Tuple of (feedback, edited_content)
    """
    # Pattern 1: Look for explicit section headers
    section_headers = [
        r"(?i)# *Revision Notes:?.*?# *Revised Content:?",
        r"(?i)# *Feedback:?.*?# *Improved Content:?",
        r"(?i)# *Editor Notes:?.*?# *Edited Version:?",
        r"(?i)## *Revision Notes:?.*?## *Revised Content:?",
        r"(?i)## *Feedback:?.*?## *Improved Content:?",
        r"(?i)## *Editor Notes:?.*?## *Edited Version:?",
    ]
    
    for pattern in section_headers:
        match = re.search(pattern, response, re.DOTALL)
        if match:
            split_point = match.end()
            # Extract section before split point as feedback (removing the header)
            feedback_part = response[:split_point]
            # Remove the first header (Revision Notes, Feedback, etc.)
            for header in [
                r"(?i)# *Revision Notes:?", r"(?i)# *Feedback:?", r"(?i)# *Editor Notes:?",
                r"(?i)## *Revision Notes:?", r"(?i)## *Feedback:?", r"(?i)## *Editor Notes:?"
            ]:
                feedback_part = re.sub(header, "", feedback_part, 1)
            
            # Extract content after split point (removing the header)
            content_part = response[split_point:]
            # Remove the second header (Revised Content, Improved Content, etc.)
            for header in [
                r"(?i)# *Revised Content:?", r"(?i)# *Improved Content:?", r"(?i)# *Edited Version:?",
                r"(?i)## *Revised Content:?", r"(?i)## *Improved Content:?", r"(?i)## *Edited Version:?"
            ]:
                content_part = re.sub(header, "", content_part, 1)
                
            return feedback_part.strip(), content_part.strip()
    
    # Pattern 2: Look for common separators
    separators = [
        "REVISED CONTENT:",
        "IMPROVED VERSION:",
        "EDITED VERSION:",
        "HERE'S THE REVISED VERSION:",
        "IMPROVED CONTENT:",
        "---",
        "***",
        "===",
    ]
    
    for separator in separators:
        if separator in response:
            parts = response.split(separator, 1)
            return parts[0].strip(), parts[1].strip()
    
    # Pattern 3: Look for numbered sections (1. Feedback, 2. Revised content)
    if re.search(r"(?:^|\n)1[\.\)] ", response) and re.search(r"(?:^|\n)2[\.\)] ", response):
        # Find position of section 2
        match = re.search(r"(?:^|\n)2[\.\)] ", response)
        if match:
            split_point = match.start()
            return response[:split_point].strip(), response[split_point:].strip()
    
    # Fallback: If we can't identify a clear structure, return empty feedback
    # and the entire response as content
    logger.warning("Could not identify clear sections in editor response. Returning entire response as content.")
    return "", response

# Editor templates for different editing styles
EDITOR_TEMPLATES = {
    "standard": {
        "name": "Standard Editor",
        "system_prompt": """You are a strategic editor who knows the user's tone and goals. 
Your task is to review content and provide both feedback and improvements while maintaining 
the authentic voice of the original author. Focus on improving clarity, structure, impact, 
and engagement without changing the core style or message.""",

        "instruction_template": """Review this {content_type} and return:

1. Clear revision notes (structure, clarity, voice, impact)
2. A cleaner, improved version of the content

Do not change the author's voice—refine and focus the ideas. Be concise and specific.

Content to review:
{content}
"""
    },
    
    "brevity": {
        "name": "Brevity Editor",
        "system_prompt": """You are an editor focused on brevity and impact. 
Your task is to tighten content while preserving meaning and voice.
Look for unnecessary words, redundant phrases, and overly complex explanations.
Your goal is to make the content more concise without losing key information or changing tone.""",

        "instruction_template": """Review this {content_type} and return:

1. Notes on unnecessary text that can be removed
2. A tighter, more concise version that maintains impact

Cut at least 25% of the length while preserving all key points.

Content to review:
{content}
"""
    },
    
    "engagement": {
        "name": "Engagement Editor",
        "system_prompt": """You are an editor specialized in making content more engaging and captivating. 
Your task is to enhance the hook, flow, and reader connection.
Focus on creating compelling openings, smoother transitions, and more impactful conclusions.
Look for opportunities to add vivid language, rhetorical questions, and reader-focused elements.""",

        "instruction_template": """Review this {content_type} and return:

1. Notes on engagement opportunities
2. A revised version with stronger hooks, better flow, and more compelling language

Make this content impossible to stop reading while maintaining the author's authentic voice.

Content to review:
{content}
"""
    },
    
    "strategic": {
        "name": "Strategic Clarity Editor",
        "system_prompt": """You are a strategic editor who specializes in making content more 
impactful for business and thought leadership contexts.
Your task is to enhance clarity, strengthen the strategic framework, and highlight actionable insights.
Ensure the content has a clear purpose, logical structure, and valuable takeaways.""",

        "instruction_template": """Review this {content_type} and return:

1. Notes on strategic clarity and impact
2. A revised version that enhances the strategic value and actionable insights

Make this content more valuable for decision-makers while maintaining the author's authentic voice.

Content to review:
{content}
"""
    }
}

# Helper functions for common editor tasks
async def apply_editor_to_outline(context: Dict[str, Any]) -> Dict[str, Any]:
    """Apply editor to an outline"""
    # Get outline from context
    outline = context.get("outline")
    if not outline:
        raise ValueError("No outline provided for editing")
    
    # Create new context for the editor
    editor_context = {
        "content": outline,
        "content_type": "outline",
        "config": context.get("config", {})
    }
    
    # Apply the editor
    editor_result = await apply_editor(editor_context)
    
    return {
        "edited_outline": editor_result["edited_content"],
        "outline_feedback": editor_result["feedback"],
        "metadata": editor_result["metadata"]
    }

async def apply_editor_to_blog(context: Dict[str, Any]) -> Dict[str, Any]:
    """Apply editor to a blog post"""
    # Get blog post from context
    blog_post = context.get("blog_post")
    if not blog_post:
        raise ValueError("No blog post provided for editing")
    
    # Create new context for the editor
    editor_context = {
        "content": blog_post,
        "content_type": "blog post",
        "config": context.get("config", {})
    }
    
    # Apply the editor
    editor_result = await apply_editor(editor_context)
    
    return {
        "edited_blog_post": editor_result["edited_content"],
        "blog_feedback": editor_result["feedback"],
        "metadata": editor_result["metadata"]
    }

async def apply_editor_to_social(context: Dict[str, Any]) -> Dict[str, Any]:
    """Apply editor to social media content"""
    # Get social content from context
    social_content = context.get("social_content")
    if not social_content:
        raise ValueError("No social content provided for editing")
    
    # Create new context for the editor
    editor_context = {
        "content": social_content,
        "content_type": "social media posts",
        "config": context.get("config", {})
    }
    
    # Apply the editor
    editor_result = await apply_editor(editor_context)
    
    return {
        "edited_social_content": editor_result["edited_content"],
        "social_feedback": editor_result["feedback"],
        "metadata": editor_result["metadata"]
    } 