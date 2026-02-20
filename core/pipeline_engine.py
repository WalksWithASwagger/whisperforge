"""
Pipeline Engine
================

Pure business-logic pipeline orchestration with ZERO Streamlit dependencies.
Extracts the content-generation workflow from pipeline.py so it can be driven
by any front-end (Streamlit, CLI, API server, tests).
"""

from __future__ import annotations

import logging
import os
import tempfile
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Protocol

from .content_generation import (
    generate_article,
    generate_outline,
    generate_social_content,
    generate_wisdom,
    transcribe_audio,
)
from .notion_integration import create_notion_page, generate_ai_title
from .prompt_loader import get_prompt_for_step, load_custom_prompts, load_template

logger = logging.getLogger(__name__)

# Pipeline step definitions (mirrors pipeline.py)
PIPELINE_STEP_NAMES = [
    "Transcription",
    "Wisdom Extraction",
    "Outline Creation",
    "Article Generation",
    "Social Content",
    "Publishing",
]


# ---------------------------------------------------------------------------
# Listener protocol -- callers implement this to receive progress updates
# ---------------------------------------------------------------------------


class PipelineListener(Protocol):
    """Observer interface for pipeline progress events."""

    def on_step_start(self, step_index: int, step_name: str, message: str) -> None: ...

    def on_step_progress(self, step_index: int, step_progress: int, total_progress: int, message: str) -> None: ...

    def on_step_complete(self, step_index: int, step_name: str, result: Any) -> None: ...

    def on_error(self, step_index: int, error: Exception) -> None: ...

    def on_pipeline_complete(self, results: dict) -> None: ...


class NullListener:
    """No-op listener -- silently ignores every event."""

    def on_step_start(self, step_index: int, step_name: str, message: str) -> None:
        pass

    def on_step_progress(self, step_index: int, step_progress: int, total_progress: int, message: str) -> None:
        pass

    def on_step_complete(self, step_index: int, step_name: str, result: Any) -> None:
        pass

    def on_error(self, step_index: int, error: Exception) -> None:
        pass

    def on_pipeline_complete(self, results: dict) -> None:
        pass


# ---------------------------------------------------------------------------
# Pipeline configuration
# ---------------------------------------------------------------------------


@dataclass
class PipelineConfig:
    """Configuration knobs for a single pipeline run."""

    custom_prompts: dict[str, str] = field(default_factory=dict)
    article_template: str | None = None
    knowledge_base: dict[str, str] = field(default_factory=dict)
    user_id: int | str | None = None
    publish_to_notion: bool = True


# ---------------------------------------------------------------------------
# Content store protocol -- abstracts away the persistence layer
# ---------------------------------------------------------------------------


class ContentStore(Protocol):
    """Persistence interface for generated content."""

    def save_content(self, user_id: int | str, content_data: dict) -> str | None: ...


class NullContentStore:
    """No-op content store -- discards everything."""

    def save_content(self, user_id: int | str, content_data: dict) -> str | None:
        return None


# ---------------------------------------------------------------------------
# Main orchestration
# ---------------------------------------------------------------------------


def run_pipeline(
    *,
    audio_file: Any = None,
    transcript: str | None = None,
    config: PipelineConfig | None = None,
    content_store: ContentStore | None = None,
    listener: PipelineListener | None = None,
) -> dict | None:
    """Execute the full content-generation pipeline.

    Supply *audio_file* (a file-like object with ``.name`` and ``.getvalue()``)
    to transcribe first, or *transcript* to skip transcription.

    Returns the results dict on success, or ``None`` on failure.
    """
    if config is None:
        config = PipelineConfig()
    if content_store is None:
        content_store = NullContentStore()
    if listener is None:
        listener = NullListener()

    # Load custom prompts from disk when none were injected
    custom_prompts = config.custom_prompts
    if not custom_prompts:
        custom_prompts = load_custom_prompts()
        if custom_prompts:
            logger.info("Loaded %d custom prompts from disk", len(custom_prompts))

    results: dict = {}

    try:
        # ------------------------------------------------------------------
        # Step 0 -- Transcription
        # ------------------------------------------------------------------
        if audio_file is not None:
            listener.on_step_start(0, "Transcription", "Starting transcription...")
            listener.on_step_progress(0, 0, 0, "Starting transcription...")

            suffix = os.path.splitext(audio_file.name)[1]
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                tmp.write(audio_file.getvalue())
                tmp_path = tmp.name

            try:
                listener.on_step_progress(0, 50, 8, "Transcribing audio with Whisper AI...")
                transcript = transcribe_audio(tmp_path)
                if not transcript:
                    error = RuntimeError("Transcription failed: empty result")
                    listener.on_error(0, error)
                    logger.error("Transcription returned empty result")
                    return None
            finally:
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)

            results["transcript"] = transcript
            listener.on_step_progress(0, 100, 17, "Transcription complete!")
            listener.on_step_complete(0, "Transcription", transcript)
        else:
            if not transcript:
                error = ValueError("No audio file or transcript provided.")
                listener.on_error(0, error)
                logger.error("No audio file or transcript provided")
                return None
            results["transcript"] = transcript
            listener.on_step_progress(1, 0, 17, f"Using pre-transcribed content ({len(transcript)} characters)")

        # ------------------------------------------------------------------
        # Step 1 -- Wisdom Extraction
        # ------------------------------------------------------------------
        listener.on_step_start(1, "Wisdom Extraction", "Extracting wisdom and insights...")
        listener.on_step_progress(1, 0, 17, "Extracting wisdom and insights...")

        wisdom_prompt = get_prompt_for_step("wisdom", custom_prompts)
        listener.on_step_progress(1, 50, 25, "Analyzing content for key insights...")

        wisdom = generate_wisdom(transcript, custom_prompt=wisdom_prompt, knowledge_base=config.knowledge_base)
        results["wisdom"] = wisdom

        listener.on_step_progress(1, 100, 33, "Wisdom extraction complete!")
        listener.on_step_complete(1, "Wisdom Extraction", wisdom)

        # ------------------------------------------------------------------
        # Step 2 -- Outline Creation
        # ------------------------------------------------------------------
        listener.on_step_start(2, "Outline Creation", "Creating structured outline...")
        listener.on_step_progress(2, 0, 33, "Creating structured outline...")

        outline_prompt = get_prompt_for_step("outline", custom_prompts)
        listener.on_step_progress(2, 50, 42, "Structuring content hierarchy...")

        outline = generate_outline(
            transcript, wisdom, custom_prompt=outline_prompt, knowledge_base=config.knowledge_base
        )
        results["outline"] = outline

        listener.on_step_progress(2, 100, 50, "Outline creation complete!")
        listener.on_step_complete(2, "Outline Creation", outline)

        # ------------------------------------------------------------------
        # Step 3 -- Article Generation
        # ------------------------------------------------------------------
        listener.on_step_start(3, "Article Generation", "Generating comprehensive article...")
        listener.on_step_progress(3, 0, 50, "Generating comprehensive article...")

        article_prompt = get_prompt_for_step("article", custom_prompts)
        if config.article_template:
            template_text = load_template(config.article_template)
            if template_text and article_prompt:
                article_prompt = template_text + "\n" + article_prompt

        listener.on_step_progress(3, 50, 58, "Writing detailed article content...")

        article = generate_article(
            transcript,
            wisdom,
            outline,
            custom_prompt=article_prompt,
            knowledge_base=config.knowledge_base,
        )
        results["article"] = article

        listener.on_step_progress(3, 100, 67, "Article generation complete!")
        listener.on_step_complete(3, "Article Generation", article)

        # ------------------------------------------------------------------
        # Step 4 -- Social Content
        # ------------------------------------------------------------------
        listener.on_step_start(4, "Social Content", "Creating social media content...")
        listener.on_step_progress(4, 0, 67, "Creating social media content...")

        social_prompt = get_prompt_for_step("social", custom_prompts)
        listener.on_step_progress(4, 50, 75, "Generating social media posts...")

        social = generate_social_content(
            wisdom, outline, article, custom_prompt=social_prompt, knowledge_base=config.knowledge_base
        )
        results["social_content"] = social

        listener.on_step_progress(4, 100, 83, "Social content creation complete!")
        listener.on_step_complete(4, "Social Content", social)

        # ------------------------------------------------------------------
        # Step 5 -- Publishing & Persistence
        # ------------------------------------------------------------------
        listener.on_step_start(5, "Publishing", "Publishing to Notion workspace...")
        listener.on_step_progress(5, 0, 83, "Publishing to Notion workspace...")

        if config.publish_to_notion and os.getenv("NOTION_API_KEY") and os.getenv("NOTION_DATABASE_ID"):
            ai_title = generate_ai_title(transcript)
            listener.on_step_progress(5, 50, 90, "Uploading content to Notion...")

            notion_url = create_notion_page(ai_title, results)
            if notion_url:
                results["notion_url"] = notion_url
            else:
                logger.warning("Notion page creation returned None")
        else:
            logger.info("Notion publishing skipped (disabled or not configured)")

        # --- Save to DB ---
        listener.on_step_progress(5, 90, 96, "Saving to database...")
        try:
            if config.user_id is not None:
                content_data = {
                    "title": results.get("title", "Untitled"),
                    "transcript": results.get("transcript", ""),
                    "wisdom": results.get("wisdom", ""),
                    "outline": results.get("outline", ""),
                    "article": results.get("article", ""),
                    "social_content": results.get("social_content", ""),
                    "notion_url": results.get("notion_url", ""),
                    "created_at": datetime.now().isoformat(),
                }
                content_store.save_content(config.user_id, content_data)
        except Exception as exc:
            logger.warning("Content saved locally but database save failed: %s", exc)

        listener.on_step_progress(5, 100, 100, "Pipeline complete! All content generated successfully.")
        listener.on_step_complete(5, "Publishing", results.get("notion_url"))
        listener.on_pipeline_complete(results)

        return results

    except Exception as exc:
        listener.on_error(0, exc)
        logger.exception("Pipeline failed: %s", exc)
        return None
