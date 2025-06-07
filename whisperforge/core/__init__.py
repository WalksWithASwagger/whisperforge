"""
WhisperForge Core Module
========================

A modular content generation pipeline built around audio transcription.
"""

__version__ = "2.0.0"
__author__ = "WhisperForge Team"

from .pipeline import ContentPipeline
from .processors import AudioProcessor, ContentGenerator
from .integrations import NotionExporter, AIProvider
from .config import Config, get_config, set_config

__all__ = [
    "ContentPipeline",
    "AudioProcessor", 
    "ContentGenerator",
    "NotionExporter",
    "AIProvider",
    "Config",
    "get_config",
    "set_config"
] 