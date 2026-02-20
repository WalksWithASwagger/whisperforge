"""
Content Processing Pipeline
=============================

Thin Streamlit UI wrapper around :mod:`pipeline_engine`.
Provides Aurora-themed progress visualisation while the pure-logic engine
does the actual work.
"""

import logging
import time

import streamlit as st

from . import pipeline_engine
from .pipeline_engine import NullListener, PipelineConfig
from .prompt_loader import load_custom_prompts
from .supabase_integration import get_supabase_client

logger = logging.getLogger(__name__)

# Pipeline step definitions
PIPELINE_STEP_NAMES = pipeline_engine.PIPELINE_STEP_NAMES


# ---------------------------------------------------------------------------
# Streamlit listener -- maps engine callbacks to Aurora UI
# ---------------------------------------------------------------------------


class StreamlitPipelineListener(NullListener):
    """Bridges :class:`pipeline_engine.PipelineListener` events to Streamlit widgets."""

    def __init__(self, pipeline_placeholder, start_time, containers):
        self.placeholder = pipeline_placeholder
        self.start_time = start_time
        self.containers = containers

    def on_step_progress(self, step_index, step_progress, total_progress, message):
        _update_pipeline(self.placeholder, step_index, step_progress, total_progress, message, self.start_time)

    def on_step_complete(self, step_index, step_name, result):
        container = self.containers.get(step_name)
        if container and result and isinstance(result, str):
            with container:
                st.markdown(f"**{step_name} Complete**")
                st.markdown(result)

    def on_error(self, step_index, error):
        st.error(f"Pipeline failed: {error!s}")

    def on_pipeline_complete(self, results):
        st.markdown(
            '<div class="aurora-celebration">'
            '<h1 class="aurora-celebration-title">Pipeline Complete!</h1>'
            '<p class="aurora-celebration-subtitle">Your content has been transformed with AI magic</p>'
            "</div>",
            unsafe_allow_html=True,
        )
        time.sleep(2)
        self.placeholder.empty()


# ---------------------------------------------------------------------------
# Public entry point -- signature unchanged for app_simple.py callers
# ---------------------------------------------------------------------------


def process_pipeline(audio_file=None, transcript: str | None = None) -> dict | None:
    """Unified content pipeline.

    Supply *audio_file* to transcribe first, or *transcript* to skip transcription.
    Returns the results dict on success, or ``None`` on failure.
    """
    start_time = time.time()

    # Load any user-defined custom prompts
    custom_prompts = load_custom_prompts()
    if custom_prompts:
        st.info(f"Using {len(custom_prompts)} custom prompts")

    # --- Streamlit UI scaffolding ---
    pipeline_placeholder = st.empty()
    st.markdown("### Live Content Generation")

    containers = {
        "Transcription": st.expander("Transcription", expanded=False),
        "Wisdom Extraction": st.expander("Wisdom Extraction", expanded=False),
        "Outline Creation": st.expander("Outline Creation", expanded=False),
        "Article Generation": st.expander("Article Generation", expanded=False),
        "Social Content": st.expander("Social Content", expanded=False),
        "Publishing": st.expander("Notion Publishing", expanded=False),
    }

    # --- Build engine config from session state ---
    config = PipelineConfig(
        custom_prompts=custom_prompts or {},
        article_template=st.session_state.get("article_template"),
        knowledge_base=st.session_state.get("knowledge_base", {}),
        user_id=st.session_state.get("user_id"),
        publish_to_notion=True,
    )

    # --- Obtain content store (Supabase) ---
    try:
        content_store = get_supabase_client()
    except Exception:
        logger.warning("Supabase client unavailable -- content will not be persisted")
        content_store = None

    # --- Create listener and run engine ---
    listener = StreamlitPipelineListener(pipeline_placeholder, start_time, containers)

    return pipeline_engine.run_pipeline(
        audio_file=audio_file,
        transcript=transcript,
        config=config,
        content_store=content_store,
        listener=listener,
    )


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
