"""
WhisperForge Wisdom Extraction Module

This module handles extracting key insights, wisdom, and actionable takeaways
from transcripts using LLM processing.
"""

import logging
import json
from typing import Dict, Any, List, Optional

# Configure logging
logger = logging.getLogger("whisperforge.pipeline.wisdom")

async def extract_wisdom(context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract key insights and wisdom points from a transcript.
    
    Args:
        context: Dictionary containing:
            - transcript: The transcript text to process
            - config: Step configuration with LLM parameters
            
    Returns:
        Dictionary containing the extracted wisdom notes
    """
    transcript = context.get("transcript")
    if not transcript:
        raise ValueError("No transcript provided for wisdom extraction")
    
    config = context.get("config", {})
    params = config.get("params", {})
    
    # Get AI provider and model from config or use defaults
    provider = params.get("ai_provider", "anthropic")
    model = params.get("ai_model")
    
    # Get knowledge documents if configured
    knowledge_docs = config.get("knowledge_docs", [])
    
    # Construct the prompt
    prompt = construct_wisdom_prompt(transcript, knowledge_docs)
    
    # Generate wisdom notes using the specified provider
    if provider == "anthropic":
        wisdom_notes = await generate_with_anthropic(prompt, model, params)
    elif provider == "openai":
        wisdom_notes = await generate_with_openai(prompt, model, params)
    else:
        raise ValueError(f"Unsupported AI provider: {provider}")
    
    return {
        "wisdom_notes": wisdom_notes,
        "metadata": {
            "provider": provider,
            "model": model,
            "knowledge_docs_used": len(knowledge_docs)
        }
    }

def construct_wisdom_prompt(transcript: str, knowledge_docs: List[str] = None) -> str:
    """
    Construct a prompt for wisdom extraction.
    
    Args:
        transcript: The transcript text to process
        knowledge_docs: Optional list of knowledge documents for context
        
    Returns:
        Formatted prompt for the LLM
    """
    # Base prompt template
    prompt_template = """
    Extract the key insights, wisdom, and actionable takeaways from this transcript.
    Focus on the most valuable, practical, and meaningful points.
    Format as concise bullet points that capture the essence of each insight.
    
    Transcript:
    {transcript}
    
    Key Insights and Wisdom:
    """
    
    # Add knowledge documents if available
    if knowledge_docs and len(knowledge_docs) > 0:
        knowledge_context = "\n\n".join(knowledge_docs)
        prompt_template += """
        
        Reference materials for voice and context:
        {knowledge_context}
        """
        
        return prompt_template.format(
            transcript=transcript,
            knowledge_context=knowledge_context
        )
    else:
        return prompt_template.format(transcript=transcript)

async def generate_with_anthropic(prompt: str, model: Optional[str] = None, params: Dict[str, Any] = None) -> str:
    """
    Generate wisdom notes using Anthropic's Claude API.
    
    Args:
        prompt: The formatted prompt
        model: Specific Claude model to use (or None for default)
        params: Additional parameters for the API call
        
    Returns:
        Generated wisdom notes
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
            model = "claude-3-haiku-20240307"
        
        # Default parameters
        max_tokens = params.get("max_tokens", 2000)
        temperature = params.get("temperature", 0.7)
        
        # System prompt for wisdom extraction
        system_prompt = """
        You extract practical wisdom and key insights from transcripts.
        Focus on actionable takeaways, surprising insights, and memorable quotes.
        Format your response as bullet points for clarity.
        Be concise but comprehensive, capturing the essence of each insight.
        """
        
        logger.info(f"Generating wisdom notes with Anthropic model: {model}")
        
        response = await client.messages.create(
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system_prompt,
            messages=[{"role": "user", "content": prompt}]
        )
        
        wisdom_notes = response.content[0].text
        return wisdom_notes
    
    except Exception as e:
        logger.error(f"Error in Anthropic generation: {str(e)}", exc_info=True)
        raise

async def generate_with_openai(prompt: str, model: Optional[str] = None, params: Dict[str, Any] = None) -> str:
    """
    Generate wisdom notes using OpenAI's API.
    
    Args:
        prompt: The formatted prompt
        model: Specific OpenAI model to use (or None for default)
        params: Additional parameters for the API call
        
    Returns:
        Generated wisdom notes
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
            model = "gpt-4o"
        
        # Default parameters
        max_tokens = params.get("max_tokens", 2000)
        temperature = params.get("temperature", 0.7)
        
        # System prompt for wisdom extraction
        system_prompt = """
        You extract practical wisdom and key insights from transcripts.
        Focus on actionable takeaways, surprising insights, and memorable quotes.
        Format your response as bullet points for clarity.
        Be concise but comprehensive, capturing the essence of each insight.
        """
        
        logger.info(f"Generating wisdom notes with OpenAI model: {model}")
        
        response = await client.chat.completions.create(
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ]
        )
        
        wisdom_notes = response.choices[0].message.content
        return wisdom_notes
    
    except Exception as e:
        logger.error(f"Error in OpenAI generation: {str(e)}", exc_info=True)
        raise 