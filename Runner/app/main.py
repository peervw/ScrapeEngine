from fastapi import FastAPI, HTTPException
from .services.scraper import scrape
from .models import ScrapeRequest
from .config.logging_config import setup_logging
import aiohttp
import os
import asyncio
import logging
from datetime import datetime
from contextlib import asynccontextmanager
import socket

# Setup logging first
setup_logging()
logger = logging.getLogger(__name__)

app = FastAPI(title=f"ScrapeEngine Runner {os.getenv('RUNNER_ID', 'unknown')}")

RUNNER_ID = f"runner-{os.getenv('HOSTNAME', socket.gethostname())}"
DISTRIBUTOR_URL = os.getenv('DISTRIBUTOR_URL')
AUTH_TOKEN = os.getenv('AUTH_TOKEN')

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.debug(f"Starting up runner {RUNNER_ID}")
    logger.debug(f"Environment variables:")
    logger.debug(f"RUNNER_ID: {RUNNER_ID}")
    logger.debug(f"DISTRIBUTOR_URL: {DISTRIBUTOR_URL}")
    logger.debug(f"AUTH_TOKEN present: {bool(AUTH_TOKEN)}")
    
    # Start registration process in background
    registration_task = asyncio.create_task(register_with_distributor())
    
    yield  # Server is running
    
    # Cleanup if needed
    if not registration_task.done():
        registration_task.cancel()

async def register_with_distributor():
    max_retries = 30  # 5 minutes total (with 10s between retries)
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            # Get the actual container hostname
            container_name = os.getenv('HOSTNAME', socket.gethostname())
            runner_url = f"http://{container_name}:8000"
            logger.debug(f"Attempting to register with URL: {runner_url}")
            
            async with aiohttp.ClientSession() as session:
                response = await session.post(
                    f"{DISTRIBUTOR_URL}/api/runners/register",
                    headers={"Authorization": AUTH_TOKEN},
                    json={
                        "runner_id": RUNNER_ID,
                        "url": runner_url
                    }
                )
                response_text = await response.text()
                
                if response.status == 200:
                    logger.info(f"Runner {RUNNER_ID} registered successfully")
                    return
                    
                logger.warning(f"Registration failed: {response.status} - {response_text}")
                
        except Exception as e:
            logger.error(f"Failed to register runner: {str(e)}")
        
        retry_count += 1
        logger.debug(f"Retry {retry_count}/{max_retries} in 10 seconds...")
        await asyncio.sleep(10)
    
    logger.error("Failed to register after maximum retries")

app = FastAPI(lifespan=lifespan)

@app.get("/health")
async def health_check():
    return {"status": "healthy", "runner_id": RUNNER_ID}

@app.post("/scrape")
async def scrape_endpoint(request: ScrapeRequest):
    try:
        result = await scrape(request.dict())
        result["runner_id"] = RUNNER_ID
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))