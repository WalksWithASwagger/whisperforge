"""
WhisperForge Pipeline Orchestrator

This module provides the core pipeline orchestration functionality for WhisperForge.
It implements a flexible, modular pipeline system for processing content through
various transformation steps.
"""

import time
import asyncio
import logging
import uuid
import json
from typing import Dict, List, Any, Optional, Callable, Union, TypedDict

# Configure logging
logger = logging.getLogger("whisperforge.pipeline")

class StepStatus:
    """Status constants for pipeline steps"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"

class StepConfig(TypedDict, total=False):
    """Configuration for a pipeline step"""
    enabled: bool
    params: Dict[str, Any]
    knowledge_docs: List[str]
    retry_attempts: int
    timeout: int

class PipelineStep:
    """Represents a single step in the content pipeline"""
    
    def __init__(
        self, 
        name: str, 
        function: Callable,
        required_inputs: Optional[List[str]] = None,
        produces_outputs: Optional[List[str]] = None,
        config: Optional[StepConfig] = None
    ):
        self.id = str(uuid.uuid4())
        self.name = name
        self.function = function
        self.required_inputs = required_inputs or []
        self.produces_outputs = produces_outputs or []
        self.config = config or {"enabled": True, "params": {}, "knowledge_docs": [], "retry_attempts": 1, "timeout": 300}
        self.status = StepStatus.PENDING
        self.start_time = None
        self.end_time = None
        self.error = None
        self.result = {}
        
    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute this step with the given context data"""
        if not self.config.get("enabled", True):
            self.status = StepStatus.SKIPPED
            logger.info(f"Skipping disabled step: {self.name}")
            return {}
            
        self.status = StepStatus.RUNNING
        self.start_time = time.time()
        retry_count = 0
        max_retries = self.config.get("retry_attempts", 1)
        
        try:
            # Check that all required inputs are available
            for input_key in self.required_inputs:
                if input_key not in context:
                    raise ValueError(f"Required input '{input_key}' not available for step '{self.name}'")
            
            # Create a local context with just the inputs this step needs
            # along with any configuration parameters
            step_context = {
                key: context[key] for key in self.required_inputs if key in context
            }
            step_context["config"] = self.config
            
            # Execute the function with relevant context data, with retry logic
            while retry_count < max_retries:
                try:
                    result = await self.function(step_context)
                    break
                except Exception as e:
                    retry_count += 1
                    if retry_count >= max_retries:
                        raise
                    logger.warning(f"Retry {retry_count}/{max_retries} for step '{self.name}' due to: {str(e)}")
                    await asyncio.sleep(1)  # Brief pause before retry
            
            # Update context with produced outputs
            self.result = result
            for output_key in self.produces_outputs:
                if output_key not in result:
                    logger.warning(f"Expected output '{output_key}' not produced by step '{self.name}'")
                    
            self.status = StepStatus.COMPLETED
            return result
        except Exception as e:
            self.status = StepStatus.FAILED
            self.error = str(e)
            logger.error(f"Error in pipeline step '{self.name}': {str(e)}", exc_info=True)
            raise
        finally:
            self.end_time = time.time()
            self.duration = self.end_time - self.start_time if self.start_time else 0
            
    def to_dict(self) -> Dict[str, Any]:
        """Convert step to dictionary for serialization"""
        return {
            "id": self.id,
            "name": self.name,
            "required_inputs": self.required_inputs,
            "produces_outputs": self.produces_outputs,
            "config": self.config,
            "status": self.status,
            "duration": self.end_time - self.start_time if self.start_time and self.end_time else None,
            "error": self.error,
        }

class ContentPipeline:
    """Orchestrates the execution of content processing steps"""
    
    def __init__(self, steps: Optional[List[PipelineStep]] = None, name: str = "Default Pipeline"):
        self.id = str(uuid.uuid4())
        self.name = name
        self.steps = steps or []
        self.context = {}
        self.results = {}
        self.status = StepStatus.PENDING
        self.start_time = None
        self.end_time = None
        self.error = None
        
    def add_step(self, step: PipelineStep) -> None:
        """Add a step to the pipeline"""
        self.steps.append(step)
        
    def get_step_by_name(self, name: str) -> Optional[PipelineStep]:
        """Get a step by name"""
        for step in self.steps:
            if step.name == name:
                return step
        return None
        
    def update_step_config(self, step_id: str, config: Dict[str, Any]) -> bool:
        """Update the configuration for a step"""
        for step in self.steps:
            if step.id == step_id:
                step.config.update(config)
                return True
        return False
    
    async def run(self, input_data: Dict[str, Any], skip_steps: Optional[List[str]] = None) -> Dict[str, Any]:
        """Execute the pipeline with the given input data"""
        self.context = input_data.copy()
        self.status = StepStatus.RUNNING
        self.start_time = time.time()
        results = {}
        
        skip_steps = skip_steps or []
        
        try:
            for step in self.steps:
                if step.name in skip_steps:
                    logger.info(f"Skipping pipeline step: {step.name}")
                    step.status = StepStatus.SKIPPED
                    continue
                    
                logger.info(f"Executing pipeline step: {step.name}")
                try:
                    step_result = await step.execute(self.context)
                    
                    # Add the results to the pipeline context for next steps
                    for key, value in step_result.items():
                        self.context[key] = value
                    
                    results[step.name] = {
                        "status": step.status,
                        "duration": step.duration,
                        "error": step.error,
                        **step_result
                    }
                    
                except Exception as e:
                    logger.error(f"Step '{step.name}' failed: {str(e)}")
                    results[step.name] = {
                        "status": StepStatus.FAILED,
                        "error": str(e)
                    }
                    
                    # Break pipeline if a step fails
                    if step.config.get("fail_pipeline_on_error", True):
                        self.status = StepStatus.FAILED
                        self.error = f"Pipeline failed at step '{step.name}': {str(e)}"
                        break
            
            if self.status != StepStatus.FAILED:
                self.status = StepStatus.COMPLETED
            
            self.results = results
            return self.get_outputs()
            
        except Exception as e:
            self.status = StepStatus.FAILED
            self.error = str(e)
            logger.error(f"Pipeline execution failed: {str(e)}", exc_info=True)
            raise
        finally:
            self.end_time = time.time()
            
    def get_outputs(self) -> Dict[str, Any]:
        """Get the combined outputs from all completed steps"""
        outputs = {}
        for step_name, result in self.results.items():
            if result.get("status") == StepStatus.COMPLETED:
                # Remove status, duration, error from output
                clean_result = {k: v for k, v in result.items() 
                               if k not in ["status", "duration", "error"]}
                outputs[step_name] = clean_result
        return outputs
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert pipeline to dictionary for serialization"""
        return {
            "id": self.id,
            "name": self.name,
            "steps": [step.to_dict() for step in self.steps],
            "status": self.status,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration": self.end_time - self.start_time if self.start_time and self.end_time else None,
            "error": self.error,
            "results": self.results
        }
        
    def save_state(self, file_path: str) -> None:
        """Save the pipeline state to a file"""
        with open(file_path, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)
            
    @classmethod
    def load_state(cls, file_path: str) -> 'ContentPipeline':
        """Load a pipeline state from a file"""
        with open(file_path, 'r') as f:
            data = json.load(f)
            
        pipeline = cls(name=data["name"])
        pipeline.id = data["id"]
        pipeline.status = data["status"]
        pipeline.start_time = data["start_time"]
        pipeline.end_time = data["end_time"]
        pipeline.error = data["error"]
        pipeline.results = data["results"]
        
        # Note: This doesn't restore the actual step functions,
        # just the metadata about the steps
        return pipeline 