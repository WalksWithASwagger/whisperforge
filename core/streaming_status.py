"""
Streaming Status Display
========================

Enhanced streaming UX with st.status() integration and visible thinking.
Includes the 2025 content display and pipeline status visualization.
"""

import streamlit as st

from .exceptions import WhisperForgeError
from .streaming_pipeline import get_pipeline_controller


def show_2025_content_display():
    """Ultra-modern 2025 Aurora content display for completed results."""
    from .streaming_results import show_streaming_content_card

    controller = get_pipeline_controller()
    results = controller.get_results()

    if not results:
        return

    st.markdown(
        """
    <div class="completion-showcase">
        <div class="showcase-bg"></div>
        <div class="showcase-content">
            <h2>\u2728 Transformation Complete</h2>
            <p>Your audio has been transformed into structured, actionable content</p>
        </div>
        <div class="showcase-orbs">
            <div class="orb orb-1"></div>
            <div class="orb orb-2"></div>
            <div class="orb orb-3"></div>
        </div>
    </div>

    <style>
    .completion-showcase {
        position: relative;
        background: linear-gradient(135deg, rgba(0, 255, 255, 0.08), rgba(64, 224, 208, 0.12));
        border: 1px solid rgba(0, 255, 255, 0.2);
        border-radius: 20px;
        padding: 48px;
        margin: 32px 0;
        text-align: center;
        overflow: hidden;
    }

    .showcase-bg {
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: radial-gradient(circle at 30% 70%, rgba(0, 255, 255, 0.1) 0%, transparent 50%),
                    radial-gradient(circle at 70% 30%, rgba(64, 224, 208, 0.08) 0%, transparent 50%);
        animation: bg-float 8s ease-in-out infinite;
    }

    .showcase-content {
        position: relative;
        z-index: 2;
    }

    .showcase-content h2 {
        margin: 0 0 12px 0;
        color: #00FFFF;
        font-size: 2.2rem;
        font-weight: 300;
        letter-spacing: 0.05em;
        text-shadow: 0 0 20px rgba(0, 255, 255, 0.3);
    }

    .showcase-content p {
        margin: 0;
        color: rgba(255, 255, 255, 0.7);
        font-size: 1.1rem;
        letter-spacing: 0.02em;
    }

    .showcase-orbs {
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        width: 200px;
        height: 200px;
        pointer-events: none;
    }

    .orb {
        position: absolute;
        border-radius: 50%;
        filter: blur(1px);
    }

    .orb-1 {
        width: 60px;
        height: 60px;
        background: radial-gradient(circle, rgba(0, 255, 255, 0.2), transparent);
        top: 20%;
        left: 20%;
        animation: orb-float-1 6s ease-in-out infinite;
    }

    .orb-2 {
        width: 40px;
        height: 40px;
        background: radial-gradient(circle, rgba(64, 224, 208, 0.15), transparent);
        top: 60%;
        right: 25%;
        animation: orb-float-2 8s ease-in-out infinite reverse;
    }

    .orb-3 {
        width: 30px;
        height: 30px;
        background: radial-gradient(circle, rgba(0, 255, 200, 0.1), transparent);
        bottom: 30%;
        left: 30%;
        animation: orb-float-3 7s ease-in-out infinite;
    }

    @keyframes bg-float {
        0%, 100% { transform: translateY(0px) rotate(0deg); }
        50% { transform: translateY(-10px) rotate(2deg); }
    }

    @keyframes orb-float-1 {
        0%, 100% { transform: translate(0, 0) scale(1); }
        33% { transform: translate(10px, -15px) scale(1.1); }
        66% { transform: translate(-8px, 12px) scale(0.9); }
    }

    @keyframes orb-float-2 {
        0%, 100% { transform: translate(0, 0) scale(1); }
        50% { transform: translate(-12px, -10px) scale(1.2); }
    }

    @keyframes orb-float-3 {
        0%, 100% { transform: translate(0, 0) scale(1); }
        25% { transform: translate(8px, -8px) scale(0.8); }
        75% { transform: translate(-6px, 10px) scale(1.1); }
    }
    </style>
    """,
        unsafe_allow_html=True,
    )

    content_map = {
        "transcription": ("\U0001f399\ufe0f", "Audio Transcription", "Complete speech-to-text conversion"),
        "wisdom_extraction": ("\U0001f48e", "Key Insights & Wisdom", "Extracted insights and actionable takeaways"),
        "research_enrichment": ("\U0001f50d", "Research Enrichment", "Supporting links and contextual information"),
        "outline_creation": ("\U0001f4cb", "Content Outline", "Structured organization and flow"),
        "article_creation": ("\U0001f4f0", "Full Article", "Complete written content ready for publication"),
        "social_content": ("\U0001f4f1", "Social Media Content", "Platform-optimized posts and captions"),
        "image_prompts": ("\U0001f5bc\ufe0f", "Image Generation Prompts", "AI-generated visual concept descriptions"),
    }

    for key, (icon, title, desc) in content_map.items():
        if key in results and results[key]:
            show_streaming_content_card(icon, title, desc, results[key], is_live=False)


def show_enhanced_streaming_status():
    """Enhanced streaming UX with st.status() integration and visible thinking."""
    controller = get_pipeline_controller()

    if not controller.is_active and not controller.is_complete:
        return

    current_step = controller.current_step_index
    pipeline_steps = [
        ("Upload Validation", "File format & compatibility check", "upload_validation"),
        ("Audio Transcription", "Speech-to-text conversion", "transcription"),
        ("Wisdom Extraction", "Key insights extraction", "wisdom_extraction"),
        ("Research Enrichment", "Supporting links & context", "research_enrichment"),
        ("Outline Generation", "Content structure creation", "outline_creation"),
        ("Article Creation", "Full article generation", "article_creation"),
        ("Social Media Posts", "Platform-optimized content", "social_content"),
        ("Image Prompts", "Visual concept generation", "image_prompts"),
        ("Database Storage", "Secure content storage", "database_storage"),
    ]

    results = controller.get_results()
    errors = controller.get_errors() if hasattr(controller, "get_errors") else {}

    # Visible thinking integration
    if controller.is_active and st.session_state.get("thinking_enabled", True):
        thinking_container = st.container()
        with thinking_container:
            st.markdown(
                """
            <div class="thinking-section">
                <div class="thinking-header">
                    <span class="thinking-icon">\U0001f9e0</span>
                    <span class="thinking-title">AI Thinking Process</span>
                    <div class="thinking-pulse"></div>
                </div>
            </div>

            <style>
            .thinking-section {
                background: linear-gradient(135deg, rgba(255, 20, 147, 0.08), rgba(138, 43, 226, 0.05));
                border: 1px solid rgba(255, 20, 147, 0.15);
                border-radius: 12px;
                padding: 16px;
                margin: 16px 0;
                position: relative;
                overflow: hidden;
            }

            .thinking-header {
                display: flex;
                align-items: center;
                gap: 12px;
            }

            .thinking-icon {
                font-size: 1.2rem;
                animation: think-pulse 2s ease-in-out infinite;
            }

            .thinking-title {
                color: rgba(255, 20, 147, 0.9);
                font-weight: 500;
                font-size: 0.9rem;
                letter-spacing: 0.02em;
            }

            .thinking-pulse {
                width: 8px;
                height: 8px;
                background: #FF1493;
                border-radius: 50%;
                margin-left: auto;
                animation: pulse-dot 1.5s ease-in-out infinite;
            }

            @keyframes think-pulse {
                0%, 100% { transform: scale(1); }
                50% { transform: scale(1.1); }
            }

            @keyframes pulse-dot {
                0%, 100% { opacity: 1; transform: scale(1); }
                50% { opacity: 0.4; transform: scale(0.8); }
            }
            </style>
            """,
                unsafe_allow_html=True,
            )

            try:
                from .visible_thinking import render_thinking_stream

                render_thinking_stream(thinking_container)
            except (WhisperForgeError, ImportError):
                st.info("\U0001f4ad AI is thinking... (thinking system loading)")

    # Main processing status
    if controller.is_active:
        current_title, current_desc, _current_key = pipeline_steps[current_step]

        with st.status(f"\U0001f504 {current_title}", expanded=True) as status:
            st.write(f"\U0001f4dd **{current_desc}**")

            progress = (current_step / len(pipeline_steps)) * 100
            st.progress(progress / 100, text=f"Progress: {progress:.0f}% ({current_step + 1}/{len(pipeline_steps)})")

            for i in range(current_step):
                title, _, step_key = pipeline_steps[i]
                if step_key in results:
                    st.write(f"\u2705 {title} - Complete")
                    if (
                        step_key in results
                        and results[step_key]
                        and step_key not in ["upload_validation", "database_storage"]
                    ):
                        result_str = str(results[step_key])
                        preview = result_str[:100] + "..." if len(result_str) > 100 else result_str
                        st.caption(f"Preview: {preview}")
                elif step_key in errors:
                    st.write(f"\u274c {title} - Error: {errors[step_key]}")
                else:
                    st.write(f"\u2705 {title} - Complete")

            st.markdown(
                f"""
            <div style="
                background: linear-gradient(135deg, rgba(0, 255, 255, 0.1), rgba(64, 224, 208, 0.05));
                border-left: 3px solid #00FFFF;
                padding: 12px 16px;
                margin: 8px 0;
                border-radius: 0 8px 8px 0;
            ">
                \U0001f504 <strong>{current_title}</strong> - {current_desc}...
            </div>
            """,
                unsafe_allow_html=True,
            )

            for i in range(current_step + 1, len(pipeline_steps)):
                title, _, _ = pipeline_steps[i]
                st.write(f"\u2b55 {title} - Pending")

            if current_step >= len(pipeline_steps) - 1:
                status.update(label="\u2705 Processing Complete!", state="complete", expanded=False)
            else:
                status.update(label=f"\U0001f504 {current_title}", state="running")

    elif controller.is_complete:
        with st.status("\u2705 All processing complete!", state="complete", expanded=False):
            st.success("Your audio has been transformed into comprehensive content!")

        st.markdown(
            """
        <div class="completion-summary">
            <h4>\U0001f31f Generation Summary</h4>
        </div>

        <style>
        .completion-summary {
            background: linear-gradient(135deg, rgba(0, 255, 255, 0.08), rgba(64, 224, 208, 0.05));
            border: 1px solid rgba(0, 255, 255, 0.15);
            border-radius: 12px;
            padding: 20px;
            margin: 16px 0;
            text-align: center;
        }

        .completion-summary h4 {
            margin: 0;
            color: #00FFFF;
            font-weight: 300;
            letter-spacing: 0.02em;
        }
        </style>
        """,
            unsafe_allow_html=True,
        )

        col1, col2, col3 = st.columns(3)

        with col1:
            completed_count = len([r for r in results.values() if r])
            st.metric("Steps Completed", completed_count, len(pipeline_steps))
        with col2:
            error_count = len(errors)
            st.metric("Errors", error_count, delta_color="inverse")
        with col3:
            success_rate = ((completed_count - error_count) / len(pipeline_steps)) * 100
            st.metric("Success Rate", f"{success_rate:.1f}%")

        if results:
            st.markdown("**Generated Content Types:**")
            content_types = []
            if results.get("transcription"):
                content_types.append("\U0001f4dd Transcription")
            if results.get("wisdom_extraction"):
                content_types.append("\U0001f48e Insights")
            if results.get("research_enrichment"):
                content_types.append("\U0001f50d Research")
            if results.get("outline_creation"):
                content_types.append("\U0001f4cb Outline")
            if results.get("article_creation"):
                content_types.append("\U0001f4f0 Article")
            if results.get("social_content"):
                content_types.append("\U0001f4f1 Social Posts")
            if results.get("image_prompts"):
                content_types.append("\U0001f5bc\ufe0f Image Prompts")

            if content_types:
                st.write(" \u2022 ".join(content_types))


def show_processing_status():
    """Display Aurora pipeline with real-time visibility - wrapper."""
    show_enhanced_streaming_status()
