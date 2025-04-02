"""
This module handles generating content outlines based on transcripts and wisdom.
"""

import time
import logging
import streamlit as st

# Import from config
from config import logger
# Import from integrations
from integrations.openai_service import get_openai_client
from integrations.anthropic_service import get_anthropic_client, stream_anthropic_completion
from integrations.grok_service import get_grok_api_key
# Import from utils
from utils.prompts import DEFAULT_PROMPTS

def generate_outline(transcript, wisdom, ai_provider, model, custom_prompt=None, knowledge_base=None):
    """
    Create a structured outline based on transcript and wisdom with streaming output.
    
    Args:
        transcript (str): The transcript text
        wisdom (str): Extracted wisdom text
        ai_provider (str): AI provider to use ('OpenAI', 'Anthropic', 'Grok')
        model (str): Model to use
        custom_prompt (str): Custom prompt template
        knowledge_base (dict): Knowledge base content for additional context
        
    Returns:
        str: Generated outline text
    """
    # Start timing for usage tracking
    start_time = time.time()
    
    # Create a placeholder for streaming output
    stream_container = st.empty()
    stream_content = ""
    
    try:
        prompt = custom_prompt or DEFAULT_PROMPTS["outline_creation"]
        
        # Include knowledge base context if available
        if knowledge_base:
            knowledge_context = "\n\n".join([
                f"## {name}\n{content}" 
                for name, content in knowledge_base.items()
            ])
            system_prompt = f"""Use the following knowledge base to inform your analysis:

{knowledge_context}

When creating the outline, please incorporate these perspectives and guidelines.

Original Prompt:
{prompt}"""
        else:
            system_prompt = prompt
        
        # Combine transcript and wisdom for better context
        content = f"TRANSCRIPT:\n{transcript}\n\nWISDOM:\n{wisdom}"
        
        # Display initial message
        stream_container.markdown("Creating outline...")
        
        # Use the selected AI provider and model
        if ai_provider == "OpenAI":
            openai_client = get_openai_client()
            if not openai_client:
                return "Error: OpenAI API key is not configured."
                
            # Stream response from OpenAI
            response = openai_client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": content}
                ],
                max_tokens=1500,
                stream=True
            )
            
            result = ""
            # Process the streaming response
            for chunk in response:
                if hasattr(chunk.choices[0].delta, "content") and chunk.choices[0].delta.content is not None:
                    content_chunk = chunk.choices[0].delta.content
                    result += content_chunk
                    stream_content += content_chunk
                    # Update the stream display
                    stream_container.markdown(stream_content)
            
        elif ai_provider == "Anthropic":
            anthropic_client = get_anthropic_client()
            if not anthropic_client:
                return "Error: Anthropic API key is not configured."
                
            # Stream response from Anthropic
            with anthropic_client.messages.stream(
                model=model,
                max_tokens=1500,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": content}
                ]
            ) as stream:
                result = ""
                for text in stream.text_stream:
                    result += text
                    stream_content += text
                    # Update the stream display
                    stream_container.markdown(stream_content)
            
        elif ai_provider == "Grok":
            grok_api_key = get_grok_api_key()
            if not grok_api_key:
                return "Error: Grok API key is not configured."
                
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
            
            # Show a progress indicator
            with st.spinner("Creating outline with Grok (this may take a moment)..."):
                response = requests.post(
                    "https://api.grok.x.ai/v1/chat/completions",
                    headers=headers,
                    json=payload
                )
                result = response.json()["choices"][0]["message"]["content"]
                # Display the complete result
                stream_container.markdown(result)
        
        # Clear the streaming container when done
        stream_container.empty()
        
        # Update usage tracking
        end_time = time.time()
        duration = end_time - start_time
        # This would typically call a function to update usage tracking
        # update_usage_tracking(duration)
        
        return result
        
    except Exception as e:
        logger.exception("Error in outline creation:")
        stream_container.error(f"Error: {str(e)}")
        return f"Error creating outline: {str(e)}" 