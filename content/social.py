"""
This module handles generating social media content based on transcripts and wisdom.
"""

import time
import logging
import streamlit as st
import json

# Import from config
from config import logger
# Import from integrations
from integrations.openai_service import get_openai_client
from integrations.anthropic_service import get_anthropic_client
from integrations.grok_service import get_grok_api_key
# Import from utils
from utils.prompts import DEFAULT_PROMPTS

def generate_social_content(transcript, wisdom, outline, platforms, ai_provider, model, custom_prompt=None, knowledge_base=None):
    """
    Generate social media content based on transcript, wisdom and outline.
    
    Args:
        transcript (str): Transcript text
        wisdom (str): Extracted wisdom text
        outline (str): Content outline
        platforms (list): List of social media platforms to generate content for
        ai_provider (str): AI provider to use ('OpenAI', 'Anthropic', 'Grok')
        model (str): Model to use
        custom_prompt (str): Custom prompt template
        knowledge_base (dict): Knowledge base content for additional context
        
    Returns:
        dict: Generated social media content by platform
    """
    try:
        # Format list of platforms for the prompt
        platforms_str = ", ".join(platforms)
        
        prompt = custom_prompt or DEFAULT_PROMPTS["social_media"]
        prompt = prompt.replace("{PLATFORMS}", platforms_str)
        
        # Include knowledge base context if available
        if knowledge_base:
            knowledge_context = "\n\n".join([
                f"## {name}\n{content}" 
                for name, content in knowledge_base.items()
            ])
            system_prompt = f"""Use the following knowledge base to inform your social media content:

{knowledge_context}

Original Prompt:
{prompt}"""
        else:
            system_prompt = prompt
        
        # Combine content for context
        content_text = f"TRANSCRIPT:\n{transcript}\n\nWISDOM:\n{wisdom}\n\nOUTLINE:\n{outline}\n\nPLATFORMS: {platforms_str}"
        
        # Create a placeholder for streaming output
        output_placeholder = st.empty()
        full_response = ""
        start_time = time.time()
        
        if ai_provider == "OpenAI":
            openai_client = get_openai_client()
            if not openai_client:
                st.error("OpenAI API key is not configured.")
                return None

            response_stream = openai_client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": content_text}
                ],
                max_tokens=2000,
                stream=True
            )
            
            for chunk in response_stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    content_chunk = chunk.choices[0].delta.content
                    full_response += content_chunk
                    output_placeholder.markdown(full_response)
                    
            logger.info(f"Generated social media content with OpenAI in {time.time() - start_time:.2f} seconds")
            
        elif ai_provider == "Anthropic":
            anthropic_client = get_anthropic_client()
            if not anthropic_client:
                st.error("Anthropic API key is not configured.")
                return None

            with anthropic_client.messages.stream(
                model=model,
                max_tokens=2000,
                system=system_prompt,
                messages=[{"role": "user", "content": content_text}]
            ) as stream:
                for text in stream.text_stream:
                    full_response += text
                    output_placeholder.markdown(full_response)
                    
            logger.info(f"Generated social media content with Anthropic in {time.time() - start_time:.2f} seconds")
            
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
                    {"role": "user", "content": content_text}
                ],
                "max_tokens": 2000
            }
            
            # Grok doesn't support streaming in the API yet, so show a progress message
            output_placeholder.markdown("Generating social media content with Grok...")
            
            response = requests.post(
                "https://api.grok.x.ai/v1/chat/completions",
                headers=headers,
                json=payload
            )
            
            full_response = response.json()["choices"][0]["message"]["content"]
            output_placeholder.markdown(full_response)
            
            logger.info(f"Generated social media content with Grok in {time.time() - start_time:.2f} seconds")
        
        # Parse the response to extract content by platform
        # The expected format is platform-specific sections separated by Markdown headers
        social_content = {}
        
        # Split by Markdown headers (## Platform Name)
        sections = full_response.split('##')
        
        for section in sections:
            if not section.strip():
                continue
                
            # Get the platform name from the first line
            lines = section.strip().split('\n')
            platform_name = lines[0].strip()
            
            # Join the rest of the lines as the content
            platform_content = '\n'.join(lines[1:]).strip()
            
            # Add to the dictionary
            social_content[platform_name] = platform_content
        
        return social_content
        
    except Exception as e:
        logger.exception(f"Error generating social media content with {ai_provider} {model}: {str(e)}")
        st.error(f"Error generating social media content with {ai_provider} {model}: {str(e)}")
        return None 