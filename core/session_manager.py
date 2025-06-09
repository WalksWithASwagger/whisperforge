"""
Advanced Session Management for WhisperForge
Handles authentication persistence, user data loading, and secure session storage
"""

import streamlit as st
import hashlib
import json
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class SessionManager:
    """Advanced session management with persistence and security"""
    
    def __init__(self):
        self.session_timeout = 24 * 60 * 60  # 24 hours in seconds
        self.refresh_threshold = 60 * 60  # Refresh token every hour
        
    def init_session(self):
        """Initialize session state with proper defaults"""
        
        # Core authentication state
        if 'authenticated' not in st.session_state:
            st.session_state.authenticated = False
        if 'user_id' not in st.session_state:
            st.session_state.user_id = None
        if 'user_email' not in st.session_state:
            st.session_state.user_email = None
            
        # Session metadata
        if 'session_start' not in st.session_state:
            st.session_state.session_start = datetime.now()
        if 'last_activity' not in st.session_state:
            st.session_state.last_activity = datetime.now()
        if 'session_token' not in st.session_state:
            st.session_state.session_token = None
            
        # App state persistence
        if 'current_page' not in st.session_state:
            st.session_state.current_page = "Content Pipeline"
        if 'ai_provider' not in st.session_state:
            st.session_state.ai_provider = "OpenAI"
        if 'ai_model' not in st.session_state:
            st.session_state.ai_model = "gpt-4o"
            
        # User data caches
        if 'prompts' not in st.session_state:
            st.session_state.prompts = {}
        if 'knowledge_base' not in st.session_state:
            st.session_state.knowledge_base = {}
        if 'api_keys' not in st.session_state:
            st.session_state.api_keys = {}
            
        # Feature settings
        if 'editor_enabled' not in st.session_state:
            st.session_state.editor_enabled = False
        if 'research_enabled' not in st.session_state:
            st.session_state.research_enabled = True
        if 'thinking_enabled' not in st.session_state:
            st.session_state.thinking_enabled = True
    
    def create_session_token(self, user_id: str, user_email: str) -> str:
        """Create a secure session token"""
        timestamp = str(int(time.time()))
        data = f"{user_id}:{user_email}:{timestamp}"
        token = hashlib.sha256(data.encode()).hexdigest()
        return f"{token}:{timestamp}"
    
    def validate_session_token(self, token: str, user_id: str) -> bool:
        """Validate session token and check expiration"""
        if not token or ':' not in token:
            return False
            
        try:
            token_hash, timestamp = token.split(':', 1)
            token_time = int(timestamp)
            current_time = int(time.time())
            
            # Check if token has expired
            if current_time - token_time > self.session_timeout:
                logger.info(f"Session token expired for user {user_id}")
                return False
                
            return True
            
        except (ValueError, TypeError) as e:
            logger.error(f"Invalid session token format: {e}")
            return False
    
    def login_user(self, user_id: str, user_email: str) -> bool:
        """Authenticate user and create persistent session"""
        try:
            # Create session token
            session_token = self.create_session_token(user_id, user_email)
            
            # Set session state
            st.session_state.authenticated = True
            st.session_state.user_id = user_id
            st.session_state.user_email = user_email
            st.session_state.session_token = session_token
            st.session_state.last_activity = datetime.now()
            
            # Store persistent session data
            self._store_persistent_session(user_id, user_email, session_token)
            
            # Load user data
            self._load_user_data()
            
            logger.info(f"User {user_email} logged in successfully")
            return True
            
        except Exception as e:
            logger.error(f"Login failed for user {user_email}: {e}")
            return False
    
    def logout_user(self):
        """Logout user and clear all session data"""
        try:
            user_email = st.session_state.get('user_email', 'unknown')
            
            # Clear persistent session
            self._clear_persistent_session()
            
            # Clear session state
            keys_to_clear = [
                'authenticated', 'user_id', 'user_email', 'session_token',
                'prompts', 'knowledge_base', 'api_keys'
            ]
            
            for key in keys_to_clear:
                if key in st.session_state:
                    del st.session_state[key]
            
            # Reset to defaults
            self.init_session()
            
            logger.info(f"User {user_email} logged out successfully")
            return True
            
        except Exception as e:
            logger.error(f"Logout failed: {e}")
            return False
    
    def check_session_validity(self) -> bool:
        """Check if current session is valid and refresh if needed"""
        try:
            if not st.session_state.get('authenticated', False):
                return False
            
            user_id = st.session_state.get('user_id')
            session_token = st.session_state.get('session_token')
            
            if not user_id or not session_token:
                return False
            
            # Validate token
            if not self.validate_session_token(session_token, user_id):
                logger.info(f"Invalid session for user {user_id}, logging out")
                self.logout_user()
                return False
            
            # Update last activity
            st.session_state.last_activity = datetime.now()
            
            # Check if we need to refresh user data
            last_refresh = st.session_state.get('last_data_refresh')
            if not last_refresh or (datetime.now() - last_refresh).seconds > self.refresh_threshold:
                self._load_user_data()
                st.session_state.last_data_refresh = datetime.now()
            
            return True
            
        except Exception as e:
            logger.error(f"Session validation failed: {e}")
            return False
    
    def restore_session_from_storage(self) -> bool:
        """Attempt to restore session from persistent storage"""
        try:
            # Check if we have persistent session data
            persistent_data = self._get_persistent_session()
            
            if not persistent_data:
                return False
            
            user_id = persistent_data.get('user_id')
            user_email = persistent_data.get('user_email') 
            session_token = persistent_data.get('session_token')
            
            if not all([user_id, user_email, session_token]):
                return False
            
            # Validate the stored token
            if not self.validate_session_token(session_token, user_id):
                self._clear_persistent_session()
                return False
            
            # Restore session
            st.session_state.authenticated = True
            st.session_state.user_id = user_id
            st.session_state.user_email = user_email
            st.session_state.session_token = session_token
            st.session_state.last_activity = datetime.now()
            
            # Load user data
            self._load_user_data()
            
            logger.info(f"Session restored for user {user_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to restore session: {e}")
            self._clear_persistent_session()
            return False
    
    def _store_persistent_session(self, user_id: str, user_email: str, session_token: str):
        """Store session data persistently using Streamlit's native storage"""
        try:
            session_data = {
                'user_id': user_id,
                'user_email': user_email,
                'session_token': session_token,
                'created_at': datetime.now().isoformat()
            }
            
            # Use Streamlit's session state as primary storage
            # Note: This persists across page refreshes within the same browser session
            st.session_state._persistent_session = session_data
            
        except Exception as e:
            logger.error(f"Failed to store persistent session: {e}")
    
    def _get_persistent_session(self) -> Optional[Dict[str, Any]]:
        """Retrieve persistent session data"""
        try:
            return st.session_state.get('_persistent_session')
        except Exception as e:
            logger.error(f"Failed to get persistent session: {e}")
            return None
    
    def _clear_persistent_session(self):
        """Clear persistent session data"""
        try:
            if '_persistent_session' in st.session_state:
                del st.session_state._persistent_session
        except Exception as e:
            logger.error(f"Failed to clear persistent session: {e}")
    
    def _load_user_data(self):
        """Load user-specific data from database"""
        try:
            from app import (
                get_user_prompts_supabase, 
                get_user_knowledge_base_supabase,
                get_user_api_keys_supabase
            )
            
            # Load prompts
            st.session_state.prompts = get_user_prompts_supabase()
            
            # Load knowledge base
            st.session_state.knowledge_base = get_user_knowledge_base_supabase()
            
            # Load API keys
            st.session_state.api_keys = get_user_api_keys_supabase()
            
            logger.info(f"User data loaded for {st.session_state.get('user_email')}")
            
        except Exception as e:
            logger.error(f"Failed to load user data: {e}")
            # Initialize with empty data on failure
            st.session_state.prompts = {}
            st.session_state.knowledge_base = {}
            st.session_state.api_keys = {}

# Global session manager instance
session_manager = SessionManager()

# Convenience functions for easy access
def init_session():
    """Initialize session management"""
    session_manager.init_session()

def login_user(user_id: str, user_email: str) -> bool:
    """Login user with persistent session"""
    return session_manager.login_user(user_id, user_email)

def logout_user():
    """Logout user and clear session"""
    return session_manager.logout_user()

def check_session() -> bool:
    """Check if session is valid"""
    return session_manager.check_session_validity()

def restore_session() -> bool:
    """Restore session from storage"""
    return session_manager.restore_session_from_storage()

def require_auth(func):
    """Decorator to require authentication for functions"""
    def wrapper(*args, **kwargs):
        if not check_session():
            st.error("Authentication required")
            st.stop()
        return func(*args, **kwargs)
    return wrapper 