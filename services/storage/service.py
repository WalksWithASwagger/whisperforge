from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
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
    metadata: Dict[str, Any] = {
        "title_prefix": "Transcription: ",
        "tags": ["transcription"],
        "custom_date": None
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.post("/store")
async def store_transcription(request: StorageRequest):
    logger.info("Received storage request")
    logger.debug(f"File name: {request.file_name}")
    
    # Check environment variables
    notion_key = os.getenv("NOTION_API_KEY")
    database_id = os.getenv("NOTION_DATABASE_ID")
    
    logger.info(f"Notion API Key present: {'Yes' if notion_key else 'No'}")
    logger.info(f"Notion Database ID present: {'Yes' if database_id else 'No'}")
    
    try:
        notion = Client(auth=os.getenv("NOTION_API_KEY"))
        database_id = os.getenv("NOTION_DATABASE_ID")

        if not database_id:
            logger.error("Notion database ID not configured")
            raise HTTPException(status_code=500, detail="Notion database ID not configured")

        # Extract metadata with defaults
        title_prefix = request.metadata.get("title_prefix", "Transcription: ")
        tags = request.metadata.get("tags", ["transcription"])
        custom_date = request.metadata.get("custom_date")

        # Prepare the date
        date_value = custom_date if custom_date else datetime.now().isoformat()

        logger.info(f"Creating Notion page for: {request.file_name}")
        logger.debug(f"Using tags: {tags}")

        try:
            # Create the page with metadata
            response = notion.pages.create(
                parent={"database_id": database_id},
                properties={
                    "Name": {
                        "title": [
                            {"text": {"content": f"{title_prefix}{request.file_name}"}}
                        ]
                    },
                    "Tags": {
                        "multi_select": [{"name": tag} for tag in tags]
                    },
                    "Created Date": {"date": {"start": date_value}},
                },
                children=[
                    {
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": [{"text": {"content": request.processed_text}}]
                        },
                    },
                    {"object": "block", "type": "divider", "divider": {}},
                    {
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": [{"text": {"content": "Full Transcription:"}}]
                        },
                    },
                    {
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": [{"text": {"content": request.transcription}}]
                        },
                    },
                ],
            )

            notion_url = response.get("url")
            logger.info(f"Successfully created Notion page: {notion_url}")
            return {"status": "success", "url": notion_url}

        except Exception as e:
            logger.error(f"Notion API error: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to create Notion page: {str(e)}"
            )

    except Exception as e:
        logger.error(f"Storage error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Storage error: {str(e)}"
        )
