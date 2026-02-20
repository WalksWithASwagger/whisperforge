"""
Prompt Loading Utilities
========================

Load and manage AI prompts from the filesystem.
"""

import logging
import os

import streamlit as st

logger = logging.getLogger(__name__)


def load_custom_prompts() -> dict[str, str]:
    """Load custom prompts from the prompts/default directory."""
    prompts = {}
    prompt_dir = "prompts/default"

    if os.path.exists(prompt_dir):
        for filename in os.listdir(prompt_dir):
            if filename.endswith(".md"):
                prompt_name = filename.replace(".md", "")
                try:
                    with open(os.path.join(prompt_dir, filename), encoding="utf-8") as f:
                        prompts[prompt_name] = f.read()
                except Exception as e:
                    st.warning(f"Failed to load prompt {filename}: {e}")

    return prompts


def load_template(template_name: str) -> str | None:
    """Load an article template by name from the templates folder."""
    template_path = os.path.join("templates", f"{template_name}.md")
    if os.path.exists(template_path):
        with open(template_path, encoding="utf-8") as f:
            return f.read()
    return None


# Maps pipeline step names to prompt file basenames
_STEP_PROMPT_MAP = {
    "wisdom": "wisdom_extraction",
    "outline": "outline_creation",
    "social": "social_media",
    "article": "article_generation",
}


def get_prompt_for_step(step_name: str, custom_prompts: dict[str, str] | None = None) -> str | None:
    """Get the appropriate prompt for a pipeline step."""
    if not custom_prompts:
        custom_prompts = load_custom_prompts()

    prompt_key = _STEP_PROMPT_MAP.get(step_name)
    if prompt_key and prompt_key in custom_prompts:
        return custom_prompts[prompt_key]

    return None
