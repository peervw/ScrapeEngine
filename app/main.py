from fastapi import FastAPI, HTTPException, Request, Header, Depends, status
from fastapi.responses import JSONResponse
import os
import logging
from .functions import *
from .webshare_proxy import *
import threading
import asyncio
from concurrent.futures import ThreadPoolExecutor, TimeoutError
from typing import Optional
import multiprocessing
import random
from pydantic import BaseModel, ValidationError, field_validator, HttpUrl
from functools import lru_cache
import cachetools
from fastapi.openapi.utils import get_openapi
from .config import Settings, get_settings

app = FastAPI()
stop_event = asyncio.Event()

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Executor for running scrapers concurrently
max_workers = int(os.getenv('MAX_WORKERS', multiprocessing.cpu_count() * 2))
executor = ThreadPoolExecutor(max_workers=max_workers)

# Authentication setup
API_TOKEN = os.getenv('AUTH_TOKEN')

# Read scraper credentials
credentials_list = read_data_from_file('scraper.txt')
if not credentials_list:
    logger.error("No credentials found in scraper.txt")
else:
    logger.info(f"Loaded {len(credentials_list)} credentials for scraping")

# Index and lock for round-robin credential usage
credentials_index = 0
credentials_lock = asyncio.Lock()  # To safely access the shared credentials index

def token_required(
    authorization: Optional[str] = Header(None),
    settings: Settings = Depends(get_settings)
):
    if not authorization or authorization not in settings.AUTH_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid token")
    return authorization

class ScrapeRequest(BaseModel):
    url: HttpUrl  # This will enforce URL validation
    link_or_article: Optional[str] = "article"
    other_params: Optional[dict] = None

    @field_validator('link_or_article')
    def validate_link_or_article(cls, v):
        if v not in ["link", "article"]:
            raise ValueError("link_or_article must be either 'link' or 'article'")
        return v

async def route_to_scraper(args):
    # Convert HttpUrl to string before passing to scraper
    if 'url' in args and hasattr(args['url'], '__str__'):
        args['url'] = str(args['url'])
    
    global credentials_index
    async with credentials_lock:
        # Get the next set of credentials in a round-robin fashion
        if not credentials_list:
            raise Exception("No credentials available for scraping")
        
        credentials = credentials_list[credentials_index]
        credentials_index = (credentials_index + 1) % len(credentials_list)

    # Add credentials to the args
    args['scraper_credentials'] = credentials
    
    # get next proxy with error handling and retry logic
    retry_attempts = 3
    for attempt in range(retry_attempts):
        try:
            args['proxy'] = get_next_proxy()
            break
        except Exception as e:
            logger.error(f"Failed to get proxy on attempt {attempt + 1}: {str(e)}")
            if attempt < retry_attempts - 1:
                await asyncio.sleep(random.uniform(1, 3))  # Wait before retrying
            else:
                raise Exception("Failed to obtain a proxy after multiple attempts")

    # Run the scraper using the executor to avoid blocking the event loop with a timeout
    loop = asyncio.get_running_loop()
    try:
        result = await asyncio.wait_for(loop.run_in_executor(executor, scrape, args), timeout=30)  # Set a 30-second timeout
        return result
    except TimeoutError:
        raise HTTPException(status_code=504, detail="Scraper request timed out")

@cachetools.cached(cache=cachetools.TTLCache(maxsize=32, ttl=14400))
def cached_read_data_from_file(filename: str):
    return read_data_from_file(filename)

@app.post('/api/scrape')
async def scrape_endpoint(
    request: ScrapeRequest,
    authorization: str = Depends(token_required)
):
    try:
        args = request.model_dump()
        result = await route_to_scraper(args)
        return JSONResponse(content=result)
    except ValidationError as e:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"error": str(e)}
        )
    except Exception as e:
        logger.error(f"An error occurred while scraping: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": str(e)}
        )

# Route to return JSON runners data
@app.get('/api/runners_json')
async def get_runners_data(authorization: str = Depends(token_required)):
    logger.info("/api/runners_json endpoint was called")
    data = cached_read_data_from_file("scraper.txt")
    logger.debug(f"Data to be returned: {data}")
    return JSONResponse(content=data)

# Route to return JSON proxy data
@app.get('/api/proxies_json')
async def get_proxies_data(authorization: str = Depends(token_required)):
    logger.info("/api/proxies_json endpoint was called")
    data = cached_read_data_from_file("proxies.txt")
    logger.debug(f"Data to be returned: {data}")
    return JSONResponse(content=data)

# Proxy manager
async def main_proxy_updater():
    while not stop_event.is_set():
        try:
            master_webshare_get_proxies()
            logging.info("Proxies updated.")
        except Exception as e:
            logging.error(f"An error occurred in proxy_updater: {str(e)}")
        await asyncio.sleep(3600)

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="CaseAlpha ScrapeEngine API",
        version="1.0.0",
        description="A robust web scraping service with proxy management",
        routes=app.routes,
    )
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

def get_uptime():
    """Returns the system uptime in seconds"""
    try:
        with open('/proc/uptime', 'r') as f:
            uptime_seconds = float(f.readline().split()[0])
        return uptime_seconds
    except:
        return 0  # Return 0 if unable to get uptime (e.g., on non-Linux systems)

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": "1.0.0",
        "uptime": get_uptime(),
        "proxy_count": len(ProxyManager().proxies),
        "scraper_count": len(credentials_list)
    }

if __name__ == '__main__':
    # Start the proxy updater thread
    threads = []
    threads.append(threading.Thread(target=lambda: asyncio.run(main_proxy_updater()), daemon=True))
    for thread in threads:
        thread.start()

    logger.info("Starting scrape engine...")
    # Running the app with an async-friendly server like uvicorn
    import uvicorn
    host = os.getenv('HOST', '0.0.0.0')
    port = int(os.getenv('PORT', 8080))
    uvicorn.run(app, host=host, port=port)
