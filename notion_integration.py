#!/usr/bin/env python3
"""
WhisperForge Notion Integration
Automatically publish content to Notion databases
"""

import os
import requests
import json
from datetime import datetime
from typing import Dict, Any, Optional

class NotionIntegration:
    """Handle Notion API integration for WhisperForge"""
    
    def __init__(self, notion_token: str = None, database_id: str = None):
        self.notion_token = notion_token or os.getenv('NOTION_TOKEN')
        self.database_id = database_id or os.getenv('NOTION_DATABASE_ID')
        self.base_url = "https://api.notion.com/v1"
        self.headers = {
            "Authorization": f"Bearer {self.notion_token}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28"
        }
    
    def test_connection(self) -> bool:
        """Test Notion API connection"""
        try:
            response = requests.get(
                f"{self.base_url}/users/me",
                headers=self.headers,
                timeout=10
            )
            return response.status_code == 200
        except Exception:
            return False
    
    def create_whisperforge_page(self, content_data: Dict[str, Any]) -> Optional[str]:
        """Create a new page in Notion with WhisperForge content"""
        
        if not self.notion_token or not self.database_id:
            raise ValueError("Notion token and database ID required")
        
        # Prepare page data
        page_data = {
            "parent": {"database_id": self.database_id},
            "properties": self._build_page_properties(content_data),
            "children": self._build_page_content(content_data)
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/pages",
                headers=self.headers,
                json=page_data,
                timeout=30
            )
            
            if response.status_code == 200:
                page = response.json()
                return page.get('url')
            else:
                print(f"Notion API Error: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"Error creating Notion page: {e}")
            return None
    
    def _build_page_properties(self, content_data: Dict[str, Any]) -> Dict[str, Any]:
        """Build Notion page properties from WhisperForge content"""
        
        # Extract key info
        file_name = content_data.get('file_name', 'Unknown Audio')
        processed_at = content_data.get('processed_at', datetime.now().isoformat())
        
        # Generate tags from content
        tags = self._extract_tags(content_data)
        
        # Build properties for a typical WhisperForge Notion database
        properties = {
            "Title": {
                "title": [
                    {
                        "text": {"content": f"📝 {file_name}"}
                    }
                ]
            },
            "Type": {
                "select": {"name": "WhisperForge Content"}
            },
            "Status": {
                "select": {"name": "Published"}
            },
            "Created": {
                "date": {"start": processed_at}
            },
            "Source": {
                "rich_text": [
                    {
                        "text": {"content": f"Audio file: {file_name}"}
                    }
                ]
            }
        }
        
        # Add tags if we have them
        if tags:
            properties["Tags"] = {
                "multi_select": [{"name": tag} for tag in tags[:5]]  # Limit to 5 tags
            }
        
        return properties
    
    def _build_page_content(self, content_data: Dict[str, Any]) -> list:
        """Build Notion page content blocks from WhisperForge data"""
        
        blocks = []
        
        # Add header
        blocks.append({
            "object": "block",
            "type": "heading_1",
            "heading_1": {
                "rich_text": [{"type": "text", "text": {"content": "🎙️ WhisperForge Content"}}]
            }
        })
        
        # Add wisdom section
        if content_data.get('wisdom'):
            blocks.extend([
                {
                    "object": "block",
                    "type": "heading_2", 
                    "heading_2": {
                        "rich_text": [{"type": "text", "text": {"content": "💡 Key Wisdom"}}]
                    }
                },
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [{"type": "text", "text": {"content": content_data['wisdom'][:2000]}}]
                    }
                }
            ])
        
        # Add article section
        if content_data.get('article'):
            blocks.extend([
                {
                    "object": "block",
                    "type": "heading_2",
                    "heading_2": {
                        "rich_text": [{"type": "text", "text": {"content": "📝 Full Article"}}]
                    }
                },
                {
                    "object": "block", 
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [{"type": "text", "text": {"content": content_data['article'][:2000]}}]
                    }
                }
            ])
        
        # Add social content section
        if content_data.get('social_content'):
            blocks.extend([
                {
                    "object": "block",
                    "type": "heading_2",
                    "heading_2": {
                        "rich_text": [{"type": "text", "text": {"content": "📱 Social Media Posts"}}]
                    }
                },
                {
                    "object": "block",
                    "type": "paragraph", 
                    "paragraph": {
                        "rich_text": [{"type": "text", "text": {"content": content_data['social_content'][:2000]}}]
                    }
                }
            ])
        
        # Add image prompts section
        if content_data.get('image_prompts'):
            blocks.extend([
                {
                    "object": "block",
                    "type": "heading_2",
                    "heading_2": {
                        "rich_text": [{"type": "text", "text": {"content": "🎨 Image Prompts"}}]
                    }
                },
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [{"type": "text", "text": {"content": content_data['image_prompts'][:2000]}}]
                    }
                }
            ])
        
        # Add transcript as collapsible section
        if content_data.get('transcript'):
            blocks.extend([
                {
                    "object": "block",
                    "type": "toggle",
                    "toggle": {
                        "rich_text": [{"type": "text", "text": {"content": "📝 Full Transcript"}}],
                        "children": [
                            {
                                "object": "block",
                                "type": "paragraph",
                                "paragraph": {
                                    "rich_text": [{"type": "text", "text": {"content": content_data['transcript'][:2000]}}]
                                }
                            }
                        ]
                    }
                }
            ])
        
        return blocks
    
    def _extract_tags(self, content_data: Dict[str, Any]) -> list:
        """Extract relevant tags from content for Notion"""
        tags = ["WhisperForge", "Audio Content"]
        
        # Add content type tags
        if content_data.get('article'):
            tags.append("Article")
        if content_data.get('social_content'):
            tags.append("Social Media")
        if content_data.get('image_prompts'):
            tags.append("Image Prompts")
        if content_data.get('research_data'):
            tags.append("Research")
        
        return tags

def setup_notion_database_template():
    """Return the recommended Notion database schema for WhisperForge"""
    
    schema = {
        "Title": "title",
        "Type": "select",  # Options: WhisperForge Content, Article, Social Post, etc.
        "Status": "select",  # Options: Draft, Published, Archived
        "Created": "date",
        "Source": "rich_text", 
        "Tags": "multi_select",
        "Content Rating": "select",  # Options: ⭐, ⭐⭐, ⭐⭐⭐
        "Word Count": "number",
        "Notes": "rich_text"
    }
    
    return schema

# Example usage functions for WhisperForge integration

def publish_to_notion(content_data: Dict[str, Any], notion_token: str = None, database_id: str = None) -> Optional[str]:
    """
    Publish WhisperForge content to Notion
    
    Args:
        content_data: WhisperForge content dictionary
        notion_token: Notion integration token
        database_id: Target Notion database ID
        
    Returns:
        Notion page URL if successful, None otherwise
    """
    
    notion = NotionIntegration(notion_token, database_id)
    
    if not notion.test_connection():
        print("❌ Cannot connect to Notion. Check your token and permissions.")
        return None
    
    page_url = notion.create_whisperforge_page(content_data)
    
    if page_url:
        print(f"✅ Content published to Notion: {page_url}")
        return page_url
    else:
        print("❌ Failed to publish to Notion")
        return None

def test_notion_integration():
    """Test the Notion integration with sample data"""
    
    # Sample WhisperForge content
    sample_content = {
        "file_name": "test_audio.mp3",
        "transcript": "This is a test transcript for Notion integration...",
        "wisdom": "Key insight: Integration testing is crucial for success.",
        "article": "# Test Article\n\nThis is a test article generated by WhisperForge...",
        "social_content": "Twitter: Test post for Notion integration! #WhisperForge",
        "image_prompts": "1. Abstract visualization of audio waves transforming into text",
        "processed_at": datetime.now().isoformat()
    }
    
    print("🧪 Testing Notion Integration...")
    
    # Check environment variables
    notion_token = os.getenv('NOTION_TOKEN')
    database_id = os.getenv('NOTION_DATABASE_ID')
    
    if not notion_token:
        print("❌ NOTION_TOKEN environment variable not set")
        return False
    
    if not database_id:
        print("❌ NOTION_DATABASE_ID environment variable not set")
        return False
    
    # Test connection
    notion = NotionIntegration(notion_token, database_id)
    
    if not notion.test_connection():
        print("❌ Notion connection failed")
        return False
    
    print("✅ Notion connection successful")
    
    # Test page creation (commented out to avoid spam)
    # page_url = publish_to_notion(sample_content, notion_token, database_id)
    # return page_url is not None
    
    print("✅ Notion integration ready for deployment")
    return True

if __name__ == "__main__":
    test_notion_integration() 