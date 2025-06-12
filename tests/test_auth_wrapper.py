"""
Tests for core.auth_wrapper module
Minimal test coverage for authentication functionality
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.auth_wrapper import AuthWrapper, get_auth, authenticate_user


class TestAuthWrapper:
    """Test cases for AuthWrapper class"""
    
    @pytest.fixture
    def mock_supabase_client(self):
        """Mock Supabase client for testing"""
        mock_client = Mock()
        mock_client.client = Mock()
        mock_client.client.table = Mock()
        return mock_client
    
    @pytest.fixture
    def mock_session_manager(self):
        """Mock SessionManager for testing"""
        mock_manager = Mock()
        mock_manager.is_authenticated.return_value = False
        mock_manager.authenticate_user.return_value = True
        mock_manager.get_user_id.return_value = "test_user_123"
        mock_manager.get_user_email.return_value = "test@example.com"
        mock_manager.set_preference.return_value = True
        return mock_manager
    
    def test_auth_wrapper_initialization(self):
        """Test that AuthWrapper can be initialized"""
        with patch('core.auth_wrapper.get_session_manager'), \
             patch('core.auth_wrapper.get_supabase_client'):
            auth_wrapper = AuthWrapper()
            assert auth_wrapper is not None
    
    @patch('core.auth_wrapper.get_session_manager')
    @patch('core.auth_wrapper.get_supabase_client')
    @patch('core.auth_wrapper.verify_password')
    def test_invalid_password_returns_false(self, mock_verify_password, mock_get_supabase, mock_get_session_manager,
                                          mock_supabase_client, mock_session_manager):
        """Test that invalid password returns False"""
        # Setup mocks
        mock_get_supabase.return_value = mock_supabase_client
        mock_get_session_manager.return_value = mock_session_manager
        mock_verify_password.return_value = False  # Invalid password
        
        # Mock user data from database
        user_data = {
            "id": "test_user_123",
            "email": "test@example.com",
            "password": "$2b$12$hashedpassword"
        }
        
        # Create a simple mock chain for the database query
        mock_execute = Mock()
        mock_execute.data = [user_data]
        
        mock_eq = Mock()
        mock_eq.execute.return_value = mock_execute
        
        mock_select = Mock()
        mock_select.eq.return_value = mock_eq
        
        mock_table = Mock()
        mock_table.select.return_value = mock_select
        
        mock_supabase_client.client.table.return_value = mock_table
        
        # Create AuthWrapper and test authentication
        auth_wrapper = AuthWrapper()
        result = auth_wrapper.authenticate_user("test@example.com", "wrongpassword")
        
        # Assertions
        assert result is False
        mock_session_manager.authenticate_user.assert_not_called()
    
    @patch('core.auth_wrapper.get_session_manager')
    @patch('core.auth_wrapper.get_supabase_client')
    def test_user_not_found_returns_false(self, mock_get_supabase, mock_get_session_manager,
                                        mock_supabase_client, mock_session_manager):
        """Test that non-existent user returns False"""
        # Setup mocks
        mock_get_supabase.return_value = mock_supabase_client
        mock_get_session_manager.return_value = mock_session_manager
        
        # Mock empty database query response (user not found)
        mock_execute = Mock()
        mock_execute.data = []  # No user found
        
        mock_eq = Mock()
        mock_eq.execute.return_value = mock_execute
        
        mock_select = Mock()
        mock_select.eq.return_value = mock_eq
        
        mock_table = Mock()
        mock_table.select.return_value = mock_select
        
        mock_supabase_client.client.table.return_value = mock_table
        
        # Create AuthWrapper and test authentication
        auth_wrapper = AuthWrapper()
        result = auth_wrapper.authenticate_user("nonexistent@example.com", "password")
        
        # Assertions
        assert result is False
        mock_session_manager.authenticate_user.assert_not_called()
    
    def test_is_authenticated_delegates_to_session_manager(self, mock_session_manager):
        """Test that is_authenticated delegates to session manager"""
        with patch('core.auth_wrapper.get_session_manager', return_value=mock_session_manager):
            mock_session_manager.is_authenticated.return_value = True
            
            auth_wrapper = AuthWrapper()
            result = auth_wrapper.is_authenticated()
            
            assert result is True
            mock_session_manager.is_authenticated.assert_called_once()
    
    def test_get_user_id_delegates_to_session_manager(self, mock_session_manager):
        """Test that get_user_id delegates to session manager"""
        with patch('core.auth_wrapper.get_session_manager', return_value=mock_session_manager):
            mock_session_manager.get_user_id.return_value = "test_user_123"
            
            auth_wrapper = AuthWrapper()
            result = auth_wrapper.get_user_id()
            
            assert result == "test_user_123"
            mock_session_manager.get_user_id.assert_called_once()


class TestAuthWrapperFunctions:
    """Test cases for module-level auth functions"""
    
    @patch('core.auth_wrapper.get_auth')
    def test_authenticate_user_function(self, mock_get_auth):
        """Test the authenticate_user convenience function"""
        mock_auth = Mock()
        mock_auth.authenticate_user.return_value = True
        mock_get_auth.return_value = mock_auth
        
        result = authenticate_user("test@example.com", "password")
        
        assert result is True
        mock_auth.authenticate_user.assert_called_once_with("test@example.com", "password")
    
    def test_get_auth_returns_singleton(self):
        """Test that get_auth returns a singleton instance"""
        auth1 = get_auth()
        auth2 = get_auth()
        
        assert auth1 is auth2  # Should be the same instance


if __name__ == "__main__":
    pytest.main([__file__]) 