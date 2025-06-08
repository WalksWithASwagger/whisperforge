"""
Streaming Results Display for WhisperForge
Shows content as it's generated with beautiful Aurora styling
"""

import streamlit as st
import html
import time
from typing import Dict, Any, Optional
from .streaming_pipeline import get_pipeline_controller


def show_streaming_results():
    """Display beautiful final results when processing is complete"""
    controller = get_pipeline_controller()
    results = controller.get_results()
    errors = controller.get_errors()
    
    # Only show final results when pipeline is complete
    if not controller.is_complete:
        return
        
    if not results and not errors:
        return
    
    # Beautiful final results header
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, rgba(0, 255, 255, 0.08), rgba(64, 224, 208, 0.12));
        border: 1px solid rgba(0, 255, 255, 0.2);
        border-radius: 16px;
        padding: 24px;
        margin: 24px 0;
        text-align: center;
    ">
        <h2 style="color: #00FFFF; margin: 0 0 8px 0;">Content Generated</h2>
        <p style="color: rgba(255, 255, 255, 0.7); margin: 0;">Your luminous wisdom, ready to share</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Export options
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("📤 Export PDF", type="secondary", use_container_width=True):
            st.info("PDF export feature coming soon!")
    with col2:
        if st.button("📝 Send to Notion", type="primary", use_container_width=True):
            st.info("Notion integration coming soon!")
    
    # Content tabs like in your screenshot
    if "social_content" in results:
        tabs = st.tabs(["📰 Blog Post", "📱 Social Posts", "💎 Wisdom", "🖼️ Images", "🎙️ Transcript"])
        
        with tabs[0]:
            if "article_creation" in results:
                st.markdown("### Full Article")
                st.markdown(results["article_creation"])
                if st.button("📋 Copy Article", key="copy_article"):
                    st.code(results["article_creation"], language="markdown")
        
        with tabs[1]:
            if "social_content" in results:
                _show_social_posts_beautiful(results["social_content"])
                
        with tabs[2]:
            if "wisdom_extraction" in results:
                st.markdown("### Key Insights")
                st.markdown(results["wisdom_extraction"])
                if st.button("📋 Copy Wisdom", key="copy_wisdom"):
                    st.code(results["wisdom_extraction"], language="markdown")
        
        with tabs[3]:
            if "image_prompts" in results:
                st.markdown("### Image Generation Prompts")
                st.markdown(results["image_prompts"])
                if st.button("📋 Copy Prompts", key="copy_images"):
                    st.code(results["image_prompts"], language="markdown")
                    
        with tabs[4]:
            if "transcription" in results:
                st.markdown("### Full Transcript")
                st.markdown(results["transcription"])
                if st.button("📋 Copy Transcript", key="copy_transcript"):
                    st.code(results["transcription"], language="markdown")


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
    """Show pipeline status with individual step containers like in the screenshots"""
    controller = get_pipeline_controller()
    
    if not controller.is_active and not controller.is_complete:
        return
    
    # Overall progress header
    current_step = controller.current_step_index
    total_steps = 8
    overall_progress = (current_step / total_steps) * 100
    
    st.markdown(f"""
    <div style="margin-bottom: 24px;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
            <h3 style="color: #00FFFF; margin: 0;">Overall Progress</h3>
            <span style="color: rgba(255, 255, 255, 0.8); font-size: 1.2rem; font-weight: bold;">{overall_progress:.0f}%</span>
        </div>
        <div style="
            background: rgba(0, 0, 0, 0.4);
            border-radius: 12px;
            height: 8px;
            overflow: hidden;
        ">
            <div style="
                background: linear-gradient(90deg, #00FFFF, #7DF9FF, #40E0D0);
                height: 100%;
                width: {overall_progress}%;
                border-radius: 12px;
                box-shadow: 0 0 16px rgba(0, 255, 255, 0.6);
                transition: width 0.8s ease;
            "></div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Pipeline steps with individual containers
    pipeline_steps = [
        ("Audio Transcription", "Converting speech to text using Whisper AI", "upload_validation"),
        ("Wisdom Extraction", "Identifying key insights and valuable knowledge", "wisdom_extraction"),  
        ("Outline Generation", "Creating structured content framework", "outline_creation"),
        ("Blog Composition", "Crafting engaging article content", "article_creation"),
        ("Social Media Posts", "Generating 5 platform-optimized posts", "social_content"),
        ("Image Prompts", "Creating visual content descriptions", "image_prompts"),
        ("Export & Metadata", "Finalizing output and Notion integration", "database_storage")
    ]
    
    results = controller.get_results()
    
    for i, (title, description, step_key) in enumerate(pipeline_steps):
        # Determine step state
        if i < current_step:
            # Completed
            state = "completed"
            icon = "✅"
            border_color = "rgba(34, 197, 94, 0.4)"
            bg_color = "rgba(34, 197, 94, 0.05)"
            progress = 100
        elif i == current_step and controller.is_active:
            # Currently processing
            state = "processing" 
            icon = "🔄"
            border_color = "rgba(0, 255, 255, 0.4)"
            bg_color = "rgba(0, 255, 255, 0.08)"
            # Simulate step progress (you can make this more accurate)
            progress = min(85, (time.time() % 10) * 10) if controller.is_active else 42
        else:
            # Pending
            state = "pending"
            icon = "⭕"
            border_color = "rgba(107, 114, 128, 0.3)"
            bg_color = "rgba(107, 114, 128, 0.05)"
            progress = 0
            
        # Create individual step container
        step_html = f"""
        <div style="
            background: {bg_color};
            border: 1px solid {border_color};
            border-radius: 12px;
            padding: 20px;
            margin: 12px 0;
            position: relative;
            overflow: hidden;
        ">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div style="display: flex; align-items: center; gap: 12px;">
                    <span style="font-size: 1.2rem;">{icon}</span>
                    <div>
                        <h4 style="color: #00FFFF; margin: 0; font-size: 1.1rem;">{title}</h4>
                        <p style="color: rgba(255, 255, 255, 0.6); margin: 4px 0 0 0; font-size: 0.9rem;">{description}</p>
                    </div>
                </div>
                <div style="text-align: right;">
                    <span style="color: rgba(255, 255, 255, 0.8); font-weight: bold;">{progress}%</span>
                    {"<span style='color: rgba(255, 255, 255, 0.5); font-size: 0.8rem; margin-left: 8px;'>▼</span>" if state == "completed" else ""}
                </div>
            </div>
        """
        
        # Add progress bar for processing steps
        if state == "processing":
            step_html += f"""
            <div style="margin-top: 16px;">
                <div style="display: flex; justify-content: space-between; margin-bottom: 6px;">
                    <span style="color: rgba(255, 255, 255, 0.7); font-size: 0.8rem;">Processing...</span>
                    <span style="color: rgba(255, 255, 255, 0.7); font-size: 0.8rem;">{progress}%</span>
                </div>
                <div style="
                    background: rgba(0, 0, 0, 0.3);
                    border-radius: 8px;
                    height: 6px;
                    overflow: hidden;
                ">
                    <div style="
                        background: linear-gradient(90deg, #00FFFF, #40E0D0);
                        height: 100%;
                        width: {progress}%;
                        border-radius: 8px;
                        box-shadow: 0 0 12px rgba(0, 255, 255, 0.5);
                        transition: width 0.5s ease;
                    "></div>
                </div>
            </div>
            """
        
        step_html += "</div>"
        
        st.markdown(step_html, unsafe_allow_html=True)
        
        # Show expandable content for completed steps
        if state == "completed" and step_key in results:
            with st.expander(f"View {title} Results", expanded=False):
                content = results[step_key]
                if len(str(content)) > 300:
                    st.markdown(f"**Preview:** {str(content)[:300]}...")
                    if st.button(f"Show Full Content", key=f"full_{step_key}"):
                        st.markdown(content)
                else:
                    st.markdown(content)
    
    # Control button
    if controller.is_active:
        st.markdown("<br>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([2, 1, 1])
        with col2:
            if st.button("⏹️ Stop Processing", key="stop_processing", type="secondary"):
                controller.reset_pipeline()
                st.rerun()
        with col3:
            if st.button("🔄 Refresh", key="refresh_status"):
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