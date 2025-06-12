"""
WhisperForge Session Manager
Provides persistent, secure session management for Streamlit apps
"""

import streamlit as st
import json
import uuid
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Union
from dataclasses import dataclass, asdict
from pathlib import Path
import hashlib
import os

# Enhanced logging
from .logging_config import logger


@dataclass
class UserSession:
    """Forward-compatible session schema with validation"""
    # Core auth fields
    authenticated: bool = False
    user_id: Optional[str] = None
    user_email: Optional[str] = None
    session_token: Optional[str] = None
    
    # User preferences (cached from DB)
    preferences: Dict[str, Any] = None
    
    # UI state (temporary)
    current_page: str = "Content Pipeline"
    pipeline_active: bool = False
    
    # Session metadata
    session_id: str = None
    created_at: datetime = None
    last_activity: datetime = None
    
    def __post_init__(self):
        """Initialize default values"""
        if self.preferences is None:
            self.preferences = {
                'ai_provider': 'OpenAI',
                'ai_model': 'gpt-4o',
                'editor_enabled': False,
                'research_enabled': True,
                'thinking_enabled': True
            }
        
        if self.session_id is None:
            self.session_id = str(uuid.uuid4())
        
        if self.created_at is None:
            self.created_at = datetime.now()
        
        if self.last_activity is None:
            self.last_activity = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        data = asdict(self)
        # Convert datetime objects to ISO strings
        data['created_at'] = self.created_at.isoformat() if self.created_at else None
        data['last_activity'] = self.last_activity.isoformat() if self.last_activity else None
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UserSession':
        """Create from dictionary with validation"""
        # Convert ISO strings back to datetime
        if data.get('created_at'):
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        if data.get('last_activity'):
            data['last_activity'] = datetime.fromisoformat(data['last_activity'])
        
        # Forward compatibility - ignore unknown keys
        known_fields = {f.name for f in cls.__dataclass_fields__.values()}
        filtered_data = {k: v for k, v in data.items() if k in known_fields}
        
        return cls(**filtered_data)


class SessionManager:
    """
    Comprehensive session manager for Streamlit apps
    Provides persistent authentication, preference caching, and secure token management
    """
    
    def __init__(self, app_name: str = "whisperforge"):
        self.app_name = app_name
        self.session_dir = Path.home() / f".{app_name}_sessions"
        self.session_dir.mkdir(exist_ok=True)
        
                # Initialize session tracking
        self._init_session_tracking()

        logger.logger.info(f"SessionManager initialized for {app_name}")
    
    def _init_session_tracking(self):
        """Initialize session tracking in Streamlit session state"""
        if "session_manager" not in st.session_state:
            st.session_state["session_manager"] = self
        
        if "user_session" not in st.session_state:
            # Try to restore from persistent storage first
            restored_session = self._restore_session()
            if restored_session and self._validate_session(restored_session):
                st.session_state["user_session"] = restored_session
                logger.logger.info(f"Session restored for user: {restored_session.user_email}")
            else:
                st.session_state["user_session"] = UserSession()
                logger.logger.info("New session created")
    
    def _get_session_file_path(self, session_id: str) -> Path:
        """Get file path for session storage"""
        return self.session_dir / f"{session_id}.json"
    
    def _generate_session_token(self, user_id: str) -> str:
        """Generate secure session token"""
        data = f"{user_id}:{datetime.now().isoformat()}:{uuid.uuid4()}"
        return hashlib.sha256(data.encode()).hexdigest()
    
    def _persist_session(self, session: UserSession) -> bool:
        """Persist session to secure local storage"""
        try:
            session_file = self._get_session_file_path(session.session_id)
            
            # Update last activity
            session.last_activity = datetime.now()
            
            with open(session_file, 'w') as f:
                json.dump(session.to_dict(), f, indent=2)
            
            # Set file permissions (readable only by user)
            os.chmod(session_file, 0o600)
            
            logger.logger.debug(f"Session persisted: {session.session_id}")
            return True
            
        except Exception as e:
            logger.log_error(e, "Failed to persist session")
            return False
    
    def _restore_session(self) -> Optional[UserSession]:
        """Restore session from persistent storage"""
        try:
            # Look for existing session files
            session_files = list(self.session_dir.glob("*.json"))
            
            if not session_files:
                return None
            
            # Find the most recent valid session
            for session_file in sorted(session_files, key=lambda f: f.stat().st_mtime, reverse=True):
                try:
                    with open(session_file, 'r') as f:
                        session_data = json.load(f)
                    
                    session = UserSession.from_dict(session_data)
                    
                    # Check if session is still valid (within 7 days)
                    if self._validate_session(session):
                        logger.logger.info(f"Restored session: {session.session_id}")
                        return session
                    else:
                        # Clean up expired session
                        session_file.unlink()
                        logger.logger.info(f"Cleaned up expired session: {session_file.name}")
                        
                except Exception as e:
                    logger.logger.warning(f"Failed to restore session from {session_file}: {e}")
                    continue
            
            return None
            
        except Exception as e:
            logger.log_error(e, "Failed to restore session")
            return None
    
    def _validate_session(self, session: UserSession) -> bool:
        """Validate session is still active and not expired"""
        if not session.authenticated:
            return False
        
        # Check if session is within 7 days
        if session.last_activity:
            age = datetime.now() - session.last_activity
            if age > timedelta(days=7):
                logger.logger.info(f"Session expired: {session.session_id}")
                return False
        
        return True
    
    def _cleanup_expired_sessions(self):
        """Clean up expired session files"""
        try:
            for session_file in self.session_dir.glob("*.json"):
                try:
                    with open(session_file, 'r') as f:
                        session_data = json.load(f)
                    
                    session = UserSession.from_dict(session_data)
                    
                    if not self._validate_session(session):
                        session_file.unlink()
                        logger.logger.info(f"Cleaned up expired session: {session_file.name}")
                        
                except Exception as e:
                    logger.logger.warning(f"Error cleaning up session {session_file}: {e}")
                    
        except Exception as e:
            logger.log_error(e, "Error during session cleanup")
    
    # Public API
    
    def is_authenticated(self) -> bool:
        """Check if user is authenticated"""
        session = st.session_state.get("user_session")
        return session and session.authenticated and self._validate_session(session)
    
    def get_user_id(self) -> Optional[str]:
        """Get current user ID"""
        if self.is_authenticated():
            return st.session_state["user_session"].user_id
        return None
    
    def get_user_email(self) -> Optional[str]:
        """Get current user email"""
        if self.is_authenticated():
            return st.session_state["user_session"].user_email
        return None
    
    def get_session_id(self) -> str:
        """Get current session ID"""
        return st.session_state["user_session"].session_id
    
    def authenticate_user(self, user_id: str, user_email: str) -> bool:
        """Set user as authenticated with persistent session"""
        try:
            session = st.session_state["user_session"]
            
            # Update session with auth info
            session.authenticated = True
            session.user_id = user_id
            session.user_email = user_email
            session.session_token = self._generate_session_token(user_id)
            session.last_activity = datetime.now()
            
            # Persist to storage
            if self._persist_session(session):
                logger.logger.info(f"User authenticated: {user_email}")
                return True
            else:
                logger.log_error(Exception(f"Failed to persist authenticated session for {user_email}"), "Authentication failed")
                return False
                
        except Exception as e:
            logger.log_error(e, "Authentication failed")
            return False
    
    def logout(self) -> bool:
        """Log out user and clear session"""
        try:
            session = st.session_state["user_session"]
            
            # Clear session file
            if session.session_id:
                session_file = self._get_session_file_path(session.session_id)
                if session_file.exists():
                    session_file.unlink()
            
            # Reset session in memory
            st.session_state["user_session"] = UserSession()
            
            # Clean up related session state
            for key in list(st.session_state.keys()):
                if key.startswith(('pipeline_', 'thinking_', 'prompts')):
                    del st.session_state[key]
            
            logger.logger.info("User logged out successfully")
            return True
            
        except Exception as e:
            logger.log_error(e, "Logout failed")
            return False
    
    def get_preference(self, key: str, default: Any = None) -> Any:
        """Get user preference with forward compatibility"""
        session = st.session_state["user_session"]
        return session.preferences.get(key, default)
    
    def set_preference(self, key: str, value: Any) -> bool:
        """Set user preference and persist"""
        try:
            session = st.session_state["user_session"]
            session.preferences[key] = value
            
            # Persist if authenticated
            if session.authenticated:
                return self._persist_session(session)
            
            return True
            
        except Exception as e:
            logger.log_error(e, f"Failed to set preference {key}")
            return False
    
    def get_current_page(self) -> str:
        """Get current page"""
        return st.session_state["user_session"].current_page
    
    def set_current_page(self, page: str) -> None:
        """Set current page"""
        st.session_state["user_session"].current_page = page
    
    def is_pipeline_active(self) -> bool:
        """Check if pipeline is active"""
        return st.session_state["user_session"].pipeline_active
    
    def set_pipeline_active(self, active: bool) -> None:
        """Set pipeline active state"""
        st.session_state["user_session"].pipeline_active = active
    
    def get_session_info(self) -> Dict[str, Any]:
        """Get session information for debugging"""
        session = st.session_state["user_session"]
        return {
            "session_id": session.session_id,
            "authenticated": session.authenticated,
            "user_id": session.user_id,
            "user_email": session.user_email,
            "current_page": session.current_page,
            "pipeline_active": session.pipeline_active,
            "created_at": session.created_at.isoformat() if session.created_at else None,
            "last_activity": session.last_activity.isoformat() if session.last_activity else None,
            "preferences": session.preferences
        }
    
    def cleanup(self):
        """Cleanup expired sessions (call periodically)"""
        self._cleanup_expired_sessions()


# Global session manager instance
_session_manager = None

def get_session_manager() -> SessionManager:
    """Get global session manager instance"""
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionManager()
    return _session_manager 