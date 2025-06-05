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

async def periodic_registration_check():
    """Periodically check if runner is still registered and re-register if needed"""
    await asyncio.sleep(60)  # Wait 1 minute after startup
    
    while True:
        try:
            await asyncio.sleep(300)  # Check every 5 minutes
            
            if not await is_registered():
                logger.warning("Runner not registered with distributor, attempting re-registration")
                await register_with_distributor()
            else:
                logger.debug("Runner still registered with distributor")
                
        except Exception as e:
            logger.error(f"Error in periodic registration check: {e}")
            # Try to re-register on any error
            try:
                await register_with_distributor()
            except Exception as re_reg_error:
                logger.error(f"Re-registration failed: {re_reg_error}")

async def is_registered() -> bool:
    """Check if this runner is still registered with the distributor"""
    try:
        container_id = os.getenv('HOSTNAME', socket.gethostname())
        runner_id = f"runner-{container_id}"
        
        timeout = aiohttp.ClientTimeout(total=10)
        
        # Prepare headers - only include auth if token is available
        headers = {}
        if AUTH_TOKEN:
            headers["Authorization"] = f"Bearer {AUTH_TOKEN}"
        
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(
                f"{DISTRIBUTOR_URL}/runners/status",  # Fixed URL path
                headers=headers
            ) as response:
                if response.status == 200:
                    runners = await response.json()
                    return runner_id in runners
                else:
                    logger.warning(f"Failed to check registration status: {response.status}")
                    return False
                    
    except Exception as e:
        logger.error(f"Error checking registration status: {e}")
        return False

async def register_with_distributor():
    """Modified to work with optional authentication"""
    max_retries = 5
    retry_count = 0
    
    if not DISTRIBUTOR_URL:
        logger.error("DISTRIBUTOR_URL environment variable is not set")
        return False
    
    # Log auth status
    if AUTH_TOKEN:
        logger.debug("Using authentication for distributor registration")
    else:
        logger.debug("No AUTH_TOKEN set, registering without authentication")
    
    while retry_count < max_retries:
        try:
            # Get container ID for unique identification
            container_id = os.getenv('HOSTNAME', socket.gethostname())
            runner_url = f"http://{container_id}:8000"
            runner_id = f"runner-{container_id}"
            
            logger.debug(f"Attempting to register with distributor at: {DISTRIBUTOR_URL}")
            
            # Configure timeout and connection settings
            timeout = aiohttp.ClientTimeout(total=30)
            connector = aiohttp.TCPConnector(
                force_close=True,
                enable_cleanup_closed=True,
                ssl=False,
                use_dns_cache=False
            )
            
            # Prepare headers - only include auth if token is available
            headers = {}
            if AUTH_TOKEN:
                headers["Authorization"] = f"Bearer {AUTH_TOKEN}"
            
            async with aiohttp.ClientSession(
                timeout=timeout,
                connector=connector
            ) as session:
                response = await session.post(
                    f"{DISTRIBUTOR_URL}/runners/register",  # Fixed URL path
                    headers=headers,
                    json={
                        "runner_id": runner_id,
                        "url": runner_url
                    }
                )
                response_text = await response.text()
                
                if response.status == 200:
                    logger.info(f"Runner {runner_id} registered successfully")
                    return True
                    
                logger.warning(f"Registration failed: {response.status} - {response_text}")
                
        except Exception as e:
            logger.error(f"Failed to register runner: {str(e)}")
        
        retry_count += 1
        if retry_count < max_retries:
            await asyncio.sleep(random.uniform(2, 5))

    logger.error(f"Failed to register after {max_retries} retries")
    return False

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.debug(f"Starting up runner {RUNNER_ID}")
    
    # Start registration process in background
    registration_task = asyncio.create_task(register_with_distributor())
    
    # Start periodic re-registration check
    heartbeat_task = asyncio.create_task(periodic_registration_check())
    
    yield  # Server is running
    
    # Cleanup
    logger.info("Cleaning up sessions...")
    await cleanup_sessions()
    if not registration_task.done():
        registration_task.cancel()
    if not heartbeat_task.done():
        heartbeat_task.cancel()

# Create the FastAPI app instance
app = FastAPI(
    title="ScrapeEngine Runner",
    description="Web scraping runner service",
    version="1.0.0",
    lifespan=lifespan
)

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

@app.post("/ping")
async def handle_ping(request: dict):
    """Handle ping from distributor to trigger re-registration"""
    try:
        action = request.get("action")
        distributor_url = request.get("distributor_url")
        
        if action == "re_register":
            logger.info("Received re-registration ping from distributor")
            
            # Trigger re-registration in background
            asyncio.create_task(register_with_distributor())
            
            return {
                "status": "success",
                "action": "re_registration_triggered",
                "runner_id": RUNNER_ID
            }
        else:
            return {"status": "unknown_action", "action": action}
            
    except Exception as e:
        logger.error(f"Error handling ping: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)