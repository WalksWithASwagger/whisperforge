"""Filesystem path validation utilities for WhisperForge.

Ensures that user-supplied filenames cannot escape a designated root
directory, preventing path-traversal attacks.
"""

import re
from pathlib import Path

# Only allow alphanumeric, hyphens, underscores, and single dots (no ..)
_SAFE_FILENAME_RE = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9._-]*$")


def safe_path(root: str, untrusted_name: str) -> Path:
    """Build a file path that is guaranteed to stay within *root*.

    Raises ValueError if the resulting path escapes the root directory
    or if the filename contains disallowed characters.
    """
    if not _SAFE_FILENAME_RE.match(untrusted_name):
        raise ValueError(
            f"Invalid filename: {untrusted_name!r}. "
            "Only alphanumeric characters, hyphens, underscores, and dots are allowed."
        )
    if ".." in untrusted_name:
        raise ValueError("Path traversal sequences are not allowed.")

    root_resolved = Path(root).resolve()
    target = (root_resolved / untrusted_name).resolve()

    if not target.is_relative_to(root_resolved):
        raise ValueError(f"Path escapes allowed directory: {target} is not under {root_resolved}")
    return target
