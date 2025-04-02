"""
WhisperForge Pipeline

This module orchestrates the content generation pipeline, coordinating the
execution of various steps to produce complete content packages.
"""

import logging
import json
import asyncio
import time
from typing import Dict, Any, List, Optional, Union

# Import specific step modules
from pipeline.steps.wisdom import extract_wisdom
from pipeline.steps.outline import generate_outline
from pipeline.steps.blog import generate_blog_post
from pipeline.steps.social import generate_social_content
from pipeline.steps.editor import apply_editor, apply_editor_to_blog, apply_editor_to_outline, apply_editor_to_social

# Configure logging
logger = logging.getLogger("whisperforge.pipeline")

class ContentPipeline:
    """
    Orchestrates the content generation pipeline with configurable steps.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the pipeline with configuration.
        
        Args:
            config: Pipeline configuration dictionary with step parameters
        """
        self.config = config or {}
        self.steps = self.config.get("steps", [])
        self.context = {}
        self.results = {}
        self.metrics = {
            "pipeline_start_time": None,
            "pipeline_end_time": None,
            "total_duration": None,
            "step_metrics": {}
        }
        
        # Register available pipeline steps
        self.available_steps = {
            "wisdom": extract_wisdom,
            "outline": generate_outline, 
            "blog": generate_blog_post,
            "social": generate_social_content,
            "editor_outline": apply_editor_to_outline,
            "editor_blog": apply_editor_to_blog,
            "editor_social": apply_editor_to_social,
        }
    
    async def run(self, initial_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the pipeline with the configured steps.
        
        Args:
            initial_context: Initial context dictionary with transcript and configuration
            
        Returns:
            Dictionary containing the results of all pipeline steps
        """
        self.context = initial_context.copy()
        self.results = {}
        
        # Record start time
        self.metrics["pipeline_start_time"] = time.time()
        
        try:
            # Run each configured step in sequence
            for step_config in self.steps:
                step_name = step_config.get("name")
                step_enabled = step_config.get("enabled", True)
                
                if not step_enabled:
                    logger.info(f"Skipping disabled step: {step_name}")
                    continue
                
                if step_name not in self.available_steps:
                    logger.warning(f"Unknown step '{step_name}' - skipping")
                    continue
                
                # Get the step function
                step_func = self.available_steps[step_name]
                
                # Add step-specific config to context
                self.context["config"] = step_config
                
                # Record step start time
                step_start_time = time.time()
                
                # Execute the step
                logger.info(f"Executing pipeline step: {step_name}")
                try:
                    step_result = await step_func(self.context)
                    
                    # Update context with step results for next steps
                    self.context.update(step_result)
                    
                    # Store results for final output
                    self.results[step_name] = step_result
                    
                    # Record step metrics
                    step_end_time = time.time()
                    self.metrics["step_metrics"][step_name] = {
                        "start_time": step_start_time,
                        "end_time": step_end_time,
                        "duration": step_end_time - step_start_time
                    }
                    
                    # If step returned its own metrics, include those
                    if "metadata" in step_result:
                        self.metrics["step_metrics"][step_name]["metadata"] = step_result["metadata"]
                    
                    logger.info(f"Completed step: {step_name} in {step_end_time - step_start_time:.2f} seconds")
                    
                except Exception as e:
                    logger.error(f"Error in pipeline step '{step_name}': {str(e)}", exc_info=True)
                    self.metrics["step_metrics"][step_name] = {
                        "start_time": step_start_time,
                        "end_time": time.time(),
                        "error": str(e)
                    }
                    
                    # If this is a critical step that should stop the pipeline on failure
                    if step_config.get("critical", False):
                        logger.error(f"Critical step '{step_name}' failed - stopping pipeline")
                        raise
                    
                    # Otherwise continue with next steps
            
            # Record pipeline completion metrics
            self.metrics["pipeline_end_time"] = time.time()
            self.metrics["total_duration"] = self.metrics["pipeline_end_time"] - self.metrics["pipeline_start_time"]
            
            # Include metrics in results
            self.results["metrics"] = self.metrics
            
            return self.results
            
        except Exception as e:
            logger.error(f"Pipeline execution failed: {str(e)}", exc_info=True)
            
            # Record final metrics even on failure
            self.metrics["pipeline_end_time"] = time.time()
            self.metrics["total_duration"] = self.metrics["pipeline_end_time"] - self.metrics["pipeline_start_time"]
            self.metrics["error"] = str(e)
            
            # Include metrics in results
            self.results["metrics"] = self.metrics
            
            raise
    
    @staticmethod
    def create_default_pipeline() -> 'ContentPipeline':
        """
        Create a pipeline with default configuration.
        
        Returns:
            ContentPipeline instance with standard steps
        """
        config = {
            "steps": [
                {
                    "name": "wisdom",
                    "enabled": True,
                    "critical": True,
                    "params": {
                        "ai_provider": "anthropic",
                        "ai_model": "claude-3-haiku-20240307"
                    }
                },
                {
                    "name": "outline",
                    "enabled": True,
                    "critical": True,
                    "params": {
                        "content_type": "blog",
                        "outline_style": "standard",
                        "ai_provider": "anthropic",
                        "ai_model": "claude-3-haiku-20240307"
                    }
                },
                {
                    "name": "editor_outline",
                    "enabled": True,
                    "critical": False,
                    "params": {
                        "editor_style": "standard",
                        "ai_provider": "anthropic",
                        "ai_model": "claude-3-haiku-20240307"
                    }
                },
                {
                    "name": "blog",
                    "enabled": True,
                    "critical": True,
                    "params": {
                        "blog_style": "standard",
                        "word_count": 800,
                        "ai_provider": "anthropic",
                        "ai_model": "claude-3-opus-20240229"
                    }
                },
                {
                    "name": "editor_blog",
                    "enabled": True,
                    "critical": False,
                    "params": {
                        "editor_style": "standard",
                        "ai_provider": "anthropic",
                        "ai_model": "claude-3-haiku-20240307"
                    }
                },
                {
                    "name": "social",
                    "enabled": True,
                    "critical": False,
                    "params": {
                        "platforms": ["twitter", "linkedin", "facebook"],
                        "post_count": 2,
                        "ai_provider": "anthropic",
                        "ai_model": "claude-3-haiku-20240307"
                    }
                },
                {
                    "name": "editor_social",
                    "enabled": True,
                    "critical": False,
                    "params": {
                        "editor_style": "engagement",
                        "ai_provider": "anthropic",
                        "ai_model": "claude-3-haiku-20240307"
                    }
                }
            ]
        }
        
        return ContentPipeline(config)
    
    @staticmethod
    def create_minimal_pipeline() -> 'ContentPipeline':
        """
        Create a pipeline with minimal steps for faster processing.
        
        Returns:
            ContentPipeline instance with minimal steps
        """
        config = {
            "steps": [
                {
                    "name": "wisdom",
                    "enabled": True,
                    "critical": True,
                    "params": {
                        "ai_provider": "anthropic", 
                        "ai_model": "claude-3-haiku-20240307"
                    }
                },
                {
                    "name": "outline",
                    "enabled": True,
                    "critical": True,
                    "params": {
                        "content_type": "blog",
                        "outline_style": "standard",
                        "ai_provider": "anthropic",
                        "ai_model": "claude-3-haiku-20240307"
                    }
                },
                {
                    "name": "blog",
                    "enabled": True,
                    "critical": True, 
                    "params": {
                        "blog_style": "standard",
                        "word_count": 800,
                        "ai_provider": "anthropic",
                        "ai_model": "claude-3-haiku-20240307"
                    }
                }
            ]
        }
        
        return ContentPipeline(config)
    
    @staticmethod
    def create_social_only_pipeline() -> 'ContentPipeline':
        """
        Create a pipeline focused only on social media content.
        
        Returns:
            ContentPipeline instance for social media generation
        """
        config = {
            "steps": [
                {
                    "name": "wisdom",
                    "enabled": True,
                    "critical": True,
                    "params": {
                        "ai_provider": "anthropic",
                        "ai_model": "claude-3-haiku-20240307"
                    }
                },
                {
                    "name": "social",
                    "enabled": True,
                    "critical": True,
                    "params": {
                        "platforms": ["twitter", "linkedin", "facebook"],
                        "post_count": 3,
                        "ai_provider": "anthropic",
                        "ai_model": "claude-3-haiku-20240307"
                    }
                },
                {
                    "name": "editor_social",
                    "enabled": True,
                    "critical": False,
                    "params": {
                        "editor_style": "engagement",
                        "ai_provider": "anthropic",
                        "ai_model": "claude-3-haiku-20240307"
                    }
                }
            ]
        }
        
        return ContentPipeline(config)

    @staticmethod
    def create_custom_pipeline(steps: List[Dict[str, Any]]) -> 'ContentPipeline':
        """
        Create a pipeline with custom configuration.
        
        Args:
            steps: List of step configurations
            
        Returns:
            ContentPipeline instance with custom steps
        """
        config = {
            "steps": steps
        }
        
        return ContentPipeline(config)

# Convenience function to run a pipeline with default configuration
async def run_default_pipeline(transcript: str, knowledge_docs: List[str] = None) -> Dict[str, Any]:
    """
    Run the default content pipeline on a transcript.
    
    Args:
        transcript: The transcript text
        knowledge_docs: Optional list of knowledge documents for style reference
        
    Returns:
        Dictionary containing the results of all pipeline steps
    """
    pipeline = ContentPipeline.create_default_pipeline()
    
    # Create initial context
    context = {
        "transcript": transcript,
        "knowledge_docs": knowledge_docs or []
    }
    
    # Run the pipeline
    return await pipeline.run(context)

# Convenience function to run a minimal pipeline
async def run_minimal_pipeline(transcript: str, knowledge_docs: List[str] = None) -> Dict[str, Any]:
    """
    Run a minimal content pipeline on a transcript.
    
    Args:
        transcript: The transcript text
        knowledge_docs: Optional list of knowledge documents for style reference
        
    Returns:
        Dictionary containing the results of all pipeline steps
    """
    pipeline = ContentPipeline.create_minimal_pipeline()
    
    # Create initial context
    context = {
        "transcript": transcript,
        "knowledge_docs": knowledge_docs or []
    }
    
    # Run the pipeline
    return await pipeline.run(context)

# Convenience function to run a social-only pipeline
async def run_social_pipeline(transcript: str, knowledge_docs: List[str] = None) -> Dict[str, Any]:
    """
    Run a social media focused pipeline on a transcript.
    
    Args:
        transcript: The transcript text
        knowledge_docs: Optional list of knowledge documents for style reference
        
    Returns:
        Dictionary containing the results of all pipeline steps
    """
    pipeline = ContentPipeline.create_social_only_pipeline()
    
    # Create initial context
    context = {
        "transcript": transcript,
        "knowledge_docs": knowledge_docs or []
    }
    
    # Run the pipeline
    return await pipeline.run(context) 