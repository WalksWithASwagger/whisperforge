from fastapi import FastAPI, Depends, HTTPException
from shared.security import SecurityHandler
from notion_client import Client
from pydantic import BaseModel
import logging
import os
from datetime import datetime
from typing import Optional

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Log startup configuration
logger.info("=== Starting Storage Service ===")
logger.info(f"NOTION_API_KEY present: {'Yes' if os.getenv('NOTION_API_KEY') else 'No'}")
logger.info(f"NOTION_DATABASE_ID: {os.getenv('NOTION_DATABASE_ID')}")

app = FastAPI(title="WhisperForge Storage Service")
security = SecurityHandler()

# Initialize Notion client
notion = Client(auth=os.getenv("NOTION_API_KEY"))

class StorageRequest(BaseModel):
    transcription: str
    processed_text: str
    filename: Optional[str] = None
    duration: Optional[float] = None
    timestamp: Optional[datetime] = None

def create_notion_page(request: StorageRequest):
    """Create a new page in Notion with the transcription results"""
    try:
        # Get current timestamp
        current_time = datetime.utcnow()
        
        properties = {
            "title": {
                "title": [{"text": {"content": request.filename}}]
            },
            "Created Date": {
                "date": {
                    "start": current_time.isoformat()
                }
            },
            "Tags": {
                "multi_select": [
                    {"name": "transcription"},
                    {"name": "Technology"},
                    {"name": "Self-Reflection"}
                ]
            },
            "Status": {
                "select": {
                    "name": "Completed"
                }
            }
        }

        # Create page with blocks
        response = notion.pages.create(
            parent={"database_id": os.getenv("NOTION_DATABASE_ID")},
            properties=properties,
            children=[
                {
                    "object": "block",
                    "type": "callout",
                    "callout": {
                        "rich_text": [{
                            "text": {"content": request.processed_text}
                        }],
                        "icon": {"emoji": "📝"}
                    }
                },
                {
                    "object": "block",
                    "type": "toggle",
                    "toggle": {
                        "rich_text": [{"text": {"content": "Key Insights"}}],
                        "children": [{"type": "paragraph", "paragraph": {"rich_text": [{"text": {"content": "To be added..."}}]}}]
                    }
                },
                {
                    "object": "block",
                    "type": "toggle",
                    "toggle": {
                        "rich_text": [{"text": {"content": "Actionable Takeaways"}}],
                        "children": [{"type": "paragraph", "paragraph": {"rich_text": [{"text": {"content": "To be added..."}}]}}]
                    }
                },
                {
                    "object": "block",
                    "type": "toggle",
                    "toggle": {
                        "rich_text": [{"text": {"content": "Full Transcription"}}],
                        "children": [
                            {
                                "type": "paragraph",
                                "paragraph": {
                                    "rich_text": [{
                                        "text": {"content": request.transcription}
                                    }]
                                }
                            }
                        ]
                    }
                }
            ]
        )
        return response

    except Exception as e:
        logger.error(f"Error creating Notion page: {str(e)}")
        raise

@app.post("/store")
async def store_results(
    request: StorageRequest,
    authenticated: bool = Depends(security.verify_token)
):
    """Store processed results in Notion"""
    try:
        logger.info(f"Storing results for file: {request.filename}")
        
        # Create Notion page
        response = create_notion_page(request)
        
        page_url = f"https://notion.so/{response['id'].replace('-', '')}"
        
        logger.info(f"Successfully created Notion page: {page_url}")
        
        return {
            "status": "success",
            "notion_url": page_url,
            "page_id": response["id"]
        }
        
    except Exception as e:
        logger.error(f"Storage error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Test Notion API connection
        notion.users.me()
        notion_status = "connected"
    except Exception as e:
        notion_status = f"not connected: {str(e)}"
    
    return {
        "status": "healthy",
        "service": "storage",
        "notion_api": notion_status,
        "database_id": os.getenv("NOTION_DATABASE_ID", "not set")
    }
