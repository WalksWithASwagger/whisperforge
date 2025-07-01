"""
Configuration Management
========================

Centralized configuration for WhisperForge v2.0
"""

import os
from typing import Dict, Optional, Any
from dataclasses import dataclass, field
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


@dataclass
class AIProviderConfig:
    """Configuration for AI providers"""

    name: str
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    models: Dict[str, Any] = field(default_factory=dict)
    rate_limits: Dict[str, int] = field(default_factory=dict)


@dataclass
class NotionConfig:
    """Configuration for Notion integration"""

    api_key: Optional[str] = None
    database_id: Optional[str] = None
    template_id: Optional[str] = None


@dataclass
class Config:
    """Main configuration class"""

    # File paths
    project_root: Path = field(default_factory=lambda: Path.cwd())
    data_dir: Path = field(default_factory=lambda: Path.cwd() / "data")
    prompts_dir: Path = field(default_factory=lambda: Path.cwd() / "prompts")
    temp_dir: Path = field(default_factory=lambda: Path.cwd() / "temp")

    # AI Providers
    openai: AIProviderConfig = field(default_factory=lambda: AIProviderConfig("openai"))
    anthropic: AIProviderConfig = field(
        default_factory=lambda: AIProviderConfig("anthropic")
    )
    grok: AIProviderConfig = field(default_factory=lambda: AIProviderConfig("grok"))

    # Integrations
    notion: NotionConfig = field(default_factory=NotionConfig)

    # Processing settings
    audio_chunk_size_mb: int = 25
    max_tokens: int = 4000
    stream_responses: bool = True

    # Environment & UI settings
    environment: str = "development"
    debug_mode: bool = False
    log_level: str = "INFO"

    @property
    def is_development(self) -> bool:
        """Check if running in development mode"""
        return self.environment.lower() == "development"

    @property
    def is_production(self) -> bool:
        """Check if running in production mode"""
        return self.environment.lower() == "production"

    @classmethod
    def from_env(cls) -> "Config":
        """Load configuration from environment variables"""
        config = cls()

        # Load API keys from environment
        config.openai.api_key = os.getenv("OPENAI_API_KEY")
        config.anthropic.api_key = os.getenv("ANTHROPIC_API_KEY")
        config.grok.api_key = os.getenv("GROK_API_KEY")
        config.notion.api_key = os.getenv("NOTION_API_KEY")
        config.notion.database_id = os.getenv("NOTION_DATABASE_ID")

        # Load other settings
        config.environment = os.getenv("ENVIRONMENT", "development")
        config.debug_mode = os.getenv("DEBUG", "false").lower() == "true"
        # Default log level varies by environment if not explicitly set
        default_level = "DEBUG" if config.environment == "development" else "INFO"
        config.log_level = os.getenv("LOG_LEVEL", default_level)

        return config

    @classmethod
    def from_file(cls, config_path: Path) -> "Config":
        """Load configuration (simplified version without YAML)"""
        # For now, just use environment variables
        logger.info(
            "Using environment variables for configuration (YAML support disabled)"
        )
        return cls.from_env()

    def validate(self) -> bool:
        """Validate configuration"""
        errors = []

        # Check for at least one AI provider
        if not any([self.openai.api_key, self.anthropic.api_key, self.grok.api_key]):
            errors.append("At least one AI provider API key is required")

        # Validate directories exist or can be created
        for dir_path in [self.data_dir, self.prompts_dir, self.temp_dir]:
            try:
                dir_path.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                errors.append(f"Cannot create directory {dir_path}: {e}")

        if errors:
            for error in errors:
                logger.error(error)
            return False

        return True

    def get_available_providers(self) -> list[str]:
        """Get list of available AI providers"""
        providers = []
        if self.openai.api_key:
            providers.append("openai")
        if self.anthropic.api_key:
            providers.append("anthropic")
        if self.grok.api_key:
            providers.append("grok")
        return providers


# Global config instance
_config: Optional[Config] = None


def get_config() -> Config:
    """Get the global configuration instance"""
    global _config
    if _config is None:
        _config = Config.from_env()
    return _config


def set_config(config: Config) -> None:
    """Set the global configuration instance"""
    global _config
    _config = config
