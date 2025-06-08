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
from .visible_thinking import render_thinking_stream

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
    
    # Always show content that's available, whether complete or not
    if not results and not errors:
        return
    
    # 🌊 NEW: Show live streaming content during processing
    if controller.is_active:
        show_live_streaming_content()
        return
    
    # Only show final results when pipeline is complete
    if not controller.is_complete:
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
        transition: all 0.3s ease;
    }}
    
    @keyframes orb-breathe {{
        0%, 100% {{ transform: translate(-50%, -50%) scale(1); opacity: 0.6; }}
        50% {{ transform: translate(-50%, -50%) scale(1.1); opacity: 0.9; }}
    }}
    
    @keyframes zen-glow {{
        0%, 100% {{ text-shadow: 0 0 20px rgba(0, 255, 255, 0.3); }}
        50% {{ text-shadow: 0 0 30px rgba(0, 255, 255, 0.6); }}
    }}
    
    @keyframes bio-pulse {{
        0%, 100% {{ opacity: 1; transform: scale(1); }}
        50% {{ opacity: 0.7; transform: scale(1.2); }}
    }}
    
    @keyframes aurora-scan {{
        0%, 100% {{ left: -100%; opacity: 0; }}
        25% {{ opacity: 1; }}
        75% {{ opacity: 1; }}
        100% {{ left: 100%; opacity: 0; }}
    }}
    </style>
    """, unsafe_allow_html=True)
    
    # Display all available results with beautiful Aurora styling
    show_2025_content_display()


def show_live_streaming_content():
    """🌊 NEW: Real-time content streaming during processing - 2025 Aurora Style"""
    controller = get_pipeline_controller()
    results = controller.get_results()
    
    if not results:
        return
    
    st.markdown("""
    <div class="live-stream-header">
        <div class="stream-pulse"></div>
        <h3>🌊 Live Generation Stream</h3>
        <div class="stream-indicator">●</div>
    </div>
    
    <style>
    .live-stream-header {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 12px;
        margin: 24px 0;
        padding: 16px;
        background: linear-gradient(135deg, rgba(0, 255, 255, 0.05), rgba(64, 224, 208, 0.08));
        border: 1px solid rgba(0, 255, 255, 0.15);
        border-radius: 12px;
        position: relative;
        overflow: hidden;
    }
    
    .stream-pulse {
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(0, 255, 255, 0.1), transparent);
        animation: stream-flow 3s ease-in-out infinite;
    }
    
    .live-stream-header h3 {
        margin: 0;
        color: #00FFFF;
        font-weight: 300;
        letter-spacing: 0.05em;
    }
    
    .stream-indicator {
        color: #00FF00;
        font-size: 12px;
        animation: blink 1s ease-in-out infinite;
    }
    
    @keyframes stream-flow {
        0%, 100% { left: -100%; opacity: 0; }
        50% { left: 100%; opacity: 1; }
    }
    
    @keyframes blink {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.3; }
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Show available content with streaming animations
    content_map = {
        'transcription': ('🎙️', 'Transcription', 'Audio-to-text conversion'),
        'wisdom_extraction': ('💎', 'Key Insights', 'Extracted wisdom and takeaways'),
        'research_enrichment': ('🔍', 'Research Links', 'Supporting context and sources'),
        'outline_creation': ('📋', 'Content Outline', 'Structured organization'),
        'article_creation': ('📰', 'Full Article', 'Complete written content'),
        'social_content': ('📱', 'Social Posts', 'Platform-optimized content'),
        'image_prompts': ('🖼️', 'Image Prompts', 'Visual concept descriptions')
    }
    
    for key, (icon, title, desc) in content_map.items():
        if key in results and results[key]:
            show_streaming_content_card(icon, title, desc, results[key], is_live=True)


def show_streaming_content_card(icon: str, title: str, description: str, content: str, is_live: bool = False):
    """🎨 Beautiful streaming content card with Aurora effects"""
    
    # Create unique key for this card
    card_key = generate_unique_key(f"stream_card_{title.lower()}")
    
    # Live vs complete styling
    border_color = "rgba(0, 255, 100, 0.2)" if is_live else "rgba(0, 255, 255, 0.15)"
    bg_gradient = "rgba(0, 255, 100, 0.03), rgba(0, 255, 255, 0.05)" if is_live else "rgba(0, 255, 255, 0.03), rgba(64, 224, 208, 0.05)"
    glow_color = "rgba(0, 255, 100, 0.4)" if is_live else "rgba(0, 255, 255, 0.3)"
    
    with st.container():
        st.markdown(f"""
        <div class="aurora-stream-card {'live' if is_live else 'complete'}">
            <div class="card-header">
                <span class="card-icon">{icon}</span>
                <div class="card-title-group">
                    <h4 class="card-title">{title}</h4>
                    <p class="card-description">{description}</p>
                </div>
                {'<div class="live-badge">LIVE</div>' if is_live else '<div class="complete-badge">✓</div>'}
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
        """, unsafe_allow_html=True)
        
        # Content preview with smart truncation
        if len(content) > 300:
            preview = content[:300] + "..."
            
            # Expandable content
            with st.expander(f"📖 Preview {title}", expanded=False):
                st.markdown(preview)
                
            with st.expander(f"📄 Full {title}", expanded=False):
                st.markdown(content)
                
                # Copy button
                copy_key = generate_unique_key(f"copy_{title}")
                if st.button(f"Copy {title}", key=copy_key, help=f"Copy {title} to clipboard"):
                    st.code(content, language="markdown")
        else:
            st.markdown(content)
            
            # Copy button for short content
            copy_key = generate_unique_key(f"copy_short_{title}")
            if st.button(f"Copy {title}", key=copy_key, help=f"Copy {title} to clipboard"):
                st.code(content, language="markdown")


def show_2025_content_display():
    """🚀 Ultra-modern 2025 Aurora content display for completed results"""
    controller = get_pipeline_controller()
    results = controller.get_results()
    
    if not results:
        return
    
    # Beautiful completion header
    st.markdown("""
    <div class="completion-showcase">
        <div class="showcase-bg"></div>
        <div class="showcase-content">
            <h2>✨ Transformation Complete</h2>
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
    """, unsafe_allow_html=True)
    
    # Display all results with modern cards
    content_map = {
        'transcription': ('🎙️', 'Audio Transcription', 'Complete speech-to-text conversion'),
        'wisdom_extraction': ('💎', 'Key Insights & Wisdom', 'Extracted insights and actionable takeaways'),
        'research_enrichment': ('🔍', 'Research Enrichment', 'Supporting links and contextual information'),
        'outline_creation': ('📋', 'Content Outline', 'Structured organization and flow'),
        'article_creation': ('📰', 'Full Article', 'Complete written content ready for publication'),
        'social_content': ('📱', 'Social Media Content', 'Platform-optimized posts and captions'),
        'image_prompts': ('🖼️', 'Image Generation Prompts', 'AI-generated visual concept descriptions')
    }
    
    for key, (icon, title, desc) in content_map.items():
        if key in results and results[key]:
            show_streaming_content_card(icon, title, desc, results[key], is_live=False)


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

def show_enhanced_streaming_status():
    """PHASE 3: ENHANCED STREAMING UX OVERHAUL - 2025 st.status() integration WITH VISIBLE THINKING"""
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
        ("Database Storage", "Secure content storage", "database_storage")
    ]
    
    results = controller.get_results()
    errors = controller.get_errors() if hasattr(controller, 'get_errors') else {}
    
    # 🧠 VISIBLE THINKING INTEGRATION - Show AI thought bubbles during processing
    if controller.is_active and st.session_state.get("thinking_enabled", True):
        # Create dedicated container for thinking bubbles
        thinking_container = st.container()
        with thinking_container:
            st.markdown("""
            <div class="thinking-section">
                <div class="thinking-header">
                    <span class="thinking-icon">🧠</span>
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
            """, unsafe_allow_html=True)
            
            # Render the actual thinking stream
            try:
                render_thinking_stream(thinking_container)
            except Exception as e:
                st.info(f"💭 AI is thinking... (thinking system loading)")
    
    # Main processing status container with st.status()
    if controller.is_active:
        current_title, current_desc, current_key = pipeline_steps[current_step]
        
        with st.status(f"🔄 {current_title}", expanded=True) as status:
            st.write(f"📝 **{current_desc}**")
            
            # Progress bar
            progress = (current_step / len(pipeline_steps)) * 100
            st.progress(progress / 100, text=f"Progress: {progress:.0f}% ({current_step + 1}/{len(pipeline_steps)})")
            
            # Show previous completed steps with content preview
            for i in range(current_step):
                title, _, step_key = pipeline_steps[i]
                if step_key in results:
                    st.write(f"✅ {title} - Complete")
                    # Show brief preview of generated content
                    if step_key in results and results[step_key] and step_key not in ["upload_validation", "database_storage"]:
                        preview = str(results[step_key])[:100] + "..." if len(str(results[step_key])) > 100 else str(results[step_key])
                        st.caption(f"Preview: {preview}")
                elif step_key in errors:
                    st.write(f"❌ {title} - Error: {errors[step_key]}")
                else:
                    st.write(f"✅ {title} - Complete")
            
            # Current step with enhanced styling
            st.markdown(f"""
            <div style="
                background: linear-gradient(135deg, rgba(0, 255, 255, 0.1), rgba(64, 224, 208, 0.05));
                border-left: 3px solid #00FFFF;
                padding: 12px 16px;
                margin: 8px 0;
                border-radius: 0 8px 8px 0;
            ">
                🔄 <strong>{current_title}</strong> - {current_desc}...
            </div>
            """, unsafe_allow_html=True)
            
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
        # Completion status with beautiful summary
        with st.status("✅ All processing complete!", state="complete", expanded=False):
            st.success("Your audio has been transformed into comprehensive content!")
        
        # Enhanced completion summary
        st.markdown("""
        <div class="completion-summary">
            <h4>🌟 Generation Summary</h4>
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
        """, unsafe_allow_html=True)
        
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
        
        # Show content type breakdown
        if results:
            st.markdown("**Generated Content Types:**")
            content_types = []
            if results.get('transcription'): content_types.append("📝 Transcription")
            if results.get('wisdom_extraction'): content_types.append("💎 Insights")
            if results.get('research_enrichment'): content_types.append("🔍 Research")
            if results.get('outline_creation'): content_types.append("📋 Outline")
            if results.get('article_creation'): content_types.append("📰 Article")
            if results.get('social_content'): content_types.append("📱 Social Posts")
            if results.get('image_prompts'): content_types.append("🖼️ Image Prompts")
            
            if content_types:
                st.write(" • ".join(content_types))

def show_processing_status():
    """Display ultra-modern Aurora pipeline with real-time visibility - WRAPPER"""
    show_enhanced_streaming_status()  # Use the new enhanced version 