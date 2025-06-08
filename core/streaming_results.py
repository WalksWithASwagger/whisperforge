"""
Streaming Results Display for WhisperForge
Shows content as it's generated with beautiful Aurora styling
"""

import streamlit as st
import html
from typing import Dict, Any, Optional
from .streaming_pipeline import get_pipeline_controller


def show_streaming_results():
    """Display results as they become available during processing"""
    controller = get_pipeline_controller()
    results = controller.get_results()
    errors = controller.get_errors()
    
    if not results and not errors:
        return
    
    # Results header
    st.markdown("""
    <div class="aurora-section">
        <div class="aurora-section-title">
            <span>✨</span>
            Generated Content
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Determine which tabs to show based on available results
    available_tabs = []
    tab_keys = []
    
    if "transcription" in results:
        available_tabs.append("📝 Transcript")
        tab_keys.append("transcription")
    
    if "wisdom_extraction" in results:
        available_tabs.append("💎 Wisdom")
        tab_keys.append("wisdom_extraction")
    
    if "outline_creation" in results:
        available_tabs.append("📋 Outline")
        tab_keys.append("outline_creation")
    
    if "article_creation" in results:
        available_tabs.append("📰 Article")
        tab_keys.append("article_creation")
    
    if "social_content" in results:
        available_tabs.append("📱 Social")
        tab_keys.append("social_content")
    
    if "image_prompts" in results:
        available_tabs.append("🖼️ Images")
        tab_keys.append("image_prompts")
    
    # Show editor critiques if available
    if st.session_state.get("editor_enabled", False):
        critique_keys = [k for k in results.keys() if k.endswith("_critique")]
        if critique_keys:
            available_tabs.append("✍️ Editor")
            tab_keys.append("editor_feedback")
    
    if not available_tabs:
        st.info("🔄 Processing started... Results will appear here as they're generated.")
        return
    
    # Create dynamic tabs
    tabs = st.tabs(available_tabs)
    
    for i, (tab, key) in enumerate(zip(tabs, tab_keys)):
        with tab:
            if key == "editor_feedback":
                _show_editor_feedback(results)
            else:
                _show_content_card(key, results.get(key, ""), errors.get(key))


def _show_content_card(content_type: str, content: str, error: Optional[str] = None):
    """Show a content card with Aurora styling"""
    
    if error:
        st.error(f"❌ Error generating {content_type.replace('_', ' ')}: {error}")
        return
    
    if not content:
        st.info(f"🔄 Generating {content_type.replace('_', ' ')}...")
        return
    
    # Get content title
    titles = {
        "transcription": "Audio Transcription",
        "wisdom_extraction": "Key Insights & Wisdom",
        "outline_creation": "Structured Content Outline",
        "article_creation": "Full Article",
        "social_content": "Social Media Content",
        "image_prompts": "AI Image Generation Prompts"
    }
    
    title = titles.get(content_type, content_type.replace('_', ' ').title())
    
    # Escape content for safe HTML display
    content_escaped = html.escape(content)
    
    st.markdown(f"""
    <div class="aurora-content-card">
        <div class="aurora-content-header">
            <span class="aurora-content-title">{title}</span>
            <div class="aurora-content-meta">
                <span class="aurora-status-badge completed">✓ Complete</span>
            </div>
        </div>
        <div class="aurora-content-body">
            {content_escaped.replace(chr(10), '<br>')}
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Copy to clipboard button
    if st.button(f"📋 Copy {title}", key=f"copy_{content_type}", use_container_width=False):
        st.code(content, language="markdown")


def _show_editor_feedback(results: Dict[str, Any]):
    """Show editor feedback and critiques"""
    
    critique_keys = [k for k in results.keys() if k.endswith("_critique")]
    
    if not critique_keys:
        st.info("📝 Editor feedback will appear here when available.")
        return
    
    st.markdown("""
    <div class="aurora-editor-section">
        <div class="aurora-editor-header">
            <span class="aurora-editor-title">✍️ Editorial Review</span>
            <div class="aurora-editor-badge">AI Editor Active</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    for critique_key in critique_keys:
        content_type = critique_key.replace("_critique", "")
        critique = results[critique_key]
        
        # Get content type display name
        type_names = {
            "wisdom": "Wisdom Extraction",
            "outline": "Content Outline", 
            "article": "Article Writing",
            "social": "Social Media Content"
        }
        
        type_name = type_names.get(content_type, content_type.title())
        
        with st.expander(f"📝 Editorial Feedback: {type_name}", expanded=False):
            st.markdown(f"""
            <div class="aurora-critique-card">
                <div class="aurora-critique-content">
                    {html.escape(critique).replace(chr(10), '<br>')}
                </div>
            </div>
            """, unsafe_allow_html=True)


def show_processing_status():
    """Show current processing status with live updates"""
    controller = get_pipeline_controller()
    
    if not controller.is_active and not controller.is_complete:
        return
    
    # Processing status section
    st.markdown("""
    <div class="aurora-section">
        <div class="aurora-section-title">
            <span>📊</span>
            Processing Status
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    if controller.is_active:
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            current_step = controller.current_step_index
            total_steps = len(controller.get_results()) + 1  # +1 for current step
            st.info(f"🔄 Processing step {current_step + 1} of 8...")
        
        with col2:
            progress = controller.progress_percentage
            st.metric("Progress", f"{progress:.1f}%")
        
        with col3:
            if st.button("⏹️ Stop Processing", key="stop_processing"):
                controller.reset_pipeline()
                st.rerun()
    
    elif controller.is_complete:
        st.success("🎉 Processing completed successfully!")
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            if st.button("🔄 Process New File", key="reset_for_new"):
                controller.reset_pipeline()
                st.rerun()
        
        with col2:
            if st.button("📥 Download Results", key="download_results"):
                _show_download_options(controller.get_results())


def _show_download_options(results: Dict[str, Any]):
    """Show download options for generated content"""
    
    st.markdown("""
    <div class="aurora-download-section">
        <div class="aurora-section-title">
            <span>📥</span>
            Download Options
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Create downloadable content formats
    formats = {
        "JSON": _create_json_download(results),
        "Markdown": _create_markdown_download(results),
        "Text": _create_text_download(results)
    }
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if "JSON" in formats:
            st.download_button(
                "📄 JSON Format",
                data=formats["JSON"],
                file_name="whisperforge_results.json",
                mime="application/json"
            )
    
    with col2:
        if "Markdown" in formats:
            st.download_button(
                "📝 Markdown Format", 
                data=formats["Markdown"],
                file_name="whisperforge_results.md",
                mime="text/markdown"
            )
    
    with col3:
        if "Text" in formats:
            st.download_button(
                "📄 Text Format",
                data=formats["Text"],
                file_name="whisperforge_results.txt",
                mime="text/plain"
            )


def _create_json_download(results: Dict[str, Any]) -> str:
    """Create JSON format download"""
    import json
    return json.dumps(results, indent=2, ensure_ascii=False)


def _create_markdown_download(results: Dict[str, Any]) -> str:
    """Create Markdown format download"""
    content = "# WhisperForge Content Generation Results\n\n"
    
    sections = {
        "transcription": "## 📝 Audio Transcription\n\n",
        "wisdom_extraction": "## 💎 Key Insights & Wisdom\n\n",
        "outline_creation": "## 📋 Content Outline\n\n", 
        "article_creation": "## 📰 Full Article\n\n",
        "social_content": "## 📱 Social Media Content\n\n",
        "image_prompts": "## 🖼️ Image Generation Prompts\n\n"
    }
    
    for key, header in sections.items():
        if key in results:
            content += header + results[key] + "\n\n---\n\n"
    
    return content


def _create_text_download(results: Dict[str, Any]) -> str:
    """Create plain text format download"""
    content = "WHISPERFORGE CONTENT GENERATION RESULTS\n"
    content += "=" * 50 + "\n\n"
    
    sections = {
        "transcription": "AUDIO TRANSCRIPTION\n" + "-" * 20 + "\n\n",
        "wisdom_extraction": "KEY INSIGHTS & WISDOM\n" + "-" * 20 + "\n\n",
        "outline_creation": "CONTENT OUTLINE\n" + "-" * 15 + "\n\n",
        "article_creation": "FULL ARTICLE\n" + "-" * 12 + "\n\n", 
        "social_content": "SOCIAL MEDIA CONTENT\n" + "-" * 20 + "\n\n",
        "image_prompts": "IMAGE GENERATION PROMPTS\n" + "-" * 25 + "\n\n"
    }
    
    for key, header in sections.items():
        if key in results:
            content += header + results[key] + "\n\n" + "=" * 50 + "\n\n"
    
    return content


# Enhanced CSS for streaming results
STREAMING_RESULTS_CSS = """
<style>
/* Aurora Streaming Results Styling */
.aurora-content-card {
    background: linear-gradient(135deg, rgba(0, 255, 255, 0.05), rgba(64, 224, 208, 0.08));
    backdrop-filter: blur(24px) saturate(180%);
    border: 1px solid rgba(0, 255, 255, 0.15);
    border-radius: 16px;
    padding: 24px;
    margin: 16px 0;
    position: relative;
    overflow: hidden;
    transition: all 0.4s cubic-bezier(0.4, 0.0, 0.2, 1);
}

.aurora-content-card::before {
    content: "";
    position: absolute;
    top: 0;
    left: -100%;
    width: 100%;
    height: 2px;
    background: linear-gradient(90deg, transparent, #00FFFF, #40E0D0, transparent);
    animation: aurora-scan 6s ease-in-out infinite;
}

.aurora-content-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 16px;
    padding-bottom: 12px;
    border-bottom: 1px solid rgba(0, 255, 255, 0.1);
}

.aurora-content-title {
    font-size: 1.1rem;
    font-weight: 600;
    color: rgba(255, 255, 255, 0.95);
}

.aurora-status-badge {
    padding: 4px 12px;
    border-radius: 12px;
    font-size: 0.75rem;
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

.aurora-status-badge.completed {
    background: rgba(0, 255, 127, 0.15);
    color: #00FF7F;
    border: 1px solid rgba(0, 255, 127, 0.3);
}

.aurora-content-body {
    color: rgba(255, 255, 255, 0.85);
    line-height: 1.6;
    font-size: 0.95rem;
}

.aurora-editor-section {
    background: rgba(255, 255, 127, 0.05);
    border: 1px solid rgba(255, 255, 127, 0.15);
    border-radius: 12px;
    padding: 16px;
    margin: 16px 0;
}

.aurora-editor-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.aurora-editor-title {
    font-weight: 600;
    color: rgba(255, 255, 255, 0.95);
}

.aurora-editor-badge {
    background: rgba(255, 255, 127, 0.15);
    color: #FFFF7F;
    padding: 4px 8px;
    border-radius: 8px;
    font-size: 0.7rem;
    font-weight: 500;
}

.aurora-critique-card {
    background: rgba(255, 255, 255, 0.02);
    border-radius: 8px;
    padding: 16px;
    margin: 12px 0;
}

.aurora-critique-content {
    color: rgba(255, 255, 255, 0.8);
    line-height: 1.5;
    font-size: 0.9rem;
}

@keyframes aurora-scan {
    0%, 100% { left: -100%; }
    50% { left: 100%; }
}
</style>
""" 