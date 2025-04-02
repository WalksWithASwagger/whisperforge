"""
WhisperForge Blog Module

This module generates blog content based on outlines, transcripts, and wisdom.
"""

import logging
import json
from typing import Dict, Any, List, Optional, Union

# Configure logging
logger = logging.getLogger("whisperforge.pipeline.blog")

async def generate_blog_post(context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate a blog post based on transcript, wisdom, and outline.
    
    Args:
        context: Dictionary containing:
            - transcript: The transcript text
            - wisdom: Optional wisdom notes extracted from transcript
            - outline: Content outline 
            - config: Step configuration with blog parameters
            
    Returns:
        Dictionary containing the generated blog post and metadata
    """
    transcript = context.get("transcript")
    if not transcript:
        raise ValueError("No transcript provided for blog generation")
    
    outline = context.get("outline")
    if not outline:
        raise ValueError("No outline provided for blog generation")
    
    # Get wisdom notes if available
    wisdom = context.get("wisdom", "")
    
    config = context.get("config", {})
    params = config.get("params", {})
    
    # Get blog style from config
    blog_style = params.get("blog_style", "standard")
    
    # Get word count target from config
    word_count = params.get("word_count", 800)
    
    # Get AI provider and model from config or use defaults
    provider = params.get("ai_provider", "anthropic")
    model = params.get("ai_model")
    
    # Get knowledge documents if available
    knowledge_docs = config.get("knowledge_docs", [])
    
    # Construct the blog prompt
    prompt, system_prompt = construct_blog_prompt(
        transcript=transcript,
        outline=outline,
        wisdom=wisdom,
        blog_style=blog_style,
        word_count=word_count,
        knowledge_docs=knowledge_docs
    )
    
    # Generate blog post using the specified provider
    if provider == "anthropic":
        response = await generate_with_anthropic(prompt, system_prompt, model, params)
    elif provider == "openai":
        response = await generate_with_openai(prompt, system_prompt, model, params)
    else:
        raise ValueError(f"Unsupported AI provider: {provider}")
    
    # Extract title and content from response
    title, content = parse_blog_response(response)
    
    return {
        "blog_post": content,
        "blog_title": title,
        "metadata": {
            "provider": provider,
            "model": model,
            "blog_style": blog_style,
            "target_word_count": word_count,
            "knowledge_docs_used": len(knowledge_docs),
            "actual_word_count": len(content.split())
        }
    }

def construct_blog_prompt(
    transcript: str,
    outline: str,
    wisdom: str = "",
    blog_style: str = "standard",
    word_count: int = 800,
    knowledge_docs: List[str] = None
) -> tuple:
    """
    Construct a prompt for blog generation.
    
    Args:
        transcript: The transcript text
        outline: The content outline
        wisdom: Optional wisdom notes extracted from transcript
        blog_style: Style of blog to generate
        word_count: Target word count for the blog
        knowledge_docs: Optional list of knowledge documents for style matching
        
    Returns:
        Tuple of (user_prompt, system_prompt)
    """
    # Get appropriate blog template
    template = BLOG_TEMPLATES.get(blog_style, BLOG_TEMPLATES["standard"])
    
    # Basic system prompt
    system_prompt = template["system_prompt"]
    
    # User instruction prompt
    instruction_template = template["instruction_template"]
    user_prompt = instruction_template.format(
        transcript=transcript,
        outline=outline,
        wisdom=wisdom if wisdom else "No wisdom notes provided.",
        word_count=word_count
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
    Generate blog content using Anthropic's Claude API.
    
    Args:
        prompt: The formatted prompt
        system_prompt: System instructions for the model
        model: Specific Claude model to use (or None for default)
        params: Additional parameters for the API call
        
    Returns:
        Generated blog post text
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
            model = "claude-3-opus-20240229"  # Use high quality model for long-form content
        
        # Default parameters for high quality blog generation
        max_tokens = params.get("max_tokens", 4000)
        temperature = params.get("temperature", 0.7)
        
        logger.info(f"Generating blog post with Anthropic model: {model}")
        
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
    Generate blog content using OpenAI's API.
    
    Args:
        prompt: The formatted prompt
        system_prompt: System instructions for the model
        model: Specific OpenAI model to use (or None for default)
        params: Additional parameters for the API call
        
    Returns:
        Generated blog post text
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
            model = "gpt-4"  # Use high quality model for long-form content
        
        # Default parameters
        max_tokens = params.get("max_tokens", 4000)
        temperature = params.get("temperature", 0.7)
        
        logger.info(f"Generating blog post with OpenAI model: {model}")
        
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

def parse_blog_response(response: str) -> tuple:
    """
    Parse the blog response to extract title and content.
    
    Args:
        response: Raw response from the LLM
        
    Returns:
        Tuple of (title, content)
    """
    # Default values
    title = "Untitled Blog Post"
    content = response
    
    # Look for common title patterns
    title_patterns = [
        r"^# (.+?)\n",     # Markdown h1
        r"^<h1>(.+?)</h1>", # HTML h1
        r"^Title: (.+?)\n", # Title: prefix
        r"^\"(.+?)\"\n",    # Quoted title
        r"^(.+?)\n={3,}",   # Underlined with ===
    ]
    
    for pattern in title_patterns:
        import re
        match = re.search(pattern, response, re.MULTILINE)
        if match:
            title = match.group(1).strip()
            # Remove the title from content to avoid duplication
            content = re.sub(pattern, "", response, count=1, flags=re.MULTILINE).strip()
            break
    
    return title, content

# Template library for different blog styles
BLOG_TEMPLATES = {
    "standard": {
        "name": "Standard Blog Post",
        "system_prompt": """You are an expert content creator who writes engaging, authoritative blog posts.
Your writing should be clear, well-structured, and engaging to readers.
Focus on creating content that is valuable, conversational yet professional, and optimized for digital reading.""",

        "instruction_template": """Write a complete blog post based on the provided outline, transcript, and wisdom notes.

The blog post should:
1. Include a compelling title and introduction
2. Follow the outline structure
3. Incorporate key insights from the wisdom notes
4. Maintain a conversational yet authoritative tone
5. Be approximately {word_count} words in length
6. Include a strong conclusion with takeaways or next steps

Your goal is to create a valuable, engaging blog post that serves the reader's needs.

OUTLINE:
{outline}

TRANSCRIPT:
{transcript}

WISDOM NOTES:
{wisdom}
"""
    },
    
    "conversational": {
        "name": "Conversational Blog Post",
        "system_prompt": """You are an expert content creator who writes in a warm, conversational style.
Your writing should feel like a friendly conversation with readers, using a personal tone.
Focus on creating content that connects emotionally while delivering value.""",

        "instruction_template": """Write a conversational blog post based on the provided outline, transcript, and wisdom notes.

The blog post should:
1. Include a personal, engaging title and introduction
2. Follow the outline structure but feel like a conversation
3. Incorporate personal perspectives on the wisdom notes
4. Use first and second person liberally (I, we, you)
5. Include relatable examples or analogies
6. Be approximately {word_count} words in length
7. End with a friendly conclusion and invitation for reader engagement

Your goal is to create content that feels like advice from a trusted friend.

OUTLINE:
{outline}

TRANSCRIPT:
{transcript}

WISDOM NOTES:
{wisdom}
"""
    },
    
    "educational": {
        "name": "Educational Blog Post",
        "system_prompt": """You are an expert educator who writes clear, instructional blog content.
Your writing should prioritize clear explanations, logical structure, and educational value.
Focus on helping readers truly understand concepts through examples, explanations, and structured learning.""",

        "instruction_template": """Write an educational blog post based on the provided outline, transcript, and wisdom notes.

The blog post should:
1. Include a clear, benefit-focused title and introduction
2. Follow the outline structure with an educational approach
3. Define key terms and concepts
4. Provide practical examples that illustrate the concepts
5. Use an organized, logical progression of ideas
6. Be approximately {word_count} words in length
7. Include summary points or a review section at the end

Your goal is to help readers genuinely learn and apply the information.

OUTLINE:
{outline}

TRANSCRIPT:
{transcript}

WISDOM NOTES:
{wisdom}
"""
    },
    
    "storytelling": {
        "name": "Storytelling Blog Post",
        "system_prompt": """You are an expert storyteller who weaves narratives into blog content.
Your writing should use story elements (characters, conflict, resolution) to engage readers.
Focus on creating an emotional connection while still delivering valuable information.""",

        "instruction_template": """Write a story-driven blog post based on the provided outline, transcript, and wisdom notes.

The blog post should:
1. Include a captivating, narrative-focused title and opening hook
2. Follow the outline structure but within a story framework
3. Incorporate narrative elements (characters, situations, transformation)
4. Use descriptive language to create vivid imagery
5. Connect the story elements to the key wisdom points
6. Be approximately {word_count} words in length
7. End with a resolution and key takeaways

Your goal is to engage readers emotionally through story while delivering value.

OUTLINE:
{outline}

TRANSCRIPT:
{transcript}

WISDOM NOTES:
{wisdom}
"""
    },
    
    "analytical": {
        "name": "Analytical Blog Post",
        "system_prompt": """You are an expert analyst who writes insightful, data-informed blog content.
Your writing should emphasize critical thinking, evidence, and logical analysis.
Focus on helping readers understand complex topics through careful examination and substantiated points.""",

        "instruction_template": """Write an analytical blog post based on the provided outline, transcript, and wisdom notes.

The blog post should:
1. Include a precise, insight-focused title and introduction
2. Follow the outline structure with analytical depth
3. Examine key points with critical thinking and evidence
4. Consider multiple perspectives or interpretations of data
5. Use clear reasoning to support conclusions
6. Be approximately {word_count} words in length
7. End with substantiated conclusions and implications

Your goal is to help readers think more deeply about the topic through reasoned analysis.

OUTLINE:
{outline}

TRANSCRIPT:
{transcript}

WISDOM NOTES:
{wisdom}
"""
    },
    
    "persuasive": {
        "name": "Persuasive Blog Post",
        "system_prompt": """You are an expert persuasive writer who creates convincing, influential blog content.
Your writing should build compelling arguments toward a specific position or call to action.
Focus on logical progression, emotional appeals, and credibility to persuade readers.""",

        "instruction_template": """Write a persuasive blog post based on the provided outline, transcript, and wisdom notes.

The blog post should:
1. Include a compelling, position-oriented title and introduction
2. Follow the outline structure with persuasive elements
3. Build a logical case for your position
4. Address potential objections or counter-arguments
5. Use both emotional and logical appeals appropriately
6. Be approximately {word_count} words in length
7. End with a strong call to action

Your goal is to convince readers to adopt a perspective or take specific action.

OUTLINE:
{outline}

TRANSCRIPT:
{transcript}

WISDOM NOTES:
{wisdom}
"""
    }
} 