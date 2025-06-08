# WhisperForge - Main Application
# Streamlit app with Supabase integration

import streamlit as st

# Page config MUST be first
st.set_page_config(
    page_title="WhisperForge",
    page_icon="🌌",
    layout="wide",
    initial_sidebar_state="expanded"
)

import os
import json
import time
import tempfile
import logging
from datetime import datetime
from pathlib import Path

# Load environment variables first
from dotenv import load_dotenv
load_dotenv()

# Import Supabase integration
from core.supabase_integration import get_supabase_client, get_mcp_integration

# Import utility functions (avoiding app.py imports)
from core.utils import hash_password, DEFAULT_PROMPTS, get_prompt
from core.content_generation import (
    transcribe_audio, generate_wisdom, generate_outline, 
    generate_social_content, generate_image_prompts
)
from core.styling import local_css, add_production_css, create_custom_header, load_js
from core.monitoring import (
    init_monitoring, track_error, track_performance, track_user_action, 
    get_health_status, init_session_tracking
)
from core.progress import (
    ProgressTracker, 
    create_whisperforge_progress_tracker,
    WHISPERFORGE_PIPELINE_STEPS
)
from core.file_upload import FileUploadManager
from core.notifications import (
    show_success, show_error, show_warning, show_info,
    create_loading_spinner
)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize monitoring
init_monitoring()

def run_content_pipeline(transcript, provider, model, knowledge_base=None):
    """Run the complete content generation pipeline"""
    with track_performance("content_pipeline", {"provider": provider, "model": model}):
        try:
            track_user_action("pipeline_start", {"provider": provider, "model": model})
            
            # Step 1: Generate wisdom
            with track_performance("generate_wisdom"):
                wisdom = generate_wisdom(transcript, provider, model, None, knowledge_base)
            
            # Step 2: Generate outline 
            with track_performance("generate_outline"):
                outline = generate_outline(transcript, wisdom, provider, model, None, knowledge_base)
            
            # Step 3: Generate social content
            with track_performance("generate_social"):
                social = generate_social_content(wisdom, outline, provider, model, None, knowledge_base)
            
            # Step 4: Generate image prompts
            with track_performance("generate_images"):
                images = generate_image_prompts(wisdom, outline, provider, model, None, knowledge_base)
            
            track_user_action("pipeline_complete", {"provider": provider, "model": model})
            
            return {
                "wisdom_extraction": wisdom,
                "outline_creation": outline, 
                "social_media": social,
                "image_prompts": images
            }
        except Exception as e:
            track_error(e, {"operation": "content_pipeline", "provider": provider, "model": model})
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



# Database operations using Supabase
def authenticate_user_supabase(email: str, password: str) -> bool:
    """Authenticate user using Supabase with migration support"""
    try:
        db, _ = init_supabase()
        if not db:
            logger.error("Failed to initialize Supabase client")
            return False
            
        logger.info(f"Attempting to authenticate user: {email}")
        
        # Get user record to check password format
        result = db.client.table("users").select("id, email, password").eq("email", email).execute()
        
        if not result.data:
            logger.warning(f"User not found: {email}")
            return False
            
        user = result.data[0]
        stored_password = user["password"]
        
        # Check if password is bcrypt (starts with $2b$) or legacy SHA-256
        if stored_password.startswith('$2b$'):
            # New bcrypt password
            from core.utils import verify_password
            if verify_password(password, stored_password):
                st.session_state.user_id = user["id"]
                st.session_state.authenticated = True
                logger.info(f"User authenticated successfully with bcrypt: {email}")
                return True
        else:
            # Legacy SHA-256 password - check and migrate
            from core.utils import legacy_hash_password, hash_password
            legacy_hash = legacy_hash_password(password)
            if legacy_hash == stored_password:
                # Password correct, migrate to bcrypt
                new_hash = hash_password(password)
                db.client.table("users").update({
                    "password": new_hash,
                    "updated_at": "now()"
                }).eq("id", user["id"]).execute()
                
                st.session_state.user_id = user["id"]
                st.session_state.authenticated = True
                logger.info(f"User authenticated and migrated to bcrypt: {email}")
                return True
        
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
def handle_oauth_callback():
    """Handle OAuth callback from Supabase"""
    query_params = st.query_params
    
    # Don't process OAuth callback if user is already authenticated (logout scenario)
    if st.session_state.get('authenticated', False):
        return False
    
    # Check if we have an OAuth callback with code
    if 'code' in query_params:
        try:
            db, _ = init_supabase()
            if db:
                # Exchange the code for a session
                code = query_params['code']
                response = db.client.auth.exchange_code_for_session({"auth_code": code})
                
                if response.user:
                    # Get or create user in our database
                    user_email = response.user.email
                    user_id = response.user.id
                    
                    # Check if user exists in our users table
                    existing_user = db.client.table("users").select("id").eq("email", user_email).execute()
                    
                    if not existing_user.data:
                        # Create new user record
                        new_user = {
                            "email": user_email,
                            "usage_quota": 60,
                            "usage_current": 0,
                            "is_admin": False,
                            "subscription_tier": "free",
                            "created_at": "now()"
                        }
                        result = db.client.table("users").insert(new_user).execute()
                        if result.data:
                            st.session_state.user_id = result.data[0]["id"]
                        else:
                            st.error("Failed to create user record")
                            return False
                    else:
                        st.session_state.user_id = existing_user.data[0]["id"]
                    
                    st.session_state.authenticated = True
                    st.success("✅ Successfully signed in with Google!")
                    st.rerun()
                    return True
                else:
                    st.error("Failed to authenticate with Google")
                    return False
        except Exception as e:
            st.error(f"OAuth callback error: {e}")
            return False
    
    return False

def show_auth_page():
    """Show authentication page with Aurora styling"""
    
    # Aurora authentication page styling
    st.markdown("""
    <style>
    /* Aurora Authentication Page Styling */
    .aurora-auth-container {
        max-width: 500px;
        margin: 0 auto;
        padding: 40px;
        background: linear-gradient(
            135deg,
            rgba(0, 255, 255, 0.05) 0%,
            rgba(64, 224, 208, 0.08) 30%,
            rgba(125, 249, 255, 0.06) 60%,
            rgba(0, 255, 127, 0.04) 100%
        );
        backdrop-filter: blur(32px) saturate(200%);
        border: 1px solid rgba(0, 255, 255, 0.2);
        border-radius: 24px;
        box-shadow: 
            0 0 48px rgba(0, 255, 255, 0.15),
            inset 0 1px 0 rgba(255, 255, 255, 0.1);
        position: relative;
        overflow: hidden;
    }
    
    .aurora-auth-container::before {
        content: "";
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 2px;
        background: linear-gradient(90deg, transparent, #00FFFF, #7DF9FF, #40E0D0, #00FF7F, transparent);
        animation: aurora-scan 5s ease-in-out infinite;
    }
    
    .aurora-auth-title {
        font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', system-ui, sans-serif;
        font-size: 2.5rem;
        font-weight: 800;
        text-align: center;
        margin-bottom: 1rem;
        background: linear-gradient(120deg, #00FFFF, #7DF9FF, #40E0D0, #00FF7F);
        background-size: 300% 100%;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        animation: aurora-text-flow 4s ease-in-out infinite;
    }
    
    .aurora-auth-subtitle {
        text-align: center;
        color: rgba(255, 255, 255, 0.8);
        font-size: 1.1rem;
        margin-bottom: 2rem;
        font-weight: 300;
    }
    
    .stButton > button {
        background: linear-gradient(135deg, rgba(0, 255, 255, 0.2) 0%, rgba(64, 224, 208, 0.25) 100%);
        border: 1px solid rgba(0, 255, 255, 0.4);
        color: rgba(255, 255, 255, 0.95);
        border-radius: 12px;
        font-weight: 600;
        transition: all 0.3s cubic-bezier(0.4, 0.0, 0.2, 1);
        backdrop-filter: blur(8px);
    }
    
    .stButton > button:hover {
        background: linear-gradient(135deg, rgba(0, 255, 255, 0.3) 0%, rgba(64, 224, 208, 0.35) 100%);
        border-color: rgba(0, 255, 255, 0.6);
        transform: translateY(-2px);
        box-shadow: 0 8px 32px rgba(0, 255, 255, 0.2);
    }
    
    .stTextInput > div > div > input {
        background: rgba(0, 255, 255, 0.05);
        border: 1px solid rgba(0, 255, 255, 0.2);
        border-radius: 12px;
        color: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(8px);
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #00FFFF;
        box-shadow: 0 0 16px rgba(0, 255, 255, 0.3);
    }
    
    .stTabs [role="tablist"] {
        background: rgba(0, 255, 255, 0.05);
        border-radius: 12px;
        padding: 4px;
    }
    
    .stTabs [role="tab"] {
        background: transparent;
        border-radius: 8px;
        color: rgba(255, 255, 255, 0.7);
        transition: all 0.3s ease;
    }
    
    .stTabs [role="tab"][aria-selected="true"] {
        background: linear-gradient(135deg, rgba(0, 255, 255, 0.15), rgba(64, 224, 208, 0.2));
        color: rgba(255, 255, 255, 0.95);
        border: 1px solid rgba(0, 255, 255, 0.3);
    }
    
    @keyframes aurora-scan {
        0% { left: -100%; }
        50% { left: 100%; }
        100% { left: 100%; }
    }
    
    @keyframes aurora-text-flow {
        0%, 100% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Aurora auth container
    st.markdown('<div class="aurora-auth-container">', unsafe_allow_html=True)
    
    st.markdown('<h1 class="aurora-auth-title">WhisperForge</h1>', unsafe_allow_html=True)
    st.markdown('<p class="aurora-auth-subtitle">Transform audio into actionable insights</p>', unsafe_allow_html=True)
    
    # Handle OAuth callback first
    if handle_oauth_callback():
        return
    
    # Google OAuth Sign-In (Clean Supabase Implementation)
    st.markdown("### Quick Sign-In")
    
    # Generate OAuth URL once and store it
    if 'oauth_url' not in st.session_state:
        try:
            db, _ = init_supabase()
            if db:
                # Environment-aware redirect URL
                import os
                
                # Use environment variable if set, otherwise detect environment
                redirect_url = os.getenv("OAUTH_REDIRECT_URL")
                
                if not redirect_url:
                    # Check for Render deployment (Render provides RENDER_SERVICE_NAME)
                    render_service_name = os.getenv("RENDER_SERVICE_NAME")
                    render_external_url = os.getenv("RENDER_EXTERNAL_URL")
                    
                    # Check for Streamlit Cloud (legacy)
                    streamlit_app_url = os.getenv("STREAMLIT_APP_URL")
                    
                    # Check multiple indicators for Streamlit Cloud
                    is_streamlit_cloud = (
                        os.getenv("STREAMLIT_SHARING") or 
                        os.getenv("STREAMLIT_SERVER_PORT") or
                        os.getenv("STREAMLIT_RUNTIME_CREDENTIALS") or
                        "streamlit.app" in os.getenv("HOSTNAME", "") or
                        streamlit_app_url
                    )
                    
                    # Check for Render deployment - Render sets RENDER_SERVICE_NAME
                    is_render = (
                        render_service_name or
                        render_external_url or
                        os.getenv("RENDER") or
                        "onrender.com" in os.getenv("RENDER_EXTERNAL_HOSTNAME", "")
                    )
                    
                    if is_render:
                        # Use custom domain if available, fallback to onrender.com
                        redirect_url = "https://whisperforge.ai"
                    elif is_streamlit_cloud and streamlit_app_url:
                        redirect_url = streamlit_app_url
                    elif is_streamlit_cloud:
                        # If on Streamlit Cloud but no URL set, show error
                        st.error("STREAMLIT_APP_URL not set in secrets! Add it to your app settings.")
                        st.code("STREAMLIT_APP_URL = \"https://your-app-name.streamlit.app\"")
                        redirect_url = None
                    else:
                        # Local development
                        redirect_url = "http://localhost:8501"
                
                if redirect_url:
                    # Use Supabase's built-in OAuth - simple and clean!
                    auth_response = db.client.auth.sign_in_with_oauth({
                        "provider": "google",
                        "options": {
                            "redirect_to": redirect_url
                        }
                    })
                    
                    if hasattr(auth_response, 'url') and auth_response.url:
                        st.session_state.oauth_url = auth_response.url
                    else:
                        st.session_state.oauth_url = None
                else:
                    st.session_state.oauth_url = None
        except Exception as e:
            st.error(f"Google sign-in setup error: {e}")
            st.session_state.oauth_url = None
    
    # Show the OAuth button
    if st.session_state.get('oauth_url'):
                    st.link_button(
                "Sign in with Google", 
                st.session_state.oauth_url, 
                type="primary", 
                use_container_width=True
            )
    else:
        if st.button("Sign in with Google", type="primary", use_container_width=True):
            st.error("Failed to generate Google sign-in URL. Please check your configuration.")
    
    st.markdown("---")
    st.markdown("### Or sign in with email")
    
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
    
    # Close aurora auth container
    st.markdown('</div>', unsafe_allow_html=True)

# Main application with top menu design
def show_main_app():
    """Show main application with sleek top menu navigation"""
    
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
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "Home"
    
    # Load user data
    st.session_state.prompts = get_user_prompts_supabase()
    st.session_state.knowledge_base = get_user_knowledge_base_supabase()
    
    # Aurora top menu styling
    st.markdown("""
    <style>
    /* Aurora Top Menu Design */
    .aurora-top-menu {
        background: linear-gradient(
            135deg,
            rgba(0, 255, 255, 0.08) 0%,
            rgba(64, 224, 208, 0.12) 25%,
            rgba(125, 249, 255, 0.10) 50%,
            rgba(0, 255, 127, 0.08) 75%,
            rgba(0, 255, 255, 0.06) 100%
        );
        backdrop-filter: blur(32px) saturate(200%);
        border: 1px solid rgba(0, 255, 255, 0.2);
        border-radius: 20px;
        padding: 24px 32px;
        margin: 0 0 32px 0;
        box-shadow: 
            0 0 40px rgba(0, 255, 255, 0.15),
            inset 0 1px 0 rgba(255, 255, 255, 0.1);
        position: relative;
        overflow: hidden;
    }
    
    .aurora-top-menu::before {
        content: "";
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 2px;
        background: linear-gradient(90deg, transparent, #00FFFF, #7DF9FF, #40E0D0, #00FF7F, transparent);
        animation: aurora-scan 4s ease-in-out infinite;
    }
    
    .aurora-menu-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 20px;
    }
    
    .aurora-logo {
        font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', system-ui, sans-serif;
        font-size: 1.8rem;
        font-weight: 800;
        background: linear-gradient(120deg, #00FFFF, #7DF9FF, #40E0D0, #00FF7F);
        background-size: 300% 100%;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        animation: aurora-text-flow 3s ease-in-out infinite;
    }
    
    .aurora-user-info {
        color: rgba(255, 255, 255, 0.9);
        font-size: 0.9rem;
        text-align: right;
    }
    
    .aurora-controls-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
        gap: 20px;
        margin-bottom: 24px;
    }
    
    .aurora-control-card {
        background: rgba(0, 255, 255, 0.05);
        border: 1px solid rgba(0, 255, 255, 0.15);
        border-radius: 16px;
        padding: 20px;
        transition: all 0.3s cubic-bezier(0.4, 0.0, 0.2, 1);
    }
    
    .aurora-control-card:hover {
        background: rgba(0, 255, 255, 0.08);
        border-color: rgba(0, 255, 255, 0.25);
        transform: translateY(-2px);
        box-shadow: 0 8px 32px rgba(0, 255, 255, 0.15);
    }
    
    .aurora-control-title {
        color: #00FFFF;
        font-weight: 700;
        font-size: 1rem;
        margin-bottom: 8px;
        font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', system-ui, sans-serif;
    }
    
    /* Hide default sidebar */
    .stSidebar {
        display: none !important;
    }
    
    /* Aurora button styling */
    .stButton > button {
        background: linear-gradient(135deg, rgba(0, 255, 255, 0.15) 0%, rgba(64, 224, 208, 0.2) 100%);
        border: 1px solid rgba(0, 255, 255, 0.3);
        color: rgba(255, 255, 255, 0.95);
        border-radius: 12px;
        font-weight: 600;
        transition: all 0.3s cubic-bezier(0.4, 0.0, 0.2, 1);
        backdrop-filter: blur(8px);
    }
    
    .stButton > button:hover {
        background: linear-gradient(135deg, rgba(0, 255, 255, 0.25) 0%, rgba(64, 224, 208, 0.3) 100%);
        border-color: rgba(0, 255, 255, 0.5);
        transform: translateY(-2px);
        box-shadow: 0 8px 24px rgba(0, 255, 255, 0.2);
    }
    
    .stSelectbox > div > div {
        background: rgba(0, 255, 255, 0.05);
        border: 1px solid rgba(0, 255, 255, 0.2);
        border-radius: 12px;
        backdrop-filter: blur(8px);
    }
    
    @keyframes aurora-scan {
        0% { left: -100%; }
        50% { left: 100%; }
        100% { left: 100%; }
    }
    
    @keyframes aurora-text-flow {
        0%, 100% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Top menu container
    st.markdown('<div class="aurora-top-menu">', unsafe_allow_html=True)
    
    # Menu header with logo and user info
    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown('<div class="aurora-logo">WhisperForge</div>', unsafe_allow_html=True)
    with col2:
        # User info and sign out
        db, _ = init_supabase()
        if db:
            user = db.get_user(st.session_state.user_id)
            if user:
                st.markdown(f'<div class="aurora-user-info">{user.get("email", "Unknown")}<br/>Plan: {user.get("subscription_tier", "free").title()}</div>', unsafe_allow_html=True)
        
        if st.button("Sign Out", key="signout_btn"):
            st.session_state.authenticated = False
            st.session_state.user_id = None
            st.query_params.clear()
            st.rerun()
    
    # Navigation and controls in one section
    st.markdown('<div class="aurora-controls-grid">', unsafe_allow_html=True)
    
    # Navigation controls
    nav_col1, nav_col2, nav_col3, nav_col4 = st.columns(4)
    
    with nav_col1:
        st.markdown('<div class="aurora-control-card">', unsafe_allow_html=True)
        st.markdown('<div class="aurora-control-title">🏠 Home</div>', unsafe_allow_html=True)
        if st.button("Go to Home", key="nav_home", use_container_width=True):
            st.session_state.current_page = "Home"
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    
    with nav_col2:
        st.markdown('<div class="aurora-control-card">', unsafe_allow_html=True)
        st.markdown('<div class="aurora-control-title">📚 History</div>', unsafe_allow_html=True)
        if st.button("View History", key="nav_history", use_container_width=True):
            st.session_state.current_page = "Content History"
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    
    with nav_col3:
        st.markdown('<div class="aurora-control-card">', unsafe_allow_html=True)
        st.markdown('<div class="aurora-control-title">⚙️ Settings</div>', unsafe_allow_html=True)
        if st.button("Open Settings", key="nav_settings", use_container_width=True):
            st.session_state.current_page = "Settings"
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    
    with nav_col4:
        st.markdown('<div class="aurora-control-card">', unsafe_allow_html=True)
        st.markdown('<div class="aurora-control-title">📊 Health</div>', unsafe_allow_html=True)
        if st.button("System Health", key="nav_health", use_container_width=True):
            st.session_state.current_page = "System Health"
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Main content area
    current_page = st.session_state.get("current_page", "Home")
    
    if current_page == "Home":
        show_home_page()
    elif current_page == "Content History":
        show_content_history_page()
    elif current_page == "Settings":
        show_settings_page()
    elif current_page == "System Health":
        show_health_page()

def show_home_page():
    """Enhanced home page with top controls and integrated progress system"""
    
    # Enhanced Aurora styling for cleaner layout
    st.markdown("""
    <style>
    /* Aurora Enhanced Layout Styling */
    .aurora-main-container {
        max-width: 1200px;
        margin: 0 auto;
    }
    
    .aurora-controls-section {
        background: linear-gradient(135deg, rgba(0, 255, 255, 0.05), rgba(64, 224, 208, 0.08));
        border: 1px solid rgba(0, 255, 255, 0.15);
        border-radius: 20px;
        padding: 32px;
        margin-bottom: 32px;
        backdrop-filter: blur(16px);
        box-shadow: 0 0 32px rgba(0, 255, 255, 0.1);
    }
    
    .aurora-upload-zone {
        background: linear-gradient(135deg, rgba(0, 255, 255, 0.03), rgba(125, 249, 255, 0.05));
        border: 2px dashed rgba(0, 255, 255, 0.3);
        border-radius: 16px;
        padding: 40px;
        text-align: center;
        margin-bottom: 24px;
        transition: all 0.3s cubic-bezier(0.4, 0.0, 0.2, 1);
    }
    
    .aurora-upload-zone:hover {
        border-color: rgba(0, 255, 255, 0.5);
        background: linear-gradient(135deg, rgba(0, 255, 255, 0.06), rgba(125, 249, 255, 0.08));
        transform: translateY(-2px);
    }
    
    .aurora-progress-container {
        margin: 32px 0;
        z-index: 10;
        position: relative;
    }
    
    .main .stMarkdown h1 {
        background: linear-gradient(
            120deg,
            #00FFFF 0%,
            #7DF9FF 25%,
            #40E0D0 50%,
            #00FF7F 75%,
            #00FFFF 100%
        );
        background-size: 300% 100%;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        animation: aurora-text-flow 4s ease-in-out infinite;
        font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', system-ui, sans-serif;
        font-weight: 800;
        letter-spacing: -0.03em;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    
    .main .stMarkdown h3 {
        color: #00FFFF;
        font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', system-ui, sans-serif;
        font-weight: 700;
        letter-spacing: -0.02em;
        text-shadow: 0 0 8px rgba(0, 255, 255, 0.3);
    }
    
    .main .stMarkdown h4 {
        color: #7DF9FF;
        font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', system-ui, sans-serif;
        font-weight: 600;
        letter-spacing: -0.015em;
    }
    
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #00FFFF 0%, #7DF9FF 50%, #40E0D0 100%);
        color: #000;
        border: none;
        border-radius: 12px;
        font-weight: 700;
        font-size: 1.1rem;
        padding: 0.75rem 2rem;
        transition: all 0.4s cubic-bezier(0.4, 0.0, 0.2, 1);
        box-shadow: 0 0 24px rgba(0, 255, 255, 0.3);
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .stButton > button[kind="primary"]:hover {
        transform: translateY(-3px);
        box-shadow: 0 0 32px rgba(0, 255, 255, 0.5);
        background: linear-gradient(135deg, #7DF9FF 0%, #00FFFF 50%, #00FF7F 100%);
    }
    
    .stSelectbox > div > div {
        background: rgba(0, 255, 255, 0.05);
        border: 1px solid rgba(0, 255, 255, 0.2);
        border-radius: 12px;
        backdrop-filter: blur(8px);
    }
    
    .stTextInput > div > div > input {
        background: rgba(0, 255, 255, 0.03);
        border: 1px solid rgba(0, 255, 255, 0.2);
        border-radius: 8px;
        color: #fff;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #00FFFF;
        box-shadow: 0 0 12px rgba(0, 255, 255, 0.3);
    }
    
    .stAlert > div {
        border-radius: 12px;
        backdrop-filter: blur(8px);
    }
    
    .stExpander {
        border: 1px solid rgba(0, 255, 255, 0.1);
        border-radius: 12px;
        background: rgba(0, 255, 255, 0.02);
    }
    
    @keyframes aurora-text-flow {
        0%, 100% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Main container
    st.markdown('<div class="aurora-main-container">', unsafe_allow_html=True)
    
    st.title("WhisperForge Content Pipeline")
    st.markdown("Transform your audio content into structured, actionable insights with AI-powered analysis.")
    
    # Top controls section
    st.markdown('<div class="aurora-controls-section">', unsafe_allow_html=True)
    
    # Configuration row
    st.markdown("### ⚙️ Processing Configuration")
    config_col1, config_col2, config_col3 = st.columns(3)
    
    with config_col1:
        st.session_state.ai_provider = st.selectbox(
            "AI Provider",
            ["Anthropic", "OpenAI", "Grok"],
            index=["Anthropic", "OpenAI", "Grok"].index(st.session_state.ai_provider),
            help="Select which AI provider to use for content generation"
        )
    
    with config_col2:
        models = {
            "Anthropic": ["claude-3-7-sonnet-20250219", "claude-3-sonnet-20240229"],
            "OpenAI": ["gpt-4", "gpt-3.5-turbo"],
            "Grok": ["grok-2-2024-08-13", "grok-2-mini-2024-08-13"]
        }
        st.session_state.ai_model = st.selectbox(
            "Model Version",
            models[st.session_state.ai_provider],
            index=0,
            help="Select the specific model variant for processing"
        )
    
    with config_col3:
        pipeline_steps = st.metric(
            "Pipeline Steps", 
            "7 stages",
            help="Number of processing stages in the pipeline"
        )
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # File upload section
    st.markdown("### 📁 Upload Your Audio Content")
    
    # Initialize file upload manager
    file_manager = FileUploadManager()
    
    # Enhanced upload zone
    st.markdown('<div class="aurora-upload-zone">', unsafe_allow_html=True)
    uploaded_file = file_manager.create_upload_zone(
        accept_types=['.mp3', '.wav', '.m4a', '.flac', '.mp4', '.mov', '.avi'],
        show_preview=True
    )
    st.markdown('</div>', unsafe_allow_html=True)
    
    if uploaded_file:
        # Validate the uploaded file
        validation = file_manager.validate_file(uploaded_file)
        
        if not validation['valid']:
            st.error("File validation failed:")
            for error in validation['errors']:
                st.error(f"• {error}")
            return
        
        if validation['warnings']:
            st.warning("Warnings:")
            for warning in validation['warnings']:
                st.warning(f"• {warning}")
        
        st.session_state.audio_file = uploaded_file
        
        # File info and processing estimation
        st.markdown("### 📊 File Analysis")
        info_col1, info_col2, info_col3 = st.columns(3)
        
        with info_col1:
            st.metric(
                "File Size", 
                validation['formatted_size'],
                help="Size of your uploaded file"
            )
        
        with info_col2:
            # Estimate processing time based on file size
            estimated_minutes = max(1, validation['file_size'] // (1024 * 1024) * 0.5)
            st.metric(
                "Est. Time", 
                f"~{estimated_minutes:.0f}min",
                help="Estimated processing time"
            )
        
        with info_col3:
            st.metric(
                "AI Model", 
                st.session_state.ai_model.split('-')[0].upper(),
                help="Selected AI provider and model"
            )
        
        # Process button prominently placed
        st.markdown("### 🚀 Ready to Process")
        
        process_button_html = """
        <div style="text-align: center; margin: 20px 0;">
            <style>
            .process-button {
                background: linear-gradient(135deg, #7928CA 0%, #FF0080 100%);
                border: none;
                border-radius: 12px;
                color: white;
                padding: 16px 32px;
                font-size: 18px;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
                text-decoration: none;
                display: inline-block;
                box-shadow: 0 4px 15px rgba(121, 40, 202, 0.3);
                position: relative;
                overflow: hidden;
            }
            
            .process-button:hover {
                transform: translateY(-2px);
                box-shadow: 0 8px 25px rgba(121, 40, 202, 0.4);
            }
            
            .process-button:active {
                transform: translateY(0px);
            }
            
            .process-button::before {
                content: "";
                position: absolute;
                top: 0;
                left: -100%;
                width: 100%;
                height: 100%;
                background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
                transition: left 0.5s ease;
            }
            
            .process-button:hover::before {
                left: 100%;
            }
            </style>
        </div>
        """
        
        st.markdown(process_button_html, unsafe_allow_html=True)
        
        if st.button("🚀 Start Aurora Processing Pipeline", type="primary", use_container_width=True, key="process_main"):
            # Create progress container for better visibility
            process_audio_pipeline(uploaded_file)
    
    else:
        # Show helpful information when no file is uploaded
        st.markdown("### How It Works")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("""
            **Upload**
            
            Upload your audio or video file in any supported format. We handle the rest!
            """)
        
        with col2:
            st.markdown("""
            **Transcribe**
            
            Our AI converts speech to text with high accuracy and speaker recognition.
            """)
        
        with col3:
            st.markdown("""
            **Generate**
            
            Extract insights, create outlines, social content, and image prompts automatically.
            """)
        
        # Feature highlights
        st.markdown("### Features")
        
        features = [
            "**Smart Content Extraction** - AI identifies key insights and wisdom",
            "**Structured Outlines** - Organized content ready for use", 
            "**Social Media Ready** - Platform-optimized content generation",
            "**Image Prompts** - AI-generated prompts for visual content",
            "**Cloud Storage** - All content saved and accessible anytime",
            "**Secure Processing** - Your data is protected and private"
        ]
        
        for feature in features:
            st.markdown(feature)
    
    # Close main container
    st.markdown('</div>', unsafe_allow_html=True)

def process_audio_pipeline(audio_file):
    """Process audio through the complete pipeline with aurora-themed progress tracking"""
    
    # Track pipeline execution
    pipeline_start = datetime.now()
    pipeline_data = {
        "type": "full",
        "ai_provider": st.session_state.ai_provider.lower(),
        "model": st.session_state.ai_model,
        "success": False,
        "metadata": {"filename": audio_file.name}
    }
    
    # Create aurora-themed progress tracker
    progress_tracker = create_whisperforge_progress_tracker()
    progress_tracker.create_display_container()
    
    try:
        # Step 1: Upload Validation
        with progress_tracker.step_context("upload_validation"):
            file_size_mb = len(audio_file.getvalue()) / (1024 * 1024)
            time.sleep(0.3)  # Brief validation simulation
        
        # Step 2: Transcription
        with progress_tracker.step_context("transcription"):
            transcript = transcribe_audio(audio_file)
            st.session_state.transcription = transcript
            
            if not transcript:
                raise Exception("Failed to transcribe audio - transcript is empty")
        
        # Display transcript with aurora styling
        st.markdown("### Transcript Generated")
        with st.expander("View Full Transcript", expanded=False):
            st.text_area("", transcript, height=200, key="transcript_display")
        
        # Step 3: Wisdom Extraction
        with progress_tracker.step_context("wisdom_extraction"):
            wisdom = generate_wisdom(
                transcript, 
                st.session_state.ai_provider, 
                st.session_state.ai_model, 
                None, 
                st.session_state.knowledge_base
            )
        
        # Step 4: Outline Creation
        with progress_tracker.step_context("outline_creation"):
            outline = generate_outline(
                transcript, 
                wisdom, 
                st.session_state.ai_provider, 
                st.session_state.ai_model, 
                None, 
                st.session_state.knowledge_base
            )
        
        # Step 5: Social Media Content
        with progress_tracker.step_context("social_content"):
            social = generate_social_content(
                wisdom, 
                outline, 
                st.session_state.ai_provider, 
                st.session_state.ai_model, 
                None, 
                st.session_state.knowledge_base
            )
        
        # Step 6: Image Prompts
        with progress_tracker.step_context("image_prompts"):
            images = generate_image_prompts(
                wisdom, 
                outline, 
                st.session_state.ai_provider, 
                st.session_state.ai_model, 
                None, 
                st.session_state.knowledge_base
            )
        
        # Step 7: Database Storage
        with progress_tracker.step_context("database_storage"):
            content_data = {
                "title": f"Content from {audio_file.name}",
                "transcript": transcript,
                "wisdom_extraction": wisdom,
                "outline_creation": outline,
                "social_media": social,
                "image_prompts": images,
                "metadata": {
                    "ai_provider": st.session_state.ai_provider,
                    "ai_model": st.session_state.ai_model,
                    "file_size": audio_file.size if hasattr(audio_file, 'size') else len(audio_file.getvalue()),
                    "created_at": datetime.now().isoformat()
                }
            }
            
            content_id = save_generated_content_supabase(content_data)
            if not content_id:
                raise Exception("Failed to save content to database")
            time.sleep(0.2)  # Brief storage simulation
                    
        # Show success message with professional notification
        st.success("Processing pipeline completed successfully!")
        
        # Display generated content in beautiful aurora-themed cards
        st.markdown("### Generated Content")
        st.markdown("*Your content is ready! Click on each tab to explore the results.*")
        
        # Create tabs for each content type with enhanced styling
        tab1, tab2, tab3, tab4 = st.tabs([
            "Wisdom & Insights", 
            "Content Outline", 
            "Social Media", 
            "Image Prompts"
        ])
        
        with tab1:
            st.markdown("#### Key Insights & Wisdom")
            st.markdown("*AI-extracted insights and valuable takeaways from your content*")
            
            # Create a beautiful aurora content card with proper HTML escaping
            import html
            wisdom_escaped = html.escape(wisdom).replace('\n', '<br>')
            wisdom_html = f"""
            <div class="aurora-content-card aurora-wisdom-card">
                <div class="aurora-content-header">
                    <span class="aurora-content-title">Wisdom & Insights</span>
                </div>
                <div class="aurora-content-body">
                    {wisdom_escaped}
                </div>
            </div>
            """
            st.markdown(wisdom_html, unsafe_allow_html=True)
            
            # Copy button
            if st.button("Copy Wisdom", key="copy_wisdom"):
                st.code(wisdom, language="markdown")
            
        with tab2:
            st.markdown("#### Structured Content Outline")
            st.markdown("*Organized structure ready for presentations, articles, or courses*")
            
            outline_escaped = html.escape(outline).replace('\n', '<br>')
            outline_html = f"""
            <div class="aurora-content-card aurora-outline-card">
                <div class="aurora-content-header">
                    <span class="aurora-content-title">Content Outline</span>
                </div>
                <div class="aurora-content-body">
                    {outline_escaped}
                </div>
            </div>
            """
            st.markdown(outline_html, unsafe_allow_html=True)
            
            if st.button("Copy Outline", key="copy_outline"):
                st.code(outline, language="markdown")
            
        with tab3:
            st.markdown("#### Social Media Ready Content")
            st.markdown("*Platform-optimized content for maximum engagement*")
            
            social_escaped = html.escape(social).replace('\n', '<br>')
            social_html = f"""
            <div class="aurora-content-card aurora-social-card">
                <div class="aurora-content-header">
                    <span class="aurora-content-title">Social Media Content</span>
                </div>
                <div class="aurora-content-body">
                    {social_escaped}
                </div>
            </div>
            """
            st.markdown(social_html, unsafe_allow_html=True)
            
            if st.button("Copy Social Content", key="copy_social"):
                st.code(social, language="markdown")
            
        with tab4:
            st.markdown("#### AI Image Generation Prompts")
            st.markdown("*Ready-to-use prompts for creating visual content with AI tools*")
            
            images_escaped = html.escape(images).replace('\n', '<br>')
            images_html = f"""
            <div class="aurora-content-card aurora-images-card">
                <div class="aurora-content-header">
                    <span class="aurora-content-title">Image Generation Prompts</span>
                </div>
                <div class="aurora-content-body">
                    {images_escaped}
                </div>
            </div>
            """
            st.markdown(images_html, unsafe_allow_html=True)
            
            if st.button("Copy Image Prompts", key="copy_images"):
                st.code(images, language="markdown")
        
        # Add award-winning aurora content card styling
        aurora_content_css = """
        <style>
        /* Aurora Content Cards - Award-Winning Design */
        :root {
            --aurora-cyan: #00FFFF;
            --aurora-turquoise: #40E0D0;
            --aurora-electric-blue: #7DF9FF;
            --aurora-spring-green: #00FF7F;
        }
        
        .aurora-content-card {
            background: linear-gradient(
                135deg,
                rgba(0, 255, 255, 0.03) 0%,
                rgba(64, 224, 208, 0.04) 30%,
                rgba(125, 249, 255, 0.03) 60%,
                rgba(0, 255, 127, 0.02) 100%
            );
            backdrop-filter: blur(24px) saturate(180%);
            border: 1px solid rgba(0, 255, 255, 0.15);
            border-radius: 20px;
            padding: 32px;
            margin: 24px 0;
            position: relative;
            overflow: hidden;
            transition: all 0.6s cubic-bezier(0.4, 0.0, 0.2, 1);
            box-shadow: 
                0 0 32px rgba(0, 255, 255, 0.08),
                inset 0 1px 0 rgba(255, 255, 255, 0.12),
                0 16px 64px rgba(0, 0, 0, 0.12);
        }
        
        .aurora-content-card::before {
            content: "";
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 2px;
            background: linear-gradient(
                90deg,
                transparent 0%,
                var(--aurora-cyan) 20%,
                var(--aurora-electric-blue) 40%,
                var(--aurora-turquoise) 60%,
                var(--aurora-spring-green) 80%,
                transparent 100%
            );
            animation: aurora-scan 5s ease-in-out infinite;
        }
        
        .aurora-content-card:hover {
            border-color: rgba(0, 255, 255, 0.25);
            box-shadow: 
                0 0 48px rgba(0, 255, 255, 0.12),
                inset 0 1px 0 rgba(255, 255, 255, 0.18),
                0 24px 96px rgba(0, 0, 0, 0.16);
            transform: translateY(-4px);
        }
        
        .aurora-content-header {
            display: flex;
            align-items: center;
            margin-bottom: 20px;
            padding-bottom: 16px;
            border-bottom: 1px solid rgba(0, 255, 255, 0.12);
        }
        
        .aurora-content-title {
            font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Segoe UI', Roboto, sans-serif;
            font-weight: 700;
            font-size: 1.2rem;
            letter-spacing: -0.03em;
            background: linear-gradient(
                120deg,
                var(--aurora-cyan) 0%,
                var(--aurora-electric-blue) 25%,
                var(--aurora-turquoise) 50%,
                var(--aurora-spring-green) 75%,
                var(--aurora-cyan) 100%
            );
            background-size: 300% 100%;
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            animation: aurora-text-flow 4s ease-in-out infinite;
        }
        
        .aurora-content-body {
            color: rgba(255, 255, 255, 0.92);
            line-height: 1.7;
            font-size: 1rem;
            letter-spacing: -0.01em;
            font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Text', system-ui, sans-serif;
        }
        
        .aurora-wisdom-card::after {
            content: "";
            position: absolute;
            top: 0;
            right: 0;
            width: 4px;
            height: 100%;
            background: linear-gradient(180deg, var(--aurora-cyan), var(--aurora-electric-blue));
            opacity: 0.6;
        }
        
        .aurora-outline-card::after {
            content: "";
            position: absolute;
            top: 0;
            right: 0;
            width: 4px;
            height: 100%;
            background: linear-gradient(180deg, var(--aurora-spring-green), var(--aurora-turquoise));
            opacity: 0.6;
        }
        
        .aurora-social-card::after {
            content: "";
            position: absolute;
            top: 0;
            right: 0;
            width: 4px;
            height: 100%;
            background: linear-gradient(180deg, var(--aurora-turquoise), var(--aurora-electric-blue));
            opacity: 0.6;
        }
        
        .aurora-images-card::after {
            content: "";
            position: absolute;
            top: 0;
            right: 0;
            width: 4px;
            height: 100%;
            background: linear-gradient(180deg, var(--aurora-electric-blue), var(--aurora-cyan));
            opacity: 0.6;
        }
        
        @keyframes aurora-scan {
            0% { transform: translateX(-100%); }
            50% { transform: translateX(100%); }
            100% { transform: translateX(-100%); }
        }
        
        @keyframes aurora-text-flow {
            0%, 100% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
        }
        
        /* Responsive Design */
        @media (max-width: 768px) {
            .aurora-content-card {
                padding: 24px 20px;
                margin: 16px 0;
                border-radius: 16px;
            }
            
            .aurora-content-title {
                font-size: 1.1rem;
            }
            
            .aurora-content-body {
                font-size: 0.95rem;
            }
        }
        </style>
        """
        
        st.markdown(aurora_content_css, unsafe_allow_html=True)
        
        # Log successful pipeline execution
        pipeline_end = datetime.now()
        pipeline_data.update({
            "success": True,
            "duration": (pipeline_end - pipeline_start).total_seconds(),
            "content_id": content_id if 'content_id' in locals() else None
        })
        
        # Show completion notification
        st.success(f"Pipeline completed successfully! Content saved with ID: {content_id if 'content_id' in locals() else 'N/A'}")
        
    except Exception as e:
        st.error(f"Pipeline error: {e}")
        pipeline_data["error"] = str(e)
        logger.exception("Pipeline error")
    
    finally:
        # Log pipeline execution
        log_pipeline_execution_supabase(pipeline_data)

def show_content_history_page():
    """Show content history page with Aurora styling"""
    
    # Aurora content history styling
    st.markdown("""
    <style>
    /* Aurora Content History Styling */
    .aurora-history-container {
        max-width: 1200px;
        margin: 0 auto;
    }
    
    .stExpander {
        background: linear-gradient(135deg, rgba(0, 255, 255, 0.03), rgba(125, 249, 255, 0.05));
        border: 1px solid rgba(0, 255, 255, 0.15);
        border-radius: 16px;
        margin-bottom: 16px;
        backdrop-filter: blur(16px);
    }
    
    .stTextArea > div > div > textarea {
        background: rgba(0, 255, 255, 0.05);
        border: 1px solid rgba(0, 255, 255, 0.1);
        border-radius: 8px;
        color: rgba(255, 255, 255, 0.95);
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown('<div class="aurora-history-container">', unsafe_allow_html=True)
    st.title("📚 Content History")
    
    content_history = get_user_content_history_supabase(50)
    
    if not content_history:
        st.info("No content history found. Generate some content to see it here!")
        st.markdown('</div>', unsafe_allow_html=True)
        return
    
    # Display content history
    for content in content_history:
        with st.expander(f"{content.get('title', 'Untitled')} - {content.get('created_at', '')[:10]}"):
            
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
    
    # Close aurora history container
    st.markdown('</div>', unsafe_allow_html=True)

def show_settings_page():
    """Show settings page with Aurora styling"""
    
    # Aurora settings page styling
    st.markdown("""
    <style>
    /* Aurora Settings Page Styling */
    .aurora-settings-container {
        max-width: 1000px;
        margin: 0 auto;
    }
    
    .aurora-settings-section {
        background: linear-gradient(135deg, rgba(0, 255, 255, 0.05), rgba(64, 224, 208, 0.08));
        border: 1px solid rgba(0, 255, 255, 0.15);
        border-radius: 16px;
        padding: 24px;
        margin-bottom: 24px;
        backdrop-filter: blur(16px);
    }
    
    .stTextInput > div > div > input {
        background: rgba(0, 255, 255, 0.05);
        border: 1px solid rgba(0, 255, 255, 0.2);
        border-radius: 8px;
        color: rgba(255, 255, 255, 0.95);
    }
    
    .stTextArea > div > div > textarea {
        background: rgba(0, 255, 255, 0.05);
        border: 1px solid rgba(0, 255, 255, 0.2);
        border-radius: 8px;
        color: rgba(255, 255, 255, 0.95);
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown('<div class="aurora-settings-container">', unsafe_allow_html=True)
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
                with st.expander(f"{name}"):
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
    
    # Close aurora settings container
    st.markdown('</div>', unsafe_allow_html=True)

def show_health_page():
    """Health check page with Aurora styling"""
    
    # Aurora health page styling
    st.markdown("""
    <style>
    /* Aurora Health Page Styling */
    .aurora-health-container {
        max-width: 1000px;
        margin: 0 auto;
    }
    
    .aurora-health-status {
        background: linear-gradient(135deg, rgba(0, 255, 255, 0.05), rgba(64, 224, 208, 0.08));
        border: 1px solid rgba(0, 255, 255, 0.15);
        border-radius: 16px;
        padding: 24px;
        margin-bottom: 24px;
        backdrop-filter: blur(16px);
        text-align: center;
    }
    
    .aurora-health-checks {
        background: linear-gradient(135deg, rgba(0, 255, 255, 0.03), rgba(125, 249, 255, 0.05));
        border: 1px solid rgba(0, 255, 255, 0.1);
        border-radius: 16px;
        padding: 24px;
        backdrop-filter: blur(16px);
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown('<div class="aurora-health-container">', unsafe_allow_html=True)
    st.title("📊 System Health")
    
    health = get_health_status()
    
    # Overall status
    if health["status"] == "healthy":
        st.success("✅ System is healthy")
    elif health["status"] == "degraded":
        st.warning("System is degraded")
    else:
        st.error("System is unhealthy")
    
    # Detailed checks
    st.subheader("System Checks")
    for check, status in health["checks"].items():
        if isinstance(status, dict):
            st.write(f"**{check.title()}:**")
            for key, value in status.items():
                st.write(f"  - {key}: {value}")
        else:
            if "error" in str(status).lower() or "unhealthy" in str(status).lower():
                st.error(f"**{check.title()}:** {status}")
            elif "missing" in str(status).lower():
                st.warning(f"**{check.title()}:** {status}")
            else:
                st.success(f"✅ **{check.title()}:** {status}")
    
    # Close aurora health container
    st.markdown('</div>', unsafe_allow_html=True)


# Main app logic
def main():
    """Main application entry point"""
    try:
        # Initialize session tracking
        init_session_tracking()
        
        # Initialize session state
        if 'authenticated' not in st.session_state:
            st.session_state.authenticated = False
        if 'user_id' not in st.session_state:
            st.session_state.user_id = None
        
        # Check for health endpoint
        query_params = st.query_params
        if 'health' in query_params:
            show_health_page()
            return
        
        # Handle OAuth callback first
        if handle_oauth_callback():
            return
        
        # Check authentication
        if not st.session_state.authenticated:
            show_auth_page()
        else:
            show_main_app()
    
    except Exception as e:
        track_error(e, {"location": "main_app"})
        st.error(f"Application error: {e}")
        logger.error("Main application error", exc_info=True)

if __name__ == "__main__":
    main() 