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
    transcribe_audio, generate_wisdom, generate_outline, generate_article,
    generate_social_content, generate_image_prompts, editor_critique
)
from core.styling import apply_aurora_theme, create_aurora_header, AuroraComponents
from core.monitoring import (
    init_monitoring, track_error, track_performance, track_user_action, 
    get_health_status, init_session_tracking
)
# Removed old progress tracker imports - using simple progress bars now
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
            
        result = db.client.table("api_keys").select("key_name, key_value").eq("user_id", st.session_state.user_id).execute()
        
        keys = {}
        for item in result.data:
            keys[item["key_name"]] = item["key_value"]
        
        return keys
    except Exception as e:
        logger.error(f"Error getting API keys: {e}")
        return {}

def update_api_key_supabase(key_name: str, key_value: str) -> bool:
    """Update/insert API key for user"""
    try:
        db, _ = init_supabase()
        if not db:
            return False
            
        # Upsert the key
        result = db.client.table("api_keys").upsert({
            "user_id": st.session_state.user_id,
            "key_name": key_name,
            "key_value": key_value,
            "updated_at": "now()"
        }).execute()
        
        return bool(result.data)
    except Exception as e:
        logger.error(f"Error updating API key: {e}")
        return False

def get_user_prompts_supabase() -> dict:
    """Get user custom prompts"""
    try:
        db, _ = init_supabase()
        if not db:
            return DEFAULT_PROMPTS
            
        result = db.client.table("prompts").select("prompt_type, content").eq("user_id", st.session_state.user_id).execute()
        
        prompts = DEFAULT_PROMPTS.copy()
        for item in result.data:
            prompts[item["prompt_type"]] = item["content"]
        
        return prompts
    except Exception as e:
        logger.error(f"Error getting prompts: {e}")
        return DEFAULT_PROMPTS

def save_user_prompt_supabase(prompt_type: str, content: str) -> bool:
    """Save user custom prompt"""
    try:
        db, _ = init_supabase()
        if not db:
            return False
            
        result = db.client.table("prompts").upsert({
            "user_id": st.session_state.user_id,
            "prompt_type": prompt_type,
            "content": content,
            "updated_at": "now()"
        }).execute()
        
        return bool(result.data)
    except Exception as e:
        logger.error(f"Error saving prompt: {e}")
        return False

def get_user_knowledge_base_supabase() -> dict:
    """Get user knowledge base files"""
    try:
        db, _ = init_supabase()
        if not db:
            return {}
            
        result = db.client.table("knowledge_base").select("filename, content").eq("user_id", st.session_state.user_id).execute()
        
        kb = {}
        for item in result.data:
            kb[item["filename"]] = item["content"]
        
        return kb
    except Exception as e:
        logger.error(f"Error getting knowledge base: {e}")
        return {}

def save_knowledge_base_file_supabase(filename: str, content: str) -> bool:
    """Save knowledge base file"""
    try:
        db, _ = init_supabase()
        if not db:
            return False
            
        result = db.client.table("knowledge_base").upsert({
            "user_id": st.session_state.user_id,
            "filename": filename,
            "content": content,
            "updated_at": "now()"
        }).execute()
        
        return bool(result.data)
    except Exception as e:
        logger.error(f"Error saving knowledge base file: {e}")
        return False

def save_generated_content_supabase(content_data: dict) -> str:
    """Save generated content to database"""
    try:
        db, _ = init_supabase()
        if not db:
            return ""
            
        result = db.client.table("generated_content").insert({
            "user_id": st.session_state.user_id,
            "content_data": content_data,
            "created_at": "now()"
        }).execute()
        
        return result.data[0]["id"] if result.data else ""
    except Exception as e:
        logger.error(f"Error saving content: {e}")
        return ""

def get_user_content_history_supabase(limit: int = 20) -> list:
    """Get user content history"""
    try:
        db, _ = init_supabase()
        if not db:
            return []
            
        result = db.client.table("generated_content")\
            .select("id, content_data, created_at")\
            .eq("user_id", st.session_state.user_id)\
            .order("created_at", desc=True)\
            .limit(limit)\
            .execute()
        
        return result.data
    except Exception as e:
        logger.error(f"Error getting content history: {e}")
        return []

def log_pipeline_execution_supabase(pipeline_data: dict) -> bool:
    """Log pipeline execution"""
    try:
        db, _ = init_supabase()
        if not db:
            return False
            
        result = db.client.table("pipeline_logs").insert({
            "user_id": st.session_state.user_id,
            "pipeline_data": pipeline_data,
            "created_at": "now()"
        }).execute()
        
        return bool(result.data)
    except Exception as e:
        logger.error(f"Error logging pipeline: {e}")
        return False

def handle_oauth_callback():
    """Handle OAuth callback from Supabase"""
    query_params = st.query_params
    
    # Only process if we have OAuth parameters (need both code and state for proper OAuth flow)
    if 'code' in query_params and not st.session_state.get('authenticated', False):
        # Add debug info to sidebar
        st.sidebar.write(f"Debug - Processing OAuth callback")
        st.sidebar.write(f"Debug - Code received: {query_params['code'][:20]}...")
        
        try:
            db, _ = init_supabase()
            if db:
                code = query_params['code']
                
                # Proper Supabase OAuth exchange - use the correct method
                try:
                    # Try the session exchange first (recommended for web apps)
                    response = db.client.auth.exchange_code_for_session({
                        "auth_code": code
                    })
                except:
                    # Fallback to the alternative method
                    response = db.client.auth.exchange_code_for_session(code)
                
                if response and hasattr(response, 'user') and response.user:
                    # Get or create user in our database
                    user_email = response.user.email
                    user_id = response.user.id
                    
                    st.sidebar.write(f"Debug - OAuth user: {user_email}")
                    
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
                            st.sidebar.error("Failed to create user record")
                            return False
                    else:
                        st.session_state.user_id = existing_user.data[0]["id"]
                    
                    # Set authentication state
                    st.session_state.authenticated = True
                    st.session_state.user_email = user_email
                    
                    st.sidebar.write("Debug - Authentication state set successfully")
                    
                    # Clear OAuth parameters to prevent re-processing
                    st.query_params.clear()
                    
                    # Show success message in main area
                    st.success("✅ Successfully signed in with Google! Redirecting...")
                    
                    # Force rerun to show main app
                    time.sleep(1)
                    st.rerun()
                    return True
                else:
                    st.sidebar.error("Failed to get user from OAuth response")
                    if response:
                        st.sidebar.write(f"Debug - Response type: {type(response)}")
                    return False
                    
        except Exception as e:
            st.sidebar.error(f"OAuth error: {str(e)}")
            import traceback
            st.sidebar.write(f"Debug - Full error: {traceback.format_exc()}")
            return False
    
    return False

def show_auth_page():
    """Clean, modern authentication page"""
    
    # Load the stable CSS framework
    try:
        from core.ui_components import load_aurora_css
        load_aurora_css()
    except:
        # Fallback CSS if ui_components not available
        st.markdown("""
        <style>
        /* Clean auth page */
        .stApp {
            background: linear-gradient(180deg, #0a0f1c 0%, #0d1421 100%);
            font-family: -apple-system, BlinkMacSystemFont, system-ui, sans-serif;
        }
        
        /* Remove default padding */
        .main .block-container {
            padding-top: 2rem !important;
            padding-bottom: 2rem !important;
            max-width: 500px !important;
            margin: 0 auto !important;
        }
        
        /* Auth card styling */
        .auth-card {
            background: rgba(255, 255, 255, 0.02);
            border: 1px solid rgba(0, 255, 255, 0.1);
            border-radius: 12px;
            padding: 2rem;
            backdrop-filter: blur(16px);
        }
        
        .auth-logo {
            font-size: 2.5rem;
            font-weight: 700;
            color: #00FFFF;
            text-align: center;
            margin-bottom: 0.5rem;
            text-shadow: 0 0 20px rgba(0, 255, 255, 0.3);
        }
        
        .auth-tagline {
            color: rgba(255, 255, 255, 0.7);
            text-align: center;
            margin-bottom: 2rem;
            font-size: 1.1rem;
        }
        
        /* Clean button styling */
        .stButton > button {
            width: 100% !important;
            background: linear-gradient(135deg, rgba(0, 255, 255, 0.1), rgba(64, 224, 208, 0.15)) !important;
            border: 1px solid rgba(0, 255, 255, 0.2) !important;
            color: white !important;
            border-radius: 8px !important;
            padding: 12px !important;
            font-weight: 500 !important;
        }
        
        .stButton > button:hover {
            background: linear-gradient(135deg, rgba(0, 255, 255, 0.15), rgba(64, 224, 208, 0.2)) !important;
            border-color: rgba(0, 255, 255, 0.3) !important;
        }
        
        .stTextInput > div > div > input {
            background: rgba(255, 255, 255, 0.05) !important;
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
            border-radius: 8px !important;
            color: white !important;
        }
        
        .stTextInput > div > div > input:focus {
            border-color: rgba(0, 255, 255, 0.4) !important;
        }
        </style>
        """, unsafe_allow_html=True)
    
    # Center the auth form
    st.markdown('<div class="auth-card">', unsafe_allow_html=True)
    
    # Logo and tagline - FIXED HEADER
    st.markdown('<div class="auth-logo">WhisperForge</div>', unsafe_allow_html=True)
    st.markdown('<div class="auth-tagline">Transform audio into structured content</div>', unsafe_allow_html=True)
    
    # Handle OAuth callback first
    if handle_oauth_callback():
        st.markdown('</div>', unsafe_allow_html=True)
        return
    
    # Generate OAuth URL
    if 'oauth_url' not in st.session_state:
        try:
            db, _ = init_supabase()
            if db:
                import os
                redirect_url = os.getenv("OAUTH_REDIRECT_URL")
                
                if not redirect_url:
                    # For local development, use the current port
                    redirect_url = "http://localhost:8501"
                
                if redirect_url:
                    # Proper Supabase OAuth URL generation
                    auth_response = db.client.auth.sign_in_with_oauth({
                        "provider": "google",
                        "options": {
                            "redirect_to": redirect_url,
                            "query_params": {
                                "access_type": "offline",
                                "prompt": "consent"
                            }
                        }
                    })
                    
                    if hasattr(auth_response, 'url') and auth_response.url:
                        st.session_state.oauth_url = auth_response.url
                    else:
                        st.session_state.oauth_url = None
                else:
                    st.session_state.oauth_url = None
        except Exception as e:
            # Only show error if it's a real OAuth configuration issue
            if "oauth" in str(e).lower() or "google" in str(e).lower():
                st.warning("Google sign-in temporarily unavailable. Use email login below.")
            st.session_state.oauth_url = None
    
    # OAuth button
    if st.session_state.get('oauth_url'):
        st.link_button("Continue with Google", st.session_state.oauth_url, type="primary", use_container_width=True)
    else:
        if st.button("Continue with Google", type="primary", use_container_width=True):
            st.error("Failed to generate Google sign-in URL. Please check your configuration.")
    
    # Divider
    st.markdown("---")
    st.markdown("<div style='text-align: center; color: rgba(255,255,255,0.5);'>or</div>", unsafe_allow_html=True)
    st.markdown("---")
    
    # Email authentication tabs
    tab1, tab2 = st.tabs(["Sign In", "Create Account"])
    
    with tab1:
        st.markdown("#### Welcome back")
        
        email = st.text_input("Email", placeholder="Enter your email", key="signin_email")
        password = st.text_input("Password", type="password", placeholder="Enter your password", key="signin_password")
        
        if st.button("Sign In", type="primary", use_container_width=True):
            if not email or not password:
                st.error("Please enter both email and password")
            elif authenticate_user_supabase(email, password):
                st.success("Welcome back!")
                st.rerun()
            else:
                st.error("Invalid credentials")
    
    with tab2:
        st.markdown("#### Create your account")
        
        email = st.text_input("Email", placeholder="Enter your email", key="register_email")
        password = st.text_input("Password", type="password", placeholder="Create a password", key="register_password")
        password_confirm = st.text_input("Confirm Password", type="password", placeholder="Confirm your password", key="register_password_confirm")
        
        if st.button("Create Account", type="primary", use_container_width=True):
            if not email or not password:
                st.error("Please enter both email and password")
            elif len(password) < 6:
                st.error("Password must be at least 6 characters")
            elif password != password_confirm:
                st.error("Passwords don't match")
            elif register_user_supabase(email, password):
                st.success("Account created! Please sign in.")
                # Clear form
                st.session_state.register_email = ""
                st.session_state.register_password = ""
                st.session_state.register_password_confirm = ""
            else:
                st.error("Error creating account")
    
    st.markdown('</div>', unsafe_allow_html=True)

def _generate_nav_buttons():
    """Generate navigation buttons for header"""
    pages = [
        ("Processing", ""),
        ("History", ""), 
        ("Settings", ""),
        ("Status", "")
    ]
    
    current_page = st.session_state.get('current_page', 'Content Pipeline')
    
    # Create column layout for buttons
    cols = st.columns(len(pages))
    
    for i, (page, icon) in enumerate(pages):
        with cols[i]:
            # Map new names to old page names for compatibility
            page_mapping = {
                "Processing": "Content Pipeline",
                "History": "Content History", 
                "Settings": "Settings",
                "Status": "Health Check"
            }
            if st.button(page, key=f"nav_{page}", 
                        type="primary" if page_mapping[page] == current_page else "secondary",
                        use_container_width=True):
                st.session_state.current_page = page_mapping[page]
                st.rerun()
    
    return ""  # Return empty string since we're using Streamlit buttons

def show_main_app():
    """Main application with clean layout"""
    
    # Initialize session state
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "Content Pipeline"
    if 'ai_provider' not in st.session_state:
        st.session_state.ai_provider = "OpenAI"
    if 'ai_model' not in st.session_state:
        st.session_state.ai_model = "gpt-4o"
    
    # Load user prompts on app initialization
    if 'prompts' not in st.session_state:
        st.session_state.prompts = get_user_prompts_supabase()
    
    # Load knowledge base on app initialization
    if 'knowledge_base' not in st.session_state:
        st.session_state.knowledge_base = get_user_knowledge_base_supabase()
    
    # Check for page navigation via query params
    query_params = st.query_params
    if 'page' in query_params:
        page = query_params['page'].replace('_', ' ')
        if page in ["Content Pipeline", "Content History", "Settings", "Health Check"]:
            st.session_state.current_page = page
            # Clear the query param after processing
            st.query_params.clear()
    
    # Load user data
    st.session_state.prompts = get_user_prompts_supabase()
    st.session_state.knowledge_base = get_user_knowledge_base_supabase()
    
    # Clean main app styling
    st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(180deg, #0a0f1c 0%, #0d1421 100%);
        font-family: -apple-system, BlinkMacSystemFont, system-ui, sans-serif;
    }
    
    /* Clean header */
    .main-header {
        background: rgba(255, 255, 255, 0.02);
        border-bottom: 1px solid rgba(0, 255, 255, 0.1);
        padding: 1rem;
        margin-bottom: 2rem;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    
    .logo {
        font-size: 1.5rem;
        font-weight: 700;
        color: #00FFFF;
    }
    
    .user-info {
        color: rgba(255, 255, 255, 0.7);
        font-size: 0.9rem;
    }
    
    /* Clean navigation */
    .stButton > button {
        width: 100% !important;
        background: rgba(255, 255, 255, 0.02) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        color: rgba(255, 255, 255, 0.8) !important;
        border-radius: 8px !important;
        text-align: left !important;
        margin-bottom: 4px !important;
    }
    
    .stButton > button:hover {
        background: rgba(0, 255, 255, 0.08) !important;
        border-color: rgba(0, 255, 255, 0.2) !important;
        color: white !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Enhanced Header with Aurora Navigation
    st.markdown("""
    <style>
    .aurora-logo {
        font-size: 2.2rem;
        font-weight: 700;
        background: linear-gradient(120deg, #00FFFF, #7DF9FF, #40E0D0);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        text-shadow: 0 0 30px rgba(0, 255, 255, 0.4);
        text-align: center;
        margin-bottom: 16px;
        position: relative;
    }
    
    .aurora-logo::after {
        content: "";
        position: absolute;
        bottom: -4px;
        left: 50%;
        transform: translateX(-50%);
        width: 60%;
        height: 2px;
        background: linear-gradient(90deg, transparent, #00FFFF, #40E0D0, transparent);
        animation: aurora-scan 4s ease-in-out infinite;
    }
    
    .aurora-status {
        text-align: center;
        color: rgba(255, 255, 255, 0.7);
        font-size: 0.9rem;
        margin-bottom: 20px;
        display: flex;
        justify-content: center;
        align-items: center;
        gap: 8px;
    }
    
    /* Enhanced button styling for navigation */
    .stButton > button {
        background: linear-gradient(135deg, rgba(0, 255, 255, 0.1), rgba(64, 224, 208, 0.15)) !important;
        border: 1px solid rgba(0, 255, 255, 0.2) !important;
        color: rgba(255, 255, 255, 0.9) !important;
        border-radius: 12px !important;
        padding: 12px !important;
        font-weight: 500 !important;
        transition: all 0.3s ease !important;
        font-size: 0.9rem !important;
    }
    
    .stButton > button:hover {
        background: linear-gradient(135deg, rgba(0, 255, 255, 0.15), rgba(64, 224, 208, 0.2)) !important;
        border-color: rgba(0, 255, 255, 0.3) !important;
        color: white !important;
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(0, 255, 255, 0.15);
    }
    
    /* Primary button styling for active nav */
    .stButton > button[data-baseweb="button"][aria-pressed="true"],
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, rgba(0, 255, 255, 0.2), rgba(64, 224, 208, 0.25)) !important;
        border-color: rgba(0, 255, 255, 0.4) !important;
        color: #00FFFF !important;
        box-shadow: 0 0 20px rgba(0, 255, 255, 0.2);
    }
    
    @keyframes aurora-scan {
        0%, 100% { left: -100%; }
        50% { left: 100%; }
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Logo and status
    st.markdown('<div class="aurora-logo">WhisperForge</div>', unsafe_allow_html=True)
    st.markdown('<div class="aurora-status"><span style="color: #00FF7F;">●</span> Authenticated</div>', unsafe_allow_html=True)
    
    # Navigation buttons
    _generate_nav_buttons()
    
    # Compact sidebar for sign out only
    with st.sidebar:
        st.markdown("---")
        if st.button("🚪 Sign Out", use_container_width=True):
            # Clear authentication
            st.session_state.authenticated = False
            st.session_state.user_id = None
            st.session_state.current_page = "Content Pipeline"
            st.rerun()
    
    # Show the selected page
    if st.session_state.current_page == "Content Pipeline":
        show_home_page()
    elif st.session_state.current_page == "Content History":
        show_content_history_page()
    elif st.session_state.current_page == "Settings":
        show_settings_page()
    elif st.session_state.current_page == "Health Check":
        show_health_page()

def show_home_page():
    """Clean, focused home page - COMPLETELY REBUILT"""
    
    # Initialize defaults
    if 'ai_provider' not in st.session_state:
        st.session_state.ai_provider = "OpenAI"
    if 'ai_model' not in st.session_state:
        st.session_state.ai_model = "gpt-4o"
    if 'editor_enabled' not in st.session_state:
        st.session_state.editor_enabled = False
    
    # Clean page header
    st.markdown("# Content Pipeline")
    st.markdown("Transform your audio content into structured, actionable insights")
    
    # Upload section
    st.markdown("### Upload Audio File")
    uploaded_file = st.file_uploader(
        "Choose audio file (MP3, WAV, M4A, FLAC, or MP4 - max 25MB)",
        type=['mp3', 'wav', 'm4a', 'flac', 'mp4'],
        key="main_file_upload"
    )
    
    # Editor toggle
    if uploaded_file is not None:
        st.markdown("---")
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown("**AI Editor:** Enhance content quality with AI review and revision")
        with col2:
            editor_enabled = st.toggle(
                "Enable", 
                value=st.session_state.get("editor_enabled", False),
                key="editor_toggle"
            )
            st.session_state.editor_enabled = editor_enabled
    
    # Processing section
    if uploaded_file is not None:
        # Import streaming components
        try:
            from core.streaming_pipeline import get_pipeline_controller
            from core.streaming_results import show_streaming_results, show_processing_status, STREAMING_RESULTS_CSS
            
            # Apply CSS
            st.markdown(STREAMING_RESULTS_CSS, unsafe_allow_html=True)
            
            controller = get_pipeline_controller()
            
            # File info
            file_size_mb = len(uploaded_file.getvalue()) / (1024 * 1024)
            st.info(f"**File:** {uploaded_file.name} ({file_size_mb:.2f} MB)")
            
            # Processing controls
            st.markdown("### Processing")
            
            col1, col2, col3 = st.columns([2, 1, 1])
            
            with col1:
                if not controller.is_active and not controller.is_complete:
                    if st.button("Start Processing", type="primary", use_container_width=True):
                        controller.start_pipeline(uploaded_file)
                        st.rerun()
                elif controller.is_active:
                    st.button("Processing...", type="primary", disabled=True, use_container_width=True)
                else:
                    st.button("Processing Complete", type="primary", disabled=True, use_container_width=True)
            
            with col2:
                if controller.is_active:
                    if st.button("Stop", use_container_width=True):
                        controller.reset_pipeline()
                        st.rerun()
            
            with col3:
                if controller.is_complete:
                    if st.button("Reset", use_container_width=True):
                        controller.reset_pipeline()
                        st.rerun()
            
            # Auto-process next step
            if controller.is_active:
                step_processed = controller.process_next_step()
                if step_processed:
                    st.rerun()
                elif not controller.is_active:
                    st.rerun()
            
            # Show status and results
            show_processing_status()
            show_streaming_results()
            
        except ImportError as e:
            st.error(f"Streaming pipeline not available: {e}")
            st.markdown("### Manual Processing")
            if st.button("Process Audio", type="primary"):
                with st.spinner("Processing..."):
                    try:
                        # Basic processing without streaming
                        transcript = transcribe_audio(uploaded_file)
                        if transcript:
                            st.success("Processing complete!")
                            st.text_area("Transcript", transcript, height=200)
                        else:
                            st.error("Failed to transcribe audio")
                    except Exception as e:
                        st.error(f"Processing error: {e}")
    
    else:
        # Welcome section
        st.markdown("---")
        st.markdown("### Key Features")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("""
            **Structured Outlines**  
            Organized content ready for publication
            """)
        
        with col2:
            st.markdown("""
            **Social Media Ready**  
            Platform-optimized content generation
            """)
        
        with col3:
            st.markdown("""
            **Image Prompts**  
            AI-generated prompts for visual content
            """)
        
        st.markdown("---")
        st.markdown("**Get started by uploading an audio file above.**")

def show_processing_results(results):
    """Display processing results in a clean format"""
    st.markdown("### Results")
    
    if not results:
        st.info("No results to display yet")
        return
    
    # Create tabs for different result types
    tabs = st.tabs(["Wisdom", "Outline", "Social Media", "Image Prompts"])
    
    with tabs[0]:
        if "wisdom_extraction" in results:
            st.markdown("#### Key Insights")
            st.markdown(results["wisdom_extraction"])
    
    with tabs[1]:
        if "outline_creation" in results:
            st.markdown("#### Content Outline")
            st.markdown(results["outline_creation"])
    
    with tabs[2]:
        if "social_media" in results:
            st.markdown("#### Social Media Content")
            st.markdown(results["social_media"])
    
    with tabs[3]:
        if "image_prompts" in results:
            st.markdown("#### Image Generation Prompts")
            st.markdown(results["image_prompts"])

def show_content_history_page():
    """Show user's content history with beautiful Aurora styling"""
    st.markdown("# 📋 Content History")
    st.markdown("Your generated content archive with transcripts, insights, and metadata")
    
    history = get_user_content_history_supabase()
    
    if not history:
        # Beautiful empty state
        st.markdown("""
        <div style="
            background: linear-gradient(135deg, rgba(0, 255, 255, 0.05), rgba(64, 224, 208, 0.08));
            border: 1px solid rgba(0, 255, 255, 0.15);
            border-radius: 16px;
            padding: 48px;
            text-align: center;
            margin: 32px 0;
        ">
            <div style="font-size: 3rem; margin-bottom: 16px; color: var(--aurora-primary);">♦</div>
            <h3 style="color: #00FFFF; margin-bottom: 8px;">No Content Yet</h3>
            <p style="color: rgba(255, 255, 255, 0.7); margin-bottom: 24px;">
                Process some audio files to see your transcripts, insights, and generated content here!
            </p>
            <p style="color: rgba(255, 255, 255, 0.5); font-size: 0.9rem;">
                Go to Content Pipeline to get started
            </p>
        </div>
        """, unsafe_allow_html=True)
        return
    
    # Show stats
    st.markdown(f"**Found {len(history)} content items**")
    
    # Display each item in beautiful Aurora containers
    for i, item in enumerate(history):
        # Parse creation date
        created_date = item.get('created_at', '')[:10] if item.get('created_at') else 'Unknown date'
        
        # Create Aurora content card
        with st.expander(f"✨ Content Generated on {created_date}", expanded=i==0):
            content_data = item.get("content_data", {})
            
            if isinstance(content_data, dict):
                # Metadata section
                if 'metadata' in content_data:
                    st.markdown("### Metadata")
                    metadata = content_data['metadata']
                    if isinstance(metadata, dict):
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("File Size", metadata.get('file_size', 'Unknown'))
                        with col2:
                            st.metric("Duration", metadata.get('duration', 'Unknown'))
                        with col3:
                            st.metric("AI Model", metadata.get('ai_model', 'Unknown'))
                
                # Display each content type in its own section
                # Map both old and new column names for backward compatibility
                content_sections = {
                            'transcript': ('♦', 'Audio Transcription', 'The original speech-to-text conversion'),
        'transcription': ('♦', 'Audio Transcription', 'The original speech-to-text conversion'),
                    'wisdom_extraction': ('◆', 'Key Insights & Wisdom', 'Extracted insights and takeaways'),
                    'outline_creation': ('◇', 'Content Outline', 'Structured organization and flow'),
                    'article': ('◈', 'Full Article', 'Complete written content'),
                    'article_creation': ('◈', 'Full Article', 'Complete written content'),
                    'social_media': ('◉', 'Social Media Posts', 'Platform-optimized content'),
                    'social_content': ('◉', 'Social Media Posts', 'Platform-optimized content'),
                    'image_prompts': ('◎', 'Image Generation Prompts', 'AI-generated visual concepts')
                }
                
                for section_key, (icon, title, description) in content_sections.items():
                    if section_key in content_data and content_data[section_key]:
                        content = content_data[section_key]
                        
                        # Aurora content section
                        st.markdown(f"""
                        <div style="
                            background: linear-gradient(135deg, rgba(0, 255, 255, 0.03), rgba(64, 224, 208, 0.05));
                            border: 1px solid rgba(0, 255, 255, 0.1);
                            border-radius: 12px;
                            padding: 20px;
                            margin: 16px 0;
                        ">
                            <h4 style="color: #00FFFF; margin-bottom: 8px;">{icon} {title}</h4>
                            <p style="color: rgba(255, 255, 255, 0.6); font-size: 0.9rem; margin-bottom: 16px;">{description}</p>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Show content with copy functionality
                        if len(str(content)) > 500:
                            # Show preview for long content
                            st.markdown(f"**Preview:** {str(content)[:300]}...")
                            if st.button(f"Show Full {title}", key=f"show_{section_key}_{i}"):
                                st.text_area(f"Full {title}", content, height=200, key=f"full_{section_key}_{i}")
                        else:
                            st.markdown(content)
                        
                        # Copy button
                        if st.button(f"Copy {title}", key=f"copy_{section_key}_{i}", help=f"Copy {title} to clipboard"):
                            st.code(content, language="markdown")
                        
                        st.markdown("---")
            else:
                # Fallback for non-dict content
                st.markdown("### Raw Content")
                st.markdown(str(content_data))

def show_settings_page():
    """Settings page with clean layout"""
    st.markdown("# Settings")
    
    tab1, tab2, tab3, tab4 = st.tabs(["AI Provider", "API Keys", "Custom Prompts", "Knowledge Base"])
    
    with tab1:
        st.markdown("#### AI Provider Settings")
        
        # Provider selection
        provider = st.selectbox(
            "AI Provider",
            ["OpenAI", "Anthropic"],
            index=0 if st.session_state.ai_provider == "OpenAI" else 1,
            key="provider_select"
        )
        st.session_state.ai_provider = provider
        
        # Model selection based on provider
        if provider == "OpenAI":
            models = ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo"]
        else:
            models = ["claude-3-5-sonnet-20241022", "claude-3-haiku-20240307"]
        
        model = st.selectbox(
            "Model",
            models,
            key="model_select"
        )
        st.session_state.ai_model = model
        
        # Editor settings
        editor_default = st.checkbox(
            "Enable AI Editor by default",
            value=st.session_state.get("editor_enabled", False)
        )
        st.session_state.editor_enabled = editor_default
    
    with tab2:
        st.markdown("#### API Keys")
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
    
    with tab3:
        st.markdown("#### Custom Prompts")
        
        prompt_types = [
            "wisdom_extraction",
            "outline_creation", 
            "social_media",
            "image_prompts"
        ]
        
        for prompt_type in prompt_types:
            st.markdown(f"##### {prompt_type.replace('_', ' ').title()}")
            
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
                    # Reload prompts from database to ensure persistence
                    st.session_state.prompts = get_user_prompts_supabase()
                    st.session_state.prompts[prompt_type] = new_prompt
                    st.rerun()  # Refresh to show updated state
    
    with tab4:
        st.markdown("#### Knowledge Base")
        
        kb = get_user_knowledge_base_supabase()
        
        if kb:
            st.markdown("**Your files:**")
            for name, content in kb.items():
                with st.expander(f"{name}"):
                    st.text_area("Content", content, height=200, key=f"kb_{name}")
        else:
            st.info("No knowledge base files yet.")
        
        # Upload new file
        st.markdown("##### Upload File")
        uploaded_kb = st.file_uploader("Choose file", type=["txt", "md"])
        
        if uploaded_kb:
            content = uploaded_kb.read().decode("utf-8")
            if st.button("Save Knowledge Base File"):
                if save_knowledge_base_file_supabase(uploaded_kb.name, content):
                    st.success(f"Saved {uploaded_kb.name}!")
                    st.rerun()

def show_health_page():
    """System health check page"""
    st.markdown("# System Health")
    
    health = get_health_status()
    
    # Overall status
    if health["status"] == "healthy":
        st.success("✅ System is healthy")
    elif health["status"] == "degraded":
        st.warning("⚠️ System is degraded")
    else:
        st.error("❌ System is unhealthy")
    
    # Detailed checks
    st.markdown("### System Checks")
    for check, status in health["checks"].items():
        if isinstance(status, dict):
            st.markdown(f"**{check.title()}:**")
            for key, value in status.items():
                st.write(f"  - {key}: {value}")
        else:
            if "error" in str(status).lower() or "unhealthy" in str(status).lower():
                st.error(f"**{check.title()}:** {status}")
            elif "missing" in str(status).lower():
                st.warning(f"**{check.title()}:** {status}")
            else:
                st.success(f"✅ **{check.title()}:** {status}")

def main():
    """Main application entry point - FIXED OAUTH ROUTING"""
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
        
        # Debug session state
        st.sidebar.write(f"Debug - Authenticated: {st.session_state.get('authenticated', False)}")
        st.sidebar.write(f"Debug - User ID: {st.session_state.get('user_id', 'None')}")
        
        # Handle OAuth callback FIRST - but don't redirect yet
        oauth_success = False
        if 'code' in query_params and not st.session_state.get('authenticated', False):
            oauth_success = handle_oauth_callback()
            if oauth_success:
                # Don't call show_main_app here, let the authentication check below handle it
                pass
        
        # Check authentication and route accordingly
        if st.session_state.get('authenticated', False):
            show_main_app()
        else:
            show_auth_page()
    
    except Exception as e:
        track_error(e, {"location": "main_app"})
        st.error(f"Application error: {e}")
        logger.error("Main application error", exc_info=True)

if __name__ == "__main__":
    main() 