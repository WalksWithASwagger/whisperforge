"""
Streaming Results Display for WhisperForge
Shows content as it's generated with beautiful Aurora styling
"""

import streamlit as st
import html
import time
from typing import Dict, Any, Optional
from .streaming_pipeline import get_pipeline_controller

# CSS for streaming results
STREAMING_RESULTS_CSS = """
<style>
/* Aurora Progress Animation */
@keyframes aurora-flow {
    0%, 100% { left: -100%; opacity: 0; }
    25% { opacity: 1; }
    75% { opacity: 1; }
    100% { left: 100%; opacity: 0; }
}

@keyframes aurora-pulse {
    0%, 100% { opacity: 1; transform: scale(1); }
    50% { opacity: 0.7; transform: scale(1.1); }
}

@keyframes completion-glow {
    0%, 100% { left: -100%; opacity: 0; }
    20% { opacity: 1; }
    80% { opacity: 1; }
    100% { left: 100%; opacity: 0; }
}

/* Enhanced Button Styling */
.stButton > button {
    background: linear-gradient(135deg, rgba(0, 255, 255, 0.1), rgba(64, 224, 208, 0.15)) !important;
    border: 1px solid rgba(0, 255, 255, 0.2) !important;
    color: rgba(255, 255, 255, 0.9) !important;
    border-radius: 8px !important;
    font-weight: 500 !important;
    transition: all 0.3s ease !important;
}

.stButton > button:hover {
    background: linear-gradient(135deg, rgba(0, 255, 255, 0.15), rgba(64, 224, 208, 0.2)) !important;
    border-color: rgba(0, 255, 255, 0.3) !important;
    color: white !important;
    transform: translateY(-1px);
    box-shadow: 0 4px 15px rgba(0, 255, 255, 0.15);
}

/* Expander Styling */
.streamlit-expanderHeader {
    background: rgba(0, 255, 255, 0.03) !important;
    border: 1px solid rgba(0, 255, 255, 0.1) !important;
    border-radius: 8px !important;
}

.streamlit-expanderContent {
    background: rgba(0, 255, 255, 0.02) !important;
    border: 1px solid rgba(0, 255, 255, 0.1) !important;
    border-top: none !important;
    border-radius: 0 0 8px 8px !important;
}
</style>
"""


def show_streaming_results():
    """Display ultra-modern Aurora final results - STREAMLINED"""
    controller = get_pipeline_controller()
    results = controller.get_results()
    errors = controller.get_errors() if hasattr(controller, 'get_errors') else {}
    
    # Only show final results when pipeline is complete
    if not controller.is_complete:
        return
        
    if not results and not errors:
        return
    
    # Ultra-compact Aurora completion header with debug info
    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, rgba(0, 255, 255, 0.1), rgba(64, 224, 208, 0.15));
        border: 1px solid rgba(0, 255, 255, 0.3);
        border-radius: 12px;
        padding: 16px 24px;
        margin: 16px 0;
        text-align: center;
        position: relative;
        overflow: hidden;
    ">
        <div style="
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 2px;
            background: linear-gradient(90deg, transparent, #00FFFF, #40E0D0, transparent);
            animation: completion-glow 3s ease-in-out infinite;
        "></div>
        <h3 style="color: #00FFFF; margin: 0 0 4px 0; font-weight: 700;">Content Generated</h3>
        <p style="color: rgba(255, 255, 255, 0.7); margin: 0; font-size: 0.9rem;">Ready to transform the world • {len(results)} items • DB save: {"✅" if "database_storage" in results else "❌"}</p>
    </div>
    
    <style>
    @keyframes completion-glow {{
        0%, 100% {{ left: -100%; opacity: 0; }}
        20% {{ opacity: 1; }}
        80% {{ opacity: 1; }}
        100% {{ left: 100%; opacity: 0; }}
    }}
    </style>
    """, unsafe_allow_html=True)
    
    # Compact export actions
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("📥 Export PDF", type="secondary", use_container_width=True):
            st.success("Feature coming soon!")
    with col2:
        if st.button("📝 Send to Notion", type="primary", use_container_width=True):
            st.success("Feature coming soon!")
    
    st.markdown("<div style='margin: 16px 0;'></div>", unsafe_allow_html=True)
    
    # Dynamic content display - no redundant tabs since we have streaming results above
    content_sections = [
        ("article_creation", "📰 Blog Post", "Your full article content"),
        ("social_content", "📱 Social Posts", "Platform-optimized social content"),
        ("wisdom_extraction", "💎 Key Insights", "Extracted wisdom and takeaways"),
        ("image_prompts", "🖼️ Visual Concepts", "AI image generation prompts"),
        ("transcription", "🎙️ Transcript", "Full audio transcription")
    ]
    
    available_content = []
    for key, title, desc in content_sections:
        if key in results and results[key]:
            available_content.append((key, title, desc, results[key]))
    
    if available_content:
        for key, title, desc, content in available_content:
            # Ultra-sleek content card
            st.markdown(f"""
            <div style="
                background: rgba(0, 255, 255, 0.03);
                border: 1px solid rgba(0, 255, 255, 0.15);
                border-radius: 8px;
                margin: 8px 0;
                transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            ">
                <div style="
                    padding: 12px 16px;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    border-bottom: 1px solid rgba(0, 255, 255, 0.1);
                ">
                    <div>
                        <h5 style="color: #00FFFF; margin: 0; font-size: 0.95rem; font-weight: 600;">{title}</h5>
                        <p style="color: rgba(255, 255, 255, 0.6); margin: 2px 0 0 0; font-size: 0.8rem;">{desc}</p>
                    </div>
                    <div style="color: rgba(255, 255, 255, 0.5); font-size: 0.7rem;">▼</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Show content in expandable section
            with st.expander(f"View {title.split(' ', 1)[1]}", expanded=False):
                if key == "social_content":
                    _show_social_posts_beautiful(content)
                else:
                    if len(content) > 800:
                        st.markdown(f"**Preview:** {content[:800]}...")
                        if st.button(f"Show Full Content", key=f"show_full_{key}_{hash(title)%1000}"):
                            st.text_area(f"Full {title} Content", content, height=400, key=f"textarea_{key}_{hash(title)%1000}")
                    else:
                        st.markdown(content)
                
                # Compact copy button
                if st.button(f"📋 Copy", key=f"copy_{key}_{hash(title)%1000}", use_container_width=False):
                    st.code(content, language="markdown")


def _show_social_posts_beautiful(social_content: str):
    """Show social posts in beautiful individual cards like the screenshot"""
    
    # Parse the social content into individual posts
    posts = []
    if social_content:
        # Try to split by common post separators
        potential_posts = social_content.split('\n\n')
        post_num = 1
        for post in potential_posts:
            if post.strip() and len(post.strip()) > 20:  # Filter out empty or very short lines
                posts.append((f"Social Post #{post_num}", post.strip()))
                post_num += 1
    
    if not posts:
        posts = [("Social Post #1", social_content)]  # Fallback to single post
    
    # Show each post in a beautiful card
    for post_title, post_content in posts[:5]:  # Limit to 5 posts max
        st.markdown(f"""
        <div style="
            background: rgba(0, 255, 255, 0.03);
            border: 1px solid rgba(0, 255, 255, 0.1);
            border-radius: 12px;
            padding: 20px;
            margin: 12px 0;
        ">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                <h4 style="color: #00FFFF; margin: 0;">{post_title}</h4>
                <button style="
                    background: transparent;
                    border: 1px solid rgba(0, 255, 255, 0.3);
                    color: #00FFFF;
                    border-radius: 6px;
                    padding: 4px 8px;
                    font-size: 0.8rem;
                    cursor: pointer;
                ">📋</button>
            </div>
            <div style="color: rgba(255, 255, 255, 0.9); line-height: 1.6;">
                {post_content.replace(chr(10), '<br>')}
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Individual copy button for each post
        if st.button(f"📋 Copy {post_title}", key=f"copy_{post_title.lower().replace(' ', '_').replace('#', '')}", use_container_width=False):
            st.code(post_content, language="text")


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
    """Display ultra-modern Aurora pipeline with real-time visibility"""
    controller = get_pipeline_controller()
    
    if not controller.is_active and not controller.is_complete:
        return
    
    current_step = controller.current_step_index
    errors = controller.get_errors() if hasattr(controller, 'get_errors') else {}
    
    # Compact Aurora processing header - FIXED string formatting
    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, rgba(0, 255, 255, 0.1), rgba(64, 224, 208, 0.15));
        border: 1px solid rgba(0, 255, 255, 0.3);
        border-radius: 12px;
        padding: 16px 24px;
        margin: 16px 0;
        text-align: center;
        position: relative;
        overflow: hidden;
    ">
        <div style="
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 2px;
            background: linear-gradient(90deg, transparent, #00FFFF, #40E0D0, transparent);
            animation: aurora-scan 4s ease-in-out infinite;
        "></div>
        <h3 style="color: #00FFFF; margin: 0; font-weight: 700; text-shadow: 0 0 20px rgba(0, 255, 255, 0.5);">
            Processing Pipeline
        </h3>
        <p style="color: rgba(255, 255, 255, 0.7); margin: 4px 0 0 0; font-size: 0.9rem;">
            Real-time transformation • Step {current_step + 1}/8
        </p>
    </div>
    
    <style>
    @keyframes aurora-scan {{
        0%, 100% {{ left: -100%; }}
        50% {{ left: 100%; }}
    }}
    </style>
    """, unsafe_allow_html=True)
    
    # Compact pipeline steps - single container each
    pipeline_steps = [
        ("Upload Validation", "File format & compatibility check", "upload_validation"),
        ("Audio Transcription", "Speech-to-text conversion", "transcription"),
        ("Wisdom Extraction", "Key insights extraction", "wisdom_extraction"),  
        ("Outline Generation", "Content structure creation", "outline_creation"),
        ("Article Creation", "Full article generation", "article_creation"),
        ("Social Media Posts", "Platform-optimized content", "social_content"),
        ("Image Prompts", "Visual concept generation", "image_prompts"),
        ("Database Storage", "Secure content storage", "database_storage")
    ]
    
    results = controller.get_results()
    
    for i, (title, description, step_key) in enumerate(pipeline_steps):
        # Determine step state and real visibility
        has_error = step_key in errors
        has_result = step_key in results
        
        if has_error:
            state = "error"
            icon = "❌"
            border_color = "rgba(255, 68, 68, 0.6)"
            bg_color = "rgba(255, 68, 68, 0.1)"
            progress = 0
            status_text = "Error"
        elif i < current_step or (i == current_step and has_result):
            state = "completed"
            icon = "✅"
            border_color = "rgba(0, 255, 136, 0.4)"
            bg_color = "rgba(0, 255, 136, 0.08)"
            progress = 100
            status_text = "Complete"
        elif i == current_step and controller.is_active:
            state = "processing"
            icon = "◐"  # More subtle processing indicator
            border_color = "rgba(0, 255, 255, 0.5)"
            bg_color = "rgba(0, 255, 255, 0.12)"
            progress = min(90, max(10, (time.time() % 8) * 12))  # More realistic progress
            status_text = "Processing..."
        else:
            state = "pending"
            icon = "○"
            border_color = "rgba(107, 114, 128, 0.2)"
            bg_color = "rgba(107, 114, 128, 0.03)"
            progress = 0
            status_text = "Pending"
        
        # Ultra-compact Aurora step container with expandable content
        expandable = has_result or has_error
        expand_key = f"expand_step_{i}"
        
        # Step container
        st.markdown(f"""
        <div style="
            background: {bg_color};
            border: 1px solid {border_color};
            border-radius: 8px;
            margin: 8px 0;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            position: relative;
            overflow: hidden;
        ">
            <div style="
                padding: 12px 16px;
                display: flex;
                justify-content: space-between;
                align-items: center;
            ">
                <div style="display: flex; align-items: center; gap: 10px; flex: 1;">
                    <span style="
                        font-size: 1rem;
                        animation: {'aurora-pulse 2s ease-in-out infinite' if state == 'processing' else 'none'};
                    ">{icon}</span>
                    <div style="flex: 1;">
                        <h5 style="color: #00FFFF; margin: 0; font-size: 0.95rem; font-weight: 600;">{title}</h5>
                        <p style="color: rgba(255, 255, 255, 0.6); margin: 2px 0 0 0; font-size: 0.8rem;">{description}</p>
                    </div>
                </div>
                <div style="display: flex; align-items: center; gap: 8px;">
                    <span style="color: rgba(255, 255, 255, 0.8); font-size: 0.85rem; font-weight: 600;">{status_text}</span>
                    {f'<span style="color: rgba(255, 255, 255, 0.5); font-size: 0.7rem;">▼</span>' if expandable else ''}
                </div>
            </div>
            
            {f'''
            <div style="margin-top: 8px; padding: 0 16px 8px;">
                <div style="
                    background: rgba(0, 0, 0, 0.3);
                    border-radius: 6px;
                    height: 4px;
                    overflow: hidden;
                ">
                    <div style="
                        background: linear-gradient(90deg, #00FFFF, #40E0D0);
                        height: 100%;
                        width: {progress}%;
                        border-radius: 6px;
                        box-shadow: 0 0 8px rgba(0, 255, 255, 0.6);
                        transition: width 0.8s cubic-bezier(0.4, 0, 0.2, 1);
                    "></div>
                </div>
            </div>
            ''' if state == 'processing' else ''}
        </div>
        
        <style>
        @keyframes aurora-pulse {{
            0%, 100% {{ opacity: 1; transform: scale(1); }}
            50% {{ opacity: 0.7; transform: scale(1.1); }}
        }}
        </style>
        """, unsafe_allow_html=True)
        
        # Expandable content using Streamlit's native expander
        if expandable:
            with st.expander(f"View {title} Details", expanded=False):
                if has_error:
                    st.error(f"**Error in {title}:**")
                    st.code(errors[step_key], language="text")
                if has_result:
                    content = results[step_key]
                    if isinstance(content, str) and len(content) > 500:
                        st.markdown(f"**Preview:** {content[:500]}...")
                        if st.button(f"Show Full Content", key=f"show_full_{step_key}_{i}"):
                            st.text_area(f"Full {title} Content", content, height=300, key=f"textarea_{step_key}_{i}")
                    else:
                        st.markdown(content if isinstance(content, str) else str(content))
    
    # Compact control buttons
    if controller.is_active or controller.is_complete:
        st.markdown("<div style='margin: 20px 0 10px 0;'></div>", unsafe_allow_html=True)
        
        if controller.is_active:
            col1, col2 = st.columns([1, 1])
            with col1:
                if st.button("⏹ Stop Processing", key="stop_processing", type="secondary", use_container_width=True):
                    controller.reset_pipeline()
                    st.rerun()
            with col2:
                if st.button("🔄 Refresh Status", key="refresh_status", use_container_width=True):
                    st.rerun()
        else:
            col1, col2 = st.columns([1, 1])
            with col1:
                if st.button("🔄 Process New File", key="reset_for_new", use_container_width=True):
                    controller.reset_pipeline()
                    st.rerun()
            with col2:
                if st.button("📥 Download Results", key="download_results", type="primary", use_container_width=True):
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