"""
WhisperForge Core Module
========================

A modular content generation pipeline built around audio transcription.
"""

__version__ = "2.0.0"
__author__ = "WhisperForge Team"

# Core modules - some legacy imports removed for cleanup
from .config import Config, get_config, set_config

__all__ = [
    "Config",
    "get_config", 
    "set_config"
] 