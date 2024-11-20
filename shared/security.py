import os
from fastapi import HTTPException, Security, Depends
from fastapi.security import APIKeyHeader
from typing import Optional
from .config import Config

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

class SecurityHandler:
    def __init__(self):
        self.api_key_header = api_key_header
        
    async def verify_token(self, api_key: Optional[str] = Depends(api_key_header)) -> str:
        """Verify the API token"""
        if not api_key:
            raise HTTPException(
                status_code=401,
                detail="API key is missing"
            )
            
        if api_key != Config.SERVICE_TOKEN:
            raise HTTPException(
                status_code=401,
                detail="Invalid API key"
            )
            
        return api_key
