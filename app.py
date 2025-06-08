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

# Main application with modern SaaS design
def show_main_app():
    """Modern main application interface with premium SaaS design that actually works"""
    
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
    
    # Modern Aurora styling that works with Streamlit
    st.markdown("""
    <style>
    /* Hide Streamlit defaults for clean look */
    .stApp > header {display: none;}
    .stDeployButton {display: none;}
    footer {display: none;}
    .stDecoration {display: none;}
    
    /* Modern Aurora App Background */
    .stApp {
        background: linear-gradient(180deg, #0a0f1c 0%, #0d1421 100%);
        font-family: -apple-system, BlinkMacSystemFont, 'Inter', 'SF Pro Display', system-ui, sans-serif;
    }
    
    /* Clean, modern header */
    .aurora-modern-header {
        background: rgba(255, 255, 255, 0.02);
        backdrop-filter: blur(24px) saturate(180%);
        border-bottom: 1px solid rgba(0, 255, 255, 0.1);
        padding: 16px 0;
        margin-bottom: 24px;
        position: relative;
    }
    
    .aurora-modern-header::before {
        content: "";
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 1px;
        background: linear-gradient(90deg, transparent, rgba(0, 255, 255, 0.4), transparent);
        animation: aurora-flow 6s ease-in-out infinite;
    }
    
    .aurora-header-content {
        display: flex;
        justify-content: space-between;
        align-items: center;
        max-width: 1200px;
        margin: 0 auto;
        padding: 0 24px;
    }
    
    .aurora-logo {
        font-size: 1.5rem;
        font-weight: 700;
        background: linear-gradient(135deg, #00FFFF, #40E0D0, #7DF9FF);
        background-size: 200% 100%;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        animation: aurora-flow 6s ease-in-out infinite;
    }
    
    .aurora-user-info {
        color: rgba(255, 255, 255, 0.7);
        font-size: 0.9rem;
        display: flex;
        align-items: center;
        gap: 16px;
    }
    
    .aurora-status-dot {
        width: 8px;
        height: 8px;
        background: #00FF7F;
        border-radius: 50%;
        box-shadow: 0 0 8px rgba(0, 255, 127, 0.6);
        animation: aurora-pulse 2s ease-in-out infinite;
    }
    
    /* Streamlit sidebar styling for modern look */
    .stSidebar {
        background: rgba(255, 255, 255, 0.01) !important;
        border-right: 1px solid rgba(0, 255, 255, 0.1) !important;
    }
    
    .stSidebar .stMarkdown {
        background: transparent !important;
    }
    
    /* Navigation section headers */
    .aurora-nav-header {
        color: rgba(255, 255, 255, 0.5);
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        margin: 20px 16px 8px 16px;
        padding-bottom: 8px;
        border-bottom: 1px solid rgba(255, 255, 255, 0.05);
    }
    
    /* Modern button styling for sidebar */
    .stButton > button {
        width: 100% !important;
        background: rgba(255, 255, 255, 0.02) !important;
        border: 1px solid rgba(255, 255, 255, 0.06) !important;
        color: rgba(255, 255, 255, 0.8) !important;
        border-radius: 8px !important;
        padding: 12px 16px !important;
        font-weight: 500 !important;
        transition: all 0.2s cubic-bezier(0.4, 0.0, 0.2, 1) !important;
        backdrop-filter: blur(8px) !important;
        margin-bottom: 4px !important;
        text-align: left !important;
        font-size: 0.9rem !important;
    }
    
    .stButton > button:hover {
        background: rgba(0, 255, 255, 0.08) !important;
        border-color: rgba(0, 255, 255, 0.2) !important;
        color: rgba(255, 255, 255, 0.95) !important;
        transform: translateX(2px) !important;
        box-shadow: 0 4px 20px rgba(0, 255, 255, 0.1) !important;
    }
    
    .stButton > button:focus:not(:active) {
        background: rgba(0, 255, 255, 0.1) !important;
        border-color: rgba(0, 255, 255, 0.3) !important;
        color: rgba(255, 255, 255, 0.95) !important;
        box-shadow: 0 0 0 3px rgba(0, 255, 255, 0.15) !important;
    }
    
    /* Main content area styling */
    .main .block-container {
        max-width: 1200px;
        padding: 32px 24px;
    }
    
    /* Page headers */
    .aurora-page-header {
        margin-bottom: 32px;
        padding-bottom: 16px;
        border-bottom: 1px solid rgba(255, 255, 255, 0.05);
    }
    
    .aurora-page-title {
        font-size: 2.5rem;
        font-weight: 700;
        color: rgba(255, 255, 255, 0.95);
        margin-bottom: 8px;
        letter-spacing: -0.02em;
        line-height: 1.2;
    }
    
    .aurora-page-subtitle {
        color: rgba(255, 255, 255, 0.6);
        font-size: 1.1rem;
        font-weight: 400;
        line-height: 1.5;
    }
    
    /* Control sections */
    .aurora-section {
        background: rgba(255, 255, 255, 0.02);
        backdrop-filter: blur(16px) saturate(180%);
        border: 1px solid rgba(0, 255, 255, 0.08);
        border-radius: 16px;
        padding: 24px;
        margin-bottom: 24px;
        position: relative;
        overflow: hidden;
    }
    
    .aurora-section::before {
        content: "";
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 1px;
        background: linear-gradient(90deg, transparent, rgba(0, 255, 255, 0.3), transparent);
        animation: aurora-scan 8s ease-in-out infinite;
    }
    
    .aurora-section-title {
        font-size: 1.1rem;
        font-weight: 600;
        color: rgba(255, 255, 255, 0.9);
        margin-bottom: 16px;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    
    /* Enhanced form controls */
    .stSelectbox > div > div > div {
        background: rgba(255, 255, 255, 0.03) !important;
        border: 1px solid rgba(0, 255, 255, 0.1) !important;
        border-radius: 8px !important;
        color: rgba(255, 255, 255, 0.95) !important;
        backdrop-filter: blur(8px) !important;
    }
    
    .stSelectbox > div > div > div:focus-within {
        border-color: rgba(0, 255, 255, 0.4) !important;
        box-shadow: 0 0 0 3px rgba(0, 255, 255, 0.1) !important;
    }
    
    .stMultiSelect > div > div > div {
        background: rgba(255, 255, 255, 0.03) !important;
        border: 1px solid rgba(0, 255, 255, 0.1) !important;
        border-radius: 8px !important;
        color: rgba(255, 255, 255, 0.95) !important;
    }
    
    .stFileUploader > div > div {
        background: rgba(255, 255, 255, 0.015) !important;
        border: 2px dashed rgba(0, 255, 255, 0.2) !important;
        border-radius: 12px !important;
        padding: 24px !important;
        text-align: center !important;
        transition: all 0.3s ease !important;
    }
    
    .stFileUploader > div > div:hover {
        border-color: rgba(0, 255, 255, 0.4) !important;
        background: rgba(255, 255, 255, 0.025) !important;
    }
    
    /* Animations */
    @keyframes aurora-flow {
        0%, 100% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
    }
    
    @keyframes aurora-scan {
        0%, 100% { left: -100%; }
        50% { left: 100%; }
    }
    
    @keyframes aurora-pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.6; }
    }
    
    /* Mobile responsive */
    @media (max-width: 768px) {
        .aurora-header-content {
            padding: 0 16px;
        }
        
        .aurora-logo {
            font-size: 1.25rem;
        }
        
        .aurora-page-title {
            font-size: 2rem;
        }
        
        .main .block-container {
            padding: 24px 16px;
        }
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Modern header
    user_email = st.session_state.get("user_email", "user@example.com")
    st.markdown(f"""
    <div class="aurora-modern-header">
        <div class="aurora-header-content">
            <div class="aurora-logo">WhisperForge</div>
            <div class="aurora-user-info">
                <div class="aurora-status-dot"></div>
                <span>{user_email}</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Use Streamlit's sidebar properly
    with st.sidebar:
        st.markdown('<div class="aurora-nav-header">MAIN</div>', unsafe_allow_html=True)
        
        # Navigation buttons
        if st.button("🏠 Home", key="nav_home"):
            st.session_state.current_page = "Home"
            st.rerun()
        
        if st.button("📊 Analytics", key="nav_analytics"):
            st.info("📊 Advanced analytics coming soon!")
        
        if st.button("📁 Projects", key="nav_projects"):
            st.info("📁 Project management coming soon!")
        
        st.markdown('<div class="aurora-nav-header">CONTENT</div>', unsafe_allow_html=True)
        
        if st.button("📝 History", key="nav_history"):
            st.session_state.current_page = "Content History"
            st.rerun()
        
        if st.button("💡 Insights", key="nav_insights"):
            st.info("💡 Advanced insights coming soon!")
        
        if st.button("🖼️ Images", key="nav_images"):
            st.info("🖼️ Image gallery coming soon!")
        
        st.markdown('<div class="aurora-nav-header">SETTINGS</div>', unsafe_allow_html=True)
        
        if st.button("⚙️ Configuration", key="nav_settings"):
            st.session_state.current_page = "Settings"
            st.rerun()
        
        if st.button("🔑 API Keys", key="nav_api_keys"):
            st.session_state.current_page = "Settings"
            st.rerun()
        
        if st.button("❤️ Health", key="nav_health"):
            st.session_state.current_page = "System Health"
            st.rerun()
        
        # Sign out section
        st.markdown('<div class="aurora-nav-header">ACCOUNT</div>', unsafe_allow_html=True)
        if st.button("🚪 Sign Out", key="nav_signout"):
            # Clear session state
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.session_state.authenticated = False
            st.rerun()
    
    # Route to appropriate page
    current_page = st.session_state.get("current_page", "Home")
    
    if current_page == "Home":
        show_home_page()
    elif current_page == "Content History":
        show_content_history_page()
    elif current_page == "Settings":
        show_settings_page()
    elif current_page == "System Health":
        show_health_page()
    else:
        show_home_page()  # Default fallback

def show_home_page():
    """Modern home page with integrated progress tracking and enhanced interactions"""
    
    # Page Header
    st.markdown("""
    <div class="aurora-page-header">
        <h1 class="aurora-page-title">Content Pipeline</h1>
        <p class="aurora-page-subtitle">Transform your audio content into structured, actionable insights with AI-powered analysis.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Initialize progress tracker in session state for persistence
    if 'progress_tracker' not in st.session_state:
        st.session_state.progress_tracker = None
        st.session_state.processing_active = False
        st.session_state.processing_results = None
    
    # AI Configuration Section
    st.markdown("""
    <div class="aurora-section">
        <div class="aurora-section-title">
            <span>⚡</span>
            AI Configuration
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # AI Provider and Model Selection in a clean grid
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
    
    # Pipeline Configuration
    st.markdown("""
    <div class="aurora-section">
        <div class="aurora-section-title">
            <span>🔄</span>
            Pipeline Configuration
        </div>
    </div>
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
    
    # File Upload Section with enhanced styling
    st.markdown("""
    <div class="aurora-section">
        <div class="aurora-section-title">
            <span>📁</span>
            Upload Audio Content
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    uploaded_file = st.file_uploader(
        "Choose audio file",
        type=['mp3', 'wav', 'm4a', 'flac', 'mp4'],
        key="main_file_upload",
        help="Supports MP3, WAV, M4A, FLAC, and MP4 files up to 25MB"
    )
    
    # Processing Section with integrated progress tracking
    if uploaded_file is not None:
        # File info display
        file_size_mb = len(uploaded_file.getvalue()) / (1024 * 1024)
        st.success(f"✅ File uploaded: **{uploaded_file.name}** ({file_size_mb:.2f} MB)")
        
        # Processing control section
        st.markdown("""
        <div class="aurora-section">
            <div class="aurora-section-title">
                <span>🚀</span>
                Processing Control
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Create columns for processing controls
        proc_col1, proc_col2, proc_col3 = st.columns([2, 1, 1])
        
        with proc_col1:
            # Main processing button with enhanced styling
            processing_disabled = st.session_state.processing_active
            button_text = "🔄 Processing..." if processing_disabled else "🚀 Start Processing"
            
            if st.button(button_text, 
                        type="primary", 
                        use_container_width=True, 
                        disabled=processing_disabled,
                        key="process_button"):
                st.session_state.processing_active = True
                st.session_state.processing_results = None
                st.rerun()
        
        with proc_col2:
            if st.session_state.processing_active and st.button("⏹️ Stop", use_container_width=True):
                st.session_state.processing_active = False
                st.session_state.progress_tracker = None
                st.rerun()
        
        with proc_col3:
            if st.session_state.processing_results and st.button("🔄 Reset", use_container_width=True):
                st.session_state.processing_active = False
                st.session_state.progress_tracker = None
                st.session_state.processing_results = None
                st.rerun()
        
        # Progress Tracking Section - Always visible when processing
        if st.session_state.processing_active:
            st.markdown("""
            <div class="aurora-section">
                <div class="aurora-section-title">
                    <span>📊</span>
                    Processing Progress
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Create and manage progress tracker
            if st.session_state.progress_tracker is None:
                from core.progress import create_whisperforge_progress_tracker
                st.session_state.progress_tracker = create_whisperforge_progress_tracker()
                st.session_state.progress_tracker.create_display_container()
            
            # Process the file with real-time updates
            try:
                results = process_audio_pipeline_with_progress(uploaded_file, st.session_state.progress_tracker)
                if results:
                    st.session_state.processing_results = results
                    st.session_state.processing_active = False
                    st.rerun()
            except Exception as e:
                st.error(f"❌ Processing failed: {str(e)}")
                st.session_state.processing_active = False
                st.session_state.progress_tracker = None
                st.rerun()
        
        # Results Section - Show when processing is complete
        if st.session_state.processing_results:
            show_processing_results(st.session_state.processing_results)
    
    else:
        # Welcome section with enhanced features showcase
        st.markdown("""
        <div class="aurora-section">
            <div class="aurora-section-title">
                <span>🌟</span>
                Welcome to WhisperForge
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Feature showcase with beautiful styling
        st.markdown("""
        <div class="aurora-features-grid">
            <div class="aurora-feature-card">
                <div class="aurora-feature-icon">🧠</div>
                <div class="aurora-feature-title">Smart Content Extraction</div>
                <div class="aurora-feature-desc">AI identifies key insights and wisdom from your audio with advanced language understanding</div>
            </div>
            
            <div class="aurora-feature-card">
                <div class="aurora-feature-icon">📋</div>
                <div class="aurora-feature-title">Structured Outlines</div>
                <div class="aurora-feature-desc">Organized content ready for presentations, articles, or educational material</div>
            </div>
            
            <div class="aurora-feature-card">
                <div class="aurora-feature-icon">📱</div>
                <div class="aurora-feature-title">Social Media Ready</div>
                <div class="aurora-feature-desc">Platform-optimized content for maximum engagement across all social networks</div>
            </div>
            
            <div class="aurora-feature-card">
                <div class="aurora-feature-icon">🎨</div>
                <div class="aurora-feature-title">Image Prompts</div>
                <div class="aurora-feature-desc">AI-generated prompts for creating compelling visual content with DALL-E, Midjourney, or Stable Diffusion</div>
            </div>
            
            <div class="aurora-feature-card">
                <div class="aurora-feature-icon">☁️</div>
                <div class="aurora-feature-title">Cloud Storage</div>
                <div class="aurora-feature-desc">All content automatically saved and accessible from anywhere, anytime</div>
            </div>
            
            <div class="aurora-feature-card">
                <div class="aurora-feature-icon">🔒</div>
                <div class="aurora-feature-title">Secure Processing</div>
                <div class="aurora-feature-desc">Your data is encrypted and protected with enterprise-grade security</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Add enhanced feature card styling
        st.markdown("""
        <style>
        .aurora-features-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin: 24px 0;
        }
        
        .aurora-feature-card {
            background: rgba(255, 255, 255, 0.02);
            backdrop-filter: blur(16px) saturate(180%);
            border: 1px solid rgba(0, 255, 255, 0.08);
            border-radius: 16px;
            padding: 24px;
            text-align: center;
            transition: all 0.4s cubic-bezier(0.4, 0.0, 0.2, 1);
            position: relative;
            overflow: hidden;
        }
        
        .aurora-feature-card::before {
            content: "";
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 1px;
            background: linear-gradient(90deg, transparent, rgba(0, 255, 255, 0.4), transparent);
            animation: aurora-scan 8s ease-in-out infinite;
            animation-delay: calc(var(--card-index, 0) * 0.5s);
        }
        
        .aurora-feature-card:hover {
            border-color: rgba(0, 255, 255, 0.2);
            transform: translateY(-4px);
            box-shadow: 0 8px 32px rgba(0, 255, 255, 0.1);
        }
        
        .aurora-feature-icon {
            font-size: 2.5rem;
            margin-bottom: 16px;
            filter: drop-shadow(0 0 8px rgba(0, 255, 255, 0.3));
        }
        
        .aurora-feature-title {
            font-size: 1.1rem;
            font-weight: 600;
            color: rgba(255, 255, 255, 0.95);
            margin-bottom: 12px;
        }
        
        .aurora-feature-desc {
            color: rgba(255, 255, 255, 0.7);
            line-height: 1.5;
            font-size: 0.9rem;
        }
        
        @keyframes aurora-scan {
            0%, 100% { left: -100%; }
            50% { left: 100%; }
        }
        </style>
        """, unsafe_allow_html=True)
        
        st.info("👆 **Upload an audio file above to get started** with AI-powered content transformation!")


def process_audio_pipeline_with_progress(audio_file, progress_tracker):
    """Enhanced audio processing with real-time progress updates"""
    
    try:
        # Step 1: Upload Validation
        with progress_tracker.step_context("upload_validation"):
            file_size_mb = len(audio_file.getvalue()) / (1024 * 1024)
            if file_size_mb > 25:
                raise Exception(f"File too large: {file_size_mb:.1f}MB (max 25MB)")
            time.sleep(0.5)  # Validation simulation
        
        # Step 2: Transcription
        with progress_tracker.step_context("transcription"):
            transcript = transcribe_audio(audio_file)
            if not transcript:
                raise Exception("Failed to transcribe audio - transcript is empty")
            st.session_state.transcription = transcript
        
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
                    "file_size": len(audio_file.getvalue()),
                    "created_at": datetime.now().isoformat()
                }
            }
            
            content_id = save_generated_content_supabase(content_data)
            if not content_id:
                raise Exception("Failed to save content to database")
            time.sleep(0.3)
        
        return {
            'transcript': transcript,
            'wisdom': wisdom,
            'outline': outline,
            'social': social,
            'images': images
        }
        
    except Exception as e:
        st.error(f"Processing failed: {str(e)}")
        return None


def show_processing_results(results):
    """Display processing results with beautiful aurora-themed cards"""
    
    st.markdown("""
    <div class="aurora-section">
        <div class="aurora-section-title">
            <span>✨</span>
            Generated Content
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.success("🎉 Processing completed successfully! Your content is ready.")
    
    # Create tabs for different result types
    tab1, tab2, tab3, tab4 = st.tabs([
        "💎 Wisdom & Insights", 
        "📋 Content Outline", 
        "📱 Social Media", 
        "🖼️ Image Prompts"
    ])
    
    with tab1:
        if 'wisdom' in results:
            import html
            wisdom_escaped = html.escape(results['wisdom'])
            st.markdown(f"""
            <div class="aurora-content-card">
                <div class="aurora-content-header">
                    <span class="aurora-content-title">Key Insights & Wisdom</span>
                </div>
                <div class="aurora-content-body">
                    {wisdom_escaped.replace(chr(10), '<br>')}
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("📋 Copy to Clipboard", key="copy_wisdom"):
                st.code(results['wisdom'], language="markdown")
    
    with tab2:
        if 'outline' in results:
            import html
            outline_escaped = html.escape(results['outline'])
            st.markdown(f"""
            <div class="aurora-content-card">
                <div class="aurora-content-header">
                    <span class="aurora-content-title">Structured Content Outline</span>
                </div>
                <div class="aurora-content-body">
                    {outline_escaped.replace(chr(10), '<br>')}
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("📋 Copy to Clipboard", key="copy_outline"):
                st.code(results['outline'], language="markdown")
    
    with tab3:
        if 'social' in results:
            import html
            social_escaped = html.escape(results['social'])
            st.markdown(f"""
            <div class="aurora-content-card">
                <div class="aurora-content-header">
                    <span class="aurora-content-title">Social Media Content</span>
                </div>
                <div class="aurora-content-body">
                    {social_escaped.replace(chr(10), '<br>')}
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("📋 Copy to Clipboard", key="copy_social"):
                st.code(results['social'], language="markdown")
    
    with tab4:
        if 'images' in results:
            import html
            images_escaped = html.escape(results['images'])
            st.markdown(f"""
            <div class="aurora-content-card">
                <div class="aurora-content-header">
                    <span class="aurora-content-title">AI Image Generation Prompts</span>
                </div>
                <div class="aurora-content-body">
                    {images_escaped.replace(chr(10), '<br>')}
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("📋 Copy to Clipboard", key="copy_images"):
                st.code(results['images'], language="markdown")
    
    # Add enhanced content card styling
    st.markdown("""
    <style>
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
    
    .aurora-content-card:hover {
        border-color: rgba(0, 255, 255, 0.25);
        transform: translateY(-2px);
        box-shadow: 0 8px 32px rgba(0, 255, 255, 0.1);
    }
    
    .aurora-content-header {
        margin-bottom: 16px;
        padding-bottom: 12px;
        border-bottom: 1px solid rgba(0, 255, 255, 0.1);
    }
    
    .aurora-content-title {
        font-size: 1.1rem;
        font-weight: 600;
        color: rgba(255, 255, 255, 0.95);
    }
    
    .aurora-content-body {
        color: rgba(255, 255, 255, 0.85);
        line-height: 1.6;
        font-size: 0.95rem;
    }
    </style>
    """, unsafe_allow_html=True)

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