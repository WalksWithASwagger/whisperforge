"""
Service Locator / DI Container
================================

Lightweight dependency-injection container for WhisperForge.
Each field defaults to ``None`` and falls back to the existing
module-level singleton on first access, so existing code keeps
working unchanged while tests and alternative front-ends can
inject their own implementations.

Usage::

    from core.services import get_services

    svc = get_services()
    cfg = svc.get_config()       # lazily loads the global Config
    db  = svc.get_db()           # lazily loads the global SupabaseClient
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .auth_wrapper import AuthWrapper
    from .config import Config
    from .session_manager import SessionManager
    from .supabase_integration import SupabaseClient

logger = logging.getLogger(__name__)


@dataclass
class Services:
    """Central service registry with lazy fallbacks to existing singletons."""

    config: Config | None = None
    db: SupabaseClient | None = None
    auth: AuthWrapper | None = None
    session: SessionManager | None = None

    # -- lazy getters -------------------------------------------------------

    def get_config(self) -> Config:
        """Return the injected Config or fall back to the global singleton."""
        if self.config is not None:
            return self.config
        from .config import get_config

        return get_config()

    def get_db(self) -> SupabaseClient:
        """Return the injected DB client or fall back to the global singleton."""
        if self.db is not None:
            return self.db
        from .supabase_integration import get_supabase_client

        return get_supabase_client()

    def get_auth(self) -> AuthWrapper:
        """Return the injected AuthWrapper or fall back to the global singleton."""
        if self.auth is not None:
            return self.auth
        from .auth_wrapper import get_auth

        return get_auth()

    def get_session(self) -> SessionManager:
        """Return the injected SessionManager or fall back to the global singleton."""
        if self.session is not None:
            return self.session
        from .session_manager import get_session_manager

        return get_session_manager()


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------

_services: Services | None = None


def get_services() -> Services:
    """Return the current global ``Services`` instance (created on first call)."""
    global _services
    if _services is None:
        _services = Services()
    return _services


def set_services(services: Services) -> None:
    """Replace the global ``Services`` instance (useful in tests)."""
    global _services
    _services = services
