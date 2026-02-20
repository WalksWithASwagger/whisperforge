"""
MCP (Model Context Protocol) Integration Module
================================================

Provides AI models with context about user data and preferences
via Supabase. Extracted from core.supabase_integration to separate
MCP concerns from the base database client.
"""

import logging
from typing import Any

from postgrest.exceptions import APIError

from .exceptions import DatabaseError

logger = logging.getLogger(__name__)


class MCPSupabaseIntegration:
    """
    Model Context Protocol integration for Supabase
    Provides AI models with context about user data and preferences
    """

    def __init__(self, supabase_client):
        self.db = supabase_client

    def get_user_context(self, user_id: int) -> dict[str, Any]:
        """Get comprehensive user context for AI models"""
        try:
            # Get user profile
            user = self.db.get_user(user_id)
            if not user:
                return {}

            # Get user's knowledge base
            knowledge_base = self.db.get_user_knowledge_base(user_id)

            # Get user's custom prompts
            custom_prompts = self.db.get_user_prompts(user_id)

            # Get recent content history (for style learning)
            recent_content = self.db.get_user_content(user_id, limit=10)

            # Get user analytics
            analytics = self.db.get_user_analytics(user_id, days=30)

            context = {
                "user_profile": {
                    "subscription_tier": user.get("subscription_tier", "free"),
                    "usage_quota": user.get("usage_quota", 60),
                    "usage_current": user.get("usage_current", 0),
                    "created_at": user.get("created_at"),
                },
                "knowledge_base": knowledge_base,
                "custom_prompts": custom_prompts,
                "content_history": recent_content,
                "analytics": analytics,
                "preferences": {
                    "preferred_ai_provider": analytics.get("ai_providers_used", ["openai"])[0]
                    if analytics.get("ai_providers_used")
                    else "openai",
                    "most_used_model": analytics.get("most_used_model", "gpt-3.5-turbo"),
                },
            }

            return context
        except APIError as e:
            logger.error(f"Error getting user context for MCP: {e}")
            return {}
        except DatabaseError as e:
            logger.error(f"Unexpected error getting user context for MCP: {e}")
            return {}

    def update_context_from_interaction(self, user_id: int, interaction_data: dict[str, Any]) -> bool:
        """Update user context based on AI interaction results"""
        try:
            # Log the interaction
            self.db.log_pipeline_execution(user_id, interaction_data)

            # Update usage if provided
            if "duration_seconds" in interaction_data:
                self.db.update_user_usage(user_id, interaction_data["duration_seconds"])

            # Save generated content if provided
            if "content" in interaction_data:
                self.db.save_content(user_id, interaction_data["content"])

            return True
        except APIError as e:
            logger.error(f"Error updating context from interaction: {e}")
            return False
        except DatabaseError as e:
            logger.error(f"Unexpected error updating context from interaction: {e}")
            return False


# Global instance
_mcp_integration = None


def get_mcp_integration() -> MCPSupabaseIntegration:
    """Get or create MCP integration instance"""
    global _mcp_integration
    if _mcp_integration is None:
        # Lazy import to avoid circular imports
        from .supabase_integration import get_supabase_client

        _mcp_integration = MCPSupabaseIntegration(get_supabase_client())
    return _mcp_integration
