"""
Progress System for WhisperForge
Beautiful, animated progress indicators and status updates
"""

import streamlit as st
import time
from typing import List, Dict, Optional
from datetime import datetime
import json

class ProgressStep:
    """Represents a single step in the progress flow"""
    def __init__(self, name: str, description: str, icon: str = "⚡"):
        self.name = name
        self.description = description
        self.icon = icon
        self.status = "pending"  # pending, running, completed, error
        self.start_time = None
        self.end_time = None
        self.error_message = None
        
    def start(self):
        self.status = "running"
        self.start_time = datetime.now()
        
    def complete(self):
        self.status = "completed"
        self.end_time = datetime.now()
        
    def error(self, message: str):
        self.status = "error"
        self.end_time = datetime.now()
        self.error_message = message
        
    @property
    def duration(self) -> Optional[float]:
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None

class ProgressTracker:
    """Main progress tracking system with beautiful UI"""
    
    def __init__(self, title: str = "Processing"):
        self.title = title
        self.steps: List[ProgressStep] = []
        self.current_step_index = -1
        self.container = None
        self.is_active = False
        
    def add_step(self, name: str, description: str, icon: str = "⚡"):
        """Add a step to the progress flow"""
        step = ProgressStep(name, description, icon)
        self.steps.append(step)
        return step
        
    def start(self):
        """Initialize the progress UI"""
        self.is_active = True
        self.container = st.empty()
        self._render()
        
    def next_step(self) -> Optional[ProgressStep]:
        """Move to the next step"""
        if self.current_step_index >= 0 and self.current_step_index < len(self.steps):
            self.steps[self.current_step_index].complete()
            
        self.current_step_index += 1
        
        if self.current_step_index < len(self.steps):
            current_step = self.steps[self.current_step_index]
            current_step.start()
            self._render()
            return current_step
        return None
        
    def error(self, message: str):
        """Mark current step as error"""
        if self.current_step_index >= 0 and self.current_step_index < len(self.steps):
            self.steps[self.current_step_index].error(message)
            self._render()
            
    def complete(self):
        """Complete the entire progress flow"""
        if self.current_step_index >= 0 and self.current_step_index < len(self.steps):
            self.steps[self.current_step_index].complete()
        self.is_active = False
        self._render()
        
    def _get_status_icon(self, status: str) -> str:
        """Get icon for status"""
        icons = {
            "pending": "⚪",
            "running": "🔄",
            "completed": "✅",
            "error": "❌"
        }
        return icons.get(status, "⚪")
        
    def _get_status_color(self, status: str) -> str:
        """Get color for status"""
        colors = {
            "pending": "#707070",
            "running": "#3ABFF8", 
            "completed": "#36D399",
            "error": "#F87272"
        }
        return colors.get(status, "#707070")
        
    def _render(self):
        """Render the progress UI"""
        if not self.container:
            return
            
        # Calculate overall progress
        completed_steps = sum(1 for step in self.steps if step.status == "completed")
        total_steps = len(self.steps)
        progress_percent = (completed_steps / total_steps * 100) if total_steps > 0 else 0
        
        # Build HTML for progress display
        html_content = f"""
        <div class="progress-container">
            <div class="progress-header">
                <h3 class="progress-title">{self.title}</h3>
                <div class="progress-stats">
                    <span class="progress-count">{completed_steps}/{total_steps}</span>
                    <span class="progress-percent">{progress_percent:.0f}%</span>
                </div>
            </div>
            
            <div class="progress-bar-container">
                <div class="progress-bar">
                    <div class="progress-fill" style="width: {progress_percent}%"></div>
                    <div class="progress-glow" style="width: {progress_percent}%"></div>
                </div>
            </div>
            
            <div class="progress-steps">
        """
        
        for i, step in enumerate(self.steps):
            is_current = i == self.current_step_index
            status_icon = self._get_status_icon(step.status)
            status_color = self._get_status_color(step.status)
            
            # Add pulsing animation for current step
            pulse_class = "pulse-animation" if is_current and step.status == "running" else ""
            
            # Duration display
            duration_text = ""
            if step.duration:
                duration_text = f"<span class='step-duration'>({step.duration:.1f}s)</span>"
            elif step.status == "running":
                duration_text = "<span class='step-duration running'>⚡</span>"
                
            html_content += f"""
                <div class="progress-step {step.status} {pulse_class}">
                    <div class="step-indicator" style="background-color: {status_color};">
                        <span class="step-icon">{status_icon}</span>
                    </div>
                    <div class="step-content">
                        <div class="step-name">{step.icon} {step.name} {duration_text}</div>
                        <div class="step-description">{step.description}</div>
                        {f'<div class="step-error">{step.error_message}</div>' if step.error_message else ''}
                    </div>
                </div>
            """
        
        html_content += """
            </div>
        </div>
        """
        
        # Add CSS
        css = """
        <style>
        .progress-container {
            background: linear-gradient(120deg, var(--bg-secondary) 0%, var(--bg-tertiary) 100%);
            border-radius: var(--card-radius);
            padding: 20px;
            margin: 15px 0;
            border: 1px solid rgba(121, 40, 202, 0.2);
            position: relative;
            overflow: hidden;
        }
        
        .progress-container::before {
            content: "";
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 2px;
            background: linear-gradient(90deg, transparent, rgba(121, 40, 202, 0.6), transparent);
            animation: progress-shine 2s ease-in-out infinite;
        }
        
        .progress-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }
        
        .progress-title {
            font-family: var(--terminal-font);
            font-size: 1.1rem;
            color: var(--text-primary);
            margin: 0;
            background: linear-gradient(90deg, #7928CA, #FF0080);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        
        .progress-stats {
            display: flex;
            gap: 12px;
            align-items: center;
        }
        
        .progress-count {
            font-family: var(--terminal-font);
            color: var(--text-secondary);
            font-size: 0.9rem;
        }
        
        .progress-percent {
            font-family: var(--terminal-font);
            color: var(--accent-primary);
            font-weight: 600;
            font-size: 1rem;
        }
        
        .progress-bar-container {
            margin-bottom: 20px;
        }
        
        .progress-bar {
            height: 6px;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 3px;
            position: relative;
            overflow: hidden;
        }
        
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #7928CA, #FF0080);
            border-radius: 3px;
            transition: width 0.8s cubic-bezier(0.4, 0, 0.2, 1);
            position: relative;
        }
        
        .progress-glow {
            position: absolute;
            top: 0;
            left: 0;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(121, 40, 202, 0.4), transparent);
            border-radius: 3px;
            animation: progress-glow 1.5s ease-in-out infinite;
        }
        
        .progress-steps {
            display: flex;
            flex-direction: column;
            gap: 8px;
        }
        
        .progress-step {
            display: flex;
            align-items: flex-start;
            gap: 12px;
            padding: 8px;
            border-radius: 6px;
            transition: all 0.3s ease;
        }
        
        .progress-step.running {
            background: rgba(58, 191, 248, 0.05);
            border: 1px solid rgba(58, 191, 248, 0.2);
        }
        
        .progress-step.completed {
            background: rgba(54, 211, 153, 0.05);
            border: 1px solid rgba(54, 211, 153, 0.2);
        }
        
        .progress-step.error {
            background: rgba(248, 114, 114, 0.05);
            border: 1px solid rgba(248, 114, 114, 0.2);
        }
        
        .step-indicator {
            width: 24px;
            height: 24px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 12px;
            flex-shrink: 0;
            transition: all 0.3s ease;
        }
        
        .step-content {
            flex: 1;
        }
        
        .step-name {
            font-weight: 600;
            color: var(--text-primary);
            font-size: 0.9rem;
            margin-bottom: 2px;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        
        .step-description {
            color: var(--text-secondary);
            font-size: 0.8rem;
            line-height: 1.3;
        }
        
        .step-duration {
            font-family: var(--terminal-font);
            font-size: 0.75rem;
            color: var(--text-muted);
        }
        
        .step-duration.running {
            color: var(--info);
            animation: pulse 1s ease-in-out infinite;
        }
        
        .step-error {
            color: var(--error);
            font-size: 0.8rem;
            margin-top: 4px;
            font-style: italic;
        }
        
        .pulse-animation {
            animation: step-pulse 1.5s ease-in-out infinite;
        }
        
        @keyframes progress-shine {
            0% { transform: translateX(-100%); }
            50% { transform: translateX(100%); }
            100% { transform: translateX(-100%); }
        }
        
        @keyframes progress-glow {
            0%, 100% { opacity: 0.3; }
            50% { opacity: 0.8; }
        }
        
        @keyframes step-pulse {
            0%, 100% { transform: scale(1); opacity: 0.8; }
            50% { transform: scale(1.02); opacity: 1; }
        }
        
        @keyframes pulse {
            0%, 100% { opacity: 0.6; }
            50% { opacity: 1; }
        }
        </style>
        """
        
        self.container.markdown(css + html_content, unsafe_allow_html=True)

# Convenience functions for common workflows
def create_audio_pipeline_progress() -> ProgressTracker:
    """Create progress tracker for audio processing pipeline"""
    tracker = ProgressTracker("🎵 Audio Processing Pipeline")
    
    tracker.add_step("upload", "Uploading and validating audio file", "📁")
    tracker.add_step("transcribe", "Transcribing audio to text", "🎤") 
    tracker.add_step("wisdom", "Extracting key insights and wisdom", "💡")
    tracker.add_step("outline", "Creating structured outline", "📋")
    tracker.add_step("social", "Generating social media content", "📱")
    tracker.add_step("images", "Creating image prompts", "🎨")
    tracker.add_step("save", "Saving content to database", "💾")
    
    return tracker

def create_file_upload_progress(filename: str) -> ProgressTracker:
    """Create progress tracker for file upload"""
    tracker = ProgressTracker(f"📤 Uploading {filename}")
    
    tracker.add_step("validate", "Validating file format and size", "✅")
    tracker.add_step("upload", "Uploading file to server", "⬆️")
    tracker.add_step("process", "Processing and preparing file", "⚙️")
    
    return tracker

# Context manager for easy progress tracking
class progress_context:
    """Context manager for progress tracking"""
    
    def __init__(self, tracker: ProgressTracker):
        self.tracker = tracker
        
    def __enter__(self):
        self.tracker.start()
        return self.tracker
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.tracker.error(str(exc_val))
        else:
            self.tracker.complete() 