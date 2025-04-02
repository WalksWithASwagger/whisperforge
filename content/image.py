"""
This module handles generating image prompts based on content.
"""

import logging
import streamlit as st

# Import from config
from config import logger
# Import from integrations
from integrations.openai_service import get_openai_client
from integrations.anthropic_service import get_anthropic_client
from integrations.grok_service import get_grok_api_key
# Import from utils
from utils.prompts import DEFAULT_PROMPTS

def generate_image_prompts(wisdom, outline, ai_provider, model, custom_prompt=None, knowledge_base=None):
    """
    Create descriptive image prompts based on wisdom and outline.
    
    Args:
        wisdom (str): Extracted wisdom text
        outline (str): Content outline text
        ai_provider (str): AI provider to use ('OpenAI', 'Anthropic', 'Grok')
        model (str): Model to use
        custom_prompt (str): Custom prompt template
        knowledge_base (dict): Knowledge base content for additional context
        
    Returns:
        str: Generated image prompts text
    """
    try:
        prompt = custom_prompt or DEFAULT_PROMPTS["image_prompts"]
        
        # Include knowledge base context if available
        if knowledge_base:
            knowledge_context = "\n\n".join([
                f"## {name}\n{content}" 
                for name, content in knowledge_base.items()
            ])
            system_prompt = f"""Use the following knowledge base to inform your image prompts:

{knowledge_context}

Original Prompt:
{prompt}"""
        else:
            system_prompt = prompt
        
        # Combine content for context
        content = f"WISDOM:\n{wisdom}\n\nOUTLINE:\n{outline}"
        
        if ai_provider == "OpenAI":
            openai_client = get_openai_client()
            if not openai_client:
                st.error("OpenAI API key is not configured.")
                return None

            response = openai_client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": content}
                ],
                max_tokens=1000
            )
            return response.choices[0].message.content
            
        elif ai_provider == "Anthropic":
            anthropic_client = get_anthropic_client()
            if not anthropic_client:
                st.error("Anthropic API key is not configured.")
                return None

            response = anthropic_client.messages.create(
                model=model,
                max_tokens=1000,
                system=system_prompt,
                messages=[{"role": "user", "content": content}]
            )
            return response.content[0].text
            
        elif ai_provider == "Grok":
            grok_api_key = get_grok_api_key()
            if not grok_api_key:
                st.error("Grok API key is not configured.")
                return None

            import requests
            headers = {
                "Authorization": f"Bearer {grok_api_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": content}
                ]
            }
            response = requests.post(
                "https://api.grok.x.ai/v1/chat/completions",
                headers=headers,
                json=payload
            )
            return response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        logger.exception(f"Error generating image prompts with {ai_provider} {model}: {str(e)}")
        st.error(f"Error generating image prompts with {ai_provider} {model}: {str(e)}")
        return None 