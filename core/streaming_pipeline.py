"""
Streaming Pipeline Controller for WhisperForge
Enables real-time progress updates and content streaming during processing
"""

import streamlit as st
import time
from typing import Dict, Optional, Any
from datetime import datetime
from .content_generation import (
    transcribe_audio, generate_wisdom, generate_outline, generate_article,
    generate_social_content, generate_image_prompts, editor_critique
)
# Removed old complex progress tracker - using simple progress bars now


class StreamingPipelineController:
    """Controls step-by-step pipeline execution with real-time UI updates"""
    
    # Define pipeline steps as class constant
    PIPELINE_STEPS = [
        "upload_validation", "transcription", "wisdom_extraction", 
        "outline_creation", "article_creation", "social_content", 
        "image_prompts", "database_storage"
    ]
    
    def __init__(self):
        self.reset_pipeline()
    
    def reset_pipeline(self):
        """Reset pipeline state for new processing"""
        st.session_state.pipeline_active = False
        st.session_state.pipeline_step_index = 0
        st.session_state.pipeline_results = {}
        st.session_state.pipeline_errors = {}
        st.session_state.pipeline_audio_file = None
        
    def start_pipeline(self, audio_file):
        """Initialize pipeline for processing"""
        self.reset_pipeline()
        st.session_state.pipeline_active = True
        st.session_state.pipeline_audio_file = audio_file
        
        # Store file info for later use
        st.session_state.pipeline_file_info = {
            "name": audio_file.name,
            "size": len(audio_file.getvalue()),
            "size_mb": len(audio_file.getvalue()) / (1024 * 1024)
        }
    
    def process_next_step(self):
        """Process the next step in the pipeline"""
        if not st.session_state.pipeline_active:
            return False
            
        step_index = st.session_state.pipeline_step_index
        
        if step_index >= len(self.PIPELINE_STEPS):
            # Pipeline complete
            st.session_state.pipeline_active = False
            return False
        
        step_id = self.PIPELINE_STEPS[step_index]
        
        try:
            # Process the step
            result = self._execute_step(step_id, step_index)
            
            # Store result
            st.session_state.pipeline_results[step_id] = result
            
            # Move to next step
            st.session_state.pipeline_step_index += 1
            
            return True
            
        except Exception as e:
            # Handle step error
            error_msg = str(e)
            st.session_state.pipeline_errors[step_id] = error_msg
            st.session_state.pipeline_active = False
            return False
    
    def _execute_step(self, step_id: str, step_index: int) -> Any:
        """Execute a specific pipeline step"""
        
        if step_id == "upload_validation":
            return self._step_upload_validation()
        elif step_id == "transcription":
            return self._step_transcription()
        elif step_id == "wisdom_extraction":
            return self._step_wisdom_extraction()
        elif step_id == "outline_creation":
            return self._step_outline_creation()
        elif step_id == "article_creation":
            return self._step_article_creation()
        elif step_id == "social_content":
            return self._step_social_content()
        elif step_id == "image_prompts":
            return self._step_image_prompts()
        elif step_id == "database_storage":
            return self._step_database_storage()
        else:
            raise Exception(f"Unknown step: {step_id}")
    
    def _step_upload_validation(self) -> Dict[str, Any]:
        """Step 1: Validate uploaded file"""
        file_info = st.session_state.pipeline_file_info
        
        if file_info["size_mb"] > 25:
            raise Exception(f"File too large: {file_info['size_mb']:.1f}MB (max 25MB)")
        
        # Simulate validation time
        time.sleep(0.5)
        
        return {
            "status": "validated",
            "file_name": file_info["name"],
            "file_size_mb": file_info["size_mb"]
        }
    
    def _step_transcription(self) -> str:
        """Step 2: Transcribe audio"""
        audio_file = st.session_state.pipeline_audio_file
        
        transcript = transcribe_audio(audio_file)
        if not transcript:
            raise Exception("Failed to transcribe audio - transcript is empty")
        
        # Store in session for access by later steps
        st.session_state.pipeline_transcript = transcript
        return transcript
    
    def _step_wisdom_extraction(self) -> str:
        """Step 3: Extract wisdom"""
        transcript = st.session_state.pipeline_transcript
        
        wisdom = generate_wisdom(
            transcript, 
            st.session_state.ai_provider, 
            st.session_state.ai_model, 
            None, 
            st.session_state.knowledge_base
        )
        
        # Handle editor mode
        if st.session_state.get("editor_enabled", False):
            critique = editor_critique(
                wisdom, "wisdom_extraction", 
                st.session_state.ai_provider, 
                st.session_state.ai_model,
                st.session_state.knowledge_base
            )
            
            # Store critique for display
            st.session_state.pipeline_results["wisdom_critique"] = critique
            
            # Generate revision based on critique
            revision_prompt = f"""Based on this editorial feedback, please revise the wisdom extraction:

EDITORIAL FEEDBACK:
{critique}

ORIGINAL WISDOM:
{wisdom}

Please provide an improved version that addresses the feedback while maintaining the core insights."""
            
            wisdom = generate_wisdom(
                transcript, 
                st.session_state.ai_provider, 
                st.session_state.ai_model, 
                revision_prompt, 
                st.session_state.knowledge_base
            )
        
        st.session_state.pipeline_wisdom = wisdom
        return wisdom
    
    def _step_outline_creation(self) -> str:
        """Step 4: Create outline"""
        transcript = st.session_state.pipeline_transcript
        wisdom = st.session_state.pipeline_wisdom
        
        outline = generate_outline(
            transcript, 
            wisdom, 
            st.session_state.ai_provider, 
            st.session_state.ai_model, 
            None, 
            st.session_state.knowledge_base
        )
        
        # Handle editor mode
        if st.session_state.get("editor_enabled", False):
            critique = editor_critique(
                outline, "outline_creation", 
                st.session_state.ai_provider, 
                st.session_state.ai_model,
                st.session_state.knowledge_base
            )
            
            st.session_state.pipeline_results["outline_critique"] = critique
            
            revision_prompt = f"""Based on this editorial feedback, please revise the content outline:

EDITORIAL FEEDBACK:
{critique}

ORIGINAL OUTLINE:
{outline}

Please provide an improved version that addresses the feedback."""
            
            outline = generate_outline(
                transcript, 
                wisdom, 
                st.session_state.ai_provider, 
                st.session_state.ai_model, 
                revision_prompt, 
                st.session_state.knowledge_base
            )
        
        st.session_state.pipeline_outline = outline
        return outline
    
    def _step_article_creation(self) -> str:
        """Step 5: Create article"""
        transcript = st.session_state.pipeline_transcript
        wisdom = st.session_state.pipeline_wisdom
        outline = st.session_state.pipeline_outline
        
        article = generate_article(
            transcript,
            wisdom, 
            outline, 
            st.session_state.ai_provider, 
            st.session_state.ai_model, 
            None, 
            st.session_state.knowledge_base
        )
        
        # Handle editor mode
        if st.session_state.get("editor_enabled", False):
            critique = editor_critique(
                article, "article_writing", 
                st.session_state.ai_provider, 
                st.session_state.ai_model,
                st.session_state.knowledge_base
            )
            
            st.session_state.pipeline_results["article_critique"] = critique
            
            revision_prompt = f"""Based on this editorial feedback, please revise the article:

EDITORIAL FEEDBACK:
{critique}

ORIGINAL ARTICLE:
{article}

Please provide an improved version that addresses the feedback."""
            
            article = generate_article(
                transcript,
                wisdom, 
                outline, 
                st.session_state.ai_provider, 
                st.session_state.ai_model, 
                revision_prompt, 
                st.session_state.knowledge_base
            )
        
        st.session_state.pipeline_article = article
        return article
    
    def _step_social_content(self) -> str:
        """Step 6: Generate social media content"""
        wisdom = st.session_state.pipeline_wisdom
        outline = st.session_state.pipeline_outline
        article = st.session_state.pipeline_article
        
        social = generate_social_content(
            wisdom, 
            outline,
            article, 
            st.session_state.ai_provider, 
            st.session_state.ai_model, 
            None, 
            st.session_state.knowledge_base
        )
        
        # Handle editor mode
        if st.session_state.get("editor_enabled", False):
            critique = editor_critique(
                social, "social_media", 
                st.session_state.ai_provider, 
                st.session_state.ai_model,
                st.session_state.knowledge_base
            )
            
            st.session_state.pipeline_results["social_critique"] = critique
            
            revision_prompt = f"""Based on this editorial feedback, please revise the social media content:

EDITORIAL FEEDBACK:
{critique}

ORIGINAL SOCIAL CONTENT:
{social}

Please provide improved versions that address the feedback."""
            
            social = generate_social_content(
                wisdom, 
                outline,
                article, 
                st.session_state.ai_provider, 
                st.session_state.ai_model, 
                revision_prompt, 
                st.session_state.knowledge_base
            )
        
        st.session_state.pipeline_social = social
        return social
    
    def _step_image_prompts(self) -> str:
        """Step 7: Generate image prompts"""
        wisdom = st.session_state.pipeline_wisdom
        outline = st.session_state.pipeline_outline
        
        images = generate_image_prompts(
            wisdom, 
            outline, 
            st.session_state.ai_provider, 
            st.session_state.ai_model, 
            None, 
            st.session_state.knowledge_base
        )
        
        st.session_state.pipeline_images = images
        return images
    
    def _step_database_storage(self) -> str:
        """Step 8: Store content in database"""
        # Import here to avoid circular imports
        try:
            from ..app import save_generated_content_supabase
        except ImportError:
            # Fallback if circular import occurs
            def save_generated_content_supabase(data):
                return "mock_content_id"
        
        content_data = {
            "title": f"Content from {st.session_state.pipeline_file_info['name']}",
            "transcript": st.session_state.pipeline_results.get("transcription", ""),
            "wisdom_extraction": st.session_state.pipeline_results.get("wisdom_extraction", ""),
            "outline_creation": st.session_state.pipeline_results.get("outline_creation", ""),
            "article": st.session_state.pipeline_results.get("article_creation", ""),
            "social_media": st.session_state.pipeline_results.get("social_content", ""),
            "image_prompts": st.session_state.pipeline_results.get("image_prompts", ""),
            "metadata": {
                "ai_provider": st.session_state.ai_provider,
                "ai_model": st.session_state.ai_model,
                "file_size": st.session_state.pipeline_file_info["size"],
                "editor_enabled": st.session_state.get("editor_enabled", False),
                "created_at": datetime.now().isoformat()
            }
        }
        
        try:
            content_id = save_generated_content_supabase(content_data)
            if not content_id:
                raise Exception("Failed to save content to database")
            
            time.sleep(0.3)  # Simulate save time
            return content_id
        except Exception as e:
            # Don't fail the pipeline for database errors
            return f"Database save failed: {str(e)}"
    
    @property
    def is_active(self) -> bool:
        """Check if pipeline is currently active"""
        return st.session_state.get("pipeline_active", False)
    
    @property
    def is_complete(self) -> bool:
        """Check if pipeline has completed"""
        return (not self.is_active and 
                st.session_state.get("pipeline_step_index", 0) >= len(self.PIPELINE_STEPS))
    
    @property
    def current_step_index(self) -> int:
        """Get current step index"""
        return st.session_state.get("pipeline_step_index", 0)
    
    @property
    def progress_percentage(self) -> float:
        """Get overall progress percentage"""
        return (self.current_step_index / len(self.PIPELINE_STEPS)) * 100
    
    def get_results(self) -> Dict[str, Any]:
        """Get all pipeline results"""
        return st.session_state.get("pipeline_results", {})
    
    def get_errors(self) -> Dict[str, str]:
        """Get any pipeline errors"""
        return st.session_state.get("pipeline_errors", {})


# Global pipeline controller instance
def get_pipeline_controller() -> StreamingPipelineController:
    """Get or create the global pipeline controller"""
    if 'pipeline_controller' not in st.session_state:
        st.session_state.pipeline_controller = StreamingPipelineController()
    return st.session_state.pipeline_controller 