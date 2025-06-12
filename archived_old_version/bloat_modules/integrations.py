"""
External Service Integrations
=============================

AI providers and other external service integrations.
"""

import json
import logging
import requests
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, Generator, Optional
from datetime import datetime

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

try:
    from anthropic import Anthropic
except ImportError:
    Anthropic = None

try:
    from notion_client import Client as NotionClient
except ImportError:
    NotionClient = None

from .config import get_config, AIProviderConfig

logger = logging.getLogger(__name__)


class AIProvider(ABC):
    """Abstract base class for AI providers"""
    
    def __init__(self, config: AIProviderConfig):
        self.config = config
        self.name = config.name
        
    @abstractmethod
    def transcribe_audio(self, audio_path: Path) -> str:
        """Transcribe audio file to text"""
        pass
    
    @abstractmethod
    def generate_completion(self, system_prompt: str, user_content: str) -> str:
        """Generate a completion for the given prompts"""
        pass
    
    @abstractmethod
    def generate_streaming(self, system_prompt: str, user_content: str) -> Generator[str, None, None]:
        """Generate a streaming completion"""
        pass
    
    @abstractmethod
    def get_available_models(self) -> list[str]:
        """Get list of available models"""
        pass


class OpenAIProvider(AIProvider):
    """OpenAI integration"""
    
    def __init__(self, config: AIProviderConfig):
        super().__init__(config)
        if OpenAI is None:
            raise RuntimeError("OpenAI library not installed")
        
        if not config.api_key:
            raise ValueError("OpenAI API key is required")
        
        self.client = OpenAI(api_key=config.api_key)
        self.default_model = "gpt-4o"
        self.whisper_model = "whisper-1"
    
    def transcribe_audio(self, audio_path: Path) -> str:
        """Transcribe audio using Whisper"""
        logger.debug(f"Making OpenAI Whisper API request for: {audio_path}")
        
        try:
            with open(audio_path, "rb") as audio_file:
                response = self.client.audio.transcriptions.create(
                    model=self.whisper_model,
                    file=audio_file,
                    response_format="text"
                )
            
            if isinstance(response, str):
                return response
            else:
                return response.text if hasattr(response, 'text') else str(response)
                
        except Exception as e:
            logger.error(f"OpenAI transcription error: {e}")
            raise
    
    def generate_completion(self, system_prompt: str, user_content: str, model: str = None) -> str:
        """Generate completion using ChatGPT"""
        model = model or self.default_model
        
        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content}
                ],
                max_tokens=get_config().max_tokens
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"OpenAI completion error: {e}")
            raise
    
    def generate_streaming(self, system_prompt: str, user_content: str, model: str = None) -> Generator[str, None, None]:
        """Generate streaming completion"""
        model = model or self.default_model
        
        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content}
                ],
                max_tokens=get_config().max_tokens,
                stream=True
            )
            
            for chunk in response:
                if hasattr(chunk.choices[0].delta, "content") and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            logger.error(f"OpenAI streaming error: {e}")
            raise
    
    def get_available_models(self) -> list[str]:
        """Get available OpenAI models"""
        return [
            "gpt-4o",
            "gpt-4o-mini", 
            "gpt-4-turbo",
            "gpt-3.5-turbo"
        ]


class AnthropicProvider(AIProvider):
    """Anthropic Claude integration"""
    
    def __init__(self, config: AIProviderConfig):
        super().__init__(config)
        if Anthropic is None:
            raise RuntimeError("Anthropic library not installed")
        
        if not config.api_key:
            raise ValueError("Anthropic API key is required")
        
        self.client = Anthropic(api_key=config.api_key)
        self.default_model = "claude-3-5-sonnet-20241022"
    
    def transcribe_audio(self, audio_path: Path) -> str:
        """Anthropic doesn't support transcription"""
        raise NotImplementedError("Anthropic doesn't support audio transcription")
    
    def generate_completion(self, system_prompt: str, user_content: str, model: str = None) -> str:
        """Generate completion using Claude"""
        model = model or self.default_model
        
        try:
            response = self.client.messages.create(
                model=model,
                max_tokens=get_config().max_tokens,
                system=system_prompt,
                messages=[{"role": "user", "content": user_content}]
            )
            
            return response.content[0].text
            
        except Exception as e:
            logger.error(f"Anthropic completion error: {e}")
            raise
    
    def generate_streaming(self, system_prompt: str, user_content: str, model: str = None) -> Generator[str, None, None]:
        """Generate streaming completion"""
        model = model or self.default_model
        
        try:
            with self.client.messages.stream(
                model=model,
                max_tokens=get_config().max_tokens,
                system=system_prompt,
                messages=[{"role": "user", "content": user_content}]
            ) as stream:
                for text in stream.text_stream:
                    yield text
                    
        except Exception as e:
            logger.error(f"Anthropic streaming error: {e}")
            raise
    
    def get_available_models(self) -> list[str]:
        """Get available Anthropic models"""
        return [
            "claude-3-5-sonnet-20241022",
            "claude-3-5-haiku-20241022",
            "claude-3-opus-20240229",
            "claude-3-sonnet-20240229",
            "claude-3-haiku-20240307"
        ]


class GrokProvider(AIProvider):
    """Grok (X.AI) integration"""
    
    def __init__(self, config: AIProviderConfig):
        super().__init__(config)
        if not config.api_key:
            raise ValueError("Grok API key is required")
        
        self.api_key = config.api_key
        self.base_url = config.base_url or "https://api.grok.x.ai/v1"
        self.default_model = "grok-1"
    
    def transcribe_audio(self, audio_path: Path) -> str:
        """Grok doesn't support transcription"""
        raise NotImplementedError("Grok doesn't support audio transcription")
    
    def generate_completion(self, system_prompt: str, user_content: str, model: str = None) -> str:
        """Generate completion using Grok API"""
        model = model or self.default_model
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ],
            "max_tokens": get_config().max_tokens
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=60
            )
            response.raise_for_status()
            
            result = response.json()
            return result["choices"][0]["message"]["content"]
            
        except Exception as e:
            logger.error(f"Grok completion error: {e}")
            raise
    
    def generate_streaming(self, system_prompt: str, user_content: str, model: str = None) -> Generator[str, None, None]:
        """Grok streaming not implemented"""
        # For now, just return the full response as a single chunk
        content = self.generate_completion(system_prompt, user_content, model)
        yield content
    
    def get_available_models(self) -> list[str]:
        """Get available Grok models"""
        return ["grok-1"]


class NotionExporter:
    """Notion integration for exporting content"""
    
    def __init__(self, api_key: str, database_id: str):
        if NotionClient is None:
            raise RuntimeError("notion-client library not installed")
        
        self.client = NotionClient(auth=api_key)
        self.database_id = database_id
    
    def create_page(
        self,
        title: str,
        transcript: str,
        content: Dict[str, str] = None,
        tags: list[str] = None
    ) -> str:
        """Create a new Notion page with content"""
        
        content = content or {}
        tags = tags or []
        
        # Build page properties
        properties = {
            "Name": {"title": [{"text": {"content": title}}]},
            "Created Date": {"date": {"start": datetime.now().isoformat()}},
        }
        
        if tags:
            properties["Tags"] = {
                "multi_select": [{"name": tag} for tag in tags[:10]]  # Notion limit
            }
        
        # Build content blocks
        children = []
        
        # Add summary if wisdom exists
        if content.get("wisdom"):
            children.append({
                "type": "callout",
                "callout": {
                    "rich_text": [{"type": "text", "text": {"content": content["wisdom"][:2000]}}],
                    "color": "purple_background",
                    "icon": {"type": "emoji", "emoji": "💡"}
                }
            })
        
        # Add content sections as toggles
        sections = [
            ("📝 Transcription", transcript),
            ("💡 Wisdom", content.get("wisdom")),
            ("📋 Outline", content.get("outline")), 
            ("📱 Social Content", content.get("social")),
            ("🎨 Image Prompts", content.get("image_prompts")),
            ("📄 Article", content.get("article"))
        ]
        
        for section_title, section_content in sections:
            if section_content:
                # Split content into chunks for Notion's block limit
                chunks = self._chunk_text(section_content, 2000)
                
                children.append({
                    "type": "toggle",
                    "toggle": {
                        "rich_text": [{"type": "text", "text": {"content": section_title}}],
                        "children": [
                            {
                                "type": "paragraph",
                                "paragraph": {
                                    "rich_text": [{"type": "text", "text": {"content": chunk}}]
                                }
                            } for chunk in chunks[:5]  # Limit chunks
                        ]
                    }
                })
        
        # Add metadata
        children.append({
            "type": "heading_2",
            "heading_2": {
                "rich_text": [{"type": "text", "text": {"content": "Metadata"}}]
            }
        })
        
        children.append({
            "type": "paragraph",
            "paragraph": {
                "rich_text": [
                    {"type": "text", "text": {"content": "Created with "}},
                    {"type": "text", "text": {"content": "WhisperForge v2.0"}, 
                     "annotations": {"bold": True, "color": "purple"}}
                ]
            }
        })
        
        try:
            response = self.client.pages.create(
                parent={"database_id": self.database_id},
                properties=properties,
                children=children
            )
            
            page_id = response["id"]
            logger.info(f"Created Notion page: {page_id}")
            return page_id
            
        except Exception as e:
            logger.error(f"Error creating Notion page: {e}")
            raise
    
    def _chunk_text(self, text: str, chunk_size: int = 2000) -> list[str]:
        """Split text into chunks for Notion blocks"""
        chunks = []
        for i in range(0, len(text), chunk_size):
            chunks.append(text[i:i + chunk_size])
        return chunks
    
    def test_connection(self) -> bool:
        """Test Notion API connection"""
        try:
            # Try to retrieve database info
            response = self.client.databases.retrieve(self.database_id)
            logger.info("Notion connection test successful")
            return True
        except Exception as e:
            logger.error(f"Notion connection test failed: {e}")
            return False


def create_ai_provider(provider_name: str) -> AIProvider:
    """Factory function to create AI providers"""
    config = get_config()
    
    if provider_name.lower() == "openai":
        return OpenAIProvider(config.openai)
    elif provider_name.lower() == "anthropic":
        return AnthropicProvider(config.anthropic)
    elif provider_name.lower() == "grok":
        return GrokProvider(config.grok)
    else:
        raise ValueError(f"Unknown AI provider: {provider_name}")


def create_notion_exporter() -> Optional[NotionExporter]:
    """Create Notion exporter if configured"""
    config = get_config()
    
    if config.notion.api_key and config.notion.database_id:
        return NotionExporter(config.notion.api_key, config.notion.database_id)
    else:
        logger.warning("Notion not configured - exporter not available")
        return None 