"""
Text processing utility functions for WhisperForge
"""

import re
import logging
from config import logger
import streamlit as st

def generate_title(transcript):
    """
    Generate a descriptive 5-7 word title based on the transcript
    
    Args:
        transcript (str): Text transcript to generate title from
        
    Returns:
        str: Generated title
    """
    # Ensure we have some text to work with
    if not transcript or len(transcript.strip()) < 10:
        return "Untitled Audio Recording"
    
    # Extract the first few hundred characters for analysis
    sample = transcript[:500].strip()
    
    # Try to find standalone sentences for consideration as titles
    sentences = re.split(r'[.!?]\s+', sample)
    
    for sentence in sentences:
        # Clean up the sentence
        candidate = sentence.strip()
        
        # Skip if too short
        if len(candidate.split()) < 3:
            continue
            
        # Title case and truncate to 5-7 words
        words = candidate.split()
        if len(words) > 7:
            title = ' '.join(words[:7])
        else:
            title = ' '.join(words)
            
        return title.title()
    
    # If no good sentence was found, just use the first few words
    words = sample.split()
    title = ' '.join(words[:7])
    return title.title()

def generate_summary(transcript):
    """
    Generate a brief summary of the transcript
    
    Args:
        transcript (str): Text transcript to summarize
        
    Returns:
        str: Generated summary
    """
    # Import individually on demand to avoid circular imports
    from content import generate_summary as content_generate_summary
    
    return content_generate_summary(transcript, "summary", "openai", "gpt-4", None, None)

def generate_short_title(text):
    """
    Generate a very concise 2-4 word title
    
    Args:
        text (str): Text to generate title from
        
    Returns:
        str: Short title
    """
    # Ensure we have some text to work with
    if not text or len(text.strip()) < 10:
        return "Audio Recording"
    
    try:
        # Get API client
        from integrations.openai_service import get_openai_client
        client = get_openai_client()
        
        if not client:
            logger.error("Failed to get OpenAI client for title generation")
            return generate_title(text)[:20]  # Fallback to basic title gen
        
        # Create prompt for title generation
        prompt = f"""
        Based on the following content, create a concise 2-4 word title that captures its essence.
        Make it catchy and memorable. Respond with ONLY the title, nothing else.
        
        Content: {text[:1000]}
        """
        
        # Use the client to generate the title
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that creates short, concise titles."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=10,
            temperature=0.7
        )
        
        # Extract and clean up the title
        short_title = response.choices[0].message.content.strip()
        
        # Remove quotes if present
        short_title = short_title.strip('"\'')
        
        return short_title
    
    except Exception as e:
        logger.error(f"Error generating short title: {str(e)}")
        return generate_title(text)[:20]  # Fallback to basic title gen

def chunk_text_for_notion(text, chunk_size=1900):
    """
    Split text into chunks for Notion API (which has a 2000 character limit per block)
    
    Args:
        text (str): Text to chunk
        chunk_size (int): Maximum size of each chunk
        
    Returns:
        list: List of text chunks
    """
    # Return empty list for empty text
    if not text or len(text.strip()) == 0:
        return []
    
    # Split by paragraphs first
    paragraphs = text.split('\n\n')
    chunks = []
    current_chunk = ""
    
    for paragraph in paragraphs:
        # If paragraph itself exceeds chunk size, split it further
        if len(paragraph) > chunk_size:
            # Process the long paragraph sentence by sentence
            sentences = re.split(r'(?<=[.!?])\s+', paragraph)
            for sentence in sentences:
                if len(current_chunk) + len(sentence) + 2 <= chunk_size:
                    if current_chunk:
                        current_chunk += " " + sentence
                    else:
                        current_chunk = sentence
                else:
                    chunks.append(current_chunk)
                    current_chunk = sentence
        else:
            # Check if adding this paragraph would exceed chunk size
            if len(current_chunk) + len(paragraph) + 2 <= chunk_size:
                if current_chunk:
                    current_chunk += "\n\n" + paragraph
                else:
                    current_chunk = paragraph
            else:
                chunks.append(current_chunk)
                current_chunk = paragraph
    
    # Add the last chunk if it's not empty
    if current_chunk:
        chunks.append(current_chunk)
    
    return chunks

def generate_content_tags(transcript, wisdom=None):
    """
    Generate content tags/keywords based on transcript and wisdom
    
    Args:
        transcript (str): Text transcript
        wisdom (str): Extracted wisdom text
        
    Returns:
        list: List of content tags/keywords
    """
    # Use just transcript if no wisdom provided
    content = wisdom if wisdom else transcript
    
    # Ensure we have content to analyze
    if not content or len(content.strip()) < 10:
        return ["audio", "recording", "transcript"]
    
    try:
        # Get API client
        from integrations.openai_service import get_openai_client
        client = get_openai_client()
        
        if not client:
            logger.error("Failed to get OpenAI client for tag generation")
            # Return some default tags based on the title
            title = generate_title(transcript)
            return [word.lower() for word in title.split()[:3]]
        
        # Create prompt for tag generation
        prompt = f"""
        Based on the following content, generate 3-7 relevant tags/keywords.
        Each tag should be a single word or short phrase (max 2-3 words).
        Respond with ONLY a comma-separated list of tags, nothing else.
        
        Content: {content[:1500]}
        """
        
        # Use the client to generate the tags
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that creates content tags."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=50,
            temperature=0.5
        )
        
        # Extract and clean up the tags
        tags_text = response.choices[0].message.content.strip()
        
        # Split by commas and clean up each tag
        tags = [tag.strip().lower() for tag in tags_text.split(',')]
        
        # Filter out empty or invalid tags
        tags = [tag for tag in tags if tag and len(tag) > 1]
        
        return tags
    
    except Exception as e:
        logger.error(f"Error generating content tags: {str(e)}")
        # Return some default tags based on the title
        title = generate_title(transcript)
        return [word.lower() for word in title.split()[:3]] 