import logging
import time
import streamlit as st

# Import from config
from config import logger
# Import from integrations
from integrations.openai_service import get_openai_client, generate_completion

def generate_wisdom(transcript, ai_provider="openai", model="gpt-4", custom_prompt=None, knowledge_base=None):
    """
    Extract key insights and wisdom from a transcript.
    
    Args:
        transcript (str): The transcript text
        ai_provider (str): AI provider to use ('openai', 'anthropic', etc.)
        model (str): Model to use
        custom_prompt (str): Custom prompt template
        knowledge_base (str): Knowledge base content for additional context
        
    Returns:
        str: Generated wisdom text
    """
    logger.info(f"Generating wisdom using {ai_provider} with model {model}")
    
    # Create progress indicators
    progress_placeholder = st.empty()
    progress_bar = progress_placeholder.progress(0)
    status_text = st.empty()
    
    def update_status(message, progress):
        """Update the status display"""
        status_text.text(message)
        progress_bar.progress(progress)
    
    try:
        update_status("Preparing wisdom extraction...", 0.1)
        
        # Determine the prompt to use
        if custom_prompt:
            # Replace variables in the custom prompt
            prompt = custom_prompt.replace("{transcript}", transcript)
            if knowledge_base:
                prompt = prompt.replace("{knowledge_base}", knowledge_base)
            else:
                prompt = prompt.replace("{knowledge_base}", "No knowledge base provided.")
        else:
            # Default prompt
            prompt = f"""
            I want you to extract the key insights, wisdom, and actionable advice from the following transcript.
            Focus on the most valuable and transformative ideas.
            
            Format your response in clear, concise bullet points that are easy to read and understand.
            Group related insights together under appropriate headings.
            
            Transcript:
            {transcript}
            """
            
            # Add knowledge base if provided
            if knowledge_base:
                prompt += f"""
                
                Additional context from knowledge base:
                {knowledge_base}
                
                Please incorporate this context when appropriate, but focus primarily on the transcript content.
                """
        
        update_status("Processing content...", 0.3)
        
        # Generate content based on the selected AI provider
        if ai_provider == "openai":
            # Use OpenAI
            response = generate_openai_wisdom(prompt, model)
        elif ai_provider == "anthropic":
            # Use Anthropic
            from integrations.anthropic_service import generate_anthropic_completion
            response = generate_anthropic_completion(prompt, model)
        elif ai_provider == "grok":
            # Use Grok
            from integrations.grok_service import generate_grok_completion
            response = generate_grok_completion(prompt)
        else:
            # Default to OpenAI
            response = generate_openai_wisdom(prompt, model)
        
        update_status("Formatting response...", 0.9)
        
        # Remove progress indicators
        time.sleep(0.5)
        progress_placeholder.empty()
        progress_bar.empty()
        status_text.empty()
        
        return response
    
    except Exception as e:
        logger.exception(f"Error generating wisdom: {str(e)}")
        
        # Remove progress indicators
        progress_placeholder.empty()
        progress_bar.empty()
        status_text.empty()
        
        return f"Error generating wisdom: {str(e)}"

def generate_openai_wisdom(prompt, model="gpt-4"):
    """
    Generate wisdom using OpenAI.
    
    Args:
        prompt (str): The prompt text
        model (str): OpenAI model to use
        
    Returns:
        str: Generated wisdom text
    """
    client = get_openai_client()
    if not client:
        return "Error: Could not initialize OpenAI client."
    
    try:
        # Use the general completion function from openai_service
        return generate_completion(prompt, model=model, temperature=0.7, max_tokens=2000)
    except Exception as e:
        logger.error(f"Error in OpenAI wisdom generation: {str(e)}")
        return f"Error generating wisdom with OpenAI: {str(e)}" 