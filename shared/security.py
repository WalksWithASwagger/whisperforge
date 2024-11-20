from fastapi import Security, HTTPException
from fastapi.security import HTTPBearer
from jose import jwt
from datetime import datetime, timedelta
from passlib.context import CryptContext
import os

pwd_context = CryptContext(schemes=["bcrypt"])
security = HTTPBearer()

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_jwt_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=30)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, os.getenv('JWT_SECRET'), "HS256")

async def verify_token(token: str = Security(security)):
    try:
        payload = jwt.decode(token, os.getenv('JWT_SECRET'), "HS256")
        return payload
    except jwt.JWTError:
        raise HTTPException(401, "Invalid token")
