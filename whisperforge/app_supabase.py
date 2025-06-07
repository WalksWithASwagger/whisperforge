# WhisperForge - Supabase Version
# Main application with Supabase integration

import streamlit as st

# Page config MUST be first
st.set_page_config(
    page_title="WhisperForge - Supabase",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

import os
import json
import tempfile
import logging
from datetime import datetime
from pathlib import Path

# Load environment variables first
from dotenv import load_dotenv
load_dotenv()

# Import Supabase integration
from core.supabase_integration import get_supabase_client, get_mcp_integration

# Import OAuth handler
from core.oauth_handler import GoogleOAuthHandler, create_google_signin_button, handle_oauth_redirect

# Import utility functions (avoiding app.py imports)
from core.utils import hash_password, DEFAULT_PROMPTS, get_prompt
from core.content_generation import (
    transcribe_audio, generate_wisdom, generate_outline, 
    generate_social_content, generate_image_prompts
)
from core.styling import local_css, add_production_css, create_custom_header, load_js

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_content_pipeline(transcript, provider, model, knowledge_base=None):
    """Run the complete content generation pipeline"""
    try:
        # Step 1: Generate wisdom
        wisdom = generate_wisdom(transcript, provider, model, None, knowledge_base)
        
        # Step 2: Generate outline 
        outline = generate_outline(transcript, wisdom, provider, model, None, knowledge_base)
        
        # Step 3: Generate social content
        social = generate_social_content(wisdom, outline, provider, model, None, knowledge_base)
        
        # Step 4: Generate image prompts
        images = generate_image_prompts(wisdom, outline, provider, model, None, knowledge_base)
        
        return {
            "wisdom_extraction": wisdom,
            "outline_creation": outline, 
            "social_media": social,
            "image_prompts": images
        }
    except Exception as e:
        logger.error(f"Pipeline error: {e}")
        return {
            "wisdom_extraction": f"Error: {str(e)}",
            "outline_creation": f"Error: {str(e)}",
            "social_media": f"Error: {str(e)}",
            "image_prompts": f"Error: {str(e)}"
        }

# Initialize Supabase client
@st.cache_resource
def init_supabase():
    """Initialize Supabase client"""
    try:
        db = get_supabase_client()
        mcp = get_mcp_integration()
        return db, mcp
    except Exception as e:
        st.error(f"Failed to connect to Supabase: {e}")
        return None, None

# Initialize OAuth handler
@st.cache_resource
def init_oauth_handler():
    """Initialize OAuth handler"""
    try:
        db, _ = init_supabase()
        if db:
            return GoogleOAuthHandler(db.client)
        return None
    except Exception as e:
        st.error(f"Failed to initialize OAuth handler: {e}")
        return None

# Database operations using Supabase
def authenticate_user_supabase(email: str, password: str) -> bool:
    """Authenticate user using Supabase"""
    try:
        db, _ = init_supabase()
        if not db:
            logger.error("Failed to initialize Supabase client")
            return False
            
        hashed_password = hash_password(password)
        logger.info(f"Attempting to authenticate user: {email}")
        
        result = db.client.table("users").select("id, email").eq("email", email).eq("password", hashed_password).execute()
        
        if result.data:
            st.session_state.user_id = result.data[0]["id"]
            st.session_state.authenticated = True
            logger.info(f"User authenticated successfully: {email}")
            return True
        else:
            logger.warning(f"Authentication failed for user: {email}")
            return False
    except Exception as e:
        logger.error(f"Authentication error: {e}")
        return False

def register_user_supabase(email: str, password: str) -> bool:
    """Register new user using Supabase"""
    try:
        db, _ = init_supabase()
        if not db:
            logger.error("Failed to initialize Supabase client")
            return False
        
        # Check if user already exists
        existing = db.client.table("users").select("id").eq("email", email).execute()
        if existing.data:
            logger.warning(f"User already exists: {email}")
            return False
            
        logger.info(f"Attempting to create new user: {email}")
        user = db.create_user(email, password)
        
        if user:
            logger.info(f"User created successfully: {email}")
            return True
        else:
            logger.error(f"Failed to create user: {email}")
            return False
    except Exception as e:
        logger.error(f"Registration error: {e}")
        return False

def get_user_api_keys_supabase() -> dict:
    """Get user API keys from Supabase"""
    try:
        if not st.session_state.get("authenticated"):
            return {}
            
        db, _ = init_supabase()
        if not db:
            return {}
            
        return db.get_user_api_keys(st.session_state.user_id)
    except Exception as e:
        logger.error(f"Error getting API keys: {e}")
        return {}

def update_api_key_supabase(key_name: str, key_value: str) -> bool:
    """Update user API key in Supabase"""
    try:
        if not st.session_state.get("authenticated"):
            return False
            
        db, _ = init_supabase()
        if not db:
            return False
            
        current_keys = db.get_user_api_keys(st.session_state.user_id)
        
        if key_value:
            current_keys[key_name] = key_value
        else:
            current_keys.pop(key_name, None)
            
        return db.save_user_api_keys(st.session_state.user_id, current_keys)
    except Exception as e:
        logger.error(f"Error updating API key: {e}")
        return False

def get_user_prompts_supabase() -> dict:
    """Get user custom prompts from Supabase"""
    try:
        if not st.session_state.get("authenticated"):
            return DEFAULT_PROMPTS
            
        db, _ = init_supabase()
        if not db:
            return DEFAULT_PROMPTS
            
        custom_prompts = db.get_user_prompts(st.session_state.user_id)
        
        # Merge with defaults
        prompts = DEFAULT_PROMPTS.copy()
        prompts.update(custom_prompts)
        return prompts
    except Exception as e:
        logger.error(f"Error getting prompts: {e}")
        return DEFAULT_PROMPTS

def save_user_prompt_supabase(prompt_type: str, content: str) -> bool:
    """Save user custom prompt to Supabase"""
    try:
        if not st.session_state.get("authenticated"):
            return False
            
        db, _ = init_supabase()
        if not db:
            return False
            
        return db.save_custom_prompt(st.session_state.user_id, prompt_type, content)
    except Exception as e:
        logger.error(f"Error saving prompt: {e}")
        return False

def get_user_knowledge_base_supabase() -> dict:
    """Get user knowledge base from Supabase"""
    try:
        if not st.session_state.get("authenticated"):
            return {}
            
        db, _ = init_supabase()
        if not db:
            return {}
            
        return db.get_user_knowledge_base(st.session_state.user_id)
    except Exception as e:
        logger.error(f"Error getting knowledge base: {e}")
        return {}

def save_knowledge_base_file_supabase(filename: str, content: str) -> bool:
    """Save knowledge base file to Supabase"""
    try:
        if not st.session_state.get("authenticated"):
            return False
            
        db, _ = init_supabase()
        if not db:
            return False
            
        return db.save_knowledge_base_file(st.session_state.user_id, filename, content)
    except Exception as e:
        logger.error(f"Error saving knowledge base file: {e}")
        return False

def save_generated_content_supabase(content_data: dict) -> str:
    """Save generated content to Supabase"""
    try:
        if not st.session_state.get("authenticated"):
            return None
            
        db, _ = init_supabase()
        if not db:
            return None
            
        return db.save_content(st.session_state.user_id, content_data)
    except Exception as e:
        logger.error(f"Error saving content: {e}")
        return None

def get_user_content_history_supabase(limit: int = 20) -> list:
    """Get user content history from Supabase"""
    try:
        if not st.session_state.get("authenticated"):
            return []
            
        db, _ = init_supabase()
        if not db:
            return []
            
        return db.get_user_content(st.session_state.user_id, limit)
    except Exception as e:
        logger.error(f"Error getting content history: {e}")
        return []

def log_pipeline_execution_supabase(pipeline_data: dict) -> bool:
    """Log pipeline execution to Supabase"""
    try:
        if not st.session_state.get("authenticated"):
            return False
            
        db, _ = init_supabase()
        if not db:
            return False
            
        return db.log_pipeline_execution(st.session_state.user_id, pipeline_data)
    except Exception as e:
        logger.error(f"Error logging pipeline execution: {e}")
        return False

# Authentication UI
def show_auth_page():
    """Show authentication page"""
    st.title("🔐 WhisperForge - Sign In")
    
    # Handle OAuth callback first
    if handle_oauth_redirect():
        oauth_handler = init_oauth_handler()
        if oauth_handler and st.session_state.get('oauth_params'):
            user_data = oauth_handler.handle_oauth_callback(st.session_state.oauth_params)
            if user_data:
                user_id = oauth_handler.get_or_create_user(user_data)
                if user_id:
                    st.session_state.user_id = user_id
                    st.session_state.authenticated = True
                    st.session_state.auth_provider = 'google'
                    st.success("✅ Signed in with Google successfully!")
                    st.rerun()
                else:
                    st.error("Failed to create/update user account")
            else:
                st.error("Failed to authenticate with Google")
    
    # Google OAuth Sign-In Section
    st.markdown("### 🚀 Quick Sign-In")
    
    oauth_handler = init_oauth_handler()
    if oauth_handler:
        try:
            oauth_url = oauth_handler.generate_oauth_url()
            
            # Create custom Google sign-in button
            google_button_html = f"""
            <style>
            .google-signin-btn {{
                display: inline-flex;
                align-items: center;
                justify-content: center;
                background-color: #4285f4;
                color: white;
                padding: 12px 24px;
                border-radius: 8px;
                text-decoration: none;
                font-family: 'Roboto', sans-serif;
                font-size: 16px;
                font-weight: 500;
                border: none;
                cursor: pointer;
                transition: background-color 0.3s ease;
                margin: 10px 0;
                min-width: 250px;
                text-align: center;
            }}
            
            .google-signin-btn:hover {{
                background-color: #3367d6;
                text-decoration: none;
                color: white;
            }}
            
            .google-icon {{
                background-color: white;
                border-radius: 4px;
                padding: 8px;
                margin-right: 12px;
                display: flex;
                align-items: center;
                justify-content: center;
            }}
            </style>
            
            <a href="{oauth_url}" class="google-signin-btn" target="_self">
                <div class="google-icon">
                    <svg width="20" height="20" viewBox="0 0 24 24">
                        <path fill="#4285f4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                        <path fill="#34a853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                        <path fill="#fbbc05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                        <path fill="#ea4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
                    </svg>
                </div>
                Sign in with Google
            </a>
            """
            
            st.markdown(google_button_html, unsafe_allow_html=True)
            
        except Exception as e:
            st.error(f"Google OAuth not available: {e}")
    
    st.markdown("---")
    st.markdown("### 📧 Or sign in with email")
    
    tab1, tab2 = st.tabs(["Sign In", "Register"])
    
    with tab1:
        st.subheader("Sign In")
        email = st.text_input("Email", key="signin_email")
        password = st.text_input("Password", type="password", key="signin_password")
        
        if st.button("Sign In"):
            if not email or not password:
                st.error("Please enter both email and password")
            elif authenticate_user_supabase(email, password):
                st.success("Signed in successfully!")
                st.rerun()
            else:
                st.error("Invalid email or password. Please check your credentials and try again.")
    
    with tab2:
        st.subheader("Create Account")
        email = st.text_input("Email", key="register_email")
        password = st.text_input("Password", type="password", key="register_password")
        password_confirm = st.text_input("Confirm Password", type="password", key="register_password_confirm")
        
        if st.button("Create Account"):
            if not email or not password:
                st.error("Please enter both email and password")
            elif len(password) < 6:
                st.error("Password must be at least 6 characters")
            elif password != password_confirm:
                st.error("Passwords don't match")
            elif register_user_supabase(email, password):
                st.success("Account created successfully! Please sign in with your new credentials.")
                # Clear the form fields
                st.session_state.register_email = ""
                st.session_state.register_password = ""
                st.session_state.register_password_confirm = ""
            else:
                st.error("Error creating account. Email may already exist or there was a database error.")

# Main application
def show_main_app():
    """Show main application"""
    
    # Apply styling
    local_css()
    add_production_css()
    load_js()
    create_custom_header()
    
    # Initialize session state
    if 'transcription' not in st.session_state:
        st.session_state.transcription = ""
    if 'wisdom' not in st.session_state:
        st.session_state.wisdom = ""
    if 'ai_provider' not in st.session_state:
        st.session_state.ai_provider = "Anthropic"
    if 'ai_model' not in st.session_state:
        st.session_state.ai_model = "claude-3-7-sonnet-20250219"
    
    # Load user data
    st.session_state.prompts = get_user_prompts_supabase()
    st.session_state.knowledge_base = get_user_knowledge_base_supabase()
    
    # Sidebar
    with st.sidebar:
        st.markdown("### 👤 Account")
        db, _ = init_supabase()
        if db:
            user = db.get_user(st.session_state.user_id)
            if user:
                st.write(f"**Email:** {user.get('email', 'Unknown')}")
                st.write(f"**Plan:** {user.get('subscription_tier', 'free').title()}")
                
                usage_current = user.get('usage_current', 0)
                usage_quota = user.get('usage_quota', 60)
                usage_percent = min(100, (usage_current / usage_quota) * 100) if usage_quota > 0 else 0
                
                st.progress(usage_percent / 100)
                st.write(f"Usage: {usage_current:.1f} / {usage_quota} minutes")
        
        if st.button("Sign Out"):
            st.session_state.authenticated = False
            st.session_state.user_id = None
            st.rerun()
        
        st.markdown("---")
        
        # Navigation
        st.markdown("### 📋 Navigation")
        page = st.selectbox("Go to", ["Home", "Content History", "Settings"], key="nav_select")
        
        if page != st.session_state.get("current_page", "Home"):
            st.session_state.current_page = page
            st.rerun()
    
    # Main content area
    current_page = st.session_state.get("current_page", "Home")
    
    if current_page == "Home":
        show_home_page()
    elif current_page == "Content History":
        show_content_history_page()
    elif current_page == "Settings":
        show_settings_page()

def show_home_page():
    """Show main content generation page"""
    st.title("⚡ WhisperForge Content Pipeline")
    
    # Audio upload
    uploaded_file = st.file_uploader(
        "Upload Audio File",
        type=['mp3', 'wav', 'm4a', 'flac', 'mp4', 'mov', 'avi'],
        help="Upload an audio file to transcribe and generate content"
    )
    
    if uploaded_file:
        st.session_state.audio_file = uploaded_file
        
        # Provider selection
        col1, col2 = st.columns(2)
        with col1:
            st.session_state.ai_provider = st.selectbox(
                "AI Provider",
                ["Anthropic", "OpenAI", "Grok"],
                index=["Anthropic", "OpenAI", "Grok"].index(st.session_state.ai_provider)
            )
        
        with col2:
            models = {
                "Anthropic": ["claude-3-7-sonnet-20250219", "claude-3-sonnet-20240229"],
                "OpenAI": ["gpt-4", "gpt-3.5-turbo"],
                "Grok": ["grok-2-2024-08-13", "grok-2-mini-2024-08-13"]
            }
            st.session_state.ai_model = st.selectbox(
                "Model",
                models[st.session_state.ai_provider],
                index=0
            )
        
        # Process button
        if st.button("🚀 Start Processing", type="primary"):
            process_audio_pipeline(uploaded_file)

def process_audio_pipeline(audio_file):
    """Process audio through the complete pipeline"""
    
    # Track pipeline execution
    pipeline_start = datetime.now()
    pipeline_data = {
        "type": "full",
        "ai_provider": st.session_state.ai_provider.lower(),
        "model": st.session_state.ai_model,
        "success": False,
        "metadata": {"filename": audio_file.name}
    }
    
    try:
        # Step 1: Transcription
        with st.spinner("🎤 Transcribing audio..."):
            transcript = transcribe_audio(audio_file)
            st.session_state.transcription = transcript
        
        if not transcript:
            st.error("Failed to transcribe audio")
            return
        
        st.success("✅ Transcription complete!")
        with st.expander("📄 View Transcript"):
            st.text_area("Transcript", transcript, height=200)
        
        # Step 2: Generate all content using the pipeline
        with st.spinner("🤖 Generating content..."):
            generated_content = run_content_pipeline(
                transcript, 
                st.session_state.ai_provider, 
                st.session_state.ai_model, 
                st.session_state.knowledge_base
            )
        
        st.success("✅ Content generation complete!")
        
        # Display generated content
        for content_type, content in generated_content.items():
            with st.expander(f"📝 {content_type.replace('_', ' ').title()}"):
                st.markdown(content)
        
        # Save content to Supabase
        content_data = {
            "title": f"Content from {audio_file.name}",
            "transcript": transcript,
            **generated_content,
            "metadata": {
                "ai_provider": st.session_state.ai_provider,
                "ai_model": st.session_state.ai_model,
                "file_size": audio_file.size,
                "created_at": datetime.now().isoformat()
            }
        }
        
        content_id = save_generated_content_supabase(content_data)
        if content_id:
            st.success(f"✅ Content saved with ID: {content_id}")
        
        # Log successful pipeline execution
        pipeline_end = datetime.now()
        pipeline_data.update({
            "success": True,
            "duration": (pipeline_end - pipeline_start).total_seconds(),
            "content_id": content_id
        })
        
    except Exception as e:
        st.error(f"❌ Pipeline error: {e}")
        pipeline_data["error"] = str(e)
        logger.exception("Pipeline error")
    
    finally:
        # Log pipeline execution
        log_pipeline_execution_supabase(pipeline_data)

def show_content_history_page():
    """Show content history page"""
    st.title("📚 Content History")
    
    content_history = get_user_content_history_supabase(50)
    
    if not content_history:
        st.info("No content history found. Generate some content to see it here!")
        return
    
    # Display content history
    for content in content_history:
        with st.expander(f"📄 {content.get('title', 'Untitled')} - {content.get('created_at', '')[:10]}"):
            
            col1, col2 = st.columns([3, 1])
            with col1:
                if content.get('transcript'):
                    st.subheader("Transcript")
                    st.text_area("", content['transcript'], height=100, key=f"transcript_{content['id']}")
                
                if content.get('wisdom'):
                    st.subheader("Wisdom")
                    st.markdown(content['wisdom'])
                
                if content.get('outline'):
                    st.subheader("Outline")
                    st.markdown(content['outline'])
            
            with col2:
                st.json(content.get('metadata', {}))

def show_settings_page():
    """Show settings page"""
    st.title("⚙️ Settings")
    
    tab1, tab2, tab3 = st.tabs(["API Keys", "Custom Prompts", "Knowledge Base"])
    
    with tab1:
        st.subheader("API Keys")
        api_keys = get_user_api_keys_supabase()
        
        # OpenAI
        openai_key = st.text_input(
            "OpenAI API Key",
            value=api_keys.get("openai_api_key", ""),
            type="password"
        )
        if st.button("Save OpenAI Key"):
            if update_api_key_supabase("openai_api_key", openai_key):
                st.success("OpenAI key saved!")
        
        # Anthropic
        anthropic_key = st.text_input(
            "Anthropic API Key",
            value=api_keys.get("anthropic_api_key", ""),
            type="password"
        )
        if st.button("Save Anthropic Key"):
            if update_api_key_supabase("anthropic_api_key", anthropic_key):
                st.success("Anthropic key saved!")
        
        # Notion
        notion_key = st.text_input(
            "Notion API Key",
            value=api_keys.get("notion_api_key", ""),
            type="password"
        )
        notion_db = st.text_input(
            "Notion Database ID",
            value=api_keys.get("notion_database_id", "")
        )
        if st.button("Save Notion Keys"):
            success = True
            if notion_key:
                success &= update_api_key_supabase("notion_api_key", notion_key)
            if notion_db:
                success &= update_api_key_supabase("notion_database_id", notion_db)
            if success:
                st.success("Notion keys saved!")
    
    with tab2:
        st.subheader("Custom Prompts")
        
        prompt_types = [
            "wisdom_extraction",
            "outline_creation", 
            "social_media",
            "image_prompts"
        ]
        
        for prompt_type in prompt_types:
            st.markdown(f"#### {prompt_type.replace('_', ' ').title()}")
            
            current_prompt = st.session_state.prompts.get(prompt_type, "")
            
            new_prompt = st.text_area(
                f"Prompt for {prompt_type}",
                value=current_prompt,
                height=100,
                key=f"prompt_{prompt_type}"
            )
            
            if st.button(f"Save {prompt_type.replace('_', ' ').title()}", key=f"save_{prompt_type}"):
                if save_user_prompt_supabase(prompt_type, new_prompt):
                    st.success(f"Saved {prompt_type} prompt!")
                    st.session_state.prompts[prompt_type] = new_prompt
    
    with tab3:
        st.subheader("Knowledge Base")
        
        kb = get_user_knowledge_base_supabase()
        
        if kb:
            st.write("**Your knowledge base files:**")
            for name, content in kb.items():
                with st.expander(f"📄 {name}"):
                    st.text_area("Content", content, height=200, key=f"kb_{name}")
        else:
            st.info("No knowledge base files yet.")
        
        # Upload new file
        st.markdown("#### Upload Knowledge Base File")
        uploaded_kb = st.file_uploader("Choose file", type=["txt", "md"])
        
        if uploaded_kb:
            content = uploaded_kb.read().decode("utf-8")
            if st.button("Save Knowledge Base File"):
                if save_knowledge_base_file_supabase(uploaded_kb.name, content):
                    st.success(f"Saved {uploaded_kb.name}!")
                    st.rerun()

# Main app logic
def main():
    """Main application entry point"""
    
    # Initialize session state
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'user_id' not in st.session_state:
        st.session_state.user_id = None
    
    # Check authentication
    if not st.session_state.authenticated:
        show_auth_page()
    else:
        show_main_app()

if __name__ == "__main__":
    main() 