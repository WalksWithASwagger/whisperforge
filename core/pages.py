"""
Application Pages
=================

Secondary page functions for settings, knowledge base, and prompt management.
"""

import os

import streamlit as st
from postgrest.exceptions import APIError

from .content_display import create_enhanced_aurora_content_card
from .exceptions import APIClientError, DatabaseError, FileProcessingError
from .supabase_integration import get_supabase_client
from .utils import safe_path


def show_settings_page():
    """Settings and configuration page."""
    st.markdown("### Settings & Configuration")

    st.markdown("#### AI Provider")
    with st.expander("AI Provider Selection", expanded=True):
        provider_options = {"OpenAI": "openai", "Anthropic": "anthropic", "Grok (xAI)": "grok"}
        current_provider = st.session_state.get("ai_provider", "openai")
        # Find display name for current provider
        current_label = next((label for label, val in provider_options.items() if val == current_provider), "OpenAI")
        selected_label = st.selectbox(
            "Active AI Provider",
            list(provider_options.keys()),
            index=list(provider_options.keys()).index(current_label),
            help="Select the AI provider for content generation (wisdom, outline, article, social posts).",
        )
        st.session_state.ai_provider = provider_options[selected_label]

        st.info(
            "Whisper transcription always requires an OpenAI API key, regardless of which "
            "AI provider is selected for content generation."
        )

    st.markdown("#### API Keys & Models")
    with st.expander("API Configuration", expanded=True):
        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown("**OpenAI**")
            openai_key = st.text_input(
                "OpenAI API Key", type="password", value=os.getenv("OPENAI_API_KEY", ""), help="Your OpenAI API key"
            )
            if openai_key:
                os.environ["OPENAI_API_KEY"] = openai_key
                st.success("OpenAI key configured")

            openai_model = st.selectbox(
                "OpenAI Model",
                ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo"],
                help="Model used when OpenAI is the active provider.",
            )
            st.session_state.openai_model = openai_model

        with col2:
            st.markdown("**Anthropic**")
            anthropic_key = st.text_input(
                "Anthropic API Key",
                type="password",
                value=os.getenv("ANTHROPIC_API_KEY", ""),
                help="Your Anthropic API key",
            )
            if anthropic_key:
                os.environ["ANTHROPIC_API_KEY"] = anthropic_key
                st.success("Anthropic key configured")

            anthropic_model = st.selectbox(
                "Anthropic Model",
                ["claude-sonnet-4-20250514", "claude-haiku-4-20250514", "claude-3-5-sonnet-20241022"],
                help="Model used when Anthropic is the active provider.",
            )
            st.session_state.anthropic_model = anthropic_model

        with col3:
            st.markdown("**Grok (xAI)**")
            grok_key = st.text_input(
                "Grok API Key",
                type="password",
                value=os.getenv("GROK_API_KEY", ""),
                help="Your xAI / Grok API key",
            )
            if grok_key:
                os.environ["GROK_API_KEY"] = grok_key
                st.success("Grok key configured")

            grok_model = st.selectbox(
                "Grok Model",
                ["grok-3", "grok-3-mini", "grok-2"],
                help="Model used when Grok is the active provider.",
            )
            st.session_state.grok_model = grok_model

    st.markdown("#### Notion Integration")
    with st.expander("Notion Configuration", expanded=False):
        notion_key = st.text_input(
            "Notion API Key",
            type="password",
            value=os.getenv("NOTION_API_KEY", ""),
            help="Your Notion integration token",
        )
        if notion_key:
            os.environ["NOTION_API_KEY"] = notion_key

        notion_db = st.text_input("Notion Database ID", value=os.getenv("NOTION_DATABASE_ID", ""))
        if notion_db:
            os.environ["NOTION_DATABASE_ID"] = notion_db

        if notion_key and notion_db:
            st.success("Notion configured")

    st.markdown("#### Pipeline Configuration")
    with st.expander("Processing Pipeline", expanded=True):
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Core Features**")
            st.session_state.auto_notion = st.checkbox(
                "Auto-publish to Notion", value=st.session_state.get("auto_notion", True)
            )
            st.session_state.live_stream = st.checkbox(
                "Live Streaming", value=st.session_state.get("live_stream", False)
            )
            st.session_state.large_file_mode = st.checkbox(
                "Enhanced Large File Processing", value=st.session_state.get("large_file_mode", True)
            )

        with col2:
            st.markdown("**Quality Settings**")
            st.session_state.content_length = st.selectbox(
                "Article Length", ["Short (500-800 words)", "Medium (800-1200 words)", "Long (1200+ words)"]
            )
            st.session_state.tone_style = st.selectbox(
                "Content Tone", ["Professional", "Conversational", "Academic", "Creative"]
            )

            templates = [f.replace(".md", "") for f in os.listdir("templates")] if os.path.exists("templates") else []
            if templates:
                st.session_state.article_template = st.selectbox("Article Template", templates)
            else:
                st.session_state.article_template = None

    st.markdown("#### System Status")
    with st.expander("Connection Status", expanded=False):
        if st.button("Test All Connections"):
            with st.spinner("Testing all connections..."):
                # AI provider keys
                ai_providers = {
                    "OpenAI": "OPENAI_API_KEY",
                    "Anthropic": "ANTHROPIC_API_KEY",
                    "Grok": "GROK_API_KEY",
                }
                for name, env_var in ai_providers.items():
                    if os.getenv(env_var):
                        st.success(f"{name} API key configured")
                    else:
                        st.warning(f"{name} API key not set")

                try:
                    db = get_supabase_client()
                    if db and db.test_connection():
                        st.success("Supabase connected")
                    else:
                        st.error("Supabase connection failed")
                except APIError as e:
                    st.error(f"Supabase error: {e}")
                except DatabaseError as e:
                    st.error(f"Unexpected Supabase error: {e}")

                try:
                    if os.getenv("NOTION_API_KEY") and os.getenv("NOTION_DATABASE_ID"):
                        from notion_client import Client

                        client = Client(auth=os.getenv("NOTION_API_KEY"))
                        client.databases.retrieve(database_id=os.getenv("NOTION_DATABASE_ID"))
                        st.success("Notion connected")
                    else:
                        st.warning("Notion not configured")
                except OSError as e:
                    st.error(f"Notion error: {e}")
                except APIClientError as e:
                    st.error(f"Unexpected Notion error: {e}")


def show_knowledge_base():
    """Knowledge base management page."""
    st.markdown("### Knowledge Base")

    kb_path = "prompts/default/knowledge_base"

    st.markdown(
        "The knowledge base provides context and expertise to enhance content generation. "
        "Add domain-specific information, style guides, and reference materials here."
    )

    tabs = st.tabs(["View Knowledge", "Add Knowledge", "Manage Files"])

    with tabs[0]:
        st.markdown("#### Current Knowledge Base")
        try:
            if os.path.exists(kb_path):
                files = [f for f in os.listdir(kb_path) if f.endswith(".md")]
                if files:
                    selected_file = st.selectbox("Select knowledge file:", files)
                    if selected_file:
                        file_path = safe_path(kb_path, selected_file)
                        with open(file_path) as f:
                            content = f.read()
                        st.markdown(f"**File:** `{selected_file}`")
                        create_enhanced_aurora_content_card("Knowledge Content", content, "text", "\U0001f4d6")
                else:
                    st.info("No knowledge files found")
            else:
                st.info("Knowledge base directory not found")
        except OSError as e:
            st.error(f"Error reading knowledge base: {e}")
        except FileProcessingError as e:
            st.error(f"Unexpected error reading knowledge base: {e}")

    with tabs[1]:
        st.markdown("#### Add New Knowledge")

        col1, col2 = st.columns([2, 1])
        with col1:
            kb_title = st.text_input("Knowledge Title", placeholder="e.g., 'Marketing Guidelines'")
        with col2:
            kb_category = st.selectbox("Category", ["General", "Style Guide", "Domain Expertise", "Templates"])

        kb_content = st.text_area("Knowledge Content", placeholder="Enter your knowledge content here...", height=300)

        if st.button("Save Knowledge", type="primary"):
            if kb_title and kb_content:
                if len(kb_title) > 100:
                    st.error("Title must be 100 characters or fewer.")
                else:
                    try:
                        os.makedirs(kb_path, exist_ok=True)
                        filename = f"{kb_title.lower().replace(' ', '_')}.md"
                        file_path = safe_path(kb_path, filename)

                        with open(file_path, "w") as f:
                            f.write(f"# {kb_title}\n\n")
                            f.write(f"**Category:** {kb_category}\n\n")
                            f.write(kb_content)

                        st.success(f"Knowledge saved as `{filename}`")
                    except ValueError as e:
                        st.error(f"Invalid filename: {e}")
                    except OSError as e:
                        st.error(f"Error saving knowledge: {e}")
                    except FileProcessingError as e:
                        st.error(f"Unexpected error saving knowledge: {e}")
            else:
                st.error("Please provide both title and content")

    with tabs[2]:
        st.markdown("#### Manage Knowledge Files")
        try:
            if os.path.exists(kb_path):
                files = [f for f in os.listdir(kb_path) if f.endswith(".md")]
                if files:
                    for file in files:
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            st.markdown(f"`{file}`")
                        with col2:
                            if st.button("Delete", key=f"delete_{file}"):
                                try:
                                    validated_path = safe_path(kb_path, file)
                                    os.remove(validated_path)
                                    st.success(f"Deleted `{file}`")
                                    st.rerun()
                                except (ValueError, OSError) as e:
                                    st.error(f"Error deleting file: {e}")
                                except FileProcessingError as e:
                                    st.error(f"Unexpected error deleting file: {e}")
                else:
                    st.info("No knowledge files found")
            else:
                st.info("Knowledge base directory not found")
        except OSError as e:
            st.error(f"Error managing files: {e}")
        except FileProcessingError as e:
            st.error(f"Unexpected error managing files: {e}")


def show_prompts_page():
    """Prompts management page."""
    st.markdown("### Prompt Customization")
    st.markdown("Customize the AI prompts used in each step of the content generation pipeline.")

    prompt_types = {
        "wisdom": "Wisdom Extraction",
        "outline": "Content Outline",
        "article": "Article Generation",
        "social": "Social Media Posts",
    }

    file_mapping = {
        "wisdom": "wisdom_extraction.md",
        "outline": "outline_creation.md",
        "article": "article_generation.md",
        "social": "social_media.md",
    }

    prompt_tabs = st.tabs(list(prompt_types.values()) + ["Advanced"])

    for i, (prompt_key, prompt_name) in enumerate(prompt_types.items()):
        with prompt_tabs[i]:
            st.markdown(f"#### {prompt_name}")

            prompt_file = f"prompts/default/{file_mapping[prompt_key]}"
            current_prompt = ""

            try:
                if os.path.exists(prompt_file):
                    with open(prompt_file) as f:
                        current_prompt = f.read()
                else:
                    current_prompt = f"# {prompt_name} Prompt\n\nDefault prompt for {prompt_key} generation."
            except OSError as e:
                st.error(f"Error loading prompt: {e}")
            except FileProcessingError as e:
                st.error(f"Unexpected error loading prompt: {e}")

            new_prompt = st.text_area(
                f"Edit {prompt_name} Prompt",
                value=current_prompt,
                height=400,
                help=f"Customize the prompt used for {prompt_key} generation",
            )

            col1, col2, col3 = st.columns([1, 1, 2])
            with col1:
                if st.button("Save", key=f"save_{prompt_key}"):
                    try:
                        os.makedirs("prompts/default", exist_ok=True)
                        with open(prompt_file, "w") as f:
                            f.write(new_prompt)
                        st.success(f"{prompt_name} prompt saved!")
                    except OSError as e:
                        st.error(f"Error saving prompt: {e}")
                    except FileProcessingError as e:
                        st.error(f"Unexpected error saving prompt: {e}")

            with col2:
                if st.button("Reset", key=f"reset_{prompt_key}"):
                    st.info("Reset to default functionality coming soon!")

            with col3:
                st.markdown(f"**File:** `{prompt_file}`")

    with prompt_tabs[-1]:
        st.markdown("#### Advanced Prompt Settings")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Global Settings**")
            temperature = st.slider("Temperature (Creativity)", 0.0, 1.0, 0.7, 0.1)
            max_tokens = st.number_input("Max Tokens", 100, 4000, 2000)
        with col2:
            st.markdown("**Prompt Templates**")
            if st.button("Import Prompt Set"):
                st.info("Import functionality coming soon!")
            if st.button("Export Prompt Set"):
                st.info("Export functionality coming soon!")

        st.session_state.temperature = temperature
        st.session_state.max_tokens = max_tokens
