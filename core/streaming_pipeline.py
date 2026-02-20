"""
Streaming Pipeline Controller for WhisperForge
Enables real-time progress updates and content streaming during processing
"""

import time
from typing import Any

import openai
import streamlit as st
from postgrest.exceptions import APIError

from .constants import LARGE_FILE_THRESHOLD_MB
from .content_generation import (
    ContentGenerationError,
    generate_article,
    generate_outline,
    generate_social_content,
    generate_wisdom,
    transcribe_audio,
)
from .exceptions import DatabaseError, PipelineError
from .visible_thinking import thinking_error, thinking_step_complete, thinking_step_start


class StreamingPipelineController:
    """Controls step-by-step pipeline execution with real-time UI updates"""

    PIPELINE_STEPS = [
        "upload_validation",
        "transcription",
        "wisdom_extraction",
        "outline_creation",
        "article_creation",
        "social_content",
        "database_storage",
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
        """Initialize pipeline for processing with large file support"""
        self.reset_pipeline()
        st.session_state.pipeline_active = True
        st.session_state.pipeline_audio_file = audio_file

        file_size_mb = len(audio_file.getvalue()) / (1024 * 1024)
        st.session_state.pipeline_file_info = {
            "name": audio_file.name,
            "size": len(audio_file.getvalue()),
            "size_mb": file_size_mb,
            "is_large_file": file_size_mb > LARGE_FILE_THRESHOLD_MB,
        }

        if not hasattr(st.session_state, "prompts"):
            st.session_state.prompts = {}
        if not hasattr(st.session_state, "knowledge_base"):
            st.session_state.knowledge_base = {}

    def process_next_step(self):
        """Process the next step in the pipeline"""
        if not st.session_state.pipeline_active:
            return False

        step_index = st.session_state.pipeline_step_index

        if step_index >= len(self.PIPELINE_STEPS):
            st.session_state.pipeline_active = False
            return False

        step_id = self.PIPELINE_STEPS[step_index]

        try:
            with st.status(f"Processing {step_id.replace('_', ' ').title()}...", expanded=True):
                st.write(f"Step {step_index + 1} of {len(self.PIPELINE_STEPS)}: {step_id.replace('_', ' ')}")
                result = self._execute_step(step_id, step_index)
                st.session_state.pipeline_results[step_id] = result
                st.write("Complete!")

            st.session_state.pipeline_step_index += 1
            return True

        except (ContentGenerationError, openai.APIError, ValueError) as e:
            error_msg = str(e)
            st.session_state.pipeline_errors[step_id] = error_msg
            st.session_state.pipeline_active = False
            st.error(f"Error in {step_id}: {error_msg}")
            return False
        except PipelineError as e:
            error_msg = str(e)
            st.session_state.pipeline_errors[step_id] = error_msg
            st.session_state.pipeline_active = False
            st.error(f"Unexpected error in {step_id}: {error_msg}")
            return False

    def _execute_step(self, step_id: str, step_index: int) -> Any:
        """Execute a specific pipeline step"""
        thinking_step_start(step_id)

        try:
            if step_id == "upload_validation":
                result = self._step_upload_validation()
            elif step_id == "transcription":
                result = self._step_transcription()
            elif step_id == "wisdom_extraction":
                result = self._step_wisdom_extraction()
            elif step_id == "outline_creation":
                result = self._step_outline_creation()
            elif step_id == "article_creation":
                result = self._step_article_creation()
            elif step_id == "social_content":
                result = self._step_social_content()
            elif step_id == "database_storage":
                result = self._step_database_storage()
            else:
                raise ValueError(f"Unknown step: {step_id}")

            thinking_step_complete(step_id)
            return result

        except (ContentGenerationError, openai.APIError, ValueError) as e:
            thinking_error(step_id, str(e))
            raise
        except PipelineError as e:
            thinking_error(step_id, f"Unexpected: {e!s}")
            raise

    def _step_upload_validation(self) -> dict[str, Any]:
        """Step 1: Validate uploaded file"""
        file_info = st.session_state.pipeline_file_info

        from .config import get_config

        max_file_size_mb = get_config().audio_chunk_size_mb
        if file_info["size_mb"] > max_file_size_mb:
            raise ValueError(f"File too large: {file_info['size_mb']:.1f}MB (max {max_file_size_mb}MB)")

        time.sleep(0.5)

        return {"status": "validated", "file_name": file_info["name"], "file_size_mb": file_info["size_mb"]}

    def _step_transcription(self) -> str:
        """Step 2: Transcribe audio with large file support"""
        audio_file = st.session_state.pipeline_audio_file
        file_info = st.session_state.pipeline_file_info

        if file_info.get("is_large_file", False):
            return self._transcribe_large_file(audio_file)
        else:
            return self._transcribe_small_file(audio_file)

    def _transcribe_small_file(self, audio_file) -> str:
        """Transcribe small files directly"""
        st.write("Processing small file directly...")

        transcript = transcribe_audio(audio_file)
        if not transcript:
            raise ValueError("Failed to transcribe audio - transcript is empty")

        st.session_state.pipeline_transcript = transcript
        return transcript

    def _transcribe_large_file(self, audio_file) -> str:
        """Transcribe large files using chunked processing"""
        from .file_upload import EnhancedLargeFileProcessor

        st.write("Processing large file with chunked transcription...")

        processor = EnhancedLargeFileProcessor()
        result = processor.process_large_file(audio_file)

        if not result["success"]:
            raise ValueError(f"Large file transcription failed: {result['error']}")

        transcript = result["transcript"]
        if not transcript:
            raise ValueError("Large file transcription produced empty result")

        st.success(f"""
        Large File Transcription Complete!
        - Chunks processed: {result.get("chunks", "N/A")}
        - Processing time: {result.get("processing_time", "N/A")}
        - Transcript length: {len(transcript)} characters
        """)

        st.session_state.pipeline_transcript = transcript
        return transcript

    def _step_wisdom_extraction(self) -> str:
        """Step 3: Extract wisdom"""
        transcript = st.session_state.pipeline_transcript

        custom_prompt = (
            st.session_state.prompts.get("wisdom_extraction") if hasattr(st.session_state, "prompts") else None
        )

        wisdom = generate_wisdom(
            transcript, custom_prompt=custom_prompt, knowledge_base=st.session_state.knowledge_base
        )

        st.session_state.pipeline_wisdom = wisdom
        return wisdom

    def _step_outline_creation(self) -> str:
        """Step 4: Create outline"""
        transcript = st.session_state.pipeline_transcript
        wisdom = st.session_state.pipeline_wisdom

        custom_prompt = (
            st.session_state.prompts.get("outline_creation") if hasattr(st.session_state, "prompts") else None
        )

        outline = generate_outline(
            transcript, wisdom, custom_prompt=custom_prompt, knowledge_base=st.session_state.knowledge_base
        )

        st.session_state.pipeline_outline = outline
        return outline

    def _step_article_creation(self) -> str:
        """Step 5: Create article"""
        transcript = st.session_state.pipeline_transcript
        wisdom = st.session_state.pipeline_wisdom
        outline = st.session_state.pipeline_outline

        custom_prompt = (
            st.session_state.prompts.get("article_creation") if hasattr(st.session_state, "prompts") else None
        )

        article = generate_article(
            transcript, wisdom, outline, custom_prompt=custom_prompt, knowledge_base=st.session_state.knowledge_base
        )

        st.session_state.pipeline_article = article
        return article

    def _step_social_content(self) -> str:
        """Step 6: Generate social media content"""
        wisdom = st.session_state.pipeline_wisdom
        outline = st.session_state.pipeline_outline
        article = st.session_state.pipeline_article

        custom_prompt = st.session_state.prompts.get("social_media") if hasattr(st.session_state, "prompts") else None

        social = generate_social_content(
            wisdom, outline, article, custom_prompt=custom_prompt, knowledge_base=st.session_state.knowledge_base
        )

        st.session_state.pipeline_social = social
        return social

    def _step_database_storage(self) -> str:
        """Step 7: Store content in database"""
        try:
            from .supabase_integration import get_supabase_client

            db = get_supabase_client()
            if not db:
                return "Database connection failed"

            results = st.session_state.pipeline_results

            result = (
                db.client.table("content")
                .insert(
                    {
                        "user_id": st.session_state.user_id,
                        "title": f"Content from {st.session_state.pipeline_file_info['name']}",
                        "transcript": results.get("transcription", ""),
                        "wisdom": results.get("wisdom_extraction", ""),
                        "outline": results.get("outline_creation", ""),
                        "article": results.get("article_creation", ""),
                        "social_content": results.get("social_content", ""),
                        "created_at": "now()",
                    }
                )
                .execute()
            )

            content_id = result.data[0]["id"] if result.data else ""
            if not content_id:
                return "Failed to save content to database"

            time.sleep(0.3)
            return f"Content saved with ID: {content_id}"

        except APIError as e:
            return f"Database save failed: {str(e)}"
        except DatabaseError as e:
            return f"Unexpected database error: {str(e)}"

    @property
    def is_active(self) -> bool:
        """Check if pipeline is currently active"""
        return st.session_state.get("pipeline_active", False)

    @property
    def is_complete(self) -> bool:
        """Check if pipeline has completed"""
        return not self.is_active and st.session_state.get("pipeline_step_index", 0) >= len(self.PIPELINE_STEPS)

    @property
    def current_step_index(self) -> int:
        """Get current step index"""
        return st.session_state.get("pipeline_step_index", 0)

    @property
    def progress_percentage(self) -> float:
        """Get overall progress percentage"""
        return (self.current_step_index / len(self.PIPELINE_STEPS)) * 100

    def get_results(self) -> dict[str, Any]:
        """Get all pipeline results"""
        return st.session_state.get("pipeline_results", {})

    def get_errors(self) -> dict[str, str]:
        """Get any pipeline errors"""
        return st.session_state.get("pipeline_errors", {})


def get_pipeline_controller() -> StreamingPipelineController:
    """Get or create the global pipeline controller"""
    if "pipeline_controller" not in st.session_state:
        st.session_state.pipeline_controller = StreamingPipelineController()
    return st.session_state.pipeline_controller
