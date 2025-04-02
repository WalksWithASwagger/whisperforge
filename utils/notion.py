"""
Notion API utility functions for WhisperForge.

This module contains utility functions for working with the Notion API,
including creating blocks, formatting content, and other Notion-specific
operations.
"""

import logging

# Set up logging
logger = logging.getLogger("whisperforge")

def create_summary_callout(summary=None):
    """
    Create a Notion callout block with summary.
    
    Args:
        summary (str, optional): The summary text to include in the callout.
            If None, a default message will be used.
            
    Returns:
        dict: A properly formatted Notion block object with the summary
            as a callout, ready to be used with the Notion API.
    """
    try:
        if not summary:
            return {
                "object": "block",
                "type": "callout",
                "callout": {
                    "rich_text": [{"type": "text", "text": {"content": "No summary available"}}],
                    "icon": {"emoji": "📝"},
                    "color": "gray_background"
                }
            }
        
        return {
            "object": "block",
            "type": "callout",
            "callout": {
                "rich_text": [{"type": "text", "text": {"content": summary}}],
                "icon": {"emoji": "📝"},
                "color": "blue_background"
            }
        }
    except Exception as e:
        logger.error(f"Error creating summary callout: {str(e)}")
        return {
            "object": "block",
            "type": "callout",
            "callout": {
                "rich_text": [{"type": "text", "text": {"content": "Error creating summary"}}],
                "icon": {"emoji": "⚠️"},
                "color": "red_background"
            }
        } 