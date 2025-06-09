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
from .research_enrichment import generate_research_enrichment
from .visible_thinking import thinking_step_start, thinking_step_complete, thinking_error, render_thinking_stream
# Removed old complex progress tracker - using simple progress bars now


class StreamingPipelineController:
    """Controls step-by-step pipeline execution with real-time UI updates"""
    
    # Define pipeline steps as class constant
    PIPELINE_STEPS = [
        "upload_validation", "transcription", "wisdom_extraction", 
        "research_enrichment", "outline_creation", "article_creation", 
        "social_content", "image_prompts", "database_storage"
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
        
        # Initialize required session state if missing
        if not hasattr(st.session_state, 'prompts'):
            st.session_state.prompts = {}
        if not hasattr(st.session_state, 'knowledge_base'):
            st.session_state.knowledge_base = {}
        if not hasattr(st.session_state, 'ai_provider'):
            st.session_state.ai_provider = "OpenAI"
        if not hasattr(st.session_state, 'ai_model'):
            st.session_state.ai_model = "gpt-4o"
    
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
            # Show immediate status update
            with st.status(f"Processing {step_id.replace('_', ' ').title()}...", expanded=True):
                st.write(f"Step {step_index + 1} of {len(self.PIPELINE_STEPS)}: {step_id.replace('_', ' ')}")
                
                # Process the step
                result = self._execute_step(step_id, step_index)
                
                # Store result
                st.session_state.pipeline_results[step_id] = result
                
                st.write("✅ Complete!")
            
            # Move to next step
            st.session_state.pipeline_step_index += 1
            
            return True
            
        except Exception as e:
            # Handle step error
            error_msg = str(e)
            st.session_state.pipeline_errors[step_id] = error_msg
            st.session_state.pipeline_active = False
            st.error(f"❌ Error in {step_id}: {error_msg}")
            return False
    
    def _execute_step(self, step_id: str, step_index: int) -> Any:
        """Execute a specific pipeline step"""
        
        # Add visible thinking at step start
        thinking_step_start(step_id)
        
        try:
            if step_id == "upload_validation":
                result = self._step_upload_validation()
            elif step_id == "transcription":
                result = self._step_transcription()
            elif step_id == "wisdom_extraction":
                result = self._step_wisdom_extraction()
            elif step_id == "research_enrichment":
                result = self._step_research_enrichment()
            elif step_id == "outline_creation":
                result = self._step_outline_creation()
            elif step_id == "article_creation":
                result = self._step_article_creation()
            elif step_id == "social_content":
                result = self._step_social_content()
            elif step_id == "image_prompts":
                result = self._step_image_prompts()
            elif step_id == "database_storage":
                result = self._step_database_storage()
            else:
                raise Exception(f"Unknown step: {step_id}")
            
            # Add success thinking
            thinking_step_complete(step_id)
            return result
            
        except Exception as e:
            # Add error thinking
            thinking_error(step_id, str(e))
            raise
    
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
        
        # Get custom prompt if available
        custom_prompt = st.session_state.prompts.get("wisdom_extraction") if hasattr(st.session_state, 'prompts') else None
        
        wisdom = generate_wisdom(
            transcript, 
            st.session_state.ai_provider, 
            st.session_state.ai_model, 
            custom_prompt, 
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
    
    def _step_research_enrichment(self) -> Dict[str, Any]:
        """Step 3.5: Research Enrichment - NEW STEP"""
        wisdom = st.session_state.pipeline_wisdom
        transcript = st.session_state.pipeline_transcript
        
        # Check if research enrichment is enabled (default True for paid users)
        research_enabled = st.session_state.get("research_enabled", True)
        
        # Generate research enrichment
        research_data = generate_research_enrichment(
            wisdom=wisdom,
            transcript=transcript,
            ai_provider=st.session_state.ai_provider,
            ai_model=st.session_state.ai_model,
            enabled=research_enabled
        )
        
        # Store in session for access by later steps
        st.session_state.pipeline_research = research_data
        return research_data
    
    def _step_outline_creation(self) -> str:
        """Step 4: Create outline"""
        transcript = st.session_state.pipeline_transcript
        wisdom = st.session_state.pipeline_wisdom
        
        # Get custom prompt if available
        custom_prompt = st.session_state.prompts.get("outline_creation") if hasattr(st.session_state, 'prompts') else None
        
        outline = generate_outline(
            transcript, 
            wisdom, 
            st.session_state.ai_provider, 
            st.session_state.ai_model, 
            custom_prompt, 
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
        
        # Get custom prompt if available  
        custom_prompt = st.session_state.prompts.get("article_creation") if hasattr(st.session_state, 'prompts') else None
        
        article = generate_article(
            transcript,
            wisdom, 
            outline, 
            st.session_state.ai_provider, 
            st.session_state.ai_model, 
            custom_prompt, 
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
        
        # Get custom prompt if available
        custom_prompt = st.session_state.prompts.get("social_media") if hasattr(st.session_state, 'prompts') else None
        
        social = generate_social_content(
            wisdom, 
            outline,
            article, 
            st.session_state.ai_provider, 
            st.session_state.ai_model, 
            custom_prompt, 
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
        
        # Get custom prompt if available
        custom_prompt = st.session_state.prompts.get("image_prompts") if hasattr(st.session_state, 'prompts') else None
        
        images = generate_image_prompts(
            wisdom, 
            outline, 
            st.session_state.ai_provider, 
            st.session_state.ai_model, 
            custom_prompt, 
            st.session_state.knowledge_base
        )
        
        st.session_state.pipeline_images = images
        return images
    
    def _step_database_storage(self) -> str:
        """Step 8: Store content in database"""
        try:
            # Direct Supabase access to avoid circular imports
            from .supabase_integration import get_supabase_client
            
            db = get_supabase_client()
            if not db:
                return "Database connection failed"
            
            # Get results with correct step names
            results = st.session_state.pipeline_results
            
            # Direct database insert with CORRECT field names
            result = db.client.table("content").insert({
                "user_id": st.session_state.user_id,
                "title": f"Content from {st.session_state.pipeline_file_info['name']}",
                "transcript": results.get("transcription", ""),
                "wisdom": results.get("wisdom_extraction", ""), 
                "outline": results.get("outline_creation", ""),
                "article": results.get("article_creation", ""),
                "social_content": results.get("social_content", ""),
                "created_at": "now()"
            }).execute()
            
            content_id = result.data[0]["id"] if result.data else ""
            if not content_id:
                return "Failed to save content to database"
            
            time.sleep(0.3)  # Simulate save time
            return f"Content saved with ID: {content_id}"
            
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