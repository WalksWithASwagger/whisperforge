"""
Streaming Results Display for WhisperForge
Shows content as it's generated with beautiful Aurora styling
"""

import streamlit as st
import html
from typing import Dict, Any, Optional
from .streaming_pipeline import get_pipeline_controller


def show_streaming_results():
    """Display results as they become available during processing - streaming in individual containers"""
    controller = get_pipeline_controller()
    results = controller.get_results()
    errors = controller.get_errors()
    
    if not results and not errors:
        return
    
    # Results header
    st.markdown("### ✨ Generated Content")
    st.markdown("Each step streams in real-time as processing completes:")
    
    # Define the order and display info for each step
    step_order = [
        ("upload_validation", "📤 Upload Validation", "File validation and pre-processing"),
        ("transcription", "🎙️ Audio Transcription", "Converting speech to text"),
        ("wisdom_extraction", "💎 Wisdom Extraction", "Key insights and takeaways"),
        ("outline_creation", "📋 Content Outline", "Structured organization"),
        ("article_creation", "📰 Full Article", "Comprehensive content piece"),
        ("social_content", "📱 Social Media", "Platform-optimized posts"),
        ("image_prompts", "🖼️ Image Prompts", "AI-generated visual concepts"),
        ("database_storage", "💾 Content Storage", "Saving to secure database")
    ]
    
    # Show each step in its own container as it becomes available
    for step_id, step_title, step_description in step_order:
        if step_id in results or step_id in errors:
            _show_content_stream_card(step_id, step_title, step_description, 
                                    results.get(step_id, ""), errors.get(step_id))
    
    # Show editor feedback separately if available
    if st.session_state.get("editor_enabled", False):
        critique_keys = [k for k in results.keys() if k.endswith("_critique")]
        if critique_keys:
            st.markdown("---")
            st.markdown("### ✍️ Editorial Review")
            _show_editor_feedback(results)


def _show_content_stream_card(step_id: str, step_title: str, step_description: str, content: str, error: Optional[str] = None):
    """Show a streaming content card with Aurora styling for real-time display"""
    
    if error:
        st.error(f"❌ {step_title}: {error}")
        return
    
    if not content:
        st.info(f"🔄 {step_title}: {step_description}...")
        return
    
    # Create expandable container for each result
    with st.expander(f"✅ {step_title} - Complete", expanded=True):
        st.markdown(f"**{step_description}**")
        
        # Special handling for different content types
        if step_id == "upload_validation":
            if isinstance(content, dict):
                st.success(f"File validated: {content.get('file_name', 'Unknown')} ({content.get('file_size_mb', 0):.1f} MB)")
            else:
                st.success(str(content))
        elif step_id == "database_storage":
            st.success("Content saved to database successfully")
        else:
            # Show the actual content with proper formatting
            if len(content) > 1000:
                # For long content, show first part with expand option
                st.markdown(content[:500] + "...")
                with st.expander("Show full content"):
                    st.markdown(content)
            else:
                st.markdown(content)
        
        # Copy button for text content
        if step_id not in ["upload_validation", "database_storage"] and content:
            if st.button(f"📋 Copy {step_title}", key=f"copy_{step_id}", use_container_width=False):
                st.code(content, language="markdown")

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
    """Show current processing status with beautiful Aurora progress bars"""
    controller = get_pipeline_controller()
    
    if not controller.is_active and not controller.is_complete:
        return
    
    # Beautiful Aurora Progress Bar
    st.markdown("### 📊 Processing Pipeline")
    
    # Get current step info
    current_step = controller.current_step_index
    total_steps = 8
    progress_percentage = (current_step / total_steps) * 100
    
    # Create Aurora progress bar with HTML
    aurora_progress_html = f"""
    <div style="
        background: linear-gradient(135deg, rgba(0, 255, 255, 0.08), rgba(64, 224, 208, 0.12));
        backdrop-filter: blur(24px) saturate(180%);
        border: 1px solid rgba(0, 255, 255, 0.15);
        border-radius: 16px;
        padding: 24px;
        margin: 16px 0;
        position: relative;
        overflow: hidden;
    ">
        <div style="
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 16px;
        ">
            <h4 style="color: #00FFFF; margin: 0;">WhisperForge Pipeline</h4>
            <span style="color: rgba(255, 255, 255, 0.8);">{current_step}/{total_steps} steps • {progress_percentage:.1f}%</span>
        </div>
        
        <div style="
            background: rgba(0, 0, 0, 0.3);
            border-radius: 12px;
            height: 12px;
            overflow: hidden;
            margin: 16px 0;
        ">
            <div style="
                background: linear-gradient(90deg, #00FFFF, #7DF9FF, #40E0D0);
                height: 100%;
                width: {progress_percentage}%;
                border-radius: 12px;
                box-shadow: 0 0 20px rgba(0, 255, 255, 0.4);
                transition: width 0.8s ease;
            "></div>
        </div>
        
        <div style="color: rgba(255, 255, 255, 0.9); font-size: 0.9rem;">
            {'🔄 Processing...' if controller.is_active else '✅ Complete!'}
        </div>
    </div>
    """
    
    st.markdown(aurora_progress_html, unsafe_allow_html=True)
    
    # Control buttons
    if controller.is_active:
        col1, col2 = st.columns([3, 1])
        with col1:
            st.info(f"🔄 Currently processing step {current_step + 1} of {total_steps}")
        with col2:
            if st.button("⏹️ Stop", key="stop_processing"):
                controller.reset_pipeline()
                st.rerun()
    
    if controller.is_complete:
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