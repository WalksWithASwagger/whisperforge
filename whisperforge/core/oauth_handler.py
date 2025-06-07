"""
Google OAuth Handler for WhisperForge
====================================

Handles Google OAuth authentication flow with Supabase integration.
"""

import os
import streamlit as st
import logging
from typing import Optional, Dict, Any
from urllib.parse import urlencode, parse_qs, urlparse
from supabase import Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class GoogleOAuthHandler:
    """Handles Google OAuth authentication flow"""
    
    def __init__(self, supabase_client: Client):
        self.supabase = supabase_client
        
        # Note: Google OAuth credentials are configured in Supabase dashboard, not as env vars
    
    def generate_oauth_url(self, redirect_to: str = None) -> str:
        """Generate Google OAuth URL using Supabase"""
        try:
            # Determine redirect URL dynamically if not provided
            if not redirect_to:
                import os
                # Check if we're running on Streamlit Cloud
                if os.getenv('STREAMLIT_SHARING_MODE') or os.getenv('HOSTNAME') == 'streamlit':
                    # Running on Streamlit Cloud - let Supabase use current domain
                    redirect_url = None
                else:
                    # Local development
                    redirect_url = "http://localhost:8507"
            else:
                redirect_url = redirect_to
            
            # Use Supabase's built-in OAuth URL generation
            oauth_options = {
                "provider": "google",
                "options": {
                    "scopes": "email profile"
                }
            }
            
            # Only add redirect_to if we have a specific URL
            if redirect_url:
                oauth_options["options"]["redirect_to"] = redirect_url
            
            response = self.supabase.auth.sign_in_with_oauth(oauth_options)
            
            logger.info(f"Generated OAuth URL: {response.url}")
            return response.url
            
        except Exception as e:
            logger.error(f"Error generating OAuth URL: {e}")
            raise
    
    def handle_oauth_callback(self, url_params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Handle OAuth callback and extract user info"""
        try:
            # Extract code from URL parameters
            code = url_params.get('code')
            if not code:
                logger.error("No authorization code found in callback")
                return None
            
            # Exchange code for session using Supabase
            response = self.supabase.auth.exchange_code_for_session({
                "auth_code": code[0] if isinstance(code, list) else code
            })
            
            if response.user:
                user_data = {
                    "id": response.user.id,
                    "email": response.user.email,
                    "name": response.user.user_metadata.get('full_name', ''),
                    "avatar_url": response.user.user_metadata.get('avatar_url', ''),
                    "provider": "google",
                    "access_token": response.session.access_token,
                    "refresh_token": response.session.refresh_token
                }
                
                logger.info(f"OAuth callback successful for user: {user_data['email']}")
                return user_data
            else:
                logger.error("No user data returned from OAuth callback")
                return None
                
        except Exception as e:
            logger.error(f"Error handling OAuth callback: {e}")
            return None
    
    def get_or_create_user(self, oauth_user_data: Dict[str, Any]) -> Optional[int]:
        """Get existing user or create new one from OAuth data"""
        try:
            email = oauth_user_data.get('email')
            if not email:
                logger.error("No email found in OAuth user data")
                return None
            
            # Check if user exists in our database
            existing_user = self.supabase.table("users").select("*").eq("email", email).execute()
            
            if existing_user.data:
                # User exists, update their info (with fallback for missing columns)
                user_id = existing_user.data[0]["id"]
                
                # Try to update with new OAuth columns, fall back to basic update if columns don't exist
                try:
                    update_data = {
                        "google_id": oauth_user_data.get('id'),
                        "avatar_url": oauth_user_data.get('avatar_url'),
                        "last_login": "now()",
                        "auth_provider": "google"
                    }
                    self.supabase.table("users").update(update_data).eq("id", user_id).execute()
                    logger.info(f"Updated existing user with OAuth data: {email}")
                except Exception as update_error:
                    # Fallback: just update last_login if OAuth columns don't exist
                    logger.warning(f"OAuth columns not available, basic update only: {update_error}")
                    try:
                        self.supabase.table("users").update({"last_login": "now()"}).eq("id", user_id).execute()
                        logger.info(f"Updated existing user (basic): {email}")
                    except Exception as basic_error:
                        logger.error(f"Failed to update user: {basic_error}")
                
                return user_id
            else:
                # Create new user (with fallback for missing columns)
                try:
                    new_user_data = {
                        "email": email,
                        "google_id": oauth_user_data.get('id'),
                        "avatar_url": oauth_user_data.get('avatar_url'),
                        "usage_quota": 60,  # 60 minutes default
                        "usage_current": 0,
                        "is_admin": False,
                        "subscription_tier": "free",
                        "auth_provider": "google",
                        "created_at": "now()",
                        "last_login": "now()"
                    }
                    
                    result = self.supabase.table("users").insert(new_user_data).execute()
                    if result.data:
                        user_id = result.data[0]["id"]
                        logger.info(f"Created new user from Google OAuth: {email}")
                        return user_id
                    else:
                        logger.error("Failed to create new user")
                        return None
                        
                except Exception as create_error:
                    # Fallback: create user with basic fields only
                    logger.warning(f"OAuth columns not available, creating basic user: {create_error}")
                    try:
                        basic_user_data = {
                            "email": email,
                            "password": None,  # No password for OAuth users
                            "usage_quota": 60,
                            "usage_current": 0,
                            "is_admin": False,
                            "subscription_tier": "free"
                        }
                        
                        result = self.supabase.table("users").insert(basic_user_data).execute()
                        if result.data:
                            user_id = result.data[0]["id"]
                            logger.info(f"Created new user (basic) from Google OAuth: {email}")
                            return user_id
                        else:
                            logger.error("Failed to create basic user")
                            return None
                    except Exception as basic_create_error:
                        logger.error(f"Failed to create user completely: {basic_create_error}")
                        return None
                
        except Exception as e:
            logger.error(f"Error getting/creating user: {e}")
            return None
    
    def sign_out(self) -> bool:
        """Sign out user from Supabase"""
        try:
            self.supabase.auth.sign_out()
            logger.info("User signed out successfully")
            return True
        except Exception as e:
            logger.error(f"Error signing out: {e}")
            return False


def create_google_signin_button() -> str:
    """Create HTML for Google Sign-In button"""
    return """
    <style>
    .google-signin-btn {
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
        min-width: 200px;
    }
    
    .google-signin-btn:hover {
        background-color: #3367d6;
        text-decoration: none;
        color: white;
    }
    
    .google-icon {
        background-color: white;
        border-radius: 4px;
        padding: 8px;
        margin-right: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    </style>
    
    <div class="google-signin-btn" onclick="window.open('{oauth_url}', '_self')">
        <div class="google-icon">
            <svg width="20" height="20" viewBox="0 0 24 24">
                <path fill="#4285f4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                <path fill="#34a853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                <path fill="#fbbc05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                <path fill="#ea4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
            </svg>
        </div>
        Sign in with Google
    </div>
    """


def handle_oauth_redirect():
    """Handle OAuth redirect in Streamlit"""
    # Get URL parameters
    query_params = st.query_params
    
    if 'code' in query_params:
        # We have an OAuth callback
        st.session_state.oauth_callback = True
        st.session_state.oauth_params = query_params
        return True
    
    return False 