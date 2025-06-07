"""
Content Processors
==================

Audio processing and content generation classes.
"""

import logging
import tempfile
import time
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, Dict, Any, Generator, List, Union
import hashlib

try:
    from pydub import AudioSegment
    import soundfile as sf
except ImportError:
    AudioSegment = None
    sf = None

from .config import get_config
from .integrations import AIProvider

logger = logging.getLogger(__name__)


class AudioProcessor:
    """Handles audio file processing and transcription"""
    
    def __init__(self, ai_provider: AIProvider):
        self.ai_provider = ai_provider
        self.config = get_config()
        self.temp_dir = self.config.temp_dir
        self.temp_dir.mkdir(parents=True, exist_ok=True)
    
    def estimate_duration(self, audio_path: Path) -> Optional[float]:
        """Estimate audio duration in seconds"""
        try:
            if sf is not None:
                with sf.SoundFile(str(audio_path)) as f:
                    return len(f) / f.samplerate
        except Exception as e:
            logger.warning(f"Could not read audio duration: {e}")
        return None
    
    def should_chunk_audio(self, audio_path: Path) -> bool:
        """Determine if audio file should be chunked"""
        file_size_mb = audio_path.stat().st_size / (1024 * 1024)
        return file_size_mb > self.config.audio_chunk_size_mb
    
    def chunk_audio(self, audio_path: Path, chunk_size_mb: int = None) -> List[Path]:
        """Split audio file into chunks"""
        if chunk_size_mb is None:
            chunk_size_mb = self.config.audio_chunk_size_mb
        
        if AudioSegment is None:
            raise RuntimeError("pydub not available for audio chunking")
        
        try:
            audio = AudioSegment.from_file(str(audio_path))
            duration_ms = len(audio)
            
            # Calculate chunk duration based on target size
            file_size_mb = audio_path.stat().st_size / (1024 * 1024)
            chunk_duration_ms = int((chunk_size_mb / file_size_mb) * duration_ms)
            
            chunks = []
            for i in range(0, duration_ms, chunk_duration_ms):
                chunk = audio[i:i + chunk_duration_ms]
                chunk_path = self.temp_dir / f"chunk_{i//chunk_duration_ms:03d}_{audio_path.stem}.wav"
                chunk.export(str(chunk_path), format="wav")
                chunks.append(chunk_path)
            
            logger.info(f"Split audio into {len(chunks)} chunks")
            return chunks
            
        except Exception as e:
            logger.error(f"Error chunking audio: {e}")
            raise
    
    def transcribe_file(self, audio_path: Path, progress_callback=None) -> str:
        """Transcribe an audio file, chunking if necessary"""
        logger.info(f"Processing audio file: {audio_path} (Size: {audio_path.stat().st_size / (1024*1024):.2f} MB)")
        
        if self.should_chunk_audio(audio_path):
            return self._transcribe_chunked(audio_path, progress_callback)
        else:
            return self._transcribe_direct(audio_path, progress_callback)
    
    def _transcribe_direct(self, audio_path: Path, progress_callback=None) -> str:
        """Transcribe a single audio file directly"""
        logger.info(f"Starting direct transcription of file: {audio_path}")
        
        if progress_callback:
            progress_callback(0.1, "Starting transcription...")
        
        try:
            result = self.ai_provider.transcribe_audio(audio_path)
            
            if progress_callback:
                progress_callback(1.0, "Transcription complete")
            
            logger.info(f"Transcription successful, received {len(result)} characters")
            return result
            
        except Exception as e:
            logger.error(f"Error in direct transcription: {e}")
            raise
    
    def _transcribe_chunked(self, audio_path: Path, progress_callback=None) -> str:
        """Transcribe a large audio file in chunks"""
        logger.info(f"File is large, chunking for transcription: {audio_path}")
        
        if progress_callback:
            progress_callback(0.05, "Preparing audio chunks...")
        
        # Split audio into chunks
        chunks = self.chunk_audio(audio_path)
        total_chunks = len(chunks)
        
        transcriptions = []
        
        try:
            for i, chunk_path in enumerate(chunks):
                if progress_callback:
                    progress = 0.1 + (i / total_chunks) * 0.8
                    progress_callback(progress, f"Transcribing chunk {i+1}/{total_chunks}...")
                
                logger.info(f"Transcribing chunk {i+1}/{total_chunks}: {chunk_path}")
                
                chunk_result = self.ai_provider.transcribe_audio(chunk_path)
                transcriptions.append(chunk_result)
                
                # Clean up chunk file
                try:
                    chunk_path.unlink()
                except Exception as e:
                    logger.warning(f"Could not delete chunk file {chunk_path}: {e}")
            
            combined_transcription = " ".join(transcriptions)
            
            if progress_callback:
                progress_callback(1.0, "Transcription complete")
            
            logger.info(f"Combined transcription complete: {len(combined_transcription)} characters")
            return combined_transcription
            
        except Exception as e:
            # Clean up any remaining chunks
            for chunk_path in chunks:
                try:
                    if chunk_path.exists():
                        chunk_path.unlink()
                except:
                    pass
            raise


class ContentGenerator:
    """Generates various types of content from transcripts"""
    
    def __init__(self, ai_provider: AIProvider):
        self.ai_provider = ai_provider
        self.config = get_config()
        self._prompts = {}
        self.load_prompts()
    
    def load_prompts(self) -> None:
        """Load content generation prompts"""
        self._prompts = {
            "wisdom": """You are an expert content analyst. Extract the most valuable insights, key takeaways, and wisdom from the following transcript. Focus on:

1. Core insights and lessons
2. Actionable advice
3. Unique perspectives or ideas
4. Memorable quotes or statements
5. Practical applications

Present the wisdom in a clear, organized format with bullet points or sections. Be concise but comprehensive.""",

            "outline": """Create a detailed, structured outline for content based on the transcript and extracted wisdom. The outline should:

1. Have a clear hierarchical structure (main points, sub-points)
2. Flow logically from introduction to conclusion
3. Include specific examples or details from the content
4. Be suitable for creating an article, presentation, or structured content
5. Include suggested headings and key points for each section

Format as a detailed outline with numbered or bulleted sections.""",

            "social": """Create engaging social media content based on the wisdom and outline provided. Generate:

1. 3-5 Twitter/X posts (280 characters each)
2. 2-3 LinkedIn posts (longer form, professional tone)
3. 1-2 Instagram captions with hashtag suggestions
4. Key quotes suitable for quote cards

Make the content engaging, shareable, and true to the original insights. Include relevant hashtags and calls-to-action where appropriate.""",

            "article": """Write a comprehensive, well-structured article based on the transcript, wisdom, and outline provided. The article should:

1. Have an engaging introduction that hooks the reader
2. Follow the structure provided in the outline
3. Include specific examples and insights from the original content
4. Have smooth transitions between sections
5. End with a strong conclusion that reinforces key takeaways
6. Be between 800-1500 words
7. Use a professional but accessible tone

Format with clear headings and subheadings.""",

            "image_prompts": """Based on the wisdom and outline, create detailed image generation prompts for visual content. Generate:

1. 3-5 main concept illustrations
2. 2-3 quote card designs
3. 1-2 infographic concepts
4. Social media visual ideas

Each prompt should be detailed enough for AI image generation, including:
- Visual style and mood
- Color palette suggestions
- Composition ideas
- Text overlay concepts

Make the prompts specific and creative."""
        }
    
    def generate_content(
        self, 
        content_type: str, 
        transcript: str, 
        context: Dict[str, Any] = None,
        stream_callback=None
    ) -> str:
        """Generate content of specified type"""
        
        if content_type not in self._prompts:
            raise ValueError(f"Unknown content type: {content_type}")
        
        prompt = self._prompts[content_type]
        context = context or {}
        
        # Build the input based on content type
        if content_type == "wisdom":
            user_content = f"Transcript to analyze:\n\n{transcript}"
        
        elif content_type == "outline":
            wisdom = context.get("wisdom", "")
            user_content = f"TRANSCRIPT:\n{transcript}\n\nWISDOM:\n{wisdom}"
        
        elif content_type in ["social", "image_prompts"]:
            wisdom = context.get("wisdom", "")
            outline = context.get("outline", "")
            user_content = f"WISDOM:\n{wisdom}\n\nOUTLINE:\n{outline}"
        
        elif content_type == "article":
            wisdom = context.get("wisdom", "")
            outline = context.get("outline", "")
            user_content = f"TRANSCRIPT EXCERPT:\n{transcript[:1000]}...\n\nWISDOM:\n{wisdom}\n\nOUTLINE:\n{outline}"
        
        else:
            user_content = transcript
        
        logger.info(f"Generating {content_type} content...")
        
        try:
            if stream_callback and self.config.stream_responses:
                return self._generate_streaming(prompt, user_content, stream_callback)
            else:
                return self.ai_provider.generate_completion(prompt, user_content)
        
        except Exception as e:
            logger.error(f"Error generating {content_type}: {e}")
            raise
    
    def _generate_streaming(self, system_prompt: str, user_content: str, callback) -> str:
        """Generate content with streaming output"""
        full_response = ""
        
        for chunk in self.ai_provider.generate_streaming(system_prompt, user_content):
            full_response += chunk
            if callback:
                callback(chunk, full_response)
        
        return full_response
    
    def generate_all_content(
        self, 
        transcript: str, 
        progress_callback=None
    ) -> Dict[str, str]:
        """Generate all content types in sequence"""
        
        results = {}
        content_types = ["wisdom", "outline", "social", "image_prompts", "article"]
        total_steps = len(content_types)
        
        try:
            # Step 1: Generate wisdom
            if progress_callback:
                progress_callback(0.1, "Extracting wisdom...")
            
            results["wisdom"] = self.generate_content("wisdom", transcript)
            
            # Step 2: Generate outline
            if progress_callback:
                progress_callback(0.3, "Creating outline...")
            
            results["outline"] = self.generate_content(
                "outline", 
                transcript, 
                context={"wisdom": results["wisdom"]}
            )
            
            # Step 3: Generate social content
            if progress_callback:
                progress_callback(0.5, "Creating social media content...")
            
            results["social"] = self.generate_content(
                "social", 
                transcript,
                context={"wisdom": results["wisdom"], "outline": results["outline"]}
            )
            
            # Step 4: Generate image prompts
            if progress_callback:
                progress_callback(0.7, "Creating image prompts...")
            
            results["image_prompts"] = self.generate_content(
                "image_prompts",
                transcript,
                context={"wisdom": results["wisdom"], "outline": results["outline"]}
            )
            
            # Step 5: Generate article
            if progress_callback:
                progress_callback(0.9, "Writing article...")
            
            results["article"] = self.generate_content(
                "article",
                transcript,
                context={"wisdom": results["wisdom"], "outline": results["outline"]}
            )
            
            if progress_callback:
                progress_callback(1.0, "Content generation complete!")
            
            return results
            
        except Exception as e:
            logger.error(f"Error in content generation pipeline: {e}")
            raise


class ContentCache:
    """Simple file-based cache for generated content"""
    
    def __init__(self, cache_dir: Path = None):
        self.cache_dir = cache_dir or get_config().data_dir / "cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_cache_key(self, content: str, content_type: str) -> str:
        """Generate cache key from content"""
        content_hash = hashlib.md5(content.encode()).hexdigest()
        return f"{content_type}_{content_hash}"
    
    def get(self, transcript: str, content_type: str) -> Optional[str]:
        """Get cached content if available"""
        cache_key = self._get_cache_key(transcript, content_type)
        cache_file = self.cache_dir / f"{cache_key}.txt"
        
        if cache_file.exists():
            try:
                return cache_file.read_text(encoding='utf-8')
            except Exception as e:
                logger.warning(f"Error reading cache file: {e}")
        
        return None
    
    def set(self, transcript: str, content_type: str, content: str) -> None:
        """Cache generated content"""
        cache_key = self._get_cache_key(transcript, content_type)
        cache_file = self.cache_dir / f"{cache_key}.txt"
        
        try:
            cache_file.write_text(content, encoding='utf-8')
        except Exception as e:
            logger.warning(f"Error writing cache file: {e}")
    
    def clear(self) -> None:
        """Clear all cached content"""
        for cache_file in self.cache_dir.glob("*.txt"):
            try:
                cache_file.unlink()
            except Exception as e:
                logger.warning(f"Error deleting cache file {cache_file}: {e}") 