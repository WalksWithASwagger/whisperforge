"""
Supabase Integration Module
==========================

Handles Supabase database connections and operations for WhisperForge.
Designed to work with MCP (Model Context Protocol) for enhanced AI integration.
"""

import logging
import os
from datetime import datetime, timedelta
from typing import Any

from dotenv import load_dotenv
from postgrest.exceptions import APIError
from supabase import Client, create_client

from .constants import DEFAULT_ANALYTICS_DAYS, DEFAULT_CONTENT_QUERY_LIMIT, DEFAULT_USAGE_QUOTA_MINUTES
from .utils import hash_password

# Load environment variables
load_dotenv()

# Import hash_password function from utils instead of app

logger = logging.getLogger(__name__)


class SupabaseClient:
    """
    Supabase client wrapper with MCP integration capabilities
    """

    def __init__(self):
        self.url = os.getenv("SUPABASE_URL")
        # Handle both SUPABASE_KEY and SUPABASE_ANON_KEY for backward compatibility
        self.key = os.getenv("SUPABASE_ANON_KEY") or os.getenv("SUPABASE_KEY")
        self.service_role_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

        if not self.url or not self.key:
            raise ValueError(
                "SUPABASE_URL and SUPABASE_ANON_KEY (or SUPABASE_KEY) must be set in environment variables"
            )

        self.client: Client = create_client(self.url, self.key)
        self.admin_client: Client | None = None

        if self.service_role_key:
            self.admin_client = create_client(self.url, self.service_role_key)

        logger.info("Supabase client initialized successfully")

    def test_connection(self) -> bool:
        """Test the Supabase connection"""
        try:
            # Try a simple query to test connectivity
            self.client.table("users").select("id").limit(1).execute()
            logger.info("Supabase connection test successful")
            return True
        except APIError as e:
            logger.error(f"Supabase connection test failed: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error in Supabase connection test: {e}")
            return False

    # User Management
    def create_user(self, email: str, password: str, metadata: dict[str, Any] = None) -> dict[str, Any]:
        """Create a new user"""
        try:
            # Hash the password before storing
            hashed_password = hash_password(password)

            user_data = {
                "email": email,
                "password": hashed_password,  # Store hashed password
                "created_at": datetime.now().isoformat(),
                "usage_quota": DEFAULT_USAGE_QUOTA_MINUTES,
                "usage_current": 0,
                "is_admin": False,
                "subscription_tier": "free",
            }

            if metadata:
                user_data.update(metadata)

            result = self.client.table("users").insert(user_data).execute()
            logger.info(f"User created successfully: {email}")
            return result.data[0] if result.data else {}
        except APIError as e:
            logger.error(f"Error creating user: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error creating user: {e}")
            raise

    def get_user(self, user_id: int) -> dict[str, Any] | None:
        """Get user by ID"""
        try:
            result = self.client.table("users").select("*").eq("id", user_id).execute()
            return result.data[0] if result.data else None
        except APIError as e:
            logger.error(f"Error fetching user: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching user: {e}")
            return None

    def get_user_by_email(self, email: str) -> dict[str, Any] | None:
        """Get user by email"""
        try:
            result = self.client.table("users").select("*").eq("email", email).execute()
            return result.data[0] if result.data else None
        except APIError as e:
            logger.error(f"Error fetching user by email: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching user by email: {e}")
            return None

    def update_user_usage(self, user_id: int, usage_seconds: int) -> bool:
        """Update user's current usage"""
        try:
            # Convert seconds to minutes
            usage_minutes = usage_seconds / 60

            result = self.client.table("users").update({"usage_current": usage_minutes}).eq("id", user_id).execute()

            return bool(result.data)
        except APIError as e:
            logger.error(f"Error updating user usage: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error updating user usage: {e}")
            return False

    # Content Storage
    def save_content(self, user_id: int, content_data: dict[str, Any]) -> str | None:
        """Save generated content to database"""
        try:
            content_record = {
                "user_id": user_id,
                "title": content_data.get("title", "Untitled"),
                "transcript": content_data.get("transcript", ""),
                "wisdom": content_data.get("wisdom", ""),
                "outline": content_data.get("outline", ""),
                "social_content": content_data.get("social_content", ""),
                "image_prompts": content_data.get("image_prompts", ""),
                "article": content_data.get("article", ""),
                "metadata": content_data.get("metadata", {}),
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
            }

            result = self.client.table("content").insert(content_record).execute()

            if result.data:
                content_id = result.data[0]["id"]
                logger.info(f"Content saved successfully with ID: {content_id}")
                return content_id
            return None
        except APIError as e:
            logger.error(f"Error saving content: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error saving content: {e}")
            return None

    def get_user_content(self, user_id: int, limit: int = DEFAULT_CONTENT_QUERY_LIMIT) -> list[dict[str, Any]]:
        """Get user's content history"""
        try:
            result = (
                self.client.table("content")
                .select("*")
                .eq("user_id", user_id)
                .order("created_at", desc=True)
                .limit(limit)
                .execute()
            )
            return result.data or []
        except APIError as e:
            logger.error(f"Error fetching user content: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error fetching user content: {e}")
            return []

    # API Key Management
    def save_user_api_keys(self, user_id: int, api_keys: dict[str, str]) -> bool:
        """Save encrypted API keys for user"""
        try:
            # In production, encrypt the API keys before storing
            result = (
                self.client.table("users")
                .update({"api_keys": api_keys, "updated_at": datetime.now().isoformat()})
                .eq("id", user_id)
                .execute()
            )

            return bool(result.data)
        except APIError as e:
            logger.error(f"Error saving API keys: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error saving API keys: {e}")
            return False

    def get_user_api_keys(self, user_id: int) -> dict[str, str]:
        """Get user's API keys"""
        try:
            result = self.client.table("users").select("api_keys").eq("id", user_id).execute()
            if result.data and result.data[0]["api_keys"]:
                return result.data[0]["api_keys"]
            return {}
        except APIError as e:
            logger.error(f"Error fetching API keys: {e}")
            return {}
        except Exception as e:
            logger.error(f"Unexpected error fetching API keys: {e}")
            return {}

    # Knowledge Base Management
    def save_knowledge_base_file(self, user_id: int, filename: str, content: str) -> bool:
        """Save knowledge base file for user"""
        try:
            kb_record = {
                "user_id": user_id,
                "filename": filename,
                "content": content,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
            }

            # Check if file already exists for this user
            existing = (
                self.client.table("knowledge_base")
                .select("id")
                .eq("user_id", user_id)
                .eq("filename", filename)
                .execute()
            )

            if existing.data:
                # Update existing
                result = (
                    self.client.table("knowledge_base")
                    .update({"content": content, "updated_at": datetime.now().isoformat()})
                    .eq("user_id", user_id)
                    .eq("filename", filename)
                    .execute()
                )
            else:
                # Create new
                result = self.client.table("knowledge_base").insert(kb_record).execute()

            return bool(result.data)
        except APIError as e:
            logger.error(f"Error saving knowledge base file: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error saving knowledge base file: {e}")
            return False

    def get_user_knowledge_base(self, user_id: int) -> dict[str, str]:
        """Get user's knowledge base files"""
        try:
            result = self.client.table("knowledge_base").select("filename, content").eq("user_id", user_id).execute()

            kb_dict = {}
            for item in result.data or []:
                # Convert filename to display name
                name = item["filename"].replace(".txt", "").replace(".md", "").replace("_", " ").title()
                kb_dict[name] = item["content"]

            return kb_dict
        except APIError as e:
            logger.error(f"Error fetching knowledge base: {e}")
            return {}
        except Exception as e:
            logger.error(f"Unexpected error fetching knowledge base: {e}")
            return {}

    # Custom Prompts Management
    def save_custom_prompt(self, user_id: int, prompt_type: str, content: str) -> bool:
        """Save custom prompt for user"""
        try:
            prompt_record = {
                "user_id": user_id,
                "prompt_type": prompt_type,
                "content": content,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
            }

            # Check if prompt already exists for this user
            existing = (
                self.client.table("custom_prompts")
                .select("id")
                .eq("user_id", user_id)
                .eq("prompt_type", prompt_type)
                .execute()
            )

            if existing.data:
                # Update existing
                result = (
                    self.client.table("custom_prompts")
                    .update({"content": content, "updated_at": datetime.now().isoformat()})
                    .eq("user_id", user_id)
                    .eq("prompt_type", prompt_type)
                    .execute()
                )
            else:
                # Create new
                result = self.client.table("custom_prompts").insert(prompt_record).execute()

            return bool(result.data)
        except APIError as e:
            logger.error(f"Error saving custom prompt: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error saving custom prompt: {e}")
            return False

    def get_user_prompts(self, user_id: int) -> dict[str, str]:
        """Get user's custom prompts"""
        try:
            result = self.client.table("custom_prompts").select("prompt_type, content").eq("user_id", user_id).execute()

            prompts_dict = {}
            for item in result.data or []:
                prompts_dict[item["prompt_type"]] = item["content"]

            return prompts_dict
        except APIError as e:
            logger.error(f"Error fetching custom prompts: {e}")
            return {}
        except Exception as e:
            logger.error(f"Unexpected error fetching custom prompts: {e}")
            return {}

    # Analytics and Monitoring
    def log_pipeline_execution(self, user_id: int, pipeline_data: dict[str, Any]) -> bool:
        """Log pipeline execution for analytics"""
        try:
            log_record = {
                "user_id": user_id,
                "pipeline_type": pipeline_data.get("type", "full"),
                "duration_seconds": pipeline_data.get("duration", 0),
                "ai_provider": pipeline_data.get("ai_provider", "unknown"),
                "model": pipeline_data.get("model", "unknown"),
                "success": pipeline_data.get("success", False),
                "error_message": pipeline_data.get("error"),
                "metadata": pipeline_data.get("metadata", {}),
                "created_at": datetime.now().isoformat(),
            }

            result = self.client.table("pipeline_logs").insert(log_record).execute()
            return bool(result.data)
        except APIError as e:
            logger.error(f"Error logging pipeline execution: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error logging pipeline execution: {e}")
            return False

    def get_user_analytics(self, user_id: int, days: int = DEFAULT_ANALYTICS_DAYS) -> dict[str, Any]:
        """Get user analytics for the last N days"""
        try:
            start_date = (datetime.now() - timedelta(days=days)).isoformat()

            result = (
                self.client.table("pipeline_logs")
                .select("*")
                .eq("user_id", user_id)
                .gte("created_at", start_date)
                .execute()
            )

            logs = result.data or []

            analytics = {
                "total_executions": len(logs),
                "successful_executions": len([log for log in logs if log["success"]]),
                "total_duration": sum(log["duration_seconds"] for log in logs),
                "ai_providers_used": list(set(log["ai_provider"] for log in logs)),
                "most_used_model": self._get_most_frequent(logs, "model"),
                "average_duration": sum(log["duration_seconds"] for log in logs) / len(logs) if logs else 0,
            }

            return analytics
        except APIError as e:
            logger.error(f"Error fetching user analytics: {e}")
            return {}
        except Exception as e:
            logger.error(f"Unexpected error fetching user analytics: {e}")
            return {}

    def _get_most_frequent(self, logs: list[dict], field: str) -> str:
        """Helper to get most frequent value from logs"""
        if not logs:
            return "unknown"

        from collections import Counter

        values = [log.get(field, "unknown") for log in logs]
        return Counter(values).most_common(1)[0][0]


# MCP Integration Functions
class MCPSupabaseIntegration:
    """
    Model Context Protocol integration for Supabase
    Provides AI models with context about user data and preferences
    """

    def __init__(self, supabase_client: SupabaseClient):
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
        except Exception as e:
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
        except Exception as e:
            logger.error(f"Unexpected error updating context from interaction: {e}")
            return False


# Global instance
_supabase_client = None
_mcp_integration = None


def get_supabase_client() -> SupabaseClient:
    """Get or create Supabase client instance"""
    global _supabase_client
    if _supabase_client is None:
        _supabase_client = SupabaseClient()
    return _supabase_client


def get_mcp_integration() -> MCPSupabaseIntegration:
    """Get or create MCP integration instance"""
    global _mcp_integration
    if _mcp_integration is None:
        _mcp_integration = MCPSupabaseIntegration(get_supabase_client())
    return _mcp_integration
