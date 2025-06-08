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
    """Modern authentication page with premium SaaS design"""
    
    # Modern Aurora authentication styling
    st.markdown("""
    <style>
    /* Hide Streamlit default elements */
    .stApp > header {display: none;}
    .stDeployButton {display: none;}
    footer {display: none;}
    .stDecoration {display: none;}
    
    /* Modern Aurora Authentication Design */
    .aurora-auth-page {
        min-height: 100vh;
        background: 
            radial-gradient(ellipse at top, rgba(0, 255, 255, 0.1) 0%, transparent 50%),
            radial-gradient(ellipse at bottom, rgba(64, 224, 208, 0.08) 0%, transparent 50%),
            linear-gradient(180deg, #0a0f1c 0%, #0d1421 100%);
        display: flex;
        align-items: center;
        justify-content: center;
        font-family: -apple-system, BlinkMacSystemFont, 'Inter', 'SF Pro Display', system-ui, sans-serif;
    }
    
    .aurora-auth-card {
        background: rgba(255, 255, 255, 0.02);
        backdrop-filter: blur(24px) saturate(180%);
        border: 1px solid rgba(0, 255, 255, 0.1);
        border-radius: 16px;
        padding: 48px;
        width: 100%;
        max-width: 440px;
        box-shadow: 
            0 0 60px rgba(0, 255, 255, 0.1),
            inset 0 1px 0 rgba(255, 255, 255, 0.05);
        position: relative;
        overflow: hidden;
    }
    
    .aurora-auth-card::before {
        content: "";
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 1px;
        background: linear-gradient(90deg, transparent, #00FFFF, #40E0D0, transparent);
        animation: aurora-shimmer 8s ease-in-out infinite;
    }
    
    .aurora-logo-section {
        text-align: center;
        margin-bottom: 40px;
    }
    
    .aurora-logo {
        font-size: 2rem;
        font-weight: 700;
        letter-spacing: -0.02em;
        background: linear-gradient(135deg, #00FFFF, #7DF9FF, #40E0D0);
        background-size: 200% 100%;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        animation: aurora-flow 6s ease-in-out infinite;
        margin-bottom: 8px;
    }
    
    .aurora-tagline {
        color: rgba(255, 255, 255, 0.6);
        font-size: 0.95rem;
        font-weight: 400;
    }
    
    .aurora-form-section {
        margin-bottom: 32px;
    }
    
    .aurora-form-title {
        color: rgba(255, 255, 255, 0.95);
        font-size: 1.25rem;
        font-weight: 600;
        margin-bottom: 24px;
        text-align: center;
    }
    
    /* Enhanced form styling */
    .stButton > button {
        width: 100%;
        background: linear-gradient(135deg, rgba(0, 255, 255, 0.1), rgba(64, 224, 208, 0.15));
        border: 1px solid rgba(0, 255, 255, 0.2);
        color: rgba(255, 255, 255, 0.95);
        border-radius: 8px;
        padding: 12px 16px;
        font-weight: 500;
        font-size: 0.95rem;
        transition: all 0.2s cubic-bezier(0.4, 0.0, 0.2, 1);
        backdrop-filter: blur(8px);
        margin-bottom: 16px;
    }
    
    .stButton > button:hover {
        background: linear-gradient(135deg, rgba(0, 255, 255, 0.15), rgba(64, 224, 208, 0.2));
        border-color: rgba(0, 255, 255, 0.3);
        transform: translateY(-1px);
        box-shadow: 0 4px 20px rgba(0, 255, 255, 0.15);
    }
    
    .stTextInput > div > div > input {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 8px;
        color: rgba(255, 255, 255, 0.95);
        padding: 12px 16px;
        font-size: 0.95rem;
        transition: all 0.2s ease;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: rgba(0, 255, 255, 0.4);
        box-shadow: 0 0 0 3px rgba(0, 255, 255, 0.1);
        background: rgba(255, 255, 255, 0.05);
    }
    
    .stTextInput > div > div > input::placeholder {
        color: rgba(255, 255, 255, 0.4);
    }
    
    .stTabs [role="tablist"] {
        background: rgba(255, 255, 255, 0.03);
        border-radius: 8px;
        padding: 4px;
        margin-bottom: 24px;
    }
    
    .stTabs [role="tab"] {
        background: transparent;
        border-radius: 6px;
        color: rgba(255, 255, 255, 0.6);
        font-weight: 500;
        transition: all 0.2s ease;
        padding: 8px 16px;
    }
    
    .stTabs [role="tab"][aria-selected="true"] {
        background: rgba(0, 255, 255, 0.1);
        color: rgba(255, 255, 255, 0.95);
        border: 1px solid rgba(0, 255, 255, 0.2);
    }
    
    .aurora-divider {
        display: flex;
        align-items: center;
        margin: 24px 0;
        color: rgba(255, 255, 255, 0.4);
        font-size: 0.85rem;
    }
    
    .aurora-divider::before,
    .aurora-divider::after {
        content: "";
        flex: 1;
        height: 1px;
        background: rgba(255, 255, 255, 0.1);
    }
    
    .aurora-divider span {
        padding: 0 16px;
    }
    
    @keyframes aurora-shimmer {
        0%, 100% { left: -100%; }
        50% { left: 100%; }
    }
    
    @keyframes aurora-flow {
        0%, 100% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
    }
    
    /* Mobile responsive */
    @media (max-width: 768px) {
        .aurora-auth-card {
            padding: 32px 24px;
            margin: 20px;
        }
        
        .aurora-logo {
            font-size: 1.75rem;
        }
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Main auth page structure
    st.markdown('<div class="aurora-auth-page">', unsafe_allow_html=True)
    st.markdown('<div class="aurora-auth-card">', unsafe_allow_html=True)
    
    # Logo and branding
    st.markdown("""
    <div class="aurora-logo-section">
        <div class="aurora-logo">WhisperForge</div>
        <div class="aurora-tagline">Transform audio into actionable insights</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Handle OAuth callback first
    if handle_oauth_callback():
        return
    
    # Quick Sign-In Section
    st.markdown('<div class="aurora-form-section">', unsafe_allow_html=True)
    
    # Generate OAuth URL
    if 'oauth_url' not in st.session_state:
        try:
            db, _ = init_supabase()
            if db:
                import os
                redirect_url = os.getenv("OAUTH_REDIRECT_URL")
                
                if not redirect_url:
                    render_service_name = os.getenv("RENDER_SERVICE_NAME")
                    render_external_url = os.getenv("RENDER_EXTERNAL_URL")
                    streamlit_app_url = os.getenv("STREAMLIT_APP_URL")
                    
                    is_streamlit_cloud = (
                        os.getenv("STREAMLIT_SHARING") or 
                        os.getenv("STREAMLIT_SERVER_PORT") or
                        os.getenv("STREAMLIT_RUNTIME_CREDENTIALS") or
                        "streamlit.app" in os.getenv("HOSTNAME", "") or
                        streamlit_app_url
                    )
                    
                    is_render = (
                        render_service_name or
                        render_external_url or
                        os.getenv("RENDER") or
                        "onrender.com" in os.getenv("RENDER_EXTERNAL_HOSTNAME", "")
                    )
                    
                    if is_render:
                        redirect_url = "https://whisperforge.ai"
                    elif is_streamlit_cloud and streamlit_app_url:
                        redirect_url = streamlit_app_url
                    elif is_streamlit_cloud:
                        st.error("STREAMLIT_APP_URL not set in secrets! Add it to your app settings.")
                        redirect_url = None
                    else:
                        redirect_url = "http://localhost:8501"
                
                if redirect_url:
                    auth_response = db.client.auth.sign_in_with_oauth({
                        "provider": "google",
                        "options": {"redirect_to": redirect_url}
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
    
    # OAuth button
    if st.session_state.get('oauth_url'):
        st.link_button("Continue with Google", st.session_state.oauth_url, type="primary", use_container_width=True)
    else:
        if st.button("Continue with Google", type="primary", use_container_width=True):
            st.error("Failed to generate Google sign-in URL. Please check your configuration.")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Divider
    st.markdown('<div class="aurora-divider"><span>or</span></div>', unsafe_allow_html=True)
    
    # Email authentication tabs
    tab1, tab2 = st.tabs(["Sign In", "Create Account"])
    
    with tab1:
        st.markdown('<div class="aurora-form-title">Welcome back</div>', unsafe_allow_html=True)
        
        email = st.text_input("Email", placeholder="Enter your email", key="signin_email", label_visibility="collapsed")
        password = st.text_input("Password", type="password", placeholder="Enter your password", key="signin_password", label_visibility="collapsed")
        
        if st.button("Sign In", type="primary", use_container_width=True):
            if not email or not password:
                st.error("Please enter both email and password")
            elif authenticate_user_supabase(email, password):
                st.success("Welcome back!")
                st.rerun()
            else:
                st.error("Invalid credentials. Please try again.")
    
    with tab2:
        st.markdown('<div class="aurora-form-title">Create your account</div>', unsafe_allow_html=True)
        
        email = st.text_input("Email", placeholder="Enter your email", key="register_email", label_visibility="collapsed")
        password = st.text_input("Password", type="password", placeholder="Create a password", key="register_password", label_visibility="collapsed")
        password_confirm = st.text_input("Confirm Password", type="password", placeholder="Confirm your password", key="register_password_confirm", label_visibility="collapsed")
        
        if st.button("Create Account", type="primary", use_container_width=True):
            if not email or not password:
                st.error("Please enter both email and password")
            elif len(password) < 6:
                st.error("Password must be at least 6 characters")
            elif password != password_confirm:
                st.error("Passwords don't match")
            elif register_user_supabase(email, password):
                st.success("Account created! Please sign in with your new credentials.")
                st.session_state.register_email = ""
                st.session_state.register_password = ""
                st.session_state.register_password_confirm = ""
            else:
                st.error("Error creating account. Email may already exist.")
    
    # Close containers
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# Main application with top menu design
def show_main_app():
    """Modern main application interface with premium SaaS design"""
    
    # Initialize session state
    if 'transcription' not in st.session_state:
        st.session_state.transcription = ""
    if 'wisdom' not in st.session_state:
        st.session_state.wisdom = ""
    if 'ai_provider' not in st.session_state:
        st.session_state.ai_provider = "Anthropic"
    if 'ai_model' not in st.session_state:
        st.session_state.ai_model = "claude-3-5-sonnet-20241022"
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "Home"
    
    # Load user data
    st.session_state.prompts = get_user_prompts_supabase()
    st.session_state.knowledge_base = get_user_knowledge_base_supabase()
    
    # Global Aurora styling for main app
    st.markdown("""
    <style>
    /* Hide Streamlit defaults */
    .stApp > header {display: none;}
    .stDeployButton {display: none;}
    footer {display: none;}
    .stDecoration {display: none;}
    .stSidebar {display: none !important;}
    
    /* Modern SaaS App Layout */
    .aurora-app {
        background: linear-gradient(180deg, #0a0f1c 0%, #0d1421 100%);
        min-height: 100vh;
        font-family: -apple-system, BlinkMacSystemFont, 'Inter', 'SF Pro Display', system-ui, sans-serif;
    }
    
    /* Top Header Bar */
    .aurora-header {
        background: rgba(255, 255, 255, 0.02);
        backdrop-filter: blur(24px) saturate(180%);
        border-bottom: 1px solid rgba(255, 255, 255, 0.08);
        padding: 16px 24px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        position: sticky;
        top: 0;
        z-index: 100;
    }
    
    .aurora-logo-header {
        font-size: 1.25rem;
        font-weight: 700;
        background: linear-gradient(135deg, #00FFFF, #40E0D0);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    
    .aurora-user-menu {
        display: flex;
        align-items: center;
        gap: 16px;
        color: rgba(255, 255, 255, 0.8);
        font-size: 0.9rem;
    }
    
    .aurora-sign-out {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        color: rgba(255, 255, 255, 0.8);
        border-radius: 6px;
        padding: 6px 12px;
        font-size: 0.85rem;
        cursor: pointer;
        transition: all 0.2s ease;
    }
    
    .aurora-sign-out:hover {
        background: rgba(255, 255, 255, 0.08);
        color: rgba(255, 255, 255, 0.95);
    }
    
    /* Main Content Layout */
    .aurora-main-layout {
        display: flex;
        min-height: calc(100vh - 72px);
    }
    
    /* Left Sidebar */
    .aurora-sidebar {
        width: 280px;
        background: rgba(255, 255, 255, 0.01);
        border-right: 1px solid rgba(255, 255, 255, 0.06);
        padding: 24px;
        flex-shrink: 0;
    }
    
    .aurora-nav-section {
        margin-bottom: 32px;
    }
    
    .aurora-nav-title {
        font-size: 0.8rem;
        font-weight: 600;
        color: rgba(255, 255, 255, 0.5);
        text-transform: uppercase;
        letter-spacing: 0.1em;
        margin-bottom: 12px;
    }
    
    .aurora-nav-item {
        display: flex;
        align-items: center;
        padding: 12px 16px;
        border-radius: 8px;
        color: rgba(255, 255, 255, 0.7);
        cursor: pointer;
        transition: all 0.2s ease;
        margin-bottom: 4px;
        text-decoration: none;
        border: 1px solid transparent;
    }
    
    .aurora-nav-item:hover {
        background: rgba(0, 255, 255, 0.08);
        color: rgba(255, 255, 255, 0.95);
        border: 1px solid rgba(0, 255, 255, 0.2);
    }
    
    .aurora-nav-item.active {
        background: rgba(0, 255, 255, 0.1);
        color: rgba(255, 255, 255, 0.95);
        border: 1px solid rgba(0, 255, 255, 0.3);
    }
    
    .aurora-nav-icon {
        margin-right: 12px;
        font-size: 1rem;
    }
    
    /* Main Content Area */
    .aurora-content {
        flex: 1;
        padding: 32px;
        max-width: calc(100vw - 280px);
        overflow-x: hidden;
    }
    
    /* Page Headers */
    .aurora-page-header {
        margin-bottom: 32px;
    }
    
    .aurora-page-title {
        font-size: 2rem;
        font-weight: 700;
        color: rgba(255, 255, 255, 0.95);
        margin-bottom: 8px;
        letter-spacing: -0.02em;
    }
    
    .aurora-page-subtitle {
        color: rgba(255, 255, 255, 0.6);
        font-size: 1rem;
        font-weight: 400;
    }
    
    /* Control Cards */
    .aurora-control-section {
        background: rgba(255, 255, 255, 0.02);
        backdrop-filter: blur(16px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 24px;
        margin-bottom: 24px;
    }
    
    .aurora-control-title {
        font-size: 1rem;
        font-weight: 600;
        color: rgba(255, 255, 255, 0.9);
        margin-bottom: 16px;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    
    .aurora-control-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 16px;
    }
    
    /* Enhanced Streamlit Components */
    .stButton > button {
        background: linear-gradient(135deg, rgba(0, 255, 255, 0.1), rgba(64, 224, 208, 0.15));
        border: 1px solid rgba(0, 255, 255, 0.2);
        color: rgba(255, 255, 255, 0.95);
        border-radius: 8px;
        font-weight: 500;
        transition: all 0.2s ease;
        backdrop-filter: blur(8px);
    }
    
    .stButton > button:hover {
        background: linear-gradient(135deg, rgba(0, 255, 255, 0.15), rgba(64, 224, 208, 0.2));
        border-color: rgba(0, 255, 255, 0.3);
        transform: translateY(-1px);
        box-shadow: 0 4px 20px rgba(0, 255, 255, 0.15);
    }
    
    .stSelectbox > div > div > div {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 8px;
        color: rgba(255, 255, 255, 0.95);
    }
    
    .stSelectbox > div > div > div:focus-within {
        border-color: rgba(0, 255, 255, 0.4);
        box-shadow: 0 0 0 3px rgba(0, 255, 255, 0.1);
    }
    
    /* Mobile responsive */
    @media (max-width: 1024px) {
        .aurora-sidebar {
            width: 240px;
        }
        .aurora-content {
            max-width: calc(100vw - 240px);
        }
    }
    
    @media (max-width: 768px) {
        .aurora-main-layout {
            flex-direction: column;
        }
        .aurora-sidebar {
            width: 100%;
            border-right: none;
            border-bottom: 1px solid rgba(255, 255, 255, 0.06);
        }
        .aurora-content {
            max-width: 100%;
            padding: 24px 16px;
        }
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Main app container
    st.markdown('<div class="aurora-app">', unsafe_allow_html=True)
    
    # Header
    user_email = st.session_state.get("user_email", "Unknown User")
    st.markdown(f"""
    <div class="aurora-header">
        <div class="aurora-logo-header">WhisperForge</div>
        <div class="aurora-user-menu">
            <span>{user_email}</span>
            <span>•</span>
            <button class="aurora-sign-out" onclick="window.location.reload()">Sign Out</button>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Main layout
    st.markdown('<div class="aurora-main-layout">', unsafe_allow_html=True)
    
    # Sidebar Navigation with buttons
    st.markdown('<div class="aurora-sidebar">', unsafe_allow_html=True)
    
    current_page = st.session_state.get("current_page", "Home")
    
    # Main navigation
    st.markdown("""
    <div class="aurora-nav-section">
        <div class="aurora-nav-title">Main</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Home button
    home_class = "active" if current_page == "Home" else ""
    if st.button("🏠 Home", key="nav_home", use_container_width=True):
        st.session_state.current_page = "Home"
        st.rerun()
    
    # Analytics placeholder
    if st.button("📊 Analytics", key="nav_analytics", use_container_width=True):
        st.info("Analytics coming soon!")
    
    # Projects placeholder  
    if st.button("📁 Projects", key="nav_projects", use_container_width=True):
        st.info("Projects coming soon!")
    
    st.markdown("""
    <div class="aurora-nav-section">
        <div class="aurora-nav-title">Content</div>
    </div>
    """, unsafe_allow_html=True)
    
    # History button
    if st.button("📝 History", key="nav_history", use_container_width=True):
        st.session_state.current_page = "Content History"
        st.rerun()
    
    # Insights placeholder
    if st.button("💡 Insights", key="nav_insights", use_container_width=True):
        st.info("Advanced insights coming soon!")
    
    # Images placeholder
    if st.button("🖼️ Images", key="nav_images", use_container_width=True):
        st.info("Image gallery coming soon!")
    
    st.markdown("""
    <div class="aurora-nav-section">
        <div class="aurora-nav-title">Settings</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Settings button
    if st.button("⚙️ Configuration", key="nav_settings", use_container_width=True):
        st.session_state.current_page = "Settings"
        st.rerun()
    
    # API Keys placeholder (redirect to settings)
    if st.button("🔑 API Keys", key="nav_api_keys", use_container_width=True):
        st.session_state.current_page = "Settings"
        st.rerun()
    
    # Health button
    if st.button("❤️ Health", key="nav_health", use_container_width=True):
        st.session_state.current_page = "System Health"
        st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Main Content Area
    st.markdown('<div class="aurora-content">', unsafe_allow_html=True)
    
    # Route to appropriate page
    if current_page == "Home":
        show_home_page()
    elif current_page == "Content History":
        show_content_history_page()
    elif current_page == "Settings":
        show_settings_page()
    elif current_page == "System Health":
        show_health_page()
    
    # Close main content and layout
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

def show_home_page():
    """Modern home page with clean, professional design"""
    
    # Page Header
    st.markdown("""
    <div class="aurora-page-header">
        <h1 class="aurora-page-title">Content Pipeline</h1>
        <p class="aurora-page-subtitle">Transform your audio content into structured, actionable insights with AI-powered analysis.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # AI Configuration Section
    st.markdown("""
    <div class="aurora-control-section">
        <div class="aurora-control-title">
            <span>⚡</span>
            AI Configuration
        </div>
        <div class="aurora-control-grid">
    """, unsafe_allow_html=True)
    
    # AI Provider and Model Selection
    col1, col2 = st.columns(2)
    with col1:
        st.session_state.ai_provider = st.selectbox(
            "AI Provider", 
            ["Anthropic", "OpenAI"], 
            index=["Anthropic", "OpenAI"].index(st.session_state.ai_provider),
            key="main_ai_provider"
        )
    
    with col2:
        if st.session_state.ai_provider == "Anthropic":
            available_models = [
                "claude-3-5-sonnet-20241022",
                "claude-3-5-haiku-20241022", 
                "claude-3-opus-20240229",
                "claude-3-sonnet-20240229",
                "claude-3-haiku-20240307"
            ]
            # Try to maintain current selection or default to first
            try:
                current_index = available_models.index(st.session_state.ai_model)
            except ValueError:
                current_index = 0
                st.session_state.ai_model = available_models[0]
        else:  # OpenAI
            available_models = [
                "gpt-4o",
                "gpt-4o-mini", 
                "gpt-4-turbo",
                "gpt-4",
                "gpt-3.5-turbo"
            ]
            current_index = 0
            st.session_state.ai_model = available_models[0]
        
        st.session_state.ai_model = st.selectbox(
            "Model", 
            available_models, 
            index=current_index,
            key="main_selected_model"
        )
    
    st.markdown('</div></div>', unsafe_allow_html=True)
    
    # Pipeline Configuration
    st.markdown("""
    <div class="aurora-control-section">
        <div class="aurora-control-title">
            <span>🔄</span>
            Pipeline Configuration
        </div>
        <div class="aurora-control-grid">
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        pipeline_steps = st.multiselect(
            "Processing Steps",
            ["Transcription", "Summary", "Key Insights", "Action Items", "Social Media", "Images"],
            default=["Transcription", "Summary", "Key Insights"],
            key="main_pipeline_steps"
        )
    
    with col2:
        processing_mode = st.selectbox(
            "Processing Mode",
            ["Standard", "Fast", "Comprehensive"],
            key="main_processing_mode"
        )
    
    st.markdown('</div></div>', unsafe_allow_html=True)
    
    # File Upload Section
    st.markdown("""
    <div class="aurora-control-section">
        <div class="aurora-control-title">
            <span>📁</span>
            Upload Audio Content
        </div>
    """, unsafe_allow_html=True)
    
    # Upload Zone
    st.markdown("""
    <div style="
        background: rgba(255, 255, 255, 0.015);
        border: 2px dashed rgba(0, 255, 255, 0.2);
        border-radius: 12px;
        padding: 48px 24px;
        text-align: center;
        transition: all 0.3s ease;
        margin-bottom: 24px;
    ">
        <div style="font-size: 3rem; color: rgba(0, 255, 255, 0.6); margin-bottom: 16px;">📁</div>
        <div style="color: rgba(255, 255, 255, 0.8); font-size: 1.1rem; font-weight: 500; margin-bottom: 8px;">
            Drop your audio files here
        </div>
        <div style="color: rgba(255, 255, 255, 0.5); font-size: 0.9rem;">
            Supports MP3, WAV, M4A, FLAC, and MP4 files up to 25MB
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    uploaded_file = st.file_uploader(
        "Choose audio file",
        type=['mp3', 'wav', 'm4a', 'flac', 'mp4'],
        key="main_file_upload",
        label_visibility="collapsed"
    )
    
    if uploaded_file:
        # File Info Section
        st.markdown("#### File Information")
        col1, col2, col3 = st.columns(3)
        
        file_size = len(uploaded_file.getvalue())
        file_size_mb = file_size / (1024 * 1024)
        
        with col1:
            st.metric("File Size", f"{file_size_mb:.2f} MB")
        
        with col2:
            st.metric("Format", uploaded_file.type.split('/')[-1].upper())
        
        with col3:
            est_time = max(1, file_size_mb * 0.5)
            st.metric("Est. Processing Time", f"~{est_time:.0f}min")
        
        # Processing Section
        st.markdown("#### Ready to Process")
        
        if st.button("🚀 Start Processing", type="primary", use_container_width=True, key="process_button"):
            # Process the audio file using existing pipeline
            process_audio_pipeline(uploaded_file)
    
    else:
        # Empty state with helpful information
        st.markdown("#### How It Works")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("""
            **📤 Upload**
            
            Upload your audio or video file in any supported format. We handle the rest automatically.
            """)
        
        with col2:
            st.markdown("""
            **🔄 Process**
            
            Our AI transcribes and analyzes your content with high accuracy and speaker recognition.
            """)
        
        with col3:
            st.markdown("""
            **✨ Generate**
            
            Extract insights, create outlines, social content, and image prompts automatically.
            """)
        
        # Feature highlights
        st.markdown("#### Key Features")
        
        features = [
            "**Smart Content Extraction** - AI identifies key insights and wisdom from your audio",
            "**Structured Outlines** - Organized content ready for immediate use", 
            "**Social Media Ready** - Platform-optimized content generation",
            "**Image Prompts** - AI-generated prompts for visual content creation",
            "**Secure Processing** - Your data is protected and private",
            "**Multiple Formats** - Support for audio and video files"
        ]
        
        for feature in features:
            st.markdown(f"• {feature}")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Results Section (if available)
    if 'results' in st.session_state and st.session_state.results:
        st.markdown("""
        <div class="aurora-control-section">
            <div class="aurora-control-title">
                <span>✨</span>
                Generated Results
            </div>
        """, unsafe_allow_html=True)
        
        # Display results in modern tabs
        results = st.session_state.results
        
        # Create tabs for different result types
        result_tabs = []
        if 'wisdom' in results:
            result_tabs.append("💡 Insights")
        if 'outline' in results:
            result_tabs.append("📋 Outline")
        if 'social' in results:
            result_tabs.append("📱 Social")
        if 'images' in results:
            result_tabs.append("🖼️ Images")
        
        if result_tabs:
            tabs = st.tabs(result_tabs)
            
            tab_idx = 0
            if 'wisdom' in results and tab_idx < len(tabs):
                with tabs[tab_idx]:
                    st.markdown(results['wisdom'], unsafe_allow_html=True)
                tab_idx += 1
            
            if 'outline' in results and tab_idx < len(tabs):
                with tabs[tab_idx]:
                    st.markdown(results['outline'], unsafe_allow_html=True)
                tab_idx += 1
            
            if 'social' in results and tab_idx < len(tabs):
                with tabs[tab_idx]:
                    st.markdown(results['social'], unsafe_allow_html=True)
                tab_idx += 1
            
            if 'images' in results and tab_idx < len(tabs):
                with tabs[tab_idx]:
                    if isinstance(results['images'], list):
                        for idx, image_data in enumerate(results['images']):
                            st.image(image_data, caption=f"Generated Image {idx + 1}")
                    else:
                        st.markdown(results['images'], unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)


        
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