from fastapi import FastAPI, Depends, HTTPException, Header, Request
from shared.security import SecurityHandler
from shared.config import Config
from pydantic import BaseModel
import openai
import logging
from typing import Optional, Literal
import os

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="WhisperForge Processing Service")
security = SecurityHandler()
client = openai.OpenAI(api_key=Config.OPENAI_API_KEY)

class ProcessingRequest(BaseModel):
    text: str
    mode: Literal["summarize", "extract insights", "custom"]
    custom_prompt: Optional[str] = ""
    chunk_size: Optional[int] = 4000
    language: Optional[str] = None

class ProcessingError(Exception):
    """Custom exception for processing errors"""
    pass

def chunk_text(text: str, max_tokens: int = 4000) -> list[str]:
    """Split text into chunks to avoid token limits"""
    words = text.split()
    chunks = []
    current_chunk = []
    current_length = 0
    
    for word in words:
        # Rough estimate: 1 word ≈ 1.3 tokens
        word_tokens = len(word) * 1.3
        if current_length + word_tokens > max_tokens and current_chunk:
            chunks.append(" ".join(current_chunk))
            current_chunk = [word]
            current_length = word_tokens
        else:
            current_chunk.append(word)
            current_length += word_tokens
    
    if current_chunk:
        chunks.append(" ".join(current_chunk))
    
    return chunks

def get_processing_prompt(mode: str, text: str, custom_prompt: str = "", language: str = None) -> str:
    """Generate appropriate prompt based on processing mode"""
    if mode == "summarize":
        base_prompt = "Please provide a concise summary of the following text"
    elif mode == "extract insights":
        base_prompt = """Analyze the following text and provide:
        1. Key Points
        2. Main Themes
        3. Notable Insights
        4. Action Items (if any)"""
    else:
        return custom_prompt

    if language:
        base_prompt += f" in {language}"
    
    return f"{base_prompt}:\n\n{text}"

async def verify_api_key(x_api_key: str = Header(None)):
    if not x_api_key:
        raise HTTPException(status_code=401, detail="API key is missing")
    
    expected_key = os.getenv("OPENAI_API_KEY")
    if not expected_key:
        raise HTTPException(status_code=500, detail="Server API key not configured")
    
    if x_api_key != expected_key:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    return x_api_key

@app.post("/process")
async def process_text(request: Request, data: ProcessingRequest, api_key: str = Depends(verify_api_key)):
    try:
        logger.info(f"Processing text with mode: {data.mode}")
        
        prompt = get_processing_prompt(data.mode, data.text, data.custom_prompt, data.language)
        
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful assistant skilled in analyzing text."},
                {"role": "user", "content": prompt}
            ]
        )
        
        return {"result": response.choices[0].message.content}
        
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "processing",
        "openai_api": "connected" if Config.OPENAI_API_KEY else "not configured"
    }
