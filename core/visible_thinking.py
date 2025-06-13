"""
Minimal Visible Thinking Module for WhisperForge
Provides stub functions to prevent import errors in streaming pipeline
"""

import logging

import streamlit as st

logger = logging.getLogger(__name__)

def thinking_step_start(step_name: str, context: str = ""):
    """Start a thinking step - minimal implementation"""
    logger.info(f"Starting step: {step_name}")
    # Could add visual indicators here in the future
    pass

def thinking_step_complete(step_name: str, result_info: str = ""):
    """Complete a thinking step - minimal implementation"""
    logger.info(f"Completed step: {step_name}")
    # Could add completion indicators here in the future
    pass

def thinking_error(step_name: str, error_msg: str):
    """Handle thinking step error - minimal implementation"""
    logger.error(f"Error in step {step_name}: {error_msg}")
    # Could add error indicators here in the future
    pass

def render_thinking_stream():
    """Render thinking stream - minimal implementation"""
    # This function is imported but not used in current implementation
    # Could add visual thinking display here in the future
    pass 