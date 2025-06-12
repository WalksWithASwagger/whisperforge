"""
Minimal monitoring module for WhisperForge
"""

import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

def init_monitoring():
    """Initialize monitoring - minimal implementation"""
    logger.info("Monitoring initialized (minimal mode)")
    return True

def track_error(error: Exception, context: str = ""):
    """Track error - minimal implementation"""
    logger.error(f"Error tracked: {error} | Context: {context}")

def track_performance(operation: str, duration: float):
    """Track performance - minimal implementation"""
    logger.info(f"Performance: {operation} took {duration:.2f}s")

def track_user_action(action: str, user_id: Optional[str] = None):
    """Track user action - minimal implementation"""
    logger.info(f"User action: {action} | User: {user_id}")

def track_page(page: str, user_id: Optional[str] = None):
    """Track page view - minimal implementation"""
    logger.info(f"Page view: {page} | User: {user_id}")

def get_health_status() -> Dict[str, Any]:
    """Get health status - minimal implementation"""
    return {
        "status": "healthy",
        "monitoring": "minimal",
        "timestamp": "now"
    }

# Backward compatibility
class MonitoringManager:
    def __init__(self):
        self.enabled = False
    
    def track_error(self, error, context=""):
        track_error(error, context)
    
    def track_performance(self, operation, duration):
        track_performance(operation, duration)
    
    def track_user_action(self, action, user_id=None):
        track_user_action(action, user_id)

def get_monitoring_manager():
    return MonitoringManager() 