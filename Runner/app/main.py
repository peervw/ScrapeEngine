from fastapi import FastAPI, HTTPException
from .services.scraper import scrape, cleanup_sessions
from .models import ScrapeRequest
from .config.logging_config import setup_logging
import aiohttp
import os
import asyncio
import logging
from contextlib import asynccontextmanager
import socket
import random

# Setup logging first
setup_logging()
logger = logging.getLogger(__name__)

RUNNER_ID = f"runner-{os.getenv('HOSTNAME', socket.gethostname())}"
DISTRIBUTOR_URL = os.getenv('DISTRIBUTOR_URL', 'http://distributor.local:8080')
AUTH_TOKEN = os.getenv('AUTH_TOKEN')

logger.info("Startup Configuration:")
logger.info(f"RUNNER_ID: {RUNNER_ID}")
logger.info(f"DISTRIBUTOR_URL: {DISTRIBUTOR_URL}")
logger.info(f"AUTH_TOKEN present: {bool(AUTH_TOKEN)}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.debug(f"Starting up runner {RUNNER_ID}")
    
    # Start registration process in background
    registration_task = asyncio.create_task(register_with_distributor())
    
    yield  # Server is running
    
    # Cleanup
    logger.info("Cleaning up sessions...")
    await cleanup_sessions()
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
    
    # Add random delay to prevent registration conflicts
    await asyncio.sleep(random.uniform(1, 5))
    
    while retry_count < max_retries:
        try:
            # Get container ID for unique identification
            container_id = os.getenv('HOSTNAME', socket.gethostname())
            runner_url = f"http://{container_id}:8000"
            runner_id = f"runner-{container_id}"
            
            logger.debug(f"Attempting to register with distributor at: {DISTRIBUTOR_URL}")
            logger.debug(f"Using runner URL: {runner_url}")
            logger.debug(f"Using runner_id: {runner_id}")
            
            # Configure timeout and connection settings
            timeout = aiohttp.ClientTimeout(total=30)
            connector = aiohttp.TCPConnector(
                force_close=True,
                enable_cleanup_closed=True,
                ssl=False,
                use_dns_cache=False
            )
            
            async with aiohttp.ClientSession(
                timeout=timeout,
                connector=connector
            ) as session:
                response = await session.post(
                    f"{DISTRIBUTOR_URL}/api/runners/register",
                    headers={"Authorization": f"Bearer {AUTH_TOKEN}"},
                    json={
                        "runner_id": runner_id,
                        "url": runner_url
                    }
                )
                response_text = await response.text()
                
                if response.status == 200:
                    logger.info(f"Runner {runner_id} registered successfully")
                    return
                    
                logger.warning(f"Registration failed: {response.status} - {response_text}")
                
        except Exception as e:
            logger.error(f"Failed to register runner: {str(e)}")
            if isinstance(e, aiohttp.ClientError):
                logger.error(f"Connection error details: {str(e)}")
        
        retry_count += 1
        if retry_count < max_retries:
            await asyncio.sleep(random.uniform(5, 15))
            logger.debug(f"Retry {retry_count}/{max_retries}")

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