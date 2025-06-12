"""
WhisperForge User Preferences System
Persistent storage for UI preferences like theme and last-used prompts
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional
from core.logging_config import logger


class PreferencesManager:
    """Manages user preferences with persistent storage"""
    
    def __init__(self):
        self.prefs_file = Path.home() / ".whisperforge_prefs.json"
        self._cache = {}
        self._load_preferences()
    
    def _load_preferences(self) -> None:
        """Load preferences from disk into cache"""
        try:
            if self.prefs_file.exists():
                with open(self.prefs_file, 'r', encoding='utf-8') as f:
                    self._cache = json.load(f)
                logger.logger.info(f"Loaded preferences from {self.prefs_file}")
            else:
                self._cache = {}
                logger.logger.info("No existing preferences file found, starting fresh")
        except Exception as e:
            logger.logger.error(f"Error loading preferences: {e}")
            self._cache = {}
    
    def _save_preferences(self) -> bool:
        """Save preferences cache to disk"""
        try:
            # Ensure parent directory exists
            self.prefs_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.prefs_file, 'w', encoding='utf-8') as f:
                json.dump(self._cache, f, indent=2, ensure_ascii=False)
            
            logger.logger.info(f"Saved preferences to {self.prefs_file}")
            return True
        except Exception as e:
            logger.logger.error(f"Error saving preferences: {e}")
            return False
    
    def save_pref(self, key: str, value: Any) -> bool:
        """Save a preference value
        
        Args:
            key: Preference key (e.g., 'theme', 'last_prompt')
            value: Preference value (must be JSON serializable)
            
        Returns:
            bool: True if saved successfully
        """
        try:
            self._cache[key] = value
            return self._save_preferences()
        except Exception as e:
            logger.logger.error(f"Error saving preference {key}: {e}")
            return False
    
    def load_pref(self, key: str, default: Any = None) -> Any:
        """Load a preference value
        
        Args:
            key: Preference key
            default: Default value if key not found
            
        Returns:
            The preference value or default
        """
        return self._cache.get(key, default)
    
    def get_all_prefs(self) -> Dict[str, Any]:
        """Get all preferences as a dictionary"""
        return self._cache.copy()
    
    def delete_pref(self, key: str) -> bool:
        """Delete a preference
        
        Args:
            key: Preference key to delete
            
        Returns:
            bool: True if deleted successfully
        """
        try:
            if key in self._cache:
                del self._cache[key]
                return self._save_preferences()
            return True
        except Exception as e:
            logger.logger.error(f"Error deleting preference {key}: {e}")
            return False
    
    def clear_all_prefs(self) -> bool:
        """Clear all preferences
        
        Returns:
            bool: True if cleared successfully
        """
        try:
            self._cache = {}
            return self._save_preferences()
        except Exception as e:
            logger.logger.error(f"Error clearing preferences: {e}")
            return False


# Global preferences manager instance
_prefs_manager = None

def get_preferences_manager() -> PreferencesManager:
    """Get the global preferences manager instance"""
    global _prefs_manager
    if _prefs_manager is None:
        _prefs_manager = PreferencesManager()
    return _prefs_manager

# Convenience functions
def save_pref(key: str, value: Any) -> bool:
    """Save a preference value"""
    return get_preferences_manager().save_pref(key, value)

def load_pref(key: str, default: Any = None) -> Any:
    """Load a preference value"""
    return get_preferences_manager().load_pref(key, default) 