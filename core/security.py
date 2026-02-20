"""Password hashing and verification utilities for WhisperForge.

Provides bcrypt-based password hashing for current use and a deprecated
SHA-256 helper retained solely for migrating legacy credential stores.
"""

import hashlib
import logging
import warnings

import bcrypt

logger = logging.getLogger(__name__)


def hash_password(password: str) -> str:
    """Hash a password using bcrypt with salt"""
    # Generate salt and hash password
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(password: str, hashed: str) -> bool:
    """Verify a password against its hash.

    Raises on unexpected errors (e.g. DB corruption) instead of
    silently returning False which would be indistinguishable from
    a wrong password.
    """
    try:
        return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))
    except ValueError as e:
        # Malformed hash string (wrong prefix, bad encoding, etc.)
        logger.error("Password verification failed – malformed hash: %s", e)
        return False


def legacy_hash_password(password: str) -> str:
    """Legacy SHA-256 hash - DEPRECATED, use for migration only.

    .. deprecated::
        Use :func:`hash_password` (bcrypt) for all new credential storage.
    """
    warnings.warn(
        "legacy_hash_password() is deprecated and will be removed in a future release. "
        "Use hash_password() (bcrypt) instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    return hashlib.sha256(password.encode()).hexdigest()
