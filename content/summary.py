"""
This module handles generating concise summaries of content.
"""

import time
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

def generate_summary(content, content_type, ai_provider, model, custom_prompt=None, knowledge_base=None):
    """
    Generate a concise summary of the provided content.
    
    Args:
        content (str): Content to summarize (transcript, wisdom, blog post, etc.)
        content_type (str): Type of content being summarized ('transcript', 'wisdom', 'blog', etc.)
        ai_provider (str): AI provider to use ('OpenAI', 'Anthropic', 'Grok')
        model (str): Model to use
        custom_prompt (str): Custom prompt template
        knowledge_base (dict): Knowledge base content for additional context
        
    Returns:
        str: Generated summary text
    """
    try:
        prompt = custom_prompt or DEFAULT_PROMPTS["summary"]
        
        # Include knowledge base context if available
        if knowledge_base:
            knowledge_context = "\n\n".join([
                f"## {name}\n{content}" 
                for name, content in knowledge_base.items()
            ])
            system_prompt = f"""Use the following knowledge base to inform your summary:

{knowledge_context}

Original Prompt:
{prompt}"""
        else:
            system_prompt = prompt
        
        # Create a placeholder for streaming output
        output_placeholder = st.empty()
        full_response = ""
        start_time = time.time()
        
        # Create a user message that includes the content type
        user_content = f"This is a {content_type}:\n\n{content}"
        
        if ai_provider == "OpenAI":
            openai_client = get_openai_client()
            if not openai_client:
                st.error("OpenAI API key is not configured.")
                return None

            response_stream = openai_client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content}
                ],
                max_tokens=500,
                stream=True
            )
            
            for chunk in response_stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    content_chunk = chunk.choices[0].delta.content
                    full_response += content_chunk
                    output_placeholder.markdown(full_response)
                    
            logger.info(f"Generated summary with OpenAI in {time.time() - start_time:.2f} seconds")
            
        elif ai_provider == "Anthropic":
            anthropic_client = get_anthropic_client()
            if not anthropic_client:
                st.error("Anthropic API key is not configured.")
                return None

            with anthropic_client.messages.stream(
                model=model,
                max_tokens=500,
                system=system_prompt,
                messages=[{"role": "user", "content": user_content}]
            ) as stream:
                for text in stream.text_stream:
                    full_response += text
                    output_placeholder.markdown(full_response)
                    
            logger.info(f"Generated summary with Anthropic in {time.time() - start_time:.2f} seconds")
            
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
                    {"role": "user", "content": user_content}
                ],
                "max_tokens": 500
            }
            
            # Grok doesn't support streaming in the API yet, so show a progress message
            output_placeholder.markdown("Generating summary with Grok...")
            
            response = requests.post(
                "https://api.grok.x.ai/v1/chat/completions",
                headers=headers,
                json=payload
            )
            
            full_response = response.json()["choices"][0]["message"]["content"]
            output_placeholder.markdown(full_response)
            
            logger.info(f"Generated summary with Grok in {time.time() - start_time:.2f} seconds")
            
        return full_response
        
    except Exception as e:
        logger.exception(f"Error generating summary with {ai_provider} {model}: {str(e)}")
        st.error(f"Error generating summary with {ai_provider} {model}: {str(e)}")
        return None 