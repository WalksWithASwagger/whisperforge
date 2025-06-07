"""
Content Pipeline
================

Main orchestration class for the WhisperForge content generation pipeline.
"""

import logging
import tempfile
from pathlib import Path
from typing import Dict, Any, Optional, Callable, List
from datetime import datetime
import hashlib

from .config import get_config
from .processors import AudioProcessor, ContentGenerator, ContentCache
from .integrations import create_ai_provider, create_notion_exporter, AIProvider

logger = logging.getLogger(__name__)


class PipelineResult:
    """Container for pipeline execution results"""
    
    def __init__(
        self,
        transcript: str = "",
        content: Dict[str, str] = None,
        metadata: Dict[str, Any] = None,
        notion_page_id: str = None
    ):
        self.transcript = transcript
        self.content = content or {}
        self.metadata = metadata or {}
        self.notion_page_id = notion_page_id
        self.created_at = datetime.now()
    
    def get_content(self, content_type: str) -> Optional[str]:
        """Get specific content type"""
        return self.content.get(content_type)
    
    def has_content(self, content_type: str) -> bool:
        """Check if content type exists"""
        return content_type in self.content and bool(self.content[content_type])
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "transcript": self.transcript,
            "content": self.content,
            "metadata": self.metadata,
            "notion_page_id": self.notion_page_id,
            "created_at": self.created_at.isoformat()
        }


class ContentPipeline:
    """
    Main content generation pipeline
    
    Orchestrates the entire process from audio input to final content output.
    """
    
    def __init__(
        self, 
        ai_provider: str = "openai",
        use_cache: bool = True,
        export_to_notion: bool = True
    ):
        self.config = get_config()
        
        # Initialize AI provider for transcription (must support audio)
        self.transcription_provider = self._get_transcription_provider(ai_provider)
        
        # Initialize content generation provider (can be different)
        self.content_provider = create_ai_provider(ai_provider)
        
        # Initialize processors
        self.audio_processor = AudioProcessor(self.transcription_provider)
        self.content_generator = ContentGenerator(self.content_provider)
        
        # Initialize cache if enabled
        self.cache = ContentCache() if use_cache else None
        
        # Initialize Notion exporter if configured
        self.notion_exporter = create_notion_exporter() if export_to_notion else None
        
        logger.info(f"Pipeline initialized with AI provider: {ai_provider}")
    
    def _get_transcription_provider(self, provider_name: str) -> AIProvider:
        """Get AI provider that supports transcription"""
        provider = create_ai_provider(provider_name)
        
        # Only OpenAI supports transcription currently
        if provider_name.lower() != "openai":
            logger.warning(f"{provider_name} doesn't support transcription, falling back to OpenAI")
            try:
                provider = create_ai_provider("openai")
            except Exception as e:
                raise RuntimeError(f"OpenAI is required for transcription but not available: {e}")
        
        return provider
    
    def process_audio_file(
        self,
        audio_path: Path,
        generate_all_content: bool = True,
        content_types: List[str] = None,
        progress_callback: Callable[[float, str], None] = None,
        stream_callback: Callable[[str, str], None] = None
    ) -> PipelineResult:
        """
        Process audio file through the complete pipeline
        
        Args:
            audio_path: Path to audio file
            generate_all_content: Whether to generate all content types
            content_types: Specific content types to generate (if not all)
            progress_callback: Callback for progress updates (progress, message)
            stream_callback: Callback for streaming content updates (chunk, full_content)
        
        Returns:
            PipelineResult containing all generated content
        """
        
        logger.info(f"Starting pipeline for audio file: {audio_path}")
        
        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
        
        result = PipelineResult()
        
        try:
            # Step 1: Transcribe audio
            if progress_callback:
                progress_callback(0.1, "Transcribing audio...")
            
            transcript = self._transcribe_with_progress(audio_path, progress_callback)
            result.transcript = transcript
            
            if progress_callback:
                progress_callback(0.3, "Transcription complete. Generating content...")
            
            # Step 2: Generate content
            if generate_all_content:
                content = self._generate_all_content(transcript, progress_callback, stream_callback)
            else:
                content = self._generate_specific_content(
                    transcript, 
                    content_types or ["wisdom"], 
                    progress_callback, 
                    stream_callback
                )
            
            result.content = content
            
            # Step 3: Export to Notion (if configured)
            if self.notion_exporter and progress_callback:
                progress_callback(0.9, "Exporting to Notion...")
                result.notion_page_id = self._export_to_notion(result)
            
            # Step 4: Add metadata
            result.metadata = self._build_metadata(audio_path, content)
            
            if progress_callback:
                progress_callback(1.0, "Pipeline complete!")
            
            logger.info("Pipeline completed successfully")
            return result
            
        except Exception as e:
            logger.error(f"Pipeline error: {e}")
            raise
    
    def _transcribe_with_progress(
        self, 
        audio_path: Path, 
        progress_callback: Callable[[float, str], None] = None
    ) -> str:
        """Transcribe audio with progress updates"""
        
        def transcription_progress(progress: float, message: str):
            # Map transcription progress to 0.1-0.3 range of overall progress
            overall_progress = 0.1 + (progress * 0.2)
            if progress_callback:
                progress_callback(overall_progress, message)
        
        return self.audio_processor.transcribe_file(audio_path, transcription_progress)
    
    def _generate_all_content(
        self,
        transcript: str,
        progress_callback: Callable[[float, str], None] = None,
        stream_callback: Callable[[str, str], None] = None
    ) -> Dict[str, str]:
        """Generate all content types"""
        
        def content_progress(progress: float, message: str):
            # Map content generation to 0.3-0.9 range of overall progress
            overall_progress = 0.3 + (progress * 0.6)
            if progress_callback:
                progress_callback(overall_progress, message)
        
        return self.content_generator.generate_all_content(transcript, content_progress)
    
    def _generate_specific_content(
        self,
        transcript: str,
        content_types: List[str],
        progress_callback: Callable[[float, str], None] = None,
        stream_callback: Callable[[str, str], None] = None
    ) -> Dict[str, str]:
        """Generate specific content types"""
        
        content = {}
        total_types = len(content_types)
        
        for i, content_type in enumerate(content_types):
            if progress_callback:
                progress = 0.3 + ((i / total_types) * 0.6)
                progress_callback(progress, f"Generating {content_type}...")
            
            # Check cache first
            if self.cache:
                cached_content = self.cache.get(transcript, content_type)
                if cached_content:
                    content[content_type] = cached_content
                    continue
            
            # Generate content
            context = content  # Pass previously generated content as context
            generated = self.content_generator.generate_content(
                content_type, 
                transcript, 
                context, 
                stream_callback
            )
            
            content[content_type] = generated
            
            # Cache the result
            if self.cache:
                self.cache.set(transcript, content_type, generated)
        
        return content
    
    def _export_to_notion(self, result: PipelineResult) -> Optional[str]:
        """Export results to Notion"""
        if not self.notion_exporter:
            return None
        
        try:
            # Generate title from transcript
            title = self._generate_title(result.transcript)
            
            # Generate tags
            tags = self._generate_tags(result.content.get("wisdom", ""))
            
            page_id = self.notion_exporter.create_page(
                title=title,
                transcript=result.transcript,
                content=result.content,
                tags=tags
            )
            
            logger.info(f"Exported to Notion: {page_id}")
            return page_id
            
        except Exception as e:
            logger.error(f"Error exporting to Notion: {e}")
            return None
    
    def _generate_title(self, transcript: str) -> str:
        """Generate a title for the content"""
        # Use a simple approach - take first meaningful sentence or generate with AI
        try:
            prompt = "Generate a concise, descriptive title (max 60 characters) for this content:"
            title = self.content_provider.generate_completion(prompt, transcript[:500])
            return title.strip().strip('"\'')
        except Exception:
            # Fallback to simple title
            words = transcript.split()[:8]
            return " ".join(words) + ("..." if len(transcript.split()) > 8 else "")
    
    def _generate_tags(self, wisdom: str) -> List[str]:
        """Generate tags from wisdom content"""
        if not wisdom:
            return ["whisperforge", "audio", "transcription"]
        
        try:
            prompt = """Generate 3-5 relevant tags for this content. Return only the tags, separated by commas:"""
            tags_response = self.content_provider.generate_completion(prompt, wisdom[:500])
            tags = [tag.strip() for tag in tags_response.split(",")]
            return tags[:5]  # Limit to 5 tags
        except Exception:
            return ["whisperforge", "audio", "transcription"]
    
    def _build_metadata(self, audio_path: Path, content: Dict[str, str]) -> Dict[str, Any]:
        """Build metadata for the result"""
        return {
            "source_file": str(audio_path.name),
            "file_size_mb": round(audio_path.stat().st_size / (1024 * 1024), 2),
            "content_types_generated": list(content.keys()),
            "total_content_length": sum(len(c) for c in content.values()),
            "pipeline_version": "2.0.0",
            "ai_provider": self.content_provider.name,
            "processing_date": datetime.now().isoformat()
        }
    
    def process_text_input(
        self,
        text: str,
        content_types: List[str] = None,
        progress_callback: Callable[[float, str], None] = None,
        stream_callback: Callable[[str, str], None] = None
    ) -> PipelineResult:
        """
        Process text input directly (skip transcription)
        
        Useful for processing existing transcripts or text content.
        """
        
        logger.info("Starting pipeline for text input")
        
        result = PipelineResult()
        result.transcript = text
        
        try:
            if progress_callback:
                progress_callback(0.1, "Processing text input...")
            
            # Generate content
            content_types = content_types or ["wisdom", "outline", "social", "article"]
            content = self._generate_specific_content(
                text, 
                content_types, 
                progress_callback, 
                stream_callback
            )
            
            result.content = content
            
            # Export to Notion if configured
            if self.notion_exporter:
                if progress_callback:
                    progress_callback(0.9, "Exporting to Notion...")
                result.notion_page_id = self._export_to_notion(result)
            
            # Add metadata
            result.metadata = self._build_text_metadata(text, content)
            
            if progress_callback:
                progress_callback(1.0, "Processing complete!")
            
            logger.info("Text processing completed successfully")
            return result
            
        except Exception as e:
            logger.error(f"Text processing error: {e}")
            raise
    
    def _build_text_metadata(self, text: str, content: Dict[str, str]) -> Dict[str, Any]:
        """Build metadata for text input"""
        return {
            "input_type": "text",
            "input_length": len(text),
            "content_types_generated": list(content.keys()),
            "total_content_length": sum(len(c) for c in content.values()),
            "pipeline_version": "2.0.0",
            "ai_provider": self.content_provider.name,
            "processing_date": datetime.now().isoformat()
        }
    
    def get_supported_content_types(self) -> List[str]:
        """Get list of supported content types"""
        return ["wisdom", "outline", "social", "image_prompts", "article"]
    
    def test_connections(self) -> Dict[str, bool]:
        """Test all external service connections"""
        results = {}
        
        # Test AI provider
        try:
            test_response = self.content_provider.generate_completion(
                "Respond with 'OK' if this works:", 
                "Test message"
            )
            results["ai_provider"] = "OK" in test_response.upper()
        except Exception as e:
            logger.error(f"AI provider test failed: {e}")
            results["ai_provider"] = False
        
        # Test Notion if configured
        if self.notion_exporter:
            results["notion"] = self.notion_exporter.test_connection()
        else:
            results["notion"] = None  # Not configured
        
        return results
    
    def clear_cache(self) -> None:
        """Clear content cache"""
        if self.cache:
            self.cache.clear()
            logger.info("Cache cleared")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        if not self.cache:
            return {"enabled": False}
        
        cache_files = list(self.cache.cache_dir.glob("*.txt"))
        total_size = sum(f.stat().st_size for f in cache_files)
        
        return {
            "enabled": True,
            "files": len(cache_files),
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "cache_dir": str(self.cache.cache_dir)
        } 