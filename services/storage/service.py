from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime
from notion_client import Client
import os
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

class StorageRequest(BaseModel):
    transcription: str
    processed_text: str
    file_name: str
    timestamp: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = {}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.post("/store")
async def store_transcription(request: StorageRequest):
    try:
        notion = Client(auth=os.getenv("NOTION_API_KEY"))
        database_id = os.getenv("NOTION_DATABASE_ID")
        
        if not database_id:
            raise HTTPException(status_code=500, detail="Notion database ID not configured")

        # Create the page with exact properties from your database
        response = notion.pages.create(
            parent={"database_id": database_id},
            properties={
                "Name": {
                    "title": [{"text": {"content": f"Transcription: {request.file_name}"}}]
                },
                "Tags": {
                    "multi_select": [
                        {"name": "transcription"},
                        {"name": "Technology"}
                    ]
                },
                "Created Date": {
                    "date": {
                        "start": datetime.now().isoformat()
                    }
                }
            },
            children=[
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [{
                            "text": {
                                "content": request.processed_text
                            }
                        }]
                    }
                },
                {
                    "object": "block",
                    "type": "divider",
                    "divider": {}
                },
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [{
                            "text": {
                                "content": "Full Transcription:"
                            }
                        }]
                    }
                },
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [{
                            "text": {
                                "content": request.transcription
                            }
                        }]
                    }
                }
            ]
        )
        
        return {
            "status": "success",
            "url": response.get("url")
        }
    
    except Exception as e:
        logger.error(f"Storage error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
