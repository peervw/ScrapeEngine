from fastapi import FastAPI, HTTPException
from .services.scraper import scrape
from .models import ScrapeRequest
from .config.logging_config import setup_logging
import aiohttp
import os
import asyncio
import logging
from contextlib import asynccontextmanager
import socket

# Setup logging first
setup_logging()
logger = logging.getLogger(__name__)
logger.info("Environment variables:")
logger.info(f"AUTH_TOKEN present: {bool(os.getenv('AUTH_TOKEN'))}")
logger.info(f"DISTRIBUTOR_URL: {os.getenv('DISTRIBUTOR_URL')}")

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

# Create the FastAPI app AFTER defining lifespan
app = FastAPI(
    title=f"ScrapeEngine Runner {os.getenv('RUNNER_ID', 'unknown')}",
    lifespan=lifespan
)

async def register_with_distributor():
    max_retries = 30
    retry_count = 0
    
    if not AUTH_TOKEN:
        logger.error("AUTH_TOKEN environment variable is not set")
        return
        
    if not DISTRIBUTOR_URL:
        logger.error("DISTRIBUTOR_URL environment variable is not set")
        return
    
    while retry_count < max_retries:
        try:
            container_name = os.getenv('HOSTNAME', socket.gethostname())
            runner_url = f"http://{container_name}:8000"
            logger.debug(f"Attempting to register with URL: {runner_url}")
            logger.debug(f"Using AUTH_TOKEN: {AUTH_TOKEN[:4]}...")  # Log first 4 chars only
            
            async with aiohttp.ClientSession() as session:
                response = await session.post(
                    f"{DISTRIBUTOR_URL}/api/runners/register",
                    headers={"Authorization": f"Bearer {AUTH_TOKEN}"},
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
        if retry_count < max_retries:
            logger.debug(f"Retry {retry_count}/{max_retries} in 10 seconds...")
            await asyncio.sleep(10)
    
    logger.error("Failed to register after maximum retries")

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