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
from core.logging_config import logger
from core.supabase_integration import get_supabase_client


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
    Uses Supabase for persistent storage with local file fallback
    """
    
    def __init__(self, app_name: str = "whisperforge"):
        self.app_name = app_name
        
        # Try to get Supabase client for cloud storage
        try:
            self.supabase = get_supabase_client()
            self.use_database = True
            logger.logger.info("SessionManager using Supabase storage")
        except Exception as e:
            self.supabase = None
            self.use_database = False
            logger.logger.warning(f"Supabase not available, using memory-only sessions: {e}")
        
        # Local fallback directory (only used if Supabase unavailable)
        self.session_dir = None
        if not self.use_database:
            try:
                self.session_dir = Path.home() / f".{app_name}_sessions"
                self.session_dir.mkdir(exist_ok=True)
                logger.logger.info("Using local session storage fallback")
            except Exception as e:
                logger.logger.warning(f"Local session storage unavailable: {e}")
        
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
        """Get file path for session storage (fallback only)"""
        if self.session_dir:
            return self.session_dir / f"{session_id}.json"
        return None
    
    def _generate_session_token(self, user_id: str) -> str:
        """Generate secure session token"""
        data = f"{user_id}:{datetime.now().isoformat()}:{uuid.uuid4()}"
        return hashlib.sha256(data.encode()).hexdigest()
    
    def _persist_session(self, session: UserSession) -> bool:
        """Persist session to Supabase or local storage"""
        try:
            # Update last activity
            session.last_activity = datetime.now()
            session_data = session.to_dict()
            
            if self.use_database and self.supabase:
                # Store in Supabase sessions table
                try:
                    result = self.supabase.client.table("sessions").upsert({
                        "session_id": session.session_id,
                        "user_id": session.user_id,
                        "session_data": json.dumps(session_data),
                        "expires_at": (datetime.now() + timedelta(days=7)).isoformat(),
                        "updated_at": datetime.now().isoformat()
                    }).execute()
                    
                    if result.data:
                        logger.logger.debug(f"Session persisted to Supabase: {session.session_id}")
                        return True
                    else:
                        raise Exception("No data returned from upsert")
                        
                except Exception as db_error:
                    logger.logger.warning(f"Supabase session storage failed, trying local fallback: {db_error}")
                    # Fall through to local storage
            
            # Local file fallback
            if self.session_dir:
                session_file = self._get_session_file_path(session.session_id)
                if session_file:
                    with open(session_file, 'w') as f:
                        json.dump(session_data, f, indent=2)
                    
                    # Set file permissions (readable only by user)
                    os.chmod(session_file, 0o600)
                    logger.logger.debug(f"Session persisted locally: {session.session_id}")
                    return True
            
            # If we get here, no storage method worked
            logger.logger.warning("No session storage available - session will not persist")
            return False
            
        except Exception as e:
            logger.log_error(e, "Failed to persist session")
            return False
    
    def _restore_session(self) -> Optional[UserSession]:
        """Restore session from Supabase or local storage"""
        try:
            # Try Supabase first
            if self.use_database and self.supabase:
                try:
                    # Look for valid sessions for any user (we'll validate expiry)
                    result = self.supabase.client.table("sessions").select("*").gte(
                        "expires_at", datetime.now().isoformat()
                    ).order("updated_at", desc=True).limit(1).execute()
                    
                    if result.data:
                        session_record = result.data[0]
                        session_data = json.loads(session_record["session_data"])
                        session = UserSession.from_dict(session_data)
                        
                        if self._validate_session(session):
                            logger.logger.info(f"Restored session from Supabase: {session.session_id}")
                            return session
                            
                except Exception as db_error:
                    logger.logger.warning(f"Failed to restore from Supabase: {db_error}")
            
            # Try local file fallback
            if self.session_dir and self.session_dir.exists():
                session_files = list(self.session_dir.glob("*.json"))
                
                if session_files:
                    # Find the most recent valid session
                    for session_file in sorted(session_files, key=lambda f: f.stat().st_mtime, reverse=True):
                        try:
                            with open(session_file, 'r') as f:
                                session_data = json.load(f)
                            
                            session = UserSession.from_dict(session_data)
                            
                            if self._validate_session(session):
                                logger.logger.info(f"Restored session from local file: {session.session_id}")
                                return session
                            else:
                                # Clean up expired session
                                session_file.unlink()
                                logger.logger.info(f"Cleaned up expired local session: {session_file.name}")
                                
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
        """Clean up expired session files and database records"""
        try:
            # Clean up Supabase sessions
            if self.use_database and self.supabase:
                try:
                    self.supabase.client.table("sessions").delete().lt(
                        "expires_at", datetime.now().isoformat()
                    ).execute()
                    logger.logger.debug("Cleaned up expired Supabase sessions")
                except Exception as e:
                    logger.logger.warning(f"Failed to cleanup Supabase sessions: {e}")
            
            # Clean up local files
            if self.session_dir and self.session_dir.exists():
                for session_file in self.session_dir.glob("*.json"):
                    try:
                        with open(session_file, 'r') as f:
                            session_data = json.load(f)
                        
                        session = UserSession.from_dict(session_data)
                        
                        if not self._validate_session(session):
                            session_file.unlink()
                            logger.logger.info(f"Cleaned up expired local session: {session_file.name}")
                            
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
            
            # Persist to storage (will try Supabase then local fallback)
            if self._persist_session(session):
                logger.logger.info(f"User authenticated: {user_email}")
                return True
            else:
                logger.logger.warning(f"Session persisted in memory only for {user_email}")
                return True  # Still allow login even if persistence fails
                
        except Exception as e:
            logger.log_error(e, "Authentication failed")
            return False
    
    def logout(self) -> bool:
        """Log out user and clear session"""
        try:
            session = st.session_state["user_session"]
            
            # Clear from Supabase
            if self.use_database and self.supabase and session.session_id:
                try:
                    self.supabase.client.table("sessions").delete().eq(
                        "session_id", session.session_id
                    ).execute()
                except Exception as e:
                    logger.logger.warning(f"Failed to delete session from Supabase: {e}")
            
            # Clear local session file
            if self.session_dir and session.session_id:
                session_file = self._get_session_file_path(session.session_id)
                if session_file and session_file.exists():
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