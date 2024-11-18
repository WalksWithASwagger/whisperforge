import os
import jwt
from datetime import datetime, timedelta
from functools import wraps
from fastapi import HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

class SecurityHandler:
    def __init__(self):
        self.security = HTTPBearer()
        self.token = os.getenv("SERVICE_TOKEN")

    async def verify_token(self, auth: HTTPAuthorizationCredentials = Security(HTTPBearer())) -> bool:
        """Verify the Bearer token"""
        if not auth or not auth.credentials or auth.credentials != self.token:
            raise HTTPException(
                status_code=401,
                detail="Invalid authentication token"
            )
        return True
