"""
WhisperForge v2.0 - Streamlit Application
==========================================

Modern, streamlined audio-to-content pipeline with modular architecture.
"""

import streamlit as st
import logging
import tempfile
from pathlib import Path
from typing import Optional, Dict, Any
import sys

# Import our new modular components
from core import ContentPipeline, Config, set_config
from core.config import get_config

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("whisperforge_v2.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("whisperforge_v2")

# Streamlit page configuration
st.set_page_config(
    page_title="WhisperForge v2.0",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)


def init_session_state():
    """Initialize session state variables"""
    if "pipeline" not in st.session_state:
        st.session_state.pipeline = None
    if "results" not in st.session_state:
        st.session_state.results = None
    if "config_valid" not in st.session_state:
        st.session_state.config_valid = False


def configure_app():
    """Handle app configuration and setup"""
    st.sidebar.title("⚡ WhisperForge v2.0")
    st.sidebar.markdown("---")
    
    # Configuration section
    with st.sidebar.expander("⚙️ Configuration", expanded=not st.session_state.config_valid):
        st.markdown("### AI Provider Setup")
        
        # AI Provider selection
        provider = st.selectbox(
            "Primary AI Provider",
            ["openai", "anthropic", "grok"],
            help="OpenAI required for audio transcription"
        )
        
        # API Keys
        openai_key = st.text_input(
            "OpenAI API Key", 
            type="password",
            value=get_config().openai.api_key or "",
            help="Required for audio transcription"
        )
        
        anthropic_key = st.text_input(
            "Anthropic API Key", 
            type="password", 
            value=get_config().anthropic.api_key or "",
            help="Optional: For Claude models"
        )
        
        grok_key = st.text_input(
            "Grok API Key", 
            type="password",
            value=get_config().grok.api_key or "",
            help="Optional: For Grok models"
        )
        
        st.markdown("### Notion Integration")
        notion_key = st.text_input(
            "Notion API Key", 
            type="password",
            value=get_config().notion.api_key or "",
            help="Optional: For exporting content"
        )
        
        notion_db = st.text_input(
            "Notion Database ID", 
            value=get_config().notion.database_id or "",
            help="Optional: Target database for exports"
        )
        
        # Processing Options
        st.markdown("### Processing Options")
        use_cache = st.checkbox("Enable Content Caching", value=True)
        stream_responses = st.checkbox("Stream AI Responses", value=True)
        export_to_notion = st.checkbox("Auto-export to Notion", value=bool(notion_key and notion_db))
        
        # Apply configuration
        if st.button("Apply Configuration", type="primary"):
            config = get_config()
            
            # Update API keys
            config.openai.api_key = openai_key
            config.anthropic.api_key = anthropic_key  
            config.grok.api_key = grok_key
            config.notion.api_key = notion_key
            config.notion.database_id = notion_db
            
            # Update settings
            config.stream_responses = stream_responses
            
            set_config(config)
            
            # Validate configuration
            if config.validate():
                try:
                    # Initialize pipeline
                    st.session_state.pipeline = ContentPipeline(
                        ai_provider=provider,
                        use_cache=use_cache,
                        export_to_notion=export_to_notion
                    )
                    st.session_state.config_valid = True
                    st.success("✅ Configuration applied successfully!")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error initializing pipeline: {e}")
            else:
                st.error("❌ Configuration validation failed. Check your API keys.")
    
    # Pipeline status
    if st.session_state.pipeline:
        st.sidebar.markdown("### 🔗 Connection Status")
        if st.sidebar.button("Test Connections"):
            with st.spinner("Testing connections..."):
                results = st.session_state.pipeline.test_connections()
                
                for service, status in results.items():
                    if status is True:
                        st.sidebar.success(f"✅ {service.title()}")
                    elif status is False:
                        st.sidebar.error(f"❌ {service.title()}")
                    else:
                        st.sidebar.info(f"➖ {service.title()} (not configured)")
    
    # Cache management
    if st.session_state.pipeline and st.session_state.pipeline.cache:
        st.sidebar.markdown("### 💾 Cache Management")
        cache_stats = st.session_state.pipeline.get_cache_stats()
        st.sidebar.write(f"Files: {cache_stats['files']}")
        st.sidebar.write(f"Size: {cache_stats['total_size_mb']} MB")
        
        if st.sidebar.button("Clear Cache"):
            st.session_state.pipeline.clear_cache()
            st.sidebar.success("Cache cleared!")


def show_main_interface():
    """Display the main application interface"""
    if not st.session_state.config_valid or not st.session_state.pipeline:
        st.warning("⚠️ Please configure the application in the sidebar first.")
        return
    
    st.title("⚡ WhisperForge v2.0")
    st.markdown("Transform audio into comprehensive content with AI")
    
    # Input method selection
    input_method = st.radio(
        "Choose Input Method",
        ["🎙️ Upload Audio File", "📝 Enter Text Directly"],
        horizontal=True
    )
    
    if input_method == "🎙️ Upload Audio File":
        show_audio_interface()
    else:
        show_text_interface()
    
    # Show results if available
    if st.session_state.results:
        show_results()


def show_audio_interface():
    """Interface for audio file processing"""
    st.markdown("### 🎙️ Audio Processing")
    
    # File upload
    uploaded_file = st.file_uploader(
        "Upload Audio File",
        type=['mp3', 'wav', 'ogg', 'm4a', 'mp4'],
        help="Supported formats: MP3, WAV, OGG, M4A, MP4"
    )
    
    if uploaded_file is not None:
        # Show file info
        file_size_mb = len(uploaded_file.getvalue()) / (1024 * 1024)
        st.info(f"📁 File: {uploaded_file.name} ({file_size_mb:.2f} MB)")
        
        # Processing options
        col1, col2 = st.columns(2)
        
        with col1:
            generate_all = st.checkbox("Generate All Content Types", value=True)
        
        with col2:
            if not generate_all:
                available_types = st.session_state.pipeline.get_supported_content_types()
                selected_types = st.multiselect(
                    "Select Content Types",
                    available_types,
                    default=["wisdom", "outline"]
                )
            else:
                selected_types = None
        
        # Process button
        if st.button("🚀 Process Audio", type="primary", use_container_width=True):
            process_audio_file(uploaded_file, generate_all, selected_types)


def show_text_interface():
    """Interface for text processing"""
    st.markdown("### 📝 Text Processing")
    
    # Text input
    text_input = st.text_area(
        "Enter your text content",
        height=200,
        placeholder="Paste your transcript or any text content here..."
    )
    
    if text_input.strip():
        # Processing options
        available_types = st.session_state.pipeline.get_supported_content_types()
        selected_types = st.multiselect(
            "Select Content Types to Generate",
            available_types,
            default=["wisdom", "outline", "social"]
        )
        
        # Process button
        if st.button("🚀 Process Text", type="primary", use_container_width=True):
            if selected_types:
                process_text_input(text_input, selected_types)
            else:
                st.warning("Please select at least one content type.")


def process_audio_file(uploaded_file, generate_all: bool, selected_types: list):
    """Process uploaded audio file"""
    
    # Save uploaded file to temporary location
    with tempfile.NamedTemporaryFile(delete=False, suffix=Path(uploaded_file.name).suffix) as tmp_file:
        tmp_file.write(uploaded_file.getvalue())
        audio_path = Path(tmp_file.name)
    
    try:
        # Progress tracking
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        def progress_callback(progress: float, message: str):
            progress_bar.progress(progress)
            status_text.text(message)
        
        # Stream output container
        stream_container = st.empty()
        
        def stream_callback(chunk: str, full_content: str):
            if get_config().stream_responses:
                stream_container.markdown(f"**Generating...**\n\n{full_content}")
        
        # Process the file
        with st.spinner("Processing audio file..."):
            results = st.session_state.pipeline.process_audio_file(
                audio_path=audio_path,
                generate_all_content=generate_all,
                content_types=selected_types,
                progress_callback=progress_callback,
                stream_callback=stream_callback
            )
        
        # Clear progress indicators
        progress_bar.empty()
        status_text.empty()
        stream_container.empty()
        
        # Store results
        st.session_state.results = results
        
        # Show success message
        success_msg = "✅ Processing complete!"
        if results.notion_page_id:
            success_msg += f" [Exported to Notion]({results.notion_page_id})"
        
        st.success(success_msg)
        
    except Exception as e:
        st.error(f"❌ Error processing audio: {e}")
        logger.exception("Audio processing error")
    
    finally:
        # Clean up temporary file
        try:
            audio_path.unlink()
        except:
            pass


def process_text_input(text_input: str, selected_types: list):
    """Process text input"""
    
    try:
        # Progress tracking
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        def progress_callback(progress: float, message: str):
            progress_bar.progress(progress)
            status_text.text(message)
        
        # Stream output container
        stream_container = st.empty()
        
        def stream_callback(chunk: str, full_content: str):
            if get_config().stream_responses:
                stream_container.markdown(f"**Generating...**\n\n{full_content}")
        
        # Process the text
        with st.spinner("Processing text..."):
            results = st.session_state.pipeline.process_text_input(
                text=text_input,
                content_types=selected_types,
                progress_callback=progress_callback,
                stream_callback=stream_callback
            )
        
        # Clear progress indicators
        progress_bar.empty()
        status_text.empty()
        stream_container.empty()
        
        # Store results
        st.session_state.results = results
        
        # Show success message
        success_msg = "✅ Processing complete!"
        if results.notion_page_id:
            success_msg += f" [Exported to Notion]({results.notion_page_id})"
        
        st.success(success_msg)
        
    except Exception as e:
        st.error(f"❌ Error processing text: {e}")
        logger.exception("Text processing error")


def show_results():
    """Display processing results"""
    results = st.session_state.results
    
    st.markdown("---")
    st.markdown("## 📋 Results")
    
    # Metadata
    with st.expander("📊 Processing Info", expanded=False):
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Processing Date:**", results.created_at.strftime("%Y-%m-%d %H:%M:%S"))
            st.write("**Content Types:**", len(results.content))
            
        with col2:
            if results.metadata:
                st.write("**AI Provider:**", results.metadata.get("ai_provider", "Unknown"))
                st.write("**Pipeline Version:**", results.metadata.get("pipeline_version", "Unknown"))
        
        if results.notion_page_id:
            st.success(f"✅ Exported to Notion: {results.notion_page_id}")
    
    # Transcript
    if results.transcript:
        with st.expander("📝 Transcript", expanded=False):
            st.markdown(results.transcript)
    
    # Generated Content
    for content_type, content in results.content.items():
        if content:
            icon_map = {
                "wisdom": "💡",
                "outline": "📋", 
                "social": "📱",
                "image_prompts": "🎨",
                "article": "📄"
            }
            
            icon = icon_map.get(content_type, "📄")
            
            with st.expander(f"{icon} {content_type.title()}", expanded=content_type == "wisdom"):
                st.markdown(content)
    
    # Action buttons
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔄 Process Again"):
            st.session_state.results = None
            st.rerun()
    
    with col2:
        if st.button("💾 Save Results") and results:
            # Simple download as JSON
            import json
            result_data = results.to_dict()
            st.download_button(
                label="📥 Download JSON",
                data=json.dumps(result_data, indent=2),
                file_name=f"whisperforge_results_{results.created_at.strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )
    
    with col3:
        if st.button("🗑️ Clear Results"):
            st.session_state.results = None
            st.rerun()


def show_footer():
    """Display footer information"""
    st.markdown("---")
    st.markdown(
        "<div style='text-align: center; color: #666;'>"
        "🔥 WhisperForge v2.0 - Built with modern modular architecture<br>"
        "Transform your audio into comprehensive content with AI"
        "</div>",
        unsafe_allow_html=True
    )


def main():
    """Main application entry point"""
    
    # Initialize session state
    init_session_state()
    
    # Configure sidebar
    configure_app()
    
    # Show main interface
    show_main_interface()
    
    # Show footer
    show_footer()


if __name__ == "__main__":
    main() 