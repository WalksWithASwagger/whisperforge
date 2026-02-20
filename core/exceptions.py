"""
WhisperForge custom exception hierarchy.

All project-specific exceptions inherit from WhisperForgeError so callers
can catch the entire family if needed.
"""


class WhisperForgeError(Exception):
    """Base exception for all WhisperForge errors."""


class DatabaseError(WhisperForgeError):
    """Raised when a Supabase / database operation fails."""


class AuthenticationError(WhisperForgeError):
    """Raised when authentication or session operations fail."""


class PipelineError(WhisperForgeError):
    """Raised when a pipeline step fails."""


class FileProcessingError(WhisperForgeError):
    """Raised when file upload or audio processing fails."""


class APIClientError(WhisperForgeError):
    """Raised when an external API call fails."""
