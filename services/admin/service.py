from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import aiohttp
import asyncio

app = FastAPI()

@app.get("/dashboard")
async def dashboard():
    # Fetch metrics from all services
    services = {
        "transcription": "http://transcription:8000/metrics",
        "processing": "http://processing:8000/metrics",
        "storage": "http://storage:8000/metrics"
    }
    
    metrics = {}
    async with aiohttp.ClientSession() as session:
        for service, url in services.items():
            try:
                async with session.get(url) as response:
                    metrics[service] = await response.json()
            except Exception as e:
                metrics[service] = {"error": str(e)}
    
    return metrics

@app.get("/logs")
async def get_logs(service: str = None, level: str = None):
    # Fetch logs from services
    # Implementation depends on your logging setup
    pass 