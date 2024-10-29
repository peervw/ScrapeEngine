from fastapi import FastAPI, HTTPException, Request, Header, Depends
from fastapi.responses import JSONResponse
import os
import logging
from functions import *
from webshare_proxy import *
import threading
import asyncio
from concurrent.futures import ThreadPoolExecutor, TimeoutError
from typing import Optional
import multiprocessing
import random
from pydantic import BaseModel, ValidationError
from functools import lru_cache
import cachetools

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

def token_required(authorization: Optional[str] = Header(None)):
    if not authorization or authorization not in API_TOKEN:
        logger.warning("Unauthorized access attempt.")
        raise HTTPException(status_code=401, detail="Unauthorized: Invalid or missing token.")

class ScrapeRequest(BaseModel):
    url: str
    link_or_article: Optional[str] = "article"
    if link_or_article not in ["link", "article"]:
        raise ValueError("link_or_article must be either 'link', 'article' or empty")
    other_params: Optional[dict] = None  # Add other expected fields here if needed

async def route_to_scraper(args):
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

@app.get('/api/scrape')
async def scrape_endpoint(request: Request, authorization: str = Depends(token_required)):
    # Get JSON arguments
    try:
        args = await request.json()
        validated_args = ScrapeRequest(**args)
    except ValidationError as e:
        logger.error(f"Invalid input data: {e.json()}")
        return JSONResponse(status_code=400, content={"error": "Invalid input data", "details": e.errors()})
    except Exception as e:
        logger.error(f"Failed to parse request JSON: {str(e)}")
        return JSONResponse(status_code=400, content={"error": "Invalid request format"})

    # Convert validated_args to dictionary
    args = validated_args.dict()

    # Validate that the target URL is provided
    target_url = args.get('url')
    if not target_url:
        logger.error("No target URL provided in request")
        return JSONResponse(status_code=400, content={"error": "No target URL provided"})

    # Route to the next available scraper with appropriate credentials
    try:
        result = await route_to_scraper(args)
        return JSONResponse(content=result)
    except HTTPException as e:
        logger.error(f"HTTP error occurred: {str(e)}")
        return JSONResponse(status_code=e.status_code, content={"error": e.detail})
    except Exception as e:
        logger.error(f"An error occurred while scraping: {str(e)}")
        return JSONResponse(status_code=500, content={"error": str(e)})

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
