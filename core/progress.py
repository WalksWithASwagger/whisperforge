"""
Progress System for WhisperForge
Award-winning aurora borealis aesthetic with sophisticated animations
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

class AuroraProgressTracker:
    """Award-winning aurora borealis progress tracking system"""
    
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
            return "●"
        else:
            return str(self.steps.index(step) + 1)
    
    def _get_aurora_css(self) -> str:
        """Generate award-winning aurora borealis CSS"""
        return """
        <style>
        /* Aurora Borealis Design System - Award-Winning Aesthetic */
        .aurora-progress-container {
            background: linear-gradient(
                135deg,
                rgba(0, 255, 255, 0.02) 0%,
                rgba(64, 224, 208, 0.04) 30%,
                rgba(125, 249, 255, 0.03) 60%,
                rgba(0, 255, 127, 0.02) 100%
            );
            backdrop-filter: blur(24px) saturate(180%);
            border: 1px solid rgba(0, 255, 255, 0.15);
            border-radius: 20px;
            padding: 32px;
            margin: 24px 0;
            position: relative;
            overflow: hidden;
            box-shadow: 
                0 0 40px rgba(0, 255, 255, 0.08),
                inset 0 1px 0 rgba(255, 255, 255, 0.15),
                0 16px 64px rgba(0, 0, 0, 0.12);
            transition: all 0.8s cubic-bezier(0.4, 0.0, 0.2, 1);
        }
        
        .aurora-progress-container::before {
            content: "";
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 2px;
            background: linear-gradient(
                90deg,
                transparent 0%,
                #00FFFF 20%,
                #7DF9FF 40%,
                #40E0D0 60%,
                #00FF7F 80%,
                transparent 100%
            );
            animation: aurora-scan 6s ease-in-out infinite;
        }
        
        .aurora-progress-container:hover {
            border-color: rgba(0, 255, 255, 0.25);
            box-shadow: 
                0 0 60px rgba(0, 255, 255, 0.12),
                inset 0 1px 0 rgba(255, 255, 255, 0.2),
                0 24px 96px rgba(0, 0, 0, 0.16);
            transform: translateY(-4px);
        }
        
        .aurora-progress-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 28px;
        }
        
        .aurora-progress-title {
            font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Segoe UI', Roboto, sans-serif;
            font-size: 1.25rem;
            font-weight: 700;
            letter-spacing: -0.03em;
            background: linear-gradient(
                120deg,
                #00FFFF 0%,
                #7DF9FF 25%,
                #40E0D0 50%,
                #00FF7F 75%,
                #00FFFF 100%
            );
            background-size: 300% 100%;
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            animation: aurora-text-flow 4s ease-in-out infinite;
            margin: 0;
        }
        
        .aurora-progress-stats {
            display: flex;
            gap: 20px;
            align-items: center;
        }
        
        .aurora-progress-count {
            font-family: 'SF Mono', 'Monaco', 'Consolas', monospace;
            font-size: 0.9rem;
            color: rgba(255, 255, 255, 0.75);
            font-weight: 600;
            background: rgba(0, 255, 255, 0.06);
            padding: 6px 12px;
            border-radius: 8px;
            border: 1px solid rgba(0, 255, 255, 0.1);
        }
        
        .aurora-progress-percent {
            font-family: 'SF Mono', 'Monaco', 'Consolas', monospace;
            font-size: 1.1rem;
            font-weight: 800;
            color: #00FFFF;
            text-shadow: 0 0 12px rgba(0, 255, 255, 0.5);
            background: rgba(0, 255, 255, 0.08);
            padding: 8px 16px;
            border-radius: 12px;
            border: 1px solid rgba(0, 255, 255, 0.2);
        }
        
        .aurora-progress-bar-container {
            margin-bottom: 32px;
            position: relative;
        }
        
        .aurora-progress-bar {
            height: 4px;
            background: rgba(255, 255, 255, 0.08);
            border-radius: 8px;
            position: relative;
            overflow: hidden;
            backdrop-filter: blur(8px);
            box-shadow: inset 0 1px 3px rgba(0, 0, 0, 0.2);
        }
        
        .aurora-progress-fill {
            height: 100%;
            background: linear-gradient(
                90deg,
                #00FFFF 0%,
                #7DF9FF 25%,
                #40E0D0 50%,
                #00FF7F 75%,
                #00FFFF 100%
            );
            background-size: 400% 100%;
            border-radius: 8px;
            position: relative;
            transition: width 1s cubic-bezier(0.4, 0.0, 0.2, 1);
            box-shadow: 
                0 0 16px rgba(0, 255, 255, 0.4),
                0 0 32px rgba(64, 224, 208, 0.2);
            animation: aurora-flow 3s ease-in-out infinite;
        }
        
        .aurora-progress-fill::after {
            content: "";
            position: absolute;
            top: -2px;
            left: -4px;
            right: -4px;
            bottom: -2px;
            background: inherit;
            border-radius: inherit;
            filter: blur(8px);
            opacity: 0.4;
            z-index: -1;
        }
        
        .aurora-progress-steps {
            display: flex;
            flex-direction: column;
            gap: 16px;
        }
        
        .aurora-progress-step {
            display: flex;
            align-items: flex-start;
            gap: 20px;
            padding: 16px 20px;
            border-radius: 16px;
            transition: all 0.5s cubic-bezier(0.4, 0.0, 0.2, 1);
            position: relative;
            overflow: hidden;
            background: rgba(255, 255, 255, 0.02);
            border: 1px solid rgba(255, 255, 255, 0.05);
        }
        
        .aurora-progress-step::before {
            content: "";
            position: absolute;
            inset: 0;
            background: linear-gradient(
                135deg,
                rgba(0, 255, 255, 0.03),
                rgba(64, 224, 208, 0.04),
                rgba(125, 249, 255, 0.03)
            );
            opacity: 0;
            transition: opacity 0.5s cubic-bezier(0.4, 0.0, 0.2, 1);
        }
        
        .aurora-progress-step.running {
            background: rgba(0, 255, 255, 0.06);
            border: 1px solid rgba(0, 255, 255, 0.2);
            box-shadow: 
                0 0 24px rgba(0, 255, 255, 0.15),
                inset 0 1px 0 rgba(255, 255, 255, 0.1);
            animation: aurora-pulse-running 2s ease-in-out infinite;
        }
        
        .aurora-progress-step.running::before {
            opacity: 1;
        }
        
        .aurora-progress-step.completed {
            background: rgba(0, 255, 127, 0.06);
            border: 1px solid rgba(0, 255, 127, 0.2);
            box-shadow: 
                0 0 24px rgba(0, 255, 127, 0.15),
                inset 0 1px 0 rgba(255, 255, 255, 0.1);
        }
        
        .aurora-progress-step.error {
            background: rgba(255, 107, 107, 0.06);
            border: 1px solid rgba(255, 107, 107, 0.2);
            box-shadow: 
                0 0 24px rgba(255, 107, 107, 0.15),
                inset 0 1px 0 rgba(255, 255, 255, 0.1);
        }
        
        .aurora-step-indicator {
            width: 32px;
            height: 32px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 14px;
            font-weight: 700;
            flex-shrink: 0;
            position: relative;
            transition: all 0.5s cubic-bezier(0.4, 0.0, 0.2, 1);
            background: rgba(255, 255, 255, 0.08);
            border: 2px solid rgba(255, 255, 255, 0.15);
            color: rgba(255, 255, 255, 0.8);
        }
        
        .aurora-step-indicator::before {
            content: "";
            position: absolute;
            inset: -3px;
            border-radius: 50%;
            background: conic-gradient(
                from 0deg,
                transparent 0%,
                #00FFFF 25%,
                #7DF9FF 50%,
                #40E0D0 75%,
                transparent 100%
            );
            opacity: 0;
            transition: opacity 0.5s cubic-bezier(0.4, 0.0, 0.2, 1);
            z-index: -1;
            animation: aurora-rotate 4s linear infinite;
        }
        
        .aurora-progress-step.running .aurora-step-indicator {
            background: #00FFFF;
            color: #000;
            border-color: #00FFFF;
            box-shadow: 
                0 0 16px rgba(0, 255, 255, 0.6),
                0 0 32px rgba(0, 255, 255, 0.3);
            animation: aurora-pulse-indicator 1.5s ease-in-out infinite;
        }
        
        .aurora-progress-step.running .aurora-step-indicator::before {
            opacity: 1;
        }
        
        .aurora-progress-step.completed .aurora-step-indicator {
            background: #00FF7F;
            color: #000;
            border-color: #00FF7F;
            box-shadow: 
                0 0 16px rgba(0, 255, 127, 0.6),
                0 0 32px rgba(0, 255, 127, 0.3);
        }
        
        .aurora-step-content {
            flex: 1;
            min-width: 0;
        }
        
        .aurora-step-name {
            font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Segoe UI', Roboto, sans-serif;
            font-weight: 700;
            color: rgba(255, 255, 255, 0.95);
            font-size: 1rem;
            margin-bottom: 6px;
            letter-spacing: -0.02em;
            line-height: 1.2;
        }
        
        .aurora-step-description {
            color: rgba(255, 255, 255, 0.7);
            font-size: 0.875rem;
            line-height: 1.5;
            letter-spacing: -0.01em;
            margin-bottom: 8px;
        }
        
        .aurora-step-duration {
            font-family: 'SF Mono', 'Monaco', 'Consolas', monospace;
            font-size: 0.8rem;
            color: rgba(255, 255, 255, 0.6);
            font-weight: 600;
            background: rgba(255, 255, 255, 0.04);
            padding: 4px 8px;
            border-radius: 6px;
            display: inline-block;
        }
        
        .aurora-step-duration.running {
            color: #00FFFF;
            background: rgba(0, 255, 255, 0.08);
            animation: aurora-pulse-duration 1.2s ease-in-out infinite;
        }
        
        .aurora-step-error {
            color: #FF6B6B;
            font-size: 0.875rem;
            margin-top: 8px;
            font-style: italic;
            opacity: 0.9;
            background: rgba(255, 107, 107, 0.06);
            padding: 8px 12px;
            border-radius: 8px;
            border-left: 3px solid #FF6B6B;
        }
        
        /* Award-Winning Animations */
        @keyframes aurora-scan {
            0% { transform: translateX(-100%); }
            50% { transform: translateX(100%); }
            100% { transform: translateX(-100%); }
        }
        
        @keyframes aurora-text-flow {
            0%, 100% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
        }
        
        @keyframes aurora-flow {
            0%, 100% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
        }
        
        @keyframes aurora-rotate {
            from { transform: rotate(0deg); }
            to { transform: rotate(360deg); }
        }
        
        @keyframes aurora-pulse-running {
            0%, 100% { 
                box-shadow: 
                    0 0 24px rgba(0, 255, 255, 0.15),
                    inset 0 1px 0 rgba(255, 255, 255, 0.1);
            }
            50% { 
                box-shadow: 
                    0 0 32px rgba(0, 255, 255, 0.25),
                    inset 0 1px 0 rgba(255, 255, 255, 0.15);
            }
        }
        
        @keyframes aurora-pulse-indicator {
            0%, 100% { 
                transform: scale(1);
                box-shadow: 
                    0 0 16px rgba(0, 255, 255, 0.6),
                    0 0 32px rgba(0, 255, 255, 0.3);
            }
            50% { 
                transform: scale(1.05);
                box-shadow: 
                    0 0 20px rgba(0, 255, 255, 0.8),
                    0 0 40px rgba(0, 255, 255, 0.4);
            }
        }
        
        @keyframes aurora-pulse-duration {
            0%, 100% { 
                opacity: 0.8;
                background: rgba(0, 255, 255, 0.08);
            }
            50% { 
                opacity: 1;
                background: rgba(0, 255, 255, 0.12);
            }
        }
        
        /* Responsive Design */
        @media (max-width: 768px) {
            .aurora-progress-container {
                padding: 24px 20px;
                margin: 16px 0;
                border-radius: 16px;
            }
            
            .aurora-progress-header {
                flex-direction: column;
                align-items: flex-start;
                gap: 16px;
                margin-bottom: 24px;
            }
            
            .aurora-progress-stats {
                gap: 12px;
            }
            
            .aurora-progress-steps {
                gap: 12px;
            }
            
            .aurora-progress-step {
                padding: 12px 16px;
                gap: 16px;
            }
            
            .aurora-step-indicator {
                width: 28px;
                height: 28px;
                font-size: 12px;
            }
        }
        
        /* High-DPI Optimizations */
        @media (-webkit-min-device-pixel-ratio: 2), (min-resolution: 192dpi) {
            .aurora-progress-fill {
                box-shadow: 
                    0 0 12px rgba(0, 255, 255, 0.4),
                    0 0 24px rgba(64, 224, 208, 0.2);
            }
            
            .aurora-step-indicator {
                border-width: 1.5px;
            }
        }
        </style>
        """
    
    def _update_display(self) -> None:
        """Update the progress display with award-winning aurora theme"""
        if self.container is None:
            return
        
        with self.container:
            # Clear any existing content first
            st.empty()
            
            # Apply award-winning CSS first
            st.markdown(self._get_aurora_css(), unsafe_allow_html=True)
            
            # Create main progress container with proper escaping
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
            
            # Add each step with proper HTML escaping
            for step in self.steps:
                step_class = f"aurora-progress-step {step.status}"
                
                duration_html = ""
                if step.duration_str:
                    duration_class = "aurora-step-duration"
                    if step.status == "running":
                        duration_class += " running"
                    duration_html = f'<div class="{duration_class}">{step.duration_str}</div>'
                
                error_html = ""
                if step.error_message:
                    # Escape error message for safe HTML
                    escaped_error = step.error_message.replace('<', '&lt;').replace('>', '&gt;')
                    error_html = f'<div class="aurora-step-error">{escaped_error}</div>'
                
                # Escape step name and description for safe HTML
                escaped_name = step.name.replace('<', '&lt;').replace('>', '&gt;')
                escaped_desc = step.description.replace('<', '&lt;').replace('>', '&gt;')
                
                progress_html += f"""
                <div class="{step_class}">
                    <div class="aurora-step-indicator">
                        {self._get_step_icon(step)}
                    </div>
                    <div class="aurora-step-content">
                        <div class="aurora-step-name">{escaped_name}</div>
                        <div class="aurora-step-description">{escaped_desc}</div>
                        {duration_html}
                        {error_html}
                    </div>
                </div>
                """
            
            progress_html += """
                </div>
            </div>
            """
            
            # Render the HTML
            st.markdown(progress_html, unsafe_allow_html=True)
    
    def create_display_container(self) -> None:
        """Create the Streamlit container for progress display"""
        self.container = st.empty()
        # Initial display to ensure container is created
        with self.container:
            st.markdown("Initializing aurora progress system...")
        # Update with actual progress
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

# Legacy alias for backward compatibility
ProgressTracker = AuroraProgressTracker

# Professional pipeline configuration for WhisperForge
WHISPERFORGE_PIPELINE_STEPS = [
    {
        "id": "upload_validation",
        "name": "Upload Validation",
        "description": "Validating file format, size, and audio compatibility"
    },
    {
        "id": "transcription",
        "name": "Audio Transcription",
        "description": "Converting speech to text using advanced AI models"
    },
    {
        "id": "wisdom_extraction",
        "name": "Wisdom Extraction", 
        "description": "Analyzing content for key insights and valuable takeaways"
    },
    {
        "id": "outline_creation",
        "name": "Outline Generation",
        "description": "Creating structured content outline and organization"
    },
    {
        "id": "social_content",
        "name": "Social Media Content",
        "description": "Generating platform-optimized social media posts"
    },
    {
        "id": "image_prompts",
        "name": "Visual Content Prompts",
        "description": "Creating AI image generation prompts and visual concepts"
    },
    {
        "id": "database_storage",
        "name": "Content Storage",
        "description": "Saving processed content to secure database"
    }
]

def create_whisperforge_progress_tracker() -> AuroraProgressTracker:
    """Create a pre-configured progress tracker for WhisperForge pipeline"""
    tracker = AuroraProgressTracker("WhisperForge Processing Pipeline")
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
            st.success("All processing completed successfully!")

if __name__ == "__main__":
    demo_progress_tracker() 