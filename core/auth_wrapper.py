"""
Authentication Wrapper for WhisperForge
Integrates SessionManager with existing Supabase authentication
Provides backward compatibility while adding session persistence
"""

import streamlit as st
from typing import Optional, Dict, Any
from .session_manager import get_session_manager
from .supabase_integration import get_supabase_client
from .utils import hash_password, verify_password, legacy_hash_password
from core.logging_config import logger


class AuthWrapper:
    """
    Authentication wrapper that provides persistent sessions
    while maintaining compatibility with existing auth patterns
    """
    
    def __init__(self):
        self.session_manager = get_session_manager()
        self.supabase_client = None
        self._init_supabase()
    
    def _init_supabase(self):
        """Initialize Supabase client"""
        try:
            from .supabase_integration import get_supabase_client
            self.supabase_client = get_supabase_client()
        except Exception as e:
            logger.log_error(e, "Failed to initialize Supabase")
            self.supabase_client = None
    
    def is_authenticated(self) -> bool:
        """Check if user is authenticated (backward compatible)"""
        return self.session_manager.is_authenticated()
    
    def get_user_id(self) -> Optional[str]:
        """Get current user ID (backward compatible)"""
        return self.session_manager.get_user_id()
    
    def get_user_email(self) -> Optional[str]:
        """Get current user email (backward compatible)"""
        return self.session_manager.get_user_email()
    
    def authenticate_user(self, email: str, password: str) -> bool:
        """
        Authenticate user with Supabase and create persistent session
        Maintains backward compatibility with existing auth logic
        """
        try:
            logger.logger.info(f"Authentication attempt for: {email}")
            
            if not self.supabase_client:
                logger.log_error(Exception("Supabase client not available"), "Authentication failed")
                return False
            
            # Get user by email from Supabase
            result = self.supabase_client.client.table("users").select("*").eq("email", email).execute()
            
            if not result.data:
                logger.logger.warning(f"User not found: {email}")
                return False
            
            user = result.data[0]
            stored_password = user.get("password", "")
            
            # Verify password (bcrypt or legacy)
            password_valid = False
            password_migrated = False
            
            if stored_password.startswith('$2b$'):
                # bcrypt password
                password_valid = verify_password(password, stored_password)
            else:
                # Legacy password - check and migrate
                if legacy_hash_password(password) == stored_password:
                    password_valid = True
                    password_migrated = True
                    
                    # Migrate to bcrypt
                    try:
                        new_hash = hash_password(password)
                        self.supabase_client.client.table("users").update(
                            {"password": new_hash}
                        ).eq("id", user["id"]).execute()
                        logger.logger.info(f"Password migrated to bcrypt for user: {email}")
                    except Exception as e:
                        logger.log_error(e, "Failed to migrate password")
            
            if password_valid:
                # Create persistent session using SessionManager
                if self.session_manager.authenticate_user(user["id"], email):
                    logger.logger.info(f"User authenticated successfully: {email}")
                    
                    # Load user preferences from database
                    self._load_user_preferences(user["id"])
                    
                    return True
                else:
                    logger.log_error(Exception(f"Failed to create persistent session for: {email}"), "Authentication failed")
                    return False
            else:
                logger.logger.warning(f"Invalid password for user: {email}")
                return False
        
        except Exception as e:
            logger.log_error(e, f"Authentication error for {email}")
            return False
    
    def register_user(self, email: str, password: str) -> bool:
        """Register new user and create session"""
        try:
            if not self.supabase_client:
                logger.log_error(Exception("Supabase client not available for registration"), "Registration failed")
                return False
            
            # Check if user already exists
            existing = self.supabase_client.client.table("users").select("id").eq("email", email).execute()
            if existing.data:
                logger.logger.warning(f"User already exists: {email}")
                return False
            
            # Hash password
            hashed_password = hash_password(password)
            
            # Create user in database
            user_data = {
                "email": email,
                "password": hashed_password,
                "created_at": "now()"
            }
            
            result = self.supabase_client.client.table("users").insert(user_data).execute()
            
            if result.data:
                user = result.data[0]
                logger.logger.info(f"User registered successfully: {email}")
                
                # Create session for new user
                if self.session_manager.authenticate_user(user["id"], email):
                    logger.logger.info(f"Session created for new user: {email}")
                    return True
                else:
                    logger.log_error(Exception(f"Failed to create session for new user: {email}"), "Registration failed")
                    return False
            else:
                logger.log_error(Exception(f"Failed to create user in database: {email}"), "Registration failed")
                return False
        
        except Exception as e:
            logger.log_error(e, f"Registration error for {email}")
            return False
    
    def logout(self) -> bool:
        """Log out user and clear session"""
        try:
            email = self.get_user_email()
            if self.session_manager.logout():
                logger.logger.info(f"User logged out: {email}")
                return True
            else:
                logger.log_error(Exception(f"Failed to logout user: {email}"), "Logout failed")
                return False
        except Exception as e:
            logger.log_error(e, "Logout error")
            return False
    
    def _load_user_preferences(self, user_id: str):
        """Load user preferences from database into session"""
        try:
            if not self.supabase_client:
                return
            
            # Load API keys
            api_keys_result = self.supabase_client.client.table("api_keys").select(
                "key_name, key_value"
            ).eq("user_id", user_id).execute()
            
            api_keys = {}
            for item in api_keys_result.data:
                api_keys[item["key_name"]] = item["key_value"]
            
            # Load custom prompts
            prompts_result = self.supabase_client.client.table("prompts").select(
                "prompt_type, content"
            ).eq("user_id", user_id).execute()
            
            prompts = {}
            for item in prompts_result.data:
                prompts[item["prompt_type"]] = item["content"]
            
            # Store in session preferences
            self.session_manager.set_preference("api_keys", api_keys)
            self.session_manager.set_preference("custom_prompts", prompts)
            
            logger.logger.debug(f"Loaded preferences for user: {user_id}")
            
        except Exception as e:
            logger.log_error(e, "Failed to load user preferences")
    
    def get_api_keys(self) -> Dict[str, str]:
        """Get user API keys from session cache"""
        return self.session_manager.get_preference("api_keys", {})
    
    def update_api_key(self, key_name: str, key_value: str) -> bool:
        """Update API key in database and session cache"""
        try:
            if not self.supabase_client or not self.is_authenticated():
                return False
            
            user_id = self.get_user_id()
            
            # Update in database
            result = self.supabase_client.client.table("api_keys").upsert({
                "user_id": user_id,
                "key_name": key_name,
                "key_value": key_value,
                "updated_at": "now()"
            }).execute()
            
            if result.data:
                # Update session cache
                api_keys = self.get_api_keys()
                api_keys[key_name] = key_value
                self.session_manager.set_preference("api_keys", api_keys)
                
                logger.logger.info(f"API key updated: {key_name}")
                return True
            else:
                logger.log_error(Exception(f"Failed to update API key: {key_name}"), "API key update failed")
                return False
        
        except Exception as e:
            logger.log_error(e, f"Error updating API key {key_name}")
            return False
    
    def get_custom_prompts(self) -> Dict[str, str]:
        """Get user custom prompts from session cache"""
        return self.session_manager.get_preference("custom_prompts", {})
    
    def update_custom_prompt(self, prompt_type: str, content: str) -> bool:
        """Update custom prompt in database and session cache"""
        try:
            if not self.supabase_client or not self.is_authenticated():
                return False
            
            user_id = self.get_user_id()
            
            # Update in database
            result = self.supabase_client.client.table("prompts").upsert({
                "user_id": user_id,
                "prompt_type": prompt_type,
                "content": content,
                "updated_at": "now()"
            }).execute()
            
            if result.data:
                # Update session cache
                prompts = self.get_custom_prompts()
                prompts[prompt_type] = content
                self.session_manager.set_preference("custom_prompts", prompts)
                
                logger.info(f"Custom prompt updated: {prompt_type}")
                return True
            else:
                logger.log_error(Exception(f"Failed to update custom prompt: {prompt_type}"), "Custom prompt update failed")
                return False
        
        except Exception as e:
            logger.log_error(e, f"Error updating custom prompt {prompt_type}")
            return False
    
    # Session Manager delegation methods
    
    def get_preference(self, key: str, default: Any = None) -> Any:
        """Get user preference (delegated to SessionManager)"""
        return self.session_manager.get_preference(key, default)
    
    def set_preference(self, key: str, value: Any) -> bool:
        """Set user preference (delegated to SessionManager)"""
        return self.session_manager.set_preference(key, value)
    
    def get_current_page(self) -> str:
        """Get current page (delegated to SessionManager)"""
        return self.session_manager.get_current_page()
    
    def set_current_page(self, page: str) -> None:
        """Set current page (delegated to SessionManager)"""
        self.session_manager.set_current_page(page)
    
    def is_pipeline_active(self) -> bool:
        """Check if pipeline is active (delegated to SessionManager)"""
        return self.session_manager.is_pipeline_active()
    
    def set_pipeline_active(self, active: bool) -> None:
        """Set pipeline active state (delegated to SessionManager)"""
        self.session_manager.set_pipeline_active(active)
    
    def get_session_info(self) -> Dict[str, Any]:
        """Get session information for debugging"""
        return self.session_manager.get_session_info()


# Global auth wrapper instance
_auth_wrapper = None

def get_auth() -> AuthWrapper:
    """Get global authentication wrapper instance"""
    global _auth_wrapper
    if _auth_wrapper is None:
        _auth_wrapper = AuthWrapper()
    return _auth_wrapper


# Backward compatibility functions for existing code
def authenticate_user(email: str, password: str) -> bool:
    """Backward compatible authentication function"""
    return get_auth().authenticate_user(email, password)

def register_user_supabase(email: str, password: str) -> bool:
    """Backward compatible registration function"""
    return get_auth().register_user(email, password)

def get_user_api_keys_supabase() -> Dict[str, str]:
    """Backward compatible API keys function"""
    return get_auth().get_api_keys()

def update_api_key_supabase(key_name: str, key_value: str) -> bool:
    """Backward compatible API key update function"""
    return get_auth().update_api_key(key_name, key_value)

def get_user_prompts_supabase() -> Dict[str, str]:
    """Backward compatible prompts function"""
    return get_auth().get_custom_prompts()

def save_user_prompt_supabase(prompt_type: str, content: str) -> bool:
    """Backward compatible prompt save function"""
    return get_auth().update_custom_prompt(prompt_type, content) 