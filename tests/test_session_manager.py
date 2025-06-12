"""
Tests for WhisperForge Session Management System
Tests session persistence, authentication, and forward compatibility
"""

import pytest
import os
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

# Import the session management classes
from core.session_manager import SessionManager, UserSession, get_session_manager
from core.auth_wrapper import AuthWrapper, get_auth


class TestUserSession:
    """Test UserSession dataclass functionality"""
    
    def test_session_initialization(self):
        """Test session creates with default values"""
        session = UserSession()
        
        assert session.authenticated == False
        assert session.user_id is None
        assert session.user_email is None
        assert session.session_token is None
        assert session.current_page == "Content Pipeline"
        assert session.pipeline_active == False
        assert session.session_id is not None
        assert session.created_at is not None
        assert session.last_activity is not None
        
        # Check default preferences
        assert session.preferences is not None
        assert session.preferences['ai_provider'] == 'OpenAI'
        assert session.preferences['ai_model'] == 'gpt-4o'
        assert session.preferences['editor_enabled'] == False
        assert session.preferences['research_enabled'] == True
        assert session.preferences['thinking_enabled'] == True
    
    def test_session_serialization(self):
        """Test session can be serialized and deserialized"""
        session = UserSession()
        session.authenticated = True
        session.user_id = "test_user_123"
        session.user_email = "test@example.com"
        
        # Serialize to dict
        data = session.to_dict()
        
        assert data['authenticated'] == True
        assert data['user_id'] == "test_user_123"
        assert data['user_email'] == "test@example.com"
        assert 'created_at' in data
        assert 'last_activity' in data
        
        # Deserialize back to object
        restored_session = UserSession.from_dict(data)
        
        assert restored_session.authenticated == True
        assert restored_session.user_id == "test_user_123"
        assert restored_session.user_email == "test@example.com"
        assert restored_session.created_at is not None
        assert restored_session.last_activity is not None
    
    def test_forward_compatibility(self):
        """Test session ignores unknown fields (forward compatibility)"""
        data = {
            'authenticated': True,
            'user_id': "test_user",
            'user_email': "test@example.com",
            'unknown_field': "should_be_ignored",
            'future_feature': {"complex": "data"},
            'preferences': {'ai_provider': 'OpenAI'}
        }
        
        # Should not raise error with unknown fields
        session = UserSession.from_dict(data)
        
        assert session.authenticated == True
        assert session.user_id == "test_user"
        assert session.user_email == "test@example.com"
        assert hasattr(session, 'unknown_field') == False
        assert hasattr(session, 'future_feature') == False


class TestSessionManager:
    """Test SessionManager functionality"""
    
    @pytest.fixture
    def temp_session_dir(self):
        """Create temporary directory for session files"""
        temp_dir = Path(tempfile.mkdtemp())
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def mock_streamlit(self):
        """Mock Streamlit session state"""
        with patch('core.session_manager.st') as mock_st:
            mock_st.session_state = {}
            yield mock_st
    
    def test_session_manager_initialization(self, temp_session_dir, mock_streamlit):
        """Test session manager initializes correctly"""
        with patch.object(Path, 'home', return_value=temp_session_dir.parent):
            manager = SessionManager("test_app")
            
            assert manager.app_name == "test_app"
            assert manager.session_dir.exists()
            assert "session_manager" in mock_streamlit.session_state
            assert "user_session" in mock_streamlit.session_state
    
    def test_session_persistence(self, temp_session_dir, mock_streamlit):
        """Test session can be persisted and restored"""
        with patch.object(Path, 'home', return_value=temp_session_dir.parent):
            # Clean up any existing session files first
            session_dir = temp_session_dir.parent / ".test_app_sessions"
            if session_dir.exists():
                shutil.rmtree(session_dir)
                
            manager = SessionManager("test_app")
            
            # Create session with data
            session = mock_streamlit.session_state["user_session"]
            session.authenticated = True
            session.user_id = "test_user_123"
            session.user_email = "test@example.com"
            
            # Persist session
            success = manager._persist_session(session)
            assert success == True
            
            # Check session file was created
            session_files = list(manager.session_dir.glob("*.json"))
            assert len(session_files) == 1
            
            # Restore session
            restored = manager._restore_session()
            assert restored is not None
            assert restored.authenticated == True
            assert restored.user_id == "test_user_123"
            assert restored.user_email == "test@example.com"
    
    def test_session_expiration(self, temp_session_dir, mock_streamlit):
        """Test expired sessions are not restored"""
        with patch.object(Path, 'home', return_value=temp_session_dir.parent):
            # Clean up any existing session files first
            session_dir = temp_session_dir.parent / ".test_app_sessions"
            if session_dir.exists():
                shutil.rmtree(session_dir)
                
            manager = SessionManager("test_app")
            
            # Create old session
            session = mock_streamlit.session_state["user_session"]
            session.authenticated = True
            session.user_id = "old_user"
            session.last_activity = datetime.now() - timedelta(days=8)  # 8 days old
            
            # Should not validate due to age
            assert manager._validate_session(session) == False
    
    def test_authentication_flow(self, temp_session_dir, mock_streamlit):
        """Test complete authentication flow"""
        with patch.object(Path, 'home', return_value=temp_session_dir.parent):
            # Clean up any existing session files first
            session_dir = temp_session_dir.parent / ".test_app_sessions"
            if session_dir.exists():
                import shutil
                shutil.rmtree(session_dir)
                
            manager = SessionManager("test_app")
            
            # Initially not authenticated
            assert manager.is_authenticated() == False
            assert manager.get_user_id() is None
            assert manager.get_user_email() is None
            
            # Authenticate user
            success = manager.authenticate_user("user_123", "test@example.com")
            assert success == True
            
            # Should now be authenticated
            assert manager.is_authenticated() == True
            assert manager.get_user_id() == "user_123"
            assert manager.get_user_email() == "test@example.com"
            
            # Logout
            success = manager.logout()
            assert success == True
            
            # Should no longer be authenticated
            assert manager.is_authenticated() == False
            assert manager.get_user_id() is None
            assert manager.get_user_email() is None
    
    def test_preferences_management(self, temp_session_dir, mock_streamlit):
        """Test preference management"""
        with patch.object(Path, 'home', return_value=temp_session_dir.parent):
            manager = SessionManager("test_app")
            
            # Set preferences
            assert manager.set_preference("test_key", "test_value") == True
            assert manager.set_preference("number_key", 42) == True
            
            # Get preferences
            assert manager.get_preference("test_key") == "test_value"
            assert manager.get_preference("number_key") == 42
            assert manager.get_preference("nonexistent", "default") == "default"
    
    def test_page_management(self, temp_session_dir, mock_streamlit):
        """Test page state management"""
        with patch.object(Path, 'home', return_value=temp_session_dir.parent):
            manager = SessionManager("test_app")
            
            # Default page
            assert manager.get_current_page() == "Content Pipeline"
            
            # Set page
            manager.set_current_page("Settings")
            assert manager.get_current_page() == "Settings"
    
    def test_pipeline_state_management(self, temp_session_dir, mock_streamlit):
        """Test pipeline state management"""
        with patch.object(Path, 'home', return_value=temp_session_dir.parent):
            manager = SessionManager("test_app")
            
            # Default state
            assert manager.is_pipeline_active() == False
            
            # Set active
            manager.set_pipeline_active(True)
            assert manager.is_pipeline_active() == True
            
            # Set inactive
            manager.set_pipeline_active(False)
            assert manager.is_pipeline_active() == False


class TestAuthWrapper:
    """Test AuthWrapper functionality"""
    
    @pytest.fixture
    def mock_supabase_client(self):
        """Mock Supabase client"""
        mock_client = Mock()
        mock_client.client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []
        return mock_client
    
    @pytest.fixture
    def mock_session_manager(self):
        """Mock session manager"""
        with patch('core.auth_wrapper.get_session_manager') as mock_get:
            mock_manager = Mock()
            mock_get.return_value = mock_manager
            yield mock_manager
    
    def test_auth_wrapper_initialization(self, mock_session_manager):
        """Test auth wrapper initializes correctly"""
        with patch('core.auth_wrapper.get_supabase_client'):
            wrapper = AuthWrapper()
            
            assert wrapper.session_manager == mock_session_manager
    
    def test_authentication_success(self, mock_session_manager, mock_supabase_client):
        """Test successful authentication"""
        # Skip if no Supabase credentials
        if not (os.getenv('SUPABASE_URL') and os.getenv('SUPABASE_ANON_KEY')):
            pytest.skip("Supabase credentials not available")
            
        with patch('core.auth_wrapper.get_supabase_client', return_value=mock_supabase_client):
            # Mock user data
            mock_supabase_client.client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
                {"id": "user_123", "email": "test@example.com", "password": "$2b$12$test_hash"}
            ]
            
            # Mock password verification
            with patch('core.auth_wrapper.verify_password', return_value=True):
                # Mock session manager authentication
                mock_session_manager.authenticate_user.return_value = True
                
                wrapper = AuthWrapper()
                wrapper.supabase_client = mock_supabase_client
                
                result = wrapper.authenticate_user("test@example.com", "password")
                
                assert result == True
                mock_session_manager.authenticate_user.assert_called_once_with("user_123", "test@example.com")
    
    def test_authentication_user_not_found(self, mock_session_manager, mock_supabase_client):
        """Test authentication with non-existent user"""
        with patch('core.auth_wrapper.get_supabase_client', return_value=mock_supabase_client):
            # Mock no user found
            mock_supabase_client.client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []
            
            wrapper = AuthWrapper()
            wrapper.supabase_client = mock_supabase_client
            
            result = wrapper.authenticate_user("nonexistent@example.com", "password")
            
            assert result == False
    
    def test_authentication_wrong_password(self, mock_session_manager, mock_supabase_client):
        """Test authentication with wrong password"""
        with patch('core.auth_wrapper.get_supabase_client', return_value=mock_supabase_client):
            # Mock user data
            mock_supabase_client.client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
                {"id": "user_123", "email": "test@example.com", "password": "$2b$12$test_hash"}
            ]
            
            # Mock password verification failure
            with patch('core.auth_wrapper.verify_password', return_value=False):
                wrapper = AuthWrapper()
                wrapper.supabase_client = mock_supabase_client
                
                result = wrapper.authenticate_user("test@example.com", "wrong_password")
                
                assert result == False
    
    def test_legacy_password_migration(self, mock_session_manager, mock_supabase_client):
        """Test legacy password migration during authentication"""
        # Skip if no Supabase credentials
        if not (os.getenv('SUPABASE_URL') and os.getenv('SUPABASE_ANON_KEY')):
            pytest.skip("Supabase credentials not available")
            
        with patch('core.auth_wrapper.get_supabase_client', return_value=mock_supabase_client):
            # Mock user with legacy password
            mock_supabase_client.client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
                {"id": "user_123", "email": "test@example.com", "password": "legacy_hash"}
            ]
            
            # Mock legacy password verification
            with patch('core.auth_wrapper.legacy_hash_password', return_value="legacy_hash"):
                with patch('core.auth_wrapper.hash_password', return_value="new_bcrypt_hash"):
                    # Mock database update
                    mock_update = Mock()
                    mock_supabase_client.client.table.return_value.update.return_value.eq.return_value.execute = mock_update
                    
                    # Mock session manager authentication
                    mock_session_manager.authenticate_user.return_value = True
                    
                    wrapper = AuthWrapper()
                    wrapper.supabase_client = mock_supabase_client
                    
                    result = wrapper.authenticate_user("test@example.com", "password")
                    
                    assert result == True
                    # Verify password was updated
                    mock_supabase_client.client.table.return_value.update.assert_called_once()
    
    def test_user_registration(self, mock_session_manager, mock_supabase_client):
        """Test user registration"""
        # Skip if no Supabase credentials
        if not (os.getenv('SUPABASE_URL') and os.getenv('SUPABASE_ANON_KEY')):
            pytest.skip("Supabase credentials not available")
            
        with patch('core.auth_wrapper.get_supabase_client', return_value=mock_supabase_client):
            # Mock no existing user
            mock_supabase_client.client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []
            
            # Mock successful user creation
            mock_supabase_client.client.table.return_value.insert.return_value.execute.return_value.data = [
                {"id": "new_user_123", "email": "new@example.com"}
            ]
            
            # Mock session manager authentication
            mock_session_manager.authenticate_user.return_value = True
            
            with patch('core.auth_wrapper.hash_password', return_value="hashed_password"):
                wrapper = AuthWrapper()
                wrapper.supabase_client = mock_supabase_client
                
                result = wrapper.register_user("new@example.com", "password")
                
                assert result == True
                mock_session_manager.authenticate_user.assert_called_once_with("new_user_123", "new@example.com")
    
    def test_api_key_management(self, mock_session_manager, mock_supabase_client):
        """Test API key management"""
        # Skip if no Supabase credentials
        if not (os.getenv('SUPABASE_URL') and os.getenv('SUPABASE_ANON_KEY')):
            pytest.skip("Supabase credentials not available")
            
        with patch('core.auth_wrapper.get_supabase_client', return_value=mock_supabase_client):
            wrapper = AuthWrapper()
            wrapper.supabase_client = mock_supabase_client
            
            # Mock authenticated state
            mock_session_manager.is_authenticated.return_value = True
            mock_session_manager.get_user_id.return_value = "user_123"
            
            # Mock get API keys
            mock_session_manager.get_preference.return_value = {"openai_api_key": "test_key"}
            
            keys = wrapper.get_api_keys()
            assert keys == {"openai_api_key": "test_key"}
            
            # Mock update API key
            mock_supabase_client.client.table.return_value.upsert.return_value.execute.return_value.data = [{}]
            mock_session_manager.set_preference.return_value = True
            
            result = wrapper.update_api_key("openai_api_key", "new_key")
            assert result == True


class TestBackwardCompatibility:
    """Test backward compatibility functions"""
    
    def test_backward_compatible_functions_exist(self):
        """Test that all backward compatible functions exist"""
        from core.auth_wrapper import (
            authenticate_user,
            register_user_supabase,
            get_user_api_keys_supabase,
            update_api_key_supabase,
            get_user_prompts_supabase,
            save_user_prompt_supabase
        )
        
        # Just check they exist and are callable
        assert callable(authenticate_user)
        assert callable(register_user_supabase)
        assert callable(get_user_api_keys_supabase)
        assert callable(update_api_key_supabase)
        assert callable(get_user_prompts_supabase)
        assert callable(save_user_prompt_supabase)
    
    @patch('core.auth_wrapper.get_auth')
    def test_backward_compatible_authentication(self, mock_get_auth):
        """Test backward compatible authentication function"""
        from core.auth_wrapper import authenticate_user
        
        mock_auth = Mock()
        mock_auth.authenticate_user.return_value = True
        mock_get_auth.return_value = mock_auth
        
        result = authenticate_user("test@example.com", "password")
        
        assert result == True
        mock_auth.authenticate_user.assert_called_once_with("test@example.com", "password")


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 