"""
Streaming Results Display for WhisperForge
Shows content as it's generated with beautiful Aurora styling
"""

import streamlit as st
import html
import time
from typing import Dict, Any, Optional
from .streaming_pipeline import get_pipeline_controller
import uuid

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

# Enhanced UI Functions for streaming results
def apply_streaming_css():
    """Apply Aurora theme CSS for streaming results"""

# Generate truly unique keys for Streamlit widgets
def generate_unique_key(base_name: str) -> str:
    """Generate truly unique key for Streamlit widgets to prevent DuplicateWidgetID errors"""
    return f"{base_name}_{uuid.uuid4().hex[:8]}_{int(time.time() * 1000000) % 1000000}"

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
    
    # 🌌 AWARD-WINNING MINIMAL COMPLETION INTERFACE
    st.markdown(f"""
    <div class="zen-completion">
        <div class="aurora-orb"></div>
        <div class="completion-content">
            <div class="zen-title">∞</div>
            <div class="zen-subtitle">transformation complete</div>
            <div class="bio-dots">
                <span class="dot active"></span>
                <span class="dot active"></span>
                <span class="dot active"></span>
            </div>
        </div>
        <div class="aurora-pulse"></div>
    </div>
    
    <div class="action-constellation">
        <div class="action-orb primary" onclick="downloadAll()">
            <div class="orb-icon">⬇</div>
            <div class="orb-label">gather</div>
        </div>
        <div class="action-orb secondary" onclick="exportPDF()">
            <div class="orb-icon">◐</div>
            <div class="orb-label">PDF</div>
        </div>
        <div class="action-orb tertiary" onclick="sendNotion()">
            <div class="orb-icon">◑</div>
            <div class="orb-label">notion</div>
        </div>
    </div>
    
    <style>
    .zen-completion {{
        position: relative;
        padding: 2rem 0;
        display: flex;
        flex-direction: column;
        align-items: center;
        margin: 2rem 0;
        min-height: 120px;
    }}
    
    .aurora-orb {{
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        width: 80px;
        height: 80px;
        border-radius: 50%;
        background: radial-gradient(circle, rgba(0, 255, 255, 0.15), rgba(64, 224, 208, 0.05), transparent);
        animation: orb-breathe 4s ease-in-out infinite;
        filter: blur(0.5px);
    }}
    
    .completion-content {{
        position: relative;
        z-index: 2;
        text-align: center;
    }}
    
    .zen-title {{
        font-size: 2.5rem;
        font-weight: 200;
        color: rgba(0, 255, 255, 0.9);
        margin: 0;
        letter-spacing: 0.1em;
        text-shadow: 0 0 20px rgba(0, 255, 255, 0.3);
        animation: zen-glow 3s ease-in-out infinite;
    }}
    
    .zen-subtitle {{
        font-size: 0.85rem;
        color: rgba(255, 255, 255, 0.5);
        margin: 0.5rem 0 1rem 0;
        letter-spacing: 0.15em;
        font-weight: 300;
    }}
    
    .bio-dots {{
        display: flex;
        gap: 8px;
        justify-content: center;
    }}
    
    .dot {{
        width: 4px;
        height: 4px;
        border-radius: 50%;
        background: rgba(0, 255, 255, 0.3);
        transition: all 0.3s ease;
    }}
    
    .dot.active {{
        background: #00FFFF;
        box-shadow: 0 0 8px rgba(0, 255, 255, 0.6);
        animation: bio-pulse 2s ease-in-out infinite;
    }}
    
    .aurora-pulse {{
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 1px;
        background: linear-gradient(90deg, transparent, rgba(0, 255, 255, 0.6), transparent);
        animation: aurora-scan 6s ease-in-out infinite;
    }}
    
    .action-constellation {{
        display: flex;
        justify-content: center;
        gap: 2rem;
        margin: 2rem 0;
        padding: 1rem 0;
    }}
    
    .action-orb {{
        position: relative;
        width: 64px;
        height: 64px;
        border-radius: 50%;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        cursor: pointer;
        transition: all 0.4s cubic-bezier(0.23, 1, 0.32, 1);
        border: 1px solid rgba(0, 255, 255, 0.1);
        backdrop-filter: blur(10px);
    }}
    
    .action-orb.primary {{
        background: radial-gradient(circle, rgba(0, 255, 255, 0.08), rgba(64, 224, 208, 0.03));
        border-color: rgba(0, 255, 255, 0.2);
    }}
    
    .action-orb.secondary {{
        background: radial-gradient(circle, rgba(138, 43, 226, 0.06), rgba(148, 0, 211, 0.02));
        border-color: rgba(138, 43, 226, 0.15);
    }}
    
    .action-orb.tertiary {{
        background: radial-gradient(circle, rgba(255, 20, 147, 0.06), rgba(255, 69, 0, 0.02));
        border-color: rgba(255, 20, 147, 0.15);
    }}
    
    .action-orb:hover {{
        transform: translateY(-4px) scale(1.05);
        box-shadow: 0 12px 30px rgba(0, 255, 255, 0.15);
    }}
    
    .action-orb.primary:hover {{
        border-color: rgba(0, 255, 255, 0.4);
        box-shadow: 0 12px 30px rgba(0, 255, 255, 0.2);
    }}
    
    .action-orb.secondary:hover {{
        border-color: rgba(138, 43, 226, 0.3);
        box-shadow: 0 12px 30px rgba(138, 43, 226, 0.15);
    }}
    
    .action-orb.tertiary:hover {{
        border-color: rgba(255, 20, 147, 0.3);
        box-shadow: 0 12px 30px rgba(255, 20, 147, 0.15);
    }}
    
    .orb-icon {{
        font-size: 1.5rem;
        color: rgba(255, 255, 255, 0.8);
        margin-bottom: 4px;
        transition: all 0.3s ease;
    }}
    
    .orb-label {{
        font-size: 0.7rem;
        color: rgba(255, 255, 255, 0.6);
        letter-spacing: 0.05em;
        font-weight: 300;
        transition: all 0.3s ease;
    }}
    
    .action-orb:hover .orb-icon {{
        color: white;
        transform: scale(1.1);
    }}
    
    .action-orb:hover .orb-label {{
        color: rgba(255, 255, 255, 0.9);
    }}
    
    @keyframes orb-breathe {{
        0%, 100% {{ transform: translate(-50%, -50%) scale(1); opacity: 0.6; }}
        50% {{ transform: translate(-50%, -50%) scale(1.1); opacity: 0.8; }}
    }}
    
    @keyframes zen-glow {{
        0%, 100% {{ text-shadow: 0 0 20px rgba(0, 255, 255, 0.3); }}
        50% {{ text-shadow: 0 0 30px rgba(0, 255, 255, 0.6), 0 0 40px rgba(64, 224, 208, 0.3); }}
    }}
    
    @keyframes bio-pulse {{
        0%, 100% {{ opacity: 1; transform: scale(1); }}
        50% {{ opacity: 0.6; transform: scale(1.2); }}
    }}
    
    @keyframes aurora-scan {{
        0%, 100% {{ left: -100%; opacity: 0; }}
        25% {{ opacity: 1; }}
        75% {{ opacity: 1; }}
        100% {{ left: 100%; opacity: 0; }}
    }}
    </style>
    """, unsafe_allow_html=True)
    
    # Hidden Streamlit buttons for functionality (triggered by JavaScript)
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("Download All", key="hidden_download", help="Download all content"):
            _show_download_options(results)
    with col2:
        if st.button("Export PDF", key="hidden_pdf", help="Export as PDF"):
            st.info("✨ PDF export coming soon!")
    with col3:
        if st.button("Send to Notion", key="hidden_notion", help="Send to Notion"):
            st.info("🔗 Notion integration coming soon!")
    
    st.markdown("<div style='margin: 16px 0;'></div>", unsafe_allow_html=True)
    
    # 🌸 ZEN CONTENT GARDEN - Japanese minimalism meets bioluminescence
    content_sections = [
        ("article_creation", "○", "article", "Your comprehensive piece"),
        ("social_content", "◐", "social", "Platform content"),
        ("wisdom_extraction", "◑", "insights", "Core wisdom"),
        ("image_prompts", "◒", "visuals", "Image concepts"),
        ("transcription", "●", "transcript", "Source audio")
    ]
    
    available_content = []
    for key, symbol, name, desc in content_sections:
        if key in results and results[key]:
            available_content.append((key, symbol, name, desc, results[key]))
    
    if available_content:
        st.markdown("""
        <div class="content-garden">
            <div class="garden-title">created essence</div>
        </div>
        
        <style>
        .content-garden {
            text-align: center;
            margin: 3rem 0 2rem 0;
        }
        
        .garden-title {
            font-size: 1.1rem;
            color: rgba(255, 255, 255, 0.4);
            letter-spacing: 0.2em;
            font-weight: 200;
            margin-bottom: 2rem;
        }
        
        .content-zen-card {
            background: rgba(0, 255, 255, 0.01);
            border: 1px solid rgba(0, 255, 255, 0.08);
            border-radius: 16px;
            margin: 1rem 0;
            transition: all 0.5s cubic-bezier(0.23, 1, 0.32, 1);
            overflow: hidden;
            position: relative;
        }
        
        .content-zen-card:hover {
            border-color: rgba(0, 255, 255, 0.15);
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(0, 255, 255, 0.08);
        }
        
        .content-zen-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 1px;
            background: linear-gradient(90deg, transparent, rgba(0, 255, 255, 0.3), transparent);
            transition: left 0.6s ease;
        }
        
        .content-zen-card:hover::before {
            left: 100%;
        }
        
        .zen-header {
            padding: 1.5rem 2rem;
            display: flex;
            align-items: center;
            gap: 1rem;
            cursor: pointer;
        }
        
        .zen-symbol {
            font-size: 1.8rem;
            color: rgba(0, 255, 255, 0.7);
            transition: all 0.3s ease;
            width: 40px;
            text-align: center;
        }
        
        .zen-info {
            flex: 1;
        }
        
        .zen-name {
            font-size: 1rem;
            color: rgba(255, 255, 255, 0.8);
            margin: 0;
            font-weight: 300;
            letter-spacing: 0.05em;
        }
        
        .zen-desc {
            font-size: 0.8rem;
            color: rgba(255, 255, 255, 0.4);
            margin: 0.2rem 0 0 0;
            font-weight: 200;
        }
        
        .zen-expand {
            color: rgba(255, 255, 255, 0.3);
            font-size: 0.8rem;
            transition: all 0.3s ease;
        }
        
        .content-zen-card:hover .zen-symbol {
            color: #00FFFF;
            transform: scale(1.1);
        }
        
        .content-zen-card:hover .zen-expand {
            color: rgba(255, 255, 255, 0.6);
        }
        </style>
        """, unsafe_allow_html=True)
        
        for key, symbol, name, desc, content in available_content:
            # Zen content card
            st.markdown(f"""
            <div class="content-zen-card">
                <div class="zen-header">
                    <div class="zen-symbol">{symbol}</div>
                    <div class="zen-info">
                        <div class="zen-name">{name}</div>
                        <div class="zen-desc">{desc}</div>
                    </div>
                    <div class="zen-expand">◦</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Minimalist expandable content
            with st.expander(f"explore {name}", expanded=False):
                if key == "social_content":
                    _show_social_posts_zen(content)
                else:
                    # Clean content display
                    if len(content) > 1000:
                        st.markdown("**preview**")
                        st.markdown(f"*{content[:500]}...*")
                        
                        reveal_key = generate_unique_key(f"show_full_{key}_{name}")
                        if st.button(f"reveal all", key=reveal_key):
                            st.markdown("**complete**")
                            textarea_key = generate_unique_key(f"textarea_{key}_{name}")
                            st.text_area("", content, height=300, key=textarea_key)
                    else:
                        st.markdown(content)
                
                # Zen copy action
                copy_key = generate_unique_key(f"copy_{key}_{name}")
                if st.button(f"∞ capture", key=copy_key, use_container_width=False):
                    st.code(content, language="text")


def _show_social_posts_zen(social_content: str):
    """Display social posts with zen aesthetic"""
    
    # Parse the social content into individual posts
    posts = []
    if social_content:
        # Try to split by common post separators
        potential_posts = social_content.split('\n\n')
        post_num = 1
        for post in potential_posts:
            if post.strip() and len(post.strip()) > 20:
                posts.append((f"essence {post_num}", post.strip()))
                post_num += 1
    
    if not posts:
        posts = [("essence 1", social_content)]
    
    # Zen post display
    st.markdown("""
    <style>
    .zen-post {
        background: rgba(0, 255, 255, 0.005);
        border: 1px solid rgba(0, 255, 255, 0.06);
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
        transition: all 0.4s ease;
        position: relative;
        overflow: hidden;
    }
    
    .zen-post:hover {
        border-color: rgba(0, 255, 255, 0.12);
        transform: translateY(-1px);
    }
    
    .zen-post::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 1px;
        background: linear-gradient(90deg, transparent, rgba(0, 255, 255, 0.2), transparent);
        opacity: 0;
        transition: opacity 0.4s ease;
    }
    
    .zen-post:hover::before {
        opacity: 1;
    }
    
    .zen-post-title {
        font-size: 0.8rem;
        color: rgba(255, 255, 255, 0.4);
        margin-bottom: 1rem;
        letter-spacing: 0.1em;
        font-weight: 200;
    }
    
    .zen-post-content {
        color: rgba(255, 255, 255, 0.8);
        line-height: 1.7;
        font-weight: 300;
        font-size: 0.95rem;
    }
    </style>
    """, unsafe_allow_html=True)
    
    for post_title, post_content in posts[:5]:
        st.markdown(f"""
        <div class="zen-post">
            <div class="zen-post-title">{post_title}</div>
            <div class="zen-post-content">{post_content.replace(chr(10), '<br>')}</div>
        </div>
        """, unsafe_allow_html=True)
        
        # Minimal copy button
        if st.button(f"◦ capture {post_title.split()[1]}", key=f"copy_{post_title.lower().replace(' ', '_')}", use_container_width=False):
            st.code(post_content, language="text")


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


def show_enhanced_streaming_status():
    """PHASE 3: ENHANCED STREAMING UX OVERHAUL - 2025 st.status() integration"""
    controller = get_pipeline_controller()
    
    if not controller.is_active and not controller.is_complete:
        return

    current_step = controller.current_step_index
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
    errors = controller.get_errors() if hasattr(controller, 'get_errors') else {}
    
    # Main processing status container with st.status()
    if controller.is_active:
        current_title, current_desc, current_key = pipeline_steps[current_step]
        
        with st.status(f"🔄 {current_title}", expanded=True) as status:
            st.write(f"📝 **{current_desc}**")
            
            # Show previous completed steps
            for i in range(current_step):
                title, _, step_key = pipeline_steps[i]
                if step_key in results:
                    st.write(f"✅ {title} - Complete")
                elif step_key in errors:
                    st.write(f"❌ {title} - Error: {errors[step_key]}")
                else:
                    st.write(f"✅ {title} - Complete")
            
            # Current step with progress
            st.write(f"🔄 **{current_title}** - {current_desc}...")
            
            # Show preview of remaining steps
            for i in range(current_step + 1, len(pipeline_steps)):
                title, _, _ = pipeline_steps[i]
                st.write(f"⭕ {title} - Pending")
            
            # Update status based on completion
            if current_step >= len(pipeline_steps) - 1:
                status.update(label="✅ Processing Complete!", state="complete", expanded=False)
            else:
                status.update(label=f"🔄 {current_title}", state="running")
    
    elif controller.is_complete:
        st.status("✅ All processing complete!", state="complete", expanded=False)
        
        # Show completion summary
        with st.container():
            st.markdown("### 🌟 Generation Summary")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Steps Completed", len([r for r in results if r]), len(pipeline_steps))
            with col2:
                st.metric("Errors", len(errors), delta_color="inverse")
            with col3:
                success_rate = ((len(results) - len(errors)) / len(pipeline_steps)) * 100
                st.metric("Success Rate", f"{success_rate:.1f}%")


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

def show_processing_status():
    """Display ultra-modern Aurora pipeline with real-time visibility - ORIGINAL"""
    show_enhanced_streaming_status()  # Use the new enhanced version 