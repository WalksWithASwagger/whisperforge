"""
Streaming Results Display
=========================

Shows content as it's generated with Aurora styling.
CSS loaded from static/css/streaming.css.
"""

import os
import time
import uuid

import streamlit as st

from .export import create_json_download, create_markdown_download, create_text_download
from .streaming_pipeline import get_pipeline_controller
from .streaming_status import (  # noqa: F401 - re-exports
    show_2025_content_display,
    show_enhanced_streaming_status,
    show_processing_status,
)

_STREAMING_CSS_CACHE = None


def _load_streaming_css():
    """Load streaming CSS from static file (cached)."""
    global _STREAMING_CSS_CACHE  # noqa: PLW0603
    if _STREAMING_CSS_CACHE is None:
        css_path = os.path.join("static", "css", "streaming.css")
        if os.path.exists(css_path):
            with open(css_path, encoding="utf-8") as f:
                _STREAMING_CSS_CACHE = f"<style>{f.read()}</style>"
        else:
            _STREAMING_CSS_CACHE = ""
    return _STREAMING_CSS_CACHE


def apply_streaming_css():
    """Apply Aurora theme CSS for streaming results."""
    st.markdown(_load_streaming_css(), unsafe_allow_html=True)


def generate_unique_key(base_name: str) -> str:
    """Generate truly unique key for Streamlit widgets to prevent DuplicateWidgetID errors."""
    return f"{base_name}_{uuid.uuid4().hex[:8]}_{int(time.time() * 1000000) % 1000000}"


def show_streaming_results():
    """Display content as it streams - real-time streaming implementation."""
    controller = get_pipeline_controller()
    results = controller.get_results()

    if not results:
        st.markdown("### \U0001f30a Live Content Stream")
        st.info("\U0001f504 Waiting for processing to begin...")
        return

    show_real_time_content_stream(results, controller)


def show_real_time_content_stream(results, controller):
    """Show real-time streaming content with smooth reveals."""
    apply_streaming_css()

    step_map = {
        "transcription": ("\U0001f399\ufe0f", "Audio Transcription"),
        "wisdom_extraction": ("\U0001f48e", "Wisdom & Key Insights"),
        "research_enrichment": ("\U0001f50d", "Research Enrichment"),
        "outline_creation": ("\U0001f4cb", "Content Outline"),
        "article_creation": ("\U0001f4f0", "Full Article"),
        "social_content": ("\U0001f4f1", "Social Media Content"),
        "image_prompts": ("\U0001f5bc\ufe0f", "Image Prompts"),
    }

    for step_key, (icon, title) in step_map.items():
        content = results.get(step_key)
        errors = controller.get_errors() if hasattr(controller, "get_errors") else {}

        if content:
            show_completed_content_section(step_key, icon, title, content)
        elif step_key in errors:
            show_error_content_section(icon, title, errors[step_key])
        elif controller.is_active and step_key == list(step_map.keys())[controller.current_step_index]:
            show_processing_content_section(icon, title, f"Generating {title.lower()}...")

    if controller.is_complete:
        _show_download_options(results)


def show_completed_content_section(step_key: str, icon: str, title: str, content):
    """Display a completed content section with Aurora styling."""
    content_str = str(content)
    word_count = len(content_str.split())
    preview_length = 200

    st.markdown(
        f"""
    <div class="aurora-content-card">
        <div class="aurora-content-header">
            <span class="aurora-content-title">{icon} {title}</span>
            <span class="aurora-status-badge completed">\u2705 Complete \u2022 {word_count} words</span>
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )

    with st.container():
        if len(content_str) > preview_length:
            with st.expander(f"View {title}", expanded=False):
                st.markdown(content_str)

                col1, col2 = st.columns([1, 4])
                with col1:
                    copy_key = generate_unique_key(f"copy_{step_key}")
                    if st.button("\U0001f4cb Copy", key=copy_key, help=f"Copy {title}"):
                        st.code(content_str, language="markdown")
                        st.success("Content displayed - copy with Ctrl+A, Ctrl+C")

                # Editor section for article
                if step_key == "article_creation":
                    st.markdown(
                        """
                    <div class="aurora-editor-section">
                        <div class="aurora-editor-header">
                            <span class="aurora-editor-title">\u270f\ufe0f Content Editor</span>
                            <span class="aurora-editor-badge">EDIT MODE</span>
                        </div>
                    </div>
                    """,
                        unsafe_allow_html=True,
                    )

                    edit_key = generate_unique_key("edit_article")
                    edited_content = st.text_area("Edit Article Content", value=content_str, height=400, key=edit_key)

                    if edited_content != content_str:
                        save_key = generate_unique_key("save_article")
                        if st.button("\U0001f4be Save Changes", key=save_key):
                            controller = get_pipeline_controller()
                            controller.update_result(step_key, edited_content)
                            st.success("\u2705 Article updated!")
                            st.rerun()
        else:
            st.markdown(
                f"""
            <div class="aurora-content-body">
                {content_str}
            </div>
            """,
                unsafe_allow_html=True,
            )


def show_processing_content_section(icon: str, title: str, message: str):
    """Display a processing content section with animation."""
    st.markdown(
        f"""
    <div class="aurora-content-card" style="border-color: rgba(0, 255, 255, 0.3);">
        <div class="aurora-content-header">
            <span class="aurora-content-title">{icon} {title}</span>
            <span class="aurora-status-badge"
                  style="background: rgba(0, 255, 255, 0.15); color: #00FFFF;
                         border: 1px solid rgba(0, 255, 255, 0.3);
                         animation: aurora-pulse 2s ease-in-out infinite;">
                \U0001f504 Processing
            </span>
        </div>
        <div class="aurora-content-body">
            <div style="display: flex; align-items: center; gap: 12px; padding: 20px;">
                <div style="
                    width: 24px; height: 24px;
                    border: 2px solid rgba(0, 255, 255, 0.3);
                    border-top: 2px solid #00FFFF;
                    border-radius: 50%;
                    animation: spin 1s linear infinite;
                "></div>
                <span style="color: rgba(255, 255, 255, 0.7); font-style: italic;">
                    {message}
                </span>
            </div>
        </div>
    </div>

    <style>
    @keyframes spin {{
        0% {{ transform: rotate(0deg); }}
        100% {{ transform: rotate(360deg); }}
    }}
    </style>
    """,
        unsafe_allow_html=True,
    )


def show_error_content_section(icon: str, title: str, error_msg: str):
    """Display an error content section."""
    st.markdown(
        f"""
    <div class="aurora-content-card" style="border-color: rgba(255, 100, 100, 0.3);">
        <div class="aurora-content-header">
            <span class="aurora-content-title">{icon} {title}</span>
            <span class="aurora-status-badge"
                  style="background: rgba(255, 100, 100, 0.15); color: #FF6B6B;
                         border: 1px solid rgba(255, 100, 100, 0.3);">
                \u274c Error
            </span>
        </div>
        <div class="aurora-content-body" style="color: rgba(255, 100, 100, 0.8);">
            {error_msg}
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )


def show_streaming_content_card(icon: str, title: str, description: str, content: str, is_live: bool = False):
    """Beautiful streaming content card with Aurora effects."""
    border_color = "rgba(0, 255, 100, 0.2)" if is_live else "rgba(0, 255, 255, 0.15)"
    bg_gradient = (
        "rgba(0, 255, 100, 0.03), rgba(0, 255, 255, 0.05)"
        if is_live
        else "rgba(0, 255, 255, 0.03), rgba(64, 224, 208, 0.05)"
    )
    glow_color = "rgba(0, 255, 100, 0.4)" if is_live else "rgba(0, 255, 255, 0.3)"

    with st.container():
        live_badge = '<div class="live-badge">LIVE</div>' if is_live else '<div class="complete-badge">\u2713</div>'
        st.markdown(
            f"""
        <div class="aurora-stream-card {"live" if is_live else "complete"}">
            <div class="card-header">
                <span class="card-icon">{icon}</span>
                <div class="card-title-group">
                    <h4 class="card-title">{title}</h4>
                    <p class="card-description">{description}</p>
                </div>
                {live_badge}
            </div>
            <div class="card-separator"></div>
        </div>

        <style>
        .aurora-stream-card {{
            background: linear-gradient(135deg, {bg_gradient});
            border: 1px solid {border_color};
            border-radius: 16px;
            padding: 20px;
            margin: 16px 0;
            position: relative;
            overflow: hidden;
            transition: all 0.4s cubic-bezier(0.23, 1, 0.32, 1);
            backdrop-filter: blur(20px);
        }}

        .aurora-stream-card::before {{
            content: "";
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 2px;
            background: linear-gradient(90deg, transparent, {glow_color}, transparent);
            animation: card-glow 4s ease-in-out infinite;
        }}

        .aurora-stream-card.live::before {{
            animation: card-glow 2s ease-in-out infinite;
        }}

        .card-header {{
            display: flex;
            align-items: center;
            gap: 16px;
        }}

        .card-icon {{
            font-size: 1.8rem;
            filter: drop-shadow(0 0 8px {glow_color});
        }}

        .card-title-group {{
            flex: 1;
        }}

        .card-title {{
            margin: 0;
            color: #00FFFF;
            font-size: 1.1rem;
            font-weight: 500;
            letter-spacing: 0.02em;
        }}

        .card-description {{
            margin: 4px 0 0 0;
            color: rgba(255, 255, 255, 0.6);
            font-size: 0.85rem;
        }}

        .live-badge {{
            background: linear-gradient(135deg, rgba(0, 255, 100, 0.2), rgba(0, 255, 100, 0.1));
            border: 1px solid rgba(0, 255, 100, 0.3);
            border-radius: 20px;
            padding: 4px 12px;
            font-size: 0.7rem;
            color: #00FF88;
            font-weight: 600;
            letter-spacing: 0.05em;
            animation: pulse-live 2s ease-in-out infinite;
        }}

        .complete-badge {{
            background: linear-gradient(135deg, rgba(0, 255, 255, 0.2), rgba(0, 255, 255, 0.1));
            border: 1px solid rgba(0, 255, 255, 0.3);
            border-radius: 50%;
            width: 28px;
            height: 28px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 0.8rem;
            color: #00FFFF;
        }}

        .card-separator {{
            height: 1px;
            background: linear-gradient(90deg, transparent, {border_color}, transparent);
            margin: 16px 0 0 0;
        }}

        @keyframes card-glow {{
            0%, 100% {{ left: -100%; opacity: 0; }}
            50% {{ left: 100%; opacity: 1; }}
        }}

        @keyframes pulse-live {{
            0%, 100% {{ transform: scale(1); opacity: 1; }}
            50% {{ transform: scale(1.05); opacity: 0.8; }}
        }}
        </style>
        """,
            unsafe_allow_html=True,
        )

        if len(content) > 300:
            preview = content[:300] + "..."

            with st.expander(f"\U0001f4d6 Preview {title}", expanded=False):
                st.markdown(preview)

            with st.expander(f"\U0001f4c4 Full {title}", expanded=False):
                st.markdown(content)

                copy_key = generate_unique_key(f"copy_{title}")
                if st.button(f"Copy {title}", key=copy_key, help=f"Copy {title} to clipboard"):
                    st.code(content, language="markdown")
        else:
            st.markdown(content)

            copy_key = generate_unique_key(f"copy_short_{title}")
            if st.button(f"Copy {title}", key=copy_key, help=f"Copy {title} to clipboard"):
                st.code(content, language="markdown")


def _show_download_options(results):
    """Show download options for generated content."""
    st.markdown(
        """
    <div class="aurora-download-section">
        <div class="aurora-section-title">
            <span>\U0001f4e5</span>
            Download Options
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )

    formats = {
        "JSON": create_json_download(results),
        "Markdown": create_markdown_download(results),
        "Text": create_text_download(results),
    }

    col1, col2, col3 = st.columns(3)

    with col1:
        st.download_button(
            "\U0001f4c4 JSON Format",
            data=formats["JSON"],
            file_name="whisperforge_results.json",
            mime="application/json",
        )

    with col2:
        st.download_button(
            "\U0001f4dd Markdown Format",
            data=formats["Markdown"],
            file_name="whisperforge_results.md",
            mime="text/markdown",
        )

    with col3:
        st.download_button(
            "\U0001f4c4 Text Format",
            data=formats["Text"],
            file_name="whisperforge_results.txt",
            mime="text/plain",
        )
