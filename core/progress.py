"""
Progress System for WhisperForge
Beautiful, animated progress indicators and status updates
"""

import streamlit as st
import time
from typing import List, Dict, Any, Optional
from datetime import datetime
import json
from dataclasses import dataclass, field
from contextlib import contextmanager

@dataclass
class ProgressStep:
    """Represents a single step in the progress tracking system"""
    id: str
    name: str
    description: str
    status: str = "pending"  # pending, running, completed, error
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    error_message: Optional[str] = None
    
    @property
    def duration(self) -> Optional[float]:
        """Calculate duration in seconds"""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        elif self.start_time and self.status == "running":
            return (datetime.now() - self.start_time).total_seconds()
        return None
    
    @property
    def duration_str(self) -> str:
        """Get formatted duration string"""
        if self.duration is None:
            return ""
        if self.duration < 1:
            return f"{int(self.duration * 1000)}ms"
        elif self.duration < 60:
            return f"{self.duration:.1f}s"
        else:
            minutes = int(self.duration // 60)
            seconds = int(self.duration % 60)
            return f"{minutes}m {seconds}s"

class ProgressTracker:
    """Aurora-themed progress tracking system with sophisticated animations"""
    
    def __init__(self, title: str = "Processing"):
        self.title = title
        self.steps: List[ProgressStep] = []
        self.current_step_index: Optional[int] = None
        self.container = None
        
    def add_step(self, step_id: str, name: str, description: str) -> None:
        """Add a new step to the progress tracker"""
        step = ProgressStep(
            id=step_id,
            name=name,
            description=description
        )
        self.steps.append(step)
    
    def setup_steps(self, steps_config: List[Dict[str, str]]) -> None:
        """Setup multiple steps from configuration"""
        for step_config in steps_config:
            self.add_step(
                step_config["id"],
                step_config["name"],
                step_config["description"]
            )
    
    def start_step(self, step_id: str) -> None:
        """Start a specific step"""
        for i, step in enumerate(self.steps):
            if step.id == step_id:
                step.status = "running"
                step.start_time = datetime.now()
                self.current_step_index = i
                break
        self._update_display()
    
    def complete_step(self, step_id: str) -> None:
        """Complete a specific step"""
        for step in self.steps:
            if step.id == step_id:
                step.status = "completed"
                step.end_time = datetime.now()
                break
        self._update_display()
    
    def error_step(self, step_id: str, error_message: str) -> None:
        """Mark a step as error"""
        for step in self.steps:
            if step.id == step_id:
                step.status = "error"
                step.end_time = datetime.now()
                step.error_message = error_message
                break
        self._update_display()
    
    @property
    def progress_percentage(self) -> float:
        """Calculate overall progress percentage"""
        if not self.steps:
            return 0.0
        
        completed_steps = len([s for s in self.steps if s.status == "completed"])
        return (completed_steps / len(self.steps)) * 100
    
    @property
    def completed_count(self) -> int:
        """Get count of completed steps"""
        return len([s for s in self.steps if s.status == "completed"])
    
    def _get_step_icon(self, step: ProgressStep) -> str:
        """Get icon for step based on status"""
        if step.status == "completed":
            return "✓"
        elif step.status == "error":
            return "✕"
        elif step.status == "running":
            return "◉"
        else:
            return str(self.steps.index(step) + 1)
    
    def _update_display(self) -> None:
        """Update the progress display with aurora theme"""
        if self.container is None:
            return
        
        with self.container:
            # Include aurora-themed CSS inline since Streamlit doesn't support external CSS files
            try:
                import os
                css_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static", "css", "aurora-progress.css")
                if os.path.exists(css_path):
                    with open(css_path, "r") as f:
                        aurora_css = f"<style>{f.read()}</style>"
                        st.markdown(aurora_css, unsafe_allow_html=True)
            except Exception:
                # If CSS file is not found, continue without styling
                pass
            
            # Main progress container
            progress_html = f"""
            <div class="aurora-progress-container">
                <div class="aurora-progress-header">
                    <h3 class="aurora-progress-title">{self.title}</h3>
                    <div class="aurora-progress-stats">
                        <span class="aurora-progress-count">{self.completed_count}/{len(self.steps)} steps</span>
                        <span class="aurora-progress-percent">{self.progress_percentage:.1f}%</span>
                    </div>
                </div>
                
                <div class="aurora-progress-bar-container">
                    <div class="aurora-progress-bar">
                        <div class="aurora-progress-fill" style="width: {self.progress_percentage}%"></div>
                    </div>
                </div>
                
                <div class="aurora-progress-steps">
            """
            
            # Add each step
            for step in self.steps:
                step_class = f"aurora-progress-step {step.status}"
                if step.status == "running":
                    step_class += " aurora-pulse-thinking"
                
                duration_html = ""
                if step.duration_str:
                    duration_class = "aurora-step-duration"
                    if step.status == "running":
                        duration_class += " running"
                    duration_html = f'<div class="{duration_class}">{step.duration_str}</div>'
                
                error_html = ""
                if step.error_message:
                    error_html = f'<div class="aurora-step-error">{step.error_message}</div>'
                
                progress_html += f"""
                <div class="{step_class}">
                    <div class="aurora-step-indicator">
                        {self._get_step_icon(step)}
                    </div>
                    <div class="aurora-step-content">
                        <div class="aurora-step-name">{step.name}</div>
                        <div class="aurora-step-description">{step.description}</div>
                        {duration_html}
                        {error_html}
                    </div>
                </div>
                """
            
            progress_html += """
                </div>
            </div>
            """
            
            st.markdown(progress_html, unsafe_allow_html=True)
    
    def create_display_container(self) -> None:
        """Create the Streamlit container for progress display"""
        self.container = st.empty()
        self._update_display()
    
    @contextmanager
    def step_context(self, step_id: str):
        """Context manager for automatic step timing"""
        try:
            self.start_step(step_id)
            yield
            self.complete_step(step_id)
        except Exception as e:
            self.error_step(step_id, str(e))
            raise
    
    def is_completed(self) -> bool:
        """Check if all steps are completed"""
        return all(step.status == "completed" for step in self.steps)
    
    def has_errors(self) -> bool:
        """Check if any steps have errors"""
        return any(step.status == "error" for step in self.steps)

# Default pipeline configuration for WhisperForge
WHISPERFORGE_PIPELINE_STEPS = [
    {
        "id": "upload_validation",
        "name": "Upload Validation",
        "description": "Validating file format, size, and audio compatibility"
    },
    {
        "id": "transcription",
        "name": "Audio Transcription",
        "description": "Converting speech to text using AI models"
    },
    {
        "id": "wisdom_extraction",
        "name": "Wisdom Extraction",
        "description": "Analyzing content for key insights and wisdom"
    },
    {
        "id": "outline_creation",
        "name": "Outline Generation",
        "description": "Creating structured content outline"
    },
    {
        "id": "social_content",
        "name": "Social Media Content",
        "description": "Generating social media posts and summaries"
    },
    {
        "id": "image_prompts",
        "name": "Visual Content Prompts",
        "description": "Creating image generation prompts"
    },
    {
        "id": "database_storage",
        "name": "Content Storage",
        "description": "Saving processed content to database"
    }
]

def create_whisperforge_progress_tracker() -> ProgressTracker:
    """Create a pre-configured progress tracker for WhisperForge pipeline"""
    tracker = ProgressTracker("WhisperForge Processing Pipeline")
    tracker.setup_steps(WHISPERFORGE_PIPELINE_STEPS)
    return tracker

# Example usage function for testing
def demo_progress_tracker():
    """Demo function to show the aurora progress tracker in action"""
    st.title("Aurora Progress Tracker Demo")
    
    tracker = create_whisperforge_progress_tracker()
    
    if st.button("Start Demo Processing"):
        tracker.create_display_container()
        
        # Simulate processing each step
        for step_config in WHISPERFORGE_PIPELINE_STEPS:
            with tracker.step_context(step_config["id"]):
                # Simulate processing time
                time.sleep(1.5)
        
        if tracker.is_completed():
            st.success("🎉 All processing completed successfully!")
            st.balloons()

if __name__ == "__main__":
    demo_progress_tracker() 