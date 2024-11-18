from fastapi import FastAPI, Depends, HTTPException
from shared.security import SecurityHandler
from shared.config import Config
from pydantic import BaseModel
import openai
import logging
from typing import Optional, Literal

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

@app.post("/process")
async def process_text(
    request: ProcessingRequest,
    authenticated: bool = Depends(security.verify_token)
):
    """Process text using GPT-4 based on specified mode"""
    try:
        logger.info(f"Processing request with mode: {request.mode}")
        
        # Split text into chunks if needed
        chunks = chunk_text(request.text, request.chunk_size)
        processed_chunks = []
        
        for i, chunk in enumerate(chunks):
            logger.info(f"Processing chunk {i+1} of {len(chunks)}")
            
            try:
                prompt = get_processing_prompt(
                    request.mode,
                    chunk,
                    request.custom_prompt,
                    request.language
                )
                
                response = client.chat.completions.create(
                    model=Config.GPT_MODEL,
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant skilled in analysis and summarization."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7,
                    max_tokens=2000
                )
                
                processed_chunks.append(response.choices[0].message.content)
                
            except openai.RateLimitError:
                logger.error("Rate limit exceeded")
                raise HTTPException(
                    status_code=429,
                    detail="Rate limit exceeded. Please try again later."
                )
            except openai.APIError as e:
                logger.error(f"OpenAI API error: {str(e)}")
                raise ProcessingError(f"OpenAI API error: {str(e)}")
        
        # Combine chunks if multiple
        if len(processed_chunks) > 1:
            logger.info("Combining processed chunks")
            final_prompt = f"Please provide a coherent combination of these processed sections:\n\n{' '.join(processed_chunks)}"
            
            final_response = client.chat.completions.create(
                model=Config.GPT_MODEL,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant skilled in combining and synthesizing information."},
                    {"role": "user", "content": final_prompt}
                ],
                temperature=0.7,
                max_tokens=2000
            )
            
            final_text = final_response.choices[0].message.content
        else:
            final_text = processed_chunks[0]
        
        logger.info("Processing completed successfully")
        return {
            "status": "success",
            "processed_text": final_text,
            "chunks_processed": len(chunks)
        }
        
    except ProcessingError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "processing",
        "openai_api": "connected" if Config.OPENAI_API_KEY else "not configured"
    }
