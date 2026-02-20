# WhisperForge Simple - Clean, Focused Audio Content Platform
import os
import time

import streamlit as st
from dotenv import load_dotenv

from core.config import Config
from core.content_display import show_results
from core.file_upload import EnhancedLargeFileProcessor
from core.pages import show_knowledge_base, show_prompts_page, show_settings_page
from core.pipeline import process_pipeline
from core.services import Services, set_services
from core.styling import (
    apply_aurora_theme,
    create_aurora_header,
)
from core.supabase_integration import get_supabase_client

load_dotenv()

# Page config first
st.set_page_config(page_title="WhisperForge", page_icon="\U0001f30c", layout="wide")

# Apply beautiful theme
apply_aurora_theme()


# === SIMPLE AUTHENTICATION ===


def init_session():
    """Initialize simple session state and wire up the DI container."""
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if "user_id" not in st.session_state:
        st.session_state.user_id = None
    if "user_email" not in st.session_state:
        st.session_state.user_email = None

    # Initialise the service container once per process
    if "services_initialised" not in st.session_state:
        set_services(Services(config=Config.from_env()))
        st.session_state.services_initialised = True


def show_login():
    """Simple test login."""
    create_aurora_header()
    st.markdown("### Login to WhisperForge")

    if st.button("Login with Test Account", type="primary", use_container_width=True):
        st.session_state.authenticated = True
        st.session_state.user_id = 1
        st.session_state.user_email = "test@whisperforge.ai"
        st.success("Logged in successfully!")
        time.sleep(1)
        st.rerun()

    st.markdown("---")
    st.markdown("**Demo Mode**: Click above to access WhisperForge")


# === NAVIGATION ===


def create_aurora_navigation():
    """Create Aurora navigation header with 5 tabs and pipeline badges."""
    # Build pipeline badge HTML from session results
    badge_data = [
        ("transcript", "\U0001f399\ufe0f", "Transcript"),
        ("wisdom", "\U0001f4a1", "Wisdom"),
        ("outline", "\U0001f4cb", "Outline"),
        ("article", "\U0001f4f0", "Article"),
        ("social_content", "\U0001f4f1", "Social"),
    ]

    badge_spans = []
    results = st.session_state.get("current_results", {})

    for key, icon, label in badge_data:
        has_content = bool(results.get(key))
        state_class = "badge-complete" if has_content else "badge-pending"

        if has_content:
            word_count = len(str(results[key]).split())
            badge_spans.append(
                '<span class="pipeline-badge '
                + state_class
                + '" title="'
                + str(word_count)
                + ' words">'
                + icon
                + " "
                + label
                + "</span>"
            )
        else:
            badge_spans.append(
                '<span class="pipeline-badge '
                + state_class
                + '" title="No results yet">'
                + icon
                + " "
                + label
                + "</span>"
            )

    badges_html = " ".join(badge_spans)

    header_html = (
        '<div class="aurora-header">'
        '<div class="aurora-glow"></div>'
        '<h1 class="aurora-title">WhisperForge Aurora</h1>'
        '<p class="aurora-subtitle">Transform Audio into Structured Content with AI</p>'
        '<div class="aurora-pipeline">' + badges_html + "</div>"
        "</div>"
    )
    st.markdown(header_html, unsafe_allow_html=True)

    return st.tabs(["Transform", "Content Library", "Settings", "Knowledge Base", "Prompts"])


# === PAGE FUNCTIONS ===


def show_transform_page():
    """Main transformation page: file upload and processing."""
    st.markdown(
        """
    <div class="transform-header">
        <h2 class="transform-title">Transform Audio</h2>
        <p class="transform-subtitle">Upload your audio and watch it transform into structured content</p>
    </div>
    """,
        unsafe_allow_html=True,
    )

    if "upload_method" not in st.session_state:
        st.session_state.upload_method = "Standard Upload"

    # Upload method cards
    sel_std = "selected" if st.session_state.upload_method == "Standard Upload" else ""
    sel_lg = "selected" if st.session_state.upload_method == "Large File Upload" else ""
    st.markdown(
        f"""
    <div class="aurora-upload-method-selector">
        <div class="aurora-upload-method-card {sel_std}">
            <span class="aurora-upload-method-icon">\u26a1</span>
            <h3 class="aurora-upload-method-title">Standard Upload</h3>
            <p class="aurora-upload-method-description">
                Perfect for most audio files up to 25MB with instant processing</p>
            <div class="aurora-upload-method-features">
                <div class="aurora-upload-feature">
                    <span class="aurora-upload-feature-icon">\u26a1</span> Instant processing</div>
                <div class="aurora-upload-feature">
                    <span class="aurora-upload-feature-icon">\U0001f3b5</span> Audio preview</div>
                <div class="aurora-upload-feature">
                    <span class="aurora-upload-feature-icon">\U0001f4be</span> Up to 25MB</div>
            </div>
        </div>
        <div class="aurora-upload-method-card {sel_lg}">
            <span class="aurora-upload-method-icon">\U0001f680</span>
            <h3 class="aurora-upload-method-title">Large File Upload</h3>
            <p class="aurora-upload-method-description">
                Advanced processing for large files up to 2GB with intelligent chunking</p>
            <div class="aurora-upload-method-features">
                <div class="aurora-upload-feature">
                    <span class="aurora-upload-feature-icon">\U0001f527</span> FFmpeg chunking</div>
                <div class="aurora-upload-feature">
                    <span class="aurora-upload-feature-icon">\u26a1</span> Parallel processing</div>
                <div class="aurora-upload-feature">
                    <span class="aurora-upload-feature-icon">\U0001f4be</span> Up to 2GB</div>
            </div>
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )

    upload_method = st.radio(
        "Choose upload method:",
        ["Standard Upload", "Large File Upload"],
        index=0 if st.session_state.upload_method == "Standard Upload" else 1,
        help="Standard upload for smaller files, Enhanced upload for large files with FFmpeg processing",
        label_visibility="collapsed",
    )
    st.session_state.upload_method = upload_method

    if upload_method == "Standard Upload":
        _show_standard_upload()
    else:
        _show_large_file_upload()

    if "current_results" in st.session_state:
        show_results(st.session_state.current_results)


def _show_standard_upload():
    """Handle standard file upload (up to 25MB)."""
    st.markdown(
        """
    <div class="aurora-file-upload-zone">
        <div class="aurora-upload-icon-container">
            <span class="aurora-upload-icon">\U0001f3b5</span>
            <div class="aurora-upload-pulse"></div>
        </div>
        <h3 class="aurora-upload-title">Drop your audio file here</h3>
        <p class="aurora-upload-subtitle">Or click to browse and select a file</p>
        <div class="aurora-upload-formats">
            <span class="aurora-format-badge">MP3</span>
            <span class="aurora-format-badge">WAV</span>
            <span class="aurora-format-badge">M4A</span>
            <span class="aurora-format-badge">FLAC</span>
            <span class="aurora-format-badge">OGG</span>
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )

    uploaded_files = st.file_uploader(
        "Upload your audio file",
        type=["mp3", "wav", "m4a", "flac", "ogg"],
        help="Upload audio file for processing (max 25MB)",
        label_visibility="collapsed",
        accept_multiple_files=True,
    )

    if uploaded_files:
        for uploaded_file in uploaded_files:
            file_size = len(uploaded_file.getvalue()) / (1024 * 1024)

            if file_size < 50:
                st.audio(uploaded_file.getvalue())

            if st.button(
                f"Transform {uploaded_file.name}",
                key=f"process_{uploaded_file.name}",
                type="primary",
                use_container_width=True,
            ):
                if not os.getenv("OPENAI_API_KEY"):
                    st.error("Please enter your OpenAI API key in Settings")
                    return

                with st.container():
                    results = process_pipeline(audio_file=uploaded_file)
                    if results:
                        st.session_state.current_results = results


def _show_large_file_upload():
    """Handle large file upload with FFmpeg chunking."""
    st.markdown("### Enhanced Large File Processing")
    processor = EnhancedLargeFileProcessor()
    uploaded_file = processor.create_enhanced_upload_interface()

    if uploaded_file:
        validation = processor.validate_file(uploaded_file)
        if not validation["valid"]:
            st.error(f"{validation['error']}")
            return

        file_size_mb = validation["size_mb"]

        if file_size_mb < 50:
            st.audio(uploaded_file.getvalue())

        if st.button("Transform Large File to Content", type="primary", use_container_width=True):
            if not os.getenv("OPENAI_API_KEY"):
                st.error("Please enter your OpenAI API key in Settings")
                return

            with st.container():
                processing_result = processor.process_large_file(uploaded_file)

                if processing_result["success"]:
                    transcript = processing_result["transcript"]
                    st.success("Large file processing complete!")
                    st.markdown("---")
                    results = process_pipeline(transcript=transcript)
                    if results:
                        st.session_state.current_results = results
                else:
                    st.error(f"Large file processing failed: {processing_result['error']}")

                    if file_size_mb < 100:
                        st.info("Attempting fallback to standard processing...")
                        try:
                            results = process_pipeline(audio_file=uploaded_file)
                            if results:
                                st.session_state.current_results = results
                        except Exception as e:
                            st.error(f"Fallback processing also failed: {e!s}")


def show_content_library():
    """Content library/history page."""
    st.markdown("### Content Library")

    try:
        db = get_supabase_client()
        if db:
            response = db.client.table("content").select("*").order("created_at", desc=True).limit(20).execute()

            if response.data:
                st.success(f"Found {len(response.data)} content items")

                col1, col2 = st.columns([3, 1])
                with col1:
                    search_term = st.text_input("Search content", placeholder="Search by title or content...")
                with col2:
                    st.selectbox("Filter by type", ["All", "Article", "Social", "Outline"])

                cols = st.columns(2)
                for idx, item in enumerate(response.data):
                    if search_term and search_term.lower() not in item.get("title", "").lower():
                        continue

                    with cols[idx % 2].expander(f"{item.get('title', 'Untitled')} - {item.get('created_at', '')[:10]}"):
                        if item.get("transcript"):
                            st.markdown("**Transcript Preview:**")
                            preview = item["transcript"][:200]
                            st.text(preview + "..." if len(item["transcript"]) > 200 else preview)

                        if item.get("wisdom"):
                            st.markdown("**Wisdom:**")
                            st.text_area("", item["wisdom"], height=100, disabled=True, key=f"wisdom_{item.get('id')}")

                        if item.get("article"):
                            st.markdown("**Article:**")
                            st.text_area(
                                "", item["article"], height=150, disabled=True, key=f"article_{item.get('id')}"
                            )
            else:
                st.info("No content found. Process some audio files to see them here!")
        else:
            st.error("Database connection failed")
    except Exception as e:
        st.error(f"Error loading content library: {e}")


# === MAIN APP ===


def show_main_app():
    """Main application interface with navigation."""
    tabs = create_aurora_navigation()

    with tabs[0]:
        show_transform_page()
    with tabs[1]:
        show_content_library()
    with tabs[2]:
        show_settings_page()
    with tabs[3]:
        show_knowledge_base()
    with tabs[4]:
        show_prompts_page()


def main():
    """Application entry point."""
    init_session()

    if st.session_state.authenticated:
        show_main_app()
    else:
        show_login()


if __name__ == "__main__":
    main()
