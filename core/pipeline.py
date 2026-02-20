"""
Content Processing Pipeline
=============================

Core audio-to-content pipeline with Aurora visualization.
Handles transcription, wisdom extraction, outline, article, social, and Notion publishing.
"""

import logging
import os
import tempfile
import time
from datetime import datetime

import streamlit as st

from .content_generation import (
    generate_article,
    generate_outline,
    generate_social_content,
    generate_wisdom,
    transcribe_audio,
)
from .notion_integration import create_notion_page, generate_ai_title
from .prompt_loader import get_prompt_for_step, load_custom_prompts, load_template
from .supabase_integration import get_supabase_client

logger = logging.getLogger(__name__)

# Pipeline step definitions
PIPELINE_STEP_NAMES = [
    "Transcription",
    "Wisdom Extraction",
    "Outline Creation",
    "Article Generation",
    "Social Content",
    "Publishing",
]


def process_pipeline(audio_file=None, transcript: str | None = None) -> dict | None:
    """Unified content pipeline.

    Supply *audio_file* to transcribe first, or *transcript* to skip transcription.
    Returns the results dict on success, or None on failure.
    """
    results: dict = {}
    start_time = time.time()

    custom_prompts = load_custom_prompts()
    if custom_prompts:
        st.info(f"Using {len(custom_prompts)} custom prompts")

    pipeline_placeholder = st.empty()
    st.markdown("### Live Content Generation")

    transcript_container = st.expander("Transcription", expanded=False)
    wisdom_container = st.expander("Wisdom Extraction", expanded=False)
    outline_container = st.expander("Outline Creation", expanded=False)
    article_container = st.expander("Article Generation", expanded=False)
    social_container = st.expander("Social Content", expanded=False)
    notion_container = st.expander("Notion Publishing", expanded=False)

    try:
        # Step 0: Transcription (skipped when transcript is provided)
        if audio_file is not None:
            _update_pipeline(pipeline_placeholder, 0, 0, 0, "Starting transcription...", start_time)

            suffix = os.path.splitext(audio_file.name)[1]
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
                tmp_file.write(audio_file.getvalue())
                tmp_file_path = tmp_file.name

            try:
                _update_pipeline(pipeline_placeholder, 0, 50, 8, "Transcribing audio with Whisper AI...", start_time)
                transcript = transcribe_audio(tmp_file_path)
                if not transcript:
                    st.error("Transcription failed: empty result")
                    return None
            finally:
                if os.path.exists(tmp_file_path):
                    os.unlink(tmp_file_path)

            results["transcript"] = transcript
            with transcript_container:
                st.markdown("**Transcription Complete**")
                st.text_area("Transcript", transcript, height=200, disabled=True)

            _update_pipeline(pipeline_placeholder, 0, 100, 17, "Transcription complete!", start_time)
        else:
            # Pre-transcribed content
            if not transcript:
                st.error("No audio file or transcript provided.")
                return None
            results["transcript"] = transcript
            _update_pipeline(
                pipeline_placeholder,
                1,
                0,
                17,
                f"Using pre-transcribed content ({len(transcript)} characters)",
                start_time,
            )

        # Steps 1-5: Generation, publishing, saving
        _run_generation_steps(
            transcript,
            results,
            custom_prompts,
            pipeline_placeholder,
            start_time,
            wisdom_container,
            outline_container,
            article_container,
            social_container,
            notion_container,
        )

        return results

    except Exception as e:
        _update_pipeline(pipeline_placeholder, 0, 0, 0, f"Error: {e!s}", start_time)
        st.error(f"Pipeline failed: {e!s}")
        return None


def _run_generation_steps(
    transcript,
    results,
    custom_prompts,
    pipeline_placeholder,
    start_time,
    wisdom_container,
    outline_container,
    article_container,
    social_container,
    notion_container,
):
    """Execute the generation steps (wisdom through publishing)."""
    # --- Wisdom Extraction ---
    _update_pipeline(pipeline_placeholder, 1, 0, 17, "Extracting wisdom and insights...", start_time)
    wisdom_prompt = get_prompt_for_step("wisdom", custom_prompts)
    _update_pipeline(pipeline_placeholder, 1, 50, 25, "Analyzing content for key insights...", start_time)

    wisdom = generate_wisdom(transcript, custom_prompt=wisdom_prompt, knowledge_base={})
    results["wisdom"] = wisdom

    with wisdom_container:
        st.markdown("**Wisdom Extraction Complete**")
        st.markdown(wisdom)
    _update_pipeline(pipeline_placeholder, 1, 100, 33, "Wisdom extraction complete!", start_time)

    # --- Outline Creation ---
    _update_pipeline(pipeline_placeholder, 2, 0, 33, "Creating structured outline...", start_time)
    outline_prompt = get_prompt_for_step("outline", custom_prompts)
    _update_pipeline(pipeline_placeholder, 2, 50, 42, "Structuring content hierarchy...", start_time)

    outline = generate_outline(transcript, wisdom, custom_prompt=outline_prompt, knowledge_base={})
    results["outline"] = outline

    with outline_container:
        st.markdown("**Outline Creation Complete**")
        st.markdown(outline)
    _update_pipeline(pipeline_placeholder, 2, 100, 50, "Outline creation complete!", start_time)

    # --- Article Generation ---
    _update_pipeline(pipeline_placeholder, 3, 0, 50, "Generating comprehensive article...", start_time)
    article_prompt = get_prompt_for_step("article", custom_prompts)
    selected_template = st.session_state.get("article_template")
    if selected_template:
        template_text = load_template(selected_template)
        if template_text and article_prompt:
            article_prompt = template_text + "\n" + article_prompt

    _update_pipeline(pipeline_placeholder, 3, 50, 58, "Writing detailed article content...", start_time)

    article = generate_article(transcript, wisdom, outline, custom_prompt=article_prompt, knowledge_base={})
    results["article"] = article

    with article_container:
        st.markdown("**Article Generation Complete**")
        st.markdown(article)
    _update_pipeline(pipeline_placeholder, 3, 100, 67, "Article generation complete!", start_time)

    # --- Social Content ---
    _update_pipeline(pipeline_placeholder, 4, 0, 67, "Creating social media content...", start_time)
    social_prompt = get_prompt_for_step("social", custom_prompts)
    _update_pipeline(pipeline_placeholder, 4, 50, 75, "Generating social media posts...", start_time)

    social = generate_social_content(wisdom, outline, article, custom_prompt=social_prompt, knowledge_base={})
    results["social_content"] = social

    with social_container:
        st.markdown("**Social Content Creation Complete**")
        st.markdown(social)
    _update_pipeline(pipeline_placeholder, 4, 100, 83, "Social content creation complete!", start_time)

    # --- Notion Publishing ---
    _update_pipeline(pipeline_placeholder, 5, 0, 83, "Publishing to Notion workspace...", start_time)

    if os.getenv("NOTION_API_KEY") and os.getenv("NOTION_DATABASE_ID"):
        ai_title = generate_ai_title(transcript)
        _update_pipeline(pipeline_placeholder, 5, 50, 90, "Uploading content to Notion...", start_time)

        notion_url = create_notion_page(ai_title, results)
        if notion_url:
            results["notion_url"] = notion_url
            with notion_container:
                st.markdown("**Notion Publishing Complete**")
                st.markdown(f"**Page Title:** {ai_title}")
                st.markdown(f"[Open in Notion]({notion_url})")
        else:
            with notion_container:
                st.markdown("**Notion Publishing Failed**")
                st.warning("Check your Notion API configuration in Settings.")
    else:
        with notion_container:
            st.markdown("**Notion Publishing Disabled**")
            st.info("Configure Notion API in Settings to enable auto-publishing.")

    # --- Save to DB ---
    _update_pipeline(pipeline_placeholder, 5, 90, 96, "Saving to database...", start_time)
    try:
        save_content_to_db(results)
    except Exception as e:
        st.warning(f"Content saved locally but database save failed: {e}")

    _update_pipeline(
        pipeline_placeholder, 5, 100, 100, "Pipeline complete! All content generated successfully.", start_time
    )

    st.markdown(
        """
    <div class="aurora-celebration">
        <h1 class="aurora-celebration-title">Pipeline Complete!</h1>
        <p class="aurora-celebration-subtitle">Your content has been transformed with AI magic</p>
    </div>
    """,
        unsafe_allow_html=True,
    )

    time.sleep(2)
    pipeline_placeholder.empty()


def _update_pipeline(placeholder, step, step_progress, total_progress, message, start_time):
    """Update the pipeline visualization placeholder."""
    with placeholder.container():
        show_processing_pipeline(
            current_step=step,
            step_progress=step_progress,
            total_progress=total_progress,
            status_message=message,
            processing_time=f"{time.time() - start_time:.1f}s",
        )


def save_content_to_db(content_data: dict):
    """Save generated content to Supabase database."""
    try:
        supabase = get_supabase_client()
        if supabase and st.session_state.get("user_id"):
            content_id = supabase.save_content(
                st.session_state.user_id,
                {
                    "title": content_data.get("title", "Untitled"),
                    "transcript": content_data.get("transcript", ""),
                    "wisdom": content_data.get("wisdom", ""),
                    "outline": content_data.get("outline", ""),
                    "article": content_data.get("article", ""),
                    "social_content": content_data.get("social_content", ""),
                    "notion_url": content_data.get("notion_url", ""),
                    "created_at": datetime.now().isoformat(),
                },
            )
            if content_id:
                st.success(f"Content saved to database (ID: {content_id})")
    except Exception as e:
        st.warning(f"Database save failed: {e}")


def show_processing_pipeline(
    current_step=0,
    step_progress=0,
    total_progress=0,
    status_message="",
    processing_time="",
):
    """Display Aurora-styled processing pipeline visualization."""
    steps = PIPELINE_STEP_NAMES
    step_icons = ["\U0001f3a4", "\U0001f4a1", "\U0001f4cb", "\U0001f4dd", "\U0001f4f1", "\U0001f30c"]

    step_items = []
    for i, (name, icon) in enumerate(zip(steps, step_icons, strict=False)):
        if i < current_step:
            state = "completed"
        elif i == current_step:
            state = "active"
        else:
            state = "pending"

        step_items.append(f"""
        <div class="aurora-pipeline-step {state}">
            <div class="aurora-step-icon">{icon}</div>
            <div class="aurora-step-name">{name}</div>
            {'<div class="aurora-step-progress"><div class="aurora-step-progress-bar" style="width: ' + str(step_progress) + '%"></div></div>' if state == "active" else ""}
        </div>
        """)

    pipeline_html = f"""
    <div class="aurora-processing-pipeline">
        <div class="aurora-pipeline-header">
            <h3 class="aurora-pipeline-title">Content Pipeline</h3>
            <div class="aurora-pipeline-progress">
                <div class="aurora-pipeline-progress-bar" style="width: {total_progress}%"></div>
                <span class="aurora-pipeline-progress-text">{total_progress}%</span>
            </div>
        </div>
        <div class="aurora-pipeline-steps">
            {"".join(step_items)}
        </div>
        {
        f'''
        <div class="aurora-processing-status active">
            <span class="aurora-status-icon">&#x26A1;</span>
            <span class="aurora-status-text">{status_message}</span>
            <span class="aurora-status-time">{processing_time}</span>
        </div>
        '''
        if status_message
        else ""
    }
    </div>
    """

    st.markdown(pipeline_html, unsafe_allow_html=True)
