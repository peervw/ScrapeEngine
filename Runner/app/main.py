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
import random
import psycopg2

# Setup logging first
setup_logging()
logger = logging.getLogger(__name__)

RUNNER_ID = f"runner-{os.getenv('HOSTNAME', socket.gethostname())}"
DISTRIBUTOR_URL = os.getenv('DISTRIBUTOR_URL', 'http://distributor.local:8080')

logger.info("Startup Configuration:")
logger.info(f"RUNNER_ID: {RUNNER_ID}")
logger.info(f"DISTRIBUTOR_URL: {DISTRIBUTOR_URL}")

def get_api_key():
    """Get the current API key from the database"""
    try:
        conn = psycopg2.connect(
            host=os.getenv('POSTGRES_HOST', 'db'),
            port=os.getenv('POSTGRES_PORT', '5432'),
            dbname=os.getenv('POSTGRES_DB', 'scrapeengine'),
            user=os.getenv('POSTGRES_USER', 'postgres'),
            password=os.getenv('POSTGRES_PASSWORD', 'postgres')
        )
        c = conn.cursor()
        c.execute('SELECT key FROM api_keys ORDER BY created_at DESC LIMIT 1')
        key = c.fetchone()
        conn.close()
        
        if not key:
            raise Exception("No API key found in database")
        
        return key[0]
    except Exception as e:
        logger.error(f"Failed to get API key from database: {e}")
        raise

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.debug(f"Starting up runner {RUNNER_ID}")
    
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
    
    if not DISTRIBUTOR_URL:
        logger.error("DISTRIBUTOR_URL environment variable is not set")
        return
    
    # Add random delay to prevent registration conflicts
    await asyncio.sleep(random.uniform(1, 5))
    
    # Configure timeout and connection settings
    timeout = aiohttp.ClientTimeout(total=30)
    connector = aiohttp.TCPConnector(
        force_close=True,
        enable_cleanup_closed=True,
        ssl=False,
        use_dns_cache=False,
        ttl_dns_cache=300
    )
    
    async with aiohttp.ClientSession(timeout=timeout, connector=connector) as session:
        while retry_count < max_retries:
            try:
                # Get container ID for unique identification
                container_id = os.getenv('HOSTNAME', socket.gethostname())
                runner_url = f"http://{container_id}:8000"
                runner_id = f"runner-{container_id}"
                
                logger.debug(f"Attempting to register with distributor at: {DISTRIBUTOR_URL}")
                logger.debug(f"Using runner URL: {runner_url}")
                logger.debug(f"Using runner_id: {runner_id}")
                
                # Get API key from database
                api_key = get_api_key()
                logger.debug("Got API key from database")
                
                # Register with the API key
                logger.debug("Attempting registration...")
                async with session.post(
                    f"{DISTRIBUTOR_URL}/api/runners/register",
                    headers={"Authorization": f"Bearer {api_key}"},
                    json={
                        "runner_id": runner_id,
                        "url": runner_url
                    }
                ) as response:
                    response_text = await response.text()
                    
                    if response.status == 200:
                        logger.info(f"Runner {runner_id} registered successfully")
                        # Store API key for future use
                        app.state.api_key = api_key
                        # Start health check loop
                        asyncio.create_task(health_check_loop())
                        return
                    
                    logger.warning(f"Registration failed: {response.status} - {response_text}")
                    raise Exception(f"Registration failed with status {response.status}: {response_text}")
            
            except Exception as e:
                logger.error(f"Failed to register runner: {str(e)}")
                if isinstance(e, aiohttp.ClientError):
                    logger.error(f"Connection error details: {str(e)}")
            
            retry_count += 1
            if retry_count < max_retries:
                delay = min(30, 2 ** retry_count)  # Exponential backoff with max 30 seconds
                logger.debug(f"Retry {retry_count}/{max_retries} in {delay} seconds")
                await asyncio.sleep(delay)

    logger.error("Failed to register after maximum retries")

async def health_check_loop():
    """Periodically check health and re-register if needed"""
    while True:
        try:
            # Check distributor health
            async with aiohttp.ClientSession() as session:
                try:
                    async with session.get(
                        f"{DISTRIBUTOR_URL}/health/public",
                        timeout=5
                    ) as response:
                        if response.status != 200:
                            logger.warning("Distributor health check failed, attempting to re-register")
                            await register_with_distributor()
                        # check if in the response under runner_ids
                        if RUNNER_ID in response.json()["runner_ids"]:
                            logger.info("Runner is still registered")
                        else:
                            logger.warning("Runner is not registered")
                            await register_with_distributor()
                except Exception as e:
                    logger.error(f"Health check failed: {str(e)}")
                    await register_with_distributor()
        except Exception as e:
            logger.error(f"Error in health check loop: {str(e)}")
        
        await asyncio.sleep(30)  # Check every 30 seconds

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