"""Backward-compatible re-export shim for ``core.utils``.

.. deprecated::
    This module is **deprecated** and exists only so that existing import
    sites (e.g. ``from .utils import hash_password``) continue to work
    without modification.  All public symbols have been relocated to
    focused modules:

    * **Security** (``core.security``): ``hash_password``,
      ``verify_password``, ``legacy_hash_password``
    * **Path safety** (``core.path_safety``): ``safe_path``
    * **Prompts** (``core.prompts``): ``DEFAULT_PROMPTS``,
      ``load_prompt_from_file``, ``format_knowledge_base_context``,
      ``get_enhanced_prompt``
    * **API clients** (``core.api_clients``): ``get_openai_client``,
      ``get_anthropic_client``, ``get_grok_api_key``, ``get_grok_client``

    New code should import directly from those modules.
"""

import logging
import warnings

# ---- Re-exports from core.api_clients ---------------------------------
from .api_clients import (
    get_anthropic_client,
    get_grok_api_key,
    get_grok_client,
    get_openai_client,
)

# ---- Re-exports from core.path_safety ---------------------------------
from .path_safety import safe_path

# ---- Re-exports from core.prompts -------------------------------------
from .prompts import (
    DEFAULT_PROMPTS,
    format_knowledge_base_context,
    get_enhanced_prompt,
    load_prompt_from_file,
)

# ---- Re-exports from core.security ------------------------------------
from .security import hash_password, legacy_hash_password, verify_password

logger = logging.getLogger(__name__)


# ---- Deprecated helpers kept inline ------------------------------------


def update_usage_tracking(duration_seconds: float):
    """Placeholder for usage tracking - implement as needed.

    .. deprecated::
        ``update_usage_tracking`` will be removed in a future release.
    """
    warnings.warn(
        "update_usage_tracking() is deprecated and will be removed in a future release.",
        DeprecationWarning,
        stacklevel=2,
    )
    logger.info(f"Usage tracked: {duration_seconds} seconds")


def get_prompt(prompt_type: str, prompts: dict[str, str], default_prompts: dict[str, str]) -> str:
    """Get prompt from user prompts or defaults.

    .. deprecated::
        Use :func:`core.prompts.get_enhanced_prompt` instead.
    """
    warnings.warn(
        "get_prompt() is deprecated. Use get_enhanced_prompt() from core.prompts instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    return prompts.get(prompt_type, default_prompts.get(prompt_type, ""))


__all__ = [
    # core.security
    "hash_password",
    "verify_password",
    "legacy_hash_password",
    # core.path_safety
    "safe_path",
    # core.prompts
    "DEFAULT_PROMPTS",
    "load_prompt_from_file",
    "format_knowledge_base_context",
    "get_enhanced_prompt",
    # core.api_clients
    "get_openai_client",
    "get_anthropic_client",
    "get_grok_api_key",
    "get_grok_client",
    # deprecated inline helpers
    "update_usage_tracking",
    "get_prompt",
]
