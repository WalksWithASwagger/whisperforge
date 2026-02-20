from fastapi import Security, HTTPException
from fastapi.security import HTTPBearer
import jwt
from datetime import datetime, timedelta, timezone
from passlib.context import CryptContext
import os

pwd_context = CryptContext(schemes=["bcrypt"])
security = HTTPBearer()


def _get_jwt_secret() -> str:
    """Get JWT secret from environment, raising if not configured"""
    secret = os.getenv('JWT_SECRET')
    if not secret:
        raise RuntimeError(
            "JWT_SECRET environment variable is not set. "
            "Set it in your .env file before using authentication.")
    return secret


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_jwt_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=30)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, _get_jwt_secret(), algorithm="HS256")


async def verify_token(token: str = Security(security)):
    try:
        payload = jwt.decode(
            token, _get_jwt_secret(), algorithms=["HS256"])
        return payload
    except jwt.PyJWTError:
        raise HTTPException(401, "Invalid token")
