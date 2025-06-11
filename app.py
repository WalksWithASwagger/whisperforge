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
import uuid
from datetime import datetime
from pathlib import Path

# Generate truly unique keys for Streamlit widgets
def generate_unique_key(base_name: str) -> str:
    """Generate truly unique key for Streamlit widgets to prevent DuplicateWidgetID errors"""
    return f"{base_name}_{uuid.uuid4().hex[:8]}_{int(time.time() * 1000000) % 1000000}"

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
from core.file_upload import FileUploadManager, LargeFileUploadManager
from core.notifications import (
    show_success, show_error, show_warning, show_info,
    create_loading_spinner
)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize monitoring
init_monitoring()

# Removed unused run_content_pipeline - replaced by streaming_pipeline.py

# === Database Connection (Research-Backed Pattern) ===

@st.cache_resource
def init_supabase():
    """Initialize Supabase client with robust error handling"""
    try:
        from core.supabase_integration import get_supabase_client
        client = get_supabase_client()
        
        # Test connection with timeout
        if client:
            # Simple connection test
            return client, True
        else:
            logger.warning("Supabase client creation failed")
            return None, False
            
    except Exception as e:
        logger.error(f"Supabase initialization failed: {e}")
        # Don't crash the app - continue without database
        return None, False

# Database operations using Supabase
def authenticate_user(email, password):
    """Simple authentication - no complex token management"""
    try:
        db, success = init_supabase()
        if not success:
            return False
        
        # Get user by email
        result = db.client.table("users").select("*").eq("email", email).execute()
        
        if not result.data:
            logger.warning(f"No user found with email: {email}")
            return False
            
        user = result.data[0]
        stored_password = user.get("password", "")
        
        # Verify password (bcrypt or legacy)
        if stored_password.startswith('$2b$'):
            from core.utils import verify_password
            if verify_password(password, stored_password):
                # Simple session state - no tokens
                st.session_state.authenticated = True
                st.session_state.user_id = user["id"]
                st.session_state.user_email = email
                logger.info(f"User authenticated: {email}")
                return True
        else:
            # Legacy password handling
            from core.utils import legacy_hash_password, hash_password
            if legacy_hash_password(password) == stored_password:
                # Migrate to bcrypt and authenticate
                new_hash = hash_password(password)
                db.client.table("users").update({"password": new_hash}).eq("id", user["id"]).execute()
                
                st.session_state.authenticated = True
                st.session_state.user_id = user["id"]
                st.session_state.user_email = email
                logger.info(f"User authenticated and password migrated: {email}")
                return True
                
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
            
        result = db.client.table("content").insert({
            "user_id": st.session_state.user_id,
            "content_data": content_data,
            "created_at": "now()"
        }).execute()
        
        return result.data[0]["id"] if result.data else ""
    except Exception as e:
        logger.error(f"Error saving content: {e}")
        return ""

def get_user_content_history_supabase(limit: int = 20) -> list:
    """Get user content history - ENHANCED WITH DEBUG LOGGING"""
    try:
        # Enhanced authentication check
        if not st.session_state.get("authenticated", False):
            logger.warning("User not authenticated when fetching history")
            return []
            
        if not st.session_state.get("user_id"):
            logger.warning("No user_id in session state when fetching history")
            return []
        
        db, _ = init_supabase()
        if not db:
            logger.error("Failed to initialize Supabase client for history")
            return []
        
        user_id = st.session_state.user_id
        logger.info(f"Fetching content history for user_id: {user_id}")
        
        # Enhanced query with better error handling - get ALL fields
        result = db.client.table("content")\
            .select("id, title, transcript, wisdom, outline, article, social_content, created_at")\
            .eq("user_id", user_id)\
            .order("created_at", desc=True)\
            .limit(limit)\
            .execute()
        
        logger.info(f"History query result: {len(result.data) if result.data else 0} items found")
        
        # Debug: Log first item structure if available
        if result.data and len(result.data) > 0:
            logger.info(f"Sample history item keys: {list(result.data[0].keys())}")
        
        return result.data if result.data else []
        
    except Exception as e:
        logger.error(f"Error getting content history: {e}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
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
                    
                    # Simple authentication - no complex session manager
                    st.session_state.authenticated = True
                    st.session_state.user_email = user_email
                    
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
            elif authenticate_user(email, password):
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
    """Main application with clean layout and integrated navigation"""
    
    # Simple authentication check - no complex session validation
    if not st.session_state.get('authenticated', False):
        st.error("Please log in to continue.")
        st.session_state.authenticated = False
        st.rerun()
        return
    
    # Check for page navigation via query params
    query_params = st.query_params
    if 'page' in query_params:
        page = query_params['page'].replace('_', ' ')
        if page in ["Content Pipeline", "Content History", "Settings", "Health Check"]:
            st.session_state.current_page = page
            # Clear the query param after processing
            st.query_params.clear()
    
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
    
    # Apply Aurora theme and show compact header with integrated navigation
    apply_aurora_theme()
    
    # New Aurora header with integrated navigation
    create_aurora_header()
    
    # Integrated navigation with logout handling
    from core.styling import create_aurora_nav_buttons
    import time
    
    if create_aurora_nav_buttons():
        # User clicked logout - simple logout
        st.session_state.authenticated = False
        st.session_state.user_id = None
        st.session_state.user_email = None
        st.success("Logged out successfully!")
        time.sleep(1)  # Brief pause to show message
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
    
    # 🔧 SIMPLIFIED BULLETPROOF FILE UPLOAD - Core functionality only
    st.markdown("### 📁 Audio Upload")
    
    # Simple, reliable file uploader
    uploaded_file = st.file_uploader(
        "Choose an audio file",
        type=['mp3', 'wav', 'm4a', 'aac', 'ogg', 'flac', 'wma'],
        help="Upload audio files for transcription. Supported: MP3, WAV, M4A, AAC, OGG, FLAC, WMA",
        key="audio_upload"
    )
    
    # Simple file validation
    if uploaded_file is not None:
        file_size_mb = len(uploaded_file.getvalue()) / (1024 * 1024)
        
        # Basic file info
        st.success(f"✅ File loaded: **{uploaded_file.name}** ({file_size_mb:.1f} MB)")
        
        # Simple size check - be more generous for now
        if file_size_mb > 100:  # 100MB limit for stability
            st.warning(f"⚠️ Large file detected ({file_size_mb:.1f} MB). Processing may take longer.")
        
        # Show processing strategy
        if file_size_mb > 25:
            st.info("🔄 Large file will be processed with enhanced handling")
        else:
            st.info("⚡ File will be processed directly")
    
    # User preferences - simplified
    col1, col2 = st.columns(2)
    
    with col1:
        ai_provider = st.selectbox(
            "AI Provider",
            ["OpenAI", "Anthropic"],  # Removed Grok for stability
            index=0,
            help="Choose your AI provider"
        )
        st.session_state.ai_provider = ai_provider
    
    with col2:
        # Simplified model selection
        if ai_provider == "OpenAI":
            model_options = ["gpt-4o", "gpt-4o-mini"]
        else:  # Anthropic
            model_options = ["claude-3-5-sonnet-20241022", "claude-3-haiku-20240307"]
        
        ai_model = st.selectbox(
            "Model",
            model_options,
            index=0
        )
        st.session_state.ai_model = ai_model
    
    # SIMPLIFIED BULLETPROOF PROCESSING - Focus on core functionality
    if uploaded_file is not None:
        st.markdown("---")
        st.markdown("### 🎵 Processing")
        
        # Create progress containers
        progress_container = st.empty()
        results_container = st.empty()
        
        try:
            with progress_container.container():
                st.markdown("#### Processing Audio...")
                
                # Step 1: Transcription (most critical)
                with st.status("🎙️ Transcribing audio...", expanded=True) as status:
                    st.write("Converting speech to text...")
                    
                    # Use simple transcription - no complex chunking for now
                    from core.content_generation import transcribe_audio
                    transcript = transcribe_audio(uploaded_file)
                    
                    if not transcript or "Error" in transcript:
                        st.error(f"❌ Transcription failed: {transcript}")
                        st.stop()
                    
                    st.write("✅ Transcription complete!")
                    status.update(label="✅ Transcription complete!", state="complete")
                
                # Step 2: Wisdom Extraction
                with st.status("💎 Extracting insights...", expanded=True) as status:
                    st.write("Analyzing content for key insights...")
                    
                    from core.content_generation import generate_wisdom
                    wisdom = generate_wisdom(
                        transcript, 
                        st.session_state.ai_provider, 
                        st.session_state.ai_model
                    )
                    
                    if wisdom and "Error" not in wisdom:
                        st.write("✅ Insights extracted!")
                        status.update(label="✅ Insights extracted!", state="complete")
                    else:
                        st.warning("⚠️ Insights extraction had issues")
                        wisdom = "Insights extraction failed"
                
                # Step 3: Outline Creation
                with st.status("📋 Creating outline...", expanded=True) as status:
                    st.write("Structuring content outline...")
                    
                    from core.content_generation import generate_outline
                    outline = generate_outline(
                        transcript,
                        wisdom, 
                        st.session_state.ai_provider, 
                        st.session_state.ai_model
                    )
                    
                    if outline and "Error" not in outline:
                        st.write("✅ Outline created!")
                        status.update(label="✅ Outline created!", state="complete")
                    else:
                        st.warning("⚠️ Outline creation had issues")
                        outline = "Outline creation failed"
                
                # Step 4: Article Generation
                with st.status("📰 Writing article...", expanded=True) as status:
                    st.write("Generating full article...")
                    
                    from core.content_generation import generate_article
                    article = generate_article(
                        transcript,
                        wisdom,
                        outline, 
                        st.session_state.ai_provider, 
                        st.session_state.ai_model
                    )
                    
                    if article and "Error" not in article:
                        st.write("✅ Article generated!")
                        status.update(label="✅ Article generated!", state="complete")
                    else:
                        st.warning("⚠️ Article generation had issues")
                    article = "Article generation failed"
            
            # Show results
            with results_container.container():
                st.markdown("---")
                st.markdown("## ✨ Results")
                
                # Transcript
                with st.expander("🎙️ Transcript", expanded=False):
                    st.markdown(transcript)
                    if st.button("📋 Copy Transcript", key="copy_transcript"):
                        st.code(transcript)
                
                # Wisdom
                with st.expander("💎 Key Insights", expanded=True):
                    st.markdown(wisdom)
                    if st.button("📋 Copy Insights", key="copy_wisdom"):
                        st.code(wisdom)
                
                # Outline
                with st.expander("📋 Content Outline", expanded=False):
                    st.markdown(outline)
                    if st.button("📋 Copy Outline", key="copy_outline"):
                        st.code(outline)
                
                # Article
                with st.expander("📰 Full Article", expanded=False):
                    st.markdown(article)
                    if st.button("📋 Copy Article", key="copy_article"):
                        st.code(article)
                
                st.success("🎉 Processing complete!")
            
        except Exception as e:
            st.error(f"❌ Processing failed: {str(e)}")
            import traceback
            st.code(traceback.format_exc())
    
    else:
        # Welcome message when no file uploaded
        st.markdown("---")
        st.markdown("### 🎵 Welcome to WhisperForge")
        st.markdown("Upload an audio file above to get started with AI-powered content generation.")
        
        st.markdown("**Supported formats:** MP3, WAV, M4A, AAC, OGG, FLAC, WMA")
        st.markdown("**File size limit:** Up to 100MB for optimal performance")

def show_processing_results(results):
    """PHASE 6: ENHANCED CONTENT DISPLAY with modern card layouts and copy functionality"""
    
    if not results:
        st.info("🔄 No results to display yet")
        return
    
    # Beautiful results header
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, rgba(0, 255, 255, 0.08), rgba(64, 224, 208, 0.12));
        border: 1px solid rgba(0, 255, 255, 0.2);
        border-radius: 16px;
        padding: 24px;
        text-align: center;
        margin: 24px 0;
    ">
        <h2 style="color: #00FFFF; margin: 0; font-weight: 300;">✨ Generation Complete</h2>
        <p style="color: rgba(255, 255, 255, 0.7); margin: 8px 0 0 0;">Your content has been transformed</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Enhanced content sections with modern cards
    content_sections = {
        'transcription': ('🎙️', 'Audio Transcription', 'Speech-to-text conversion'),
        'wisdom_extraction': ('💎', 'Key Insights & Wisdom', 'Extracted insights and takeaways'),
        'outline_creation': ('📋', 'Content Outline', 'Structured organization and flow'),
        'article_creation': ('📰', 'Full Article', 'Complete written content'),
        'social_content': ('📱', 'Social Media Posts', 'Platform-optimized content'),
        'image_prompts': ('🖼️', 'Image Generation Prompts', 'AI-generated visual concepts')
    }
    
    # Display each result in a beautiful card
    for section_key, (icon, title, description) in content_sections.items():
        if section_key in results and results[section_key]:
            content = results[section_key]
            
            # Modern content card
            with st.container():
                st.markdown(f"""
                <div style="
                    background: linear-gradient(135deg, rgba(0, 255, 255, 0.03), rgba(64, 224, 208, 0.05));
                    border: 1px solid rgba(0, 255, 255, 0.1);
                    border-radius: 12px;
                    padding: 24px;
                    margin: 16px 0;
                    transition: all 0.3s ease;
                ">
                    <div style="display: flex; align-items: center; margin-bottom: 16px;">
                        <span style="font-size: 1.5rem; margin-right: 12px;">{icon}</span>
                        <div>
                            <h3 style="color: #00FFFF; margin: 0; font-weight: 500;">{title}</h3>
                            <p style="color: rgba(255, 255, 255, 0.6); margin: 4px 0 0 0; font-size: 0.9rem;">{description}</p>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Content display with preview/expand
                if len(str(content)) > 800:
                    # Show preview for long content
                    st.markdown(f"**Preview:**")
                    st.markdown(f"{str(content)[:400]}...")
                    
                    # Expandable full content
                    with st.expander("📖 Show Full Content", expanded=False):
                        st.markdown(content)
                        
                        # Copy button inside expander
                        copy_key = generate_unique_key(f"copy_full_{section_key}")
                        if st.button(f"📋 Copy {title}", key=copy_key, use_container_width=True):
                            st.code(content, language="markdown")
                else:
                    # Show full content for shorter text
                    st.markdown(content)
                
                # Action buttons
                col1, col2, col3 = st.columns([2, 1, 1])
                with col1:
                    copy_key = generate_unique_key(f"copy_{section_key}")
                    if st.button(f"📋 Copy {title}", key=copy_key):
                        st.code(content, language="markdown")
                        st.success(f"✅ {title} copied!")
                
                with col2:
                    download_key = generate_unique_key(f"download_{section_key}")
                    st.download_button(
                        "💾 Download",
                        data=content,
                        file_name=f"{section_key}.md",
                        mime="text/markdown",
                        key=download_key
                    )
                
                with col3:
                    share_key = generate_unique_key(f"share_{section_key}")
                    if st.button("🔗 Share", key=share_key):
                        st.info("Share functionality coming soon!")
                
                st.markdown("---")

def show_content_history_page():
    """Show user's content history with beautiful Aurora styling - ENHANCED DEBUG"""
    st.markdown("# 📋 Content History")
    st.markdown("Your generated content archive with transcripts, insights, and metadata")
    
    # Debug information in expander
    with st.expander("🔍 Debug Information", expanded=False):
        st.write(f"**Authentication Status:** {st.session_state.get('authenticated', False)}")
        st.write(f"**User ID:** {st.session_state.get('user_id', 'None')}")
        st.write(f"**Session State Keys:** {list(st.session_state.keys())}")
        
        # Test database connection
        try:
            db, _ = init_supabase()
            if db:
                st.success("✅ Database connection successful")
                
                # Test query with count
                count_result = db.client.table("content").select("id", count="exact").eq("user_id", st.session_state.get("user_id", "")).execute()
                st.write(f"**Total records in DB for user:** {count_result.count if hasattr(count_result, 'count') else 'Unknown'}")
                
                # Show raw sample data with CORRECT database fields
                sample_result = db.client.table("content").select("id, title, transcript, wisdom, outline, article, social_content, created_at").eq("user_id", st.session_state.get("user_id", "")).order("created_at", desc=True).limit(3).execute()
                if sample_result.data:
                    st.write(f"**Sample raw records ({len(sample_result.data)}):**")
                    for i, record in enumerate(sample_result.data):
                        st.write(f"Record {i+1}:")
                        st.write(f"  - ID: {record.get('id')}")
                        st.write(f"  - Title: {record.get('title', 'No title')}")
                        st.write(f"  - Has transcript: {'Yes' if record.get('transcript') else 'No'}")
                        st.write(f"  - Has wisdom: {'Yes' if record.get('wisdom') else 'No'}")
                        st.write(f"  - Has article: {'Yes' if record.get('article') else 'No'}")
                        st.write(f"  - Created: {record.get('created_at')}")
                else:
                    st.warning("No sample records found")
            else:
                st.error("❌ Database connection failed")
        except Exception as e:
            st.error(f"❌ Database test error: {e}")
            import traceback
            st.code(traceback.format_exc())
    
    history = get_user_content_history_supabase()
    
    # Enhanced empty state with debug info
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
        title = item.get('title', f'Content {i+1}')
        
        # Create Aurora content card
        with st.expander(f"✨ {title} - {created_date}", expanded=i==0):
            # Display each content type directly from database fields
            content_sections = {
                'transcript': ('♦', 'Audio Transcription', 'The original speech-to-text conversion'),
                'wisdom': ('◆', 'Key Insights & Wisdom', 'Extracted insights and takeaways'), 
                'outline': ('◇', 'Content Outline', 'Structured organization and flow'),
                'article': ('◈', 'Full Article', 'Complete written content'),
                'social_content': ('◉', 'Social Media Posts', 'Platform-optimized content')
            }
            
            # Show content for each section that exists
            for section_key, (icon, section_title, description) in content_sections.items():
                content = item.get(section_key)
                if content and content.strip():
                    # Aurora content section
                    st.markdown(f"""
                    <div style="
                        background: linear-gradient(135deg, rgba(0, 255, 255, 0.03), rgba(64, 224, 208, 0.05));
                        border: 1px solid rgba(0, 255, 255, 0.1);
                        border-radius: 12px;
                        padding: 20px;
                        margin: 16px 0;
                    ">
                        <h4 style="color: #00FFFF; margin-bottom: 8px;">{icon} {section_title}</h4>
                        <p style="color: rgba(255, 255, 255, 0.6); font-size: 0.9rem; margin-bottom: 16px;">{description}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Show content with copy functionality  
                    if len(str(content)) > 500:
                        # Show preview for long content
                        st.markdown(f"**Preview:** {str(content)[:300]}...")
                        show_full_key = generate_unique_key(f"show_{section_key}_{i}")
                        if st.button(f"Show Full {section_title}", key=show_full_key):
                            full_text_key = generate_unique_key(f"full_{section_key}_{i}")
                            st.text_area(f"Full {section_title}", content, height=200, key=full_text_key)
                    else:
                        st.markdown(content)
                    
                    # Copy button
                    copy_key = generate_unique_key(f"copy_{section_key}_{i}")
                    if st.button(f"Copy {section_title}", key=copy_key, help=f"Copy {section_title} to clipboard"):
                        st.code(content, language="markdown")
                    
                    st.markdown("---")

def _show_research_content(research_data: dict):
    """Display research enrichment content in a beautiful format"""
    
    entities = research_data.get("entities", [])
    total_entities = research_data.get("total_entities", 0)
    processing_time = research_data.get("processing_time", 0)
    status = research_data.get("status", "unknown")
    
    if status == "disabled":
        st.info("Research enrichment was disabled for this content.")
        return
    elif status == "no_entities_found":
        st.info("No entities found for research enrichment.")
        return
    elif status == "error":
        error_msg = research_data.get("error_message", "Unknown error")
        st.error(f"Research enrichment failed: {error_msg}")
        return
    
    if not entities:
        st.info("No research entities available.")
        return
    
    # Summary metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Entities Found", total_entities)
    with col2:
        st.metric("Processing Time", f"{processing_time:.1f}s")
    with col3:
        gem_count = sum(1 for entity in entities for link in entity.get("links", []) if link.get("is_gem"))
        st.metric("Gem Links", gem_count)
    
    # Display entities
    for i, entity in enumerate(entities):
        entity_name = entity.get("name", f"Entity {i+1}")
        entity_type = entity.get("type", "unknown")
        why_matters = entity.get("why_matters", "")
        links = entity.get("links", [])
        
        with st.expander(f"🔍 {entity_name} ({entity_type})", expanded=i==0):
            if why_matters:
                st.markdown(f"**Why this matters:** {why_matters}")
                st.markdown("---")
            
            if links:
                st.markdown("**Research Links:**")
                for j, link in enumerate(links):
                    title = link.get("title", f"Link {j+1}")
                    url = link.get("url", "#")
                    description = link.get("description", "")
                    is_gem = link.get("is_gem", False)
                    
                    # Style gem links differently
                    if is_gem:
                        st.markdown(f"✨ **[{title}]({url})** (Gem)")
                    else:
                        st.markdown(f"🔗 **[{title}]({url})**")
                    
                    if description:
                        st.markdown(f"  *{description}*")
                    st.markdown("")
            else:
                st.info("No research links available for this entity.")

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
            models = ["gpt-4o", "gpt-4o-mini"]
        else:
            models = ["claude-3-5-sonnet-20241022", "claude-3-haiku-20240307"]
        
        model = st.selectbox(
            "Model",
            models,
            key="model_select"
        )
        st.session_state.ai_model = model
        
        # Feature settings
        st.markdown("##### Feature Settings")
        
        editor_default = st.checkbox(
            "Enable AI Editor by default",
            value=st.session_state.get("editor_enabled", False),
            help="Enable AI-powered content critiques and revisions"
        )
        st.session_state.editor_enabled = editor_default
        
        research_enabled = st.checkbox(
            "Enable Research Enrichment",
            value=st.session_state.get("research_enabled", True),
            help="Automatically generate supporting research links for entities"
        )
        st.session_state.research_enabled = research_enabled
        
        thinking_enabled = st.checkbox(
            "Enable Visible Thinking",
            value=st.session_state.get("thinking_enabled", True),
            help="Show chat-style thinking bubbles during processing"
        )
        st.session_state.thinking_enabled = thinking_enabled
    
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
        
        # Initialize prompts in session state if not present
        if 'prompts' not in st.session_state:
            st.session_state.prompts = get_user_prompts_supabase()
        
        prompt_types = [
            "wisdom_extraction",
            "outline_creation",
            "article_writing", 
            "social_media",
            "image_prompts"
        ]
        
        # PHASE 5: ENHANCED SETTINGS PERSISTENCE with callbacks
        def save_prompt_callback(prompt_type: str):
            """Callback function to save prompt immediately"""
            def callback():
                new_value = st.session_state[f"prompt_{prompt_type}"]
                if save_user_prompt_supabase(prompt_type, new_value):
                    st.session_state.prompts[prompt_type] = new_value
                    st.session_state[f"save_status_{prompt_type}"] = "✅ Saved!"
                else:
                    st.session_state[f"save_status_{prompt_type}"] = "❌ Save failed"
            return callback
        
        for prompt_type in prompt_types:
            st.markdown(f"##### {prompt_type.replace('_', ' ').title()}")
            
            current_prompt = st.session_state.prompts.get(prompt_type, "")
            
            # Text area with on_change callback for immediate saving
            new_prompt = st.text_area(
                f"Prompt for {prompt_type}",
                value=current_prompt,
                height=100,
                key=f"prompt_{prompt_type}",
                on_change=save_prompt_callback(prompt_type),
                help="Changes are saved automatically when you modify the text"
            )
            
            # Show save status if available
            if f"save_status_{prompt_type}" in st.session_state:
                st.markdown(st.session_state[f"save_status_{prompt_type}"])
                # Clear status after showing
                del st.session_state[f"save_status_{prompt_type}"]
            
            # Manual save button as backup
            save_key = generate_unique_key(f"save_{prompt_type}")
            if st.button(f"💾 Save {prompt_type.replace('_', ' ').title()}", key=save_key):
                if save_user_prompt_supabase(prompt_type, new_prompt):
                    st.success(f"✅ Saved {prompt_type} prompt!")
                    st.session_state.prompts[prompt_type] = new_prompt
                else:
                    st.error(f"❌ Failed to save {prompt_type} prompt")
    
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

def init_simple_session_state():
    """Simple session initialization - research-backed approach"""
    # Core auth (only what's needed)
    defaults = {
        'authenticated': False,
        'user_id': None,
        'user_email': None,
        'current_page': 'Content Pipeline',
        # User preferences (cache in session)
        'ai_provider': 'OpenAI',
        'ai_model': 'gpt-4o',
        # Pipeline state (minimal)
        'pipeline_active': False,
        'pipeline_results': {},
        # UI state only
        'show_debug': False
    }
    
    for key, default_value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default_value

def main():
    """Main application function with bulletproof error handling"""
    try:
        # Initialize monitoring (optional)
        try:
            from core.monitoring import track_user_action
            track_user_action("page_view")
        except Exception as e:
            logger.warning(f"Monitoring initialization failed: {e}")
            # Continue without monitoring
        
        # Initialize Supabase (optional - app works without it)
        supabase_client, supabase_available = init_supabase()
        if not supabase_available:
            logger.warning("Running without database - some features may be limited")
        
        # Set up page config
        st.set_page_config(
            page_title="WhisperForge",
            page_icon="🌌",
            layout="wide",
            initial_sidebar_state="collapsed"
        )
        
        # Apply CSS
        apply_aurora_css()
        
        # Show main interface
        show_main_interface()
        
    except Exception as e:
        logger.error(f"Critical application error: {e}")
        st.error("⚠️ Application encountered an error. Please refresh the page.")
        st.code(str(e))

if __name__ == "__main__":
    main() 