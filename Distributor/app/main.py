from fastapi import FastAPI, HTTPException, Depends, Header
from typing import Optional
from .services.proxy_manager import ProxyManager
from .services.runner_manager import RunnerManager
from .models import ScrapeRequest
from .config.logging_config import setup_logging
import logging
import os
import asyncio
from contextlib import asynccontextmanager

# Setup logging first
setup_logging()
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.debug("Starting up distributor service...")
    try:
        app.state.runner_manager = RunnerManager()
        app.state.proxy_manager = ProxyManager()
        
        logger.info("Starting proxy maintenance task")
        asyncio.create_task(app.state.proxy_manager.start_proxy_maintenance())
        logger.info("Startup complete")
    except Exception as e:
        logger.error(f"Startup failed: {e}", exc_info=True)
        raise
    
    yield  # Server is running
    
    # Shutdown (if you need cleanup code)

app = FastAPI(
    title="ScrapeEngine Distributor",
    description="Distributed web scraping service with proxy rotation",
    version="1.0.0",
    lifespan=lifespan
)

def token_required(authorization: Optional[str] = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="No authorization token provided")
    
    try:
        # Extract token from "Bearer <token>"
        scheme, token = authorization.split()
        if scheme.lower() != 'bearer':
            raise HTTPException(status_code=401, detail="Invalid authentication scheme")
        if token != os.getenv("AUTH_TOKEN"):
            raise HTTPException(status_code=401, detail="Invalid token")
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid token format")
    
    return authorization

# Protected endpoints with authentication
@app.post('/api/scrape')
async def scrape_endpoint(
    request: ScrapeRequest,
    authorization: str = Depends(token_required)
):
    try:
        proxy = await app.state.proxy_manager.get_next_proxy()
        task_data = {
            "url": str(request.url),
            "full_content": request.full_content,
            "stealth": request.stealth,
            "cache": request.cache,
            "proxy": proxy
        }
        
        try:
            result = await app.state.runner_manager.distribute_task(task_data)
            await app.state.proxy_manager.mark_proxy_result(proxy[0], True)
            
            # Format response
            return {
                "url": request.url,
                "full_content": request.full_content,
                "stealth": request.stealth,
                "cache": request.cache,
                "proxy_used": f"{proxy[0]}:{proxy[1]}",
                "runner_used": result.get("runner_id", "unknown"),
                "method_used": result.get("method_used", "unknown"),
                "content": result,
            }
        except Exception as e:
            await app.state.proxy_manager.mark_proxy_result(proxy[0], False)
            raise e
            
    except Exception as e:
        logger.error(f"Scrape error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post('/api/runners/register')
async def register_runner(
    request: dict,
    authorization: str = Depends(token_required)
):
    """Register a new runner with the distributor"""
    logger.info(f"Received registration request: {request}")
    
    runner_id = request.get("runner_id")
    url = request.get("url")
    
    if not runner_id or not url:
        logger.error("Missing runner_id or url in registration request")
        raise HTTPException(status_code=400, detail="Missing runner_id or url")
    
    try:
        await app.state.runner_manager.register_runner(runner_id, url)
        logger.info(f"Successfully registered runner {runner_id} at {url}")
        return {
            "status": "registered",
            "runner_id": runner_id,
            "url": url
        }
    except Exception as e:
        logger.error(f"Failed to register runner {runner_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check(authorization: str = Depends(token_required)):
    return {
        "status": "healthy",
        "version": "1.0.0",
        "active_runners": len(app.state.runner_manager.runners),
        "available_proxies": len(app.state.proxy_manager.available_proxies)
    }

@app.get("/health/public")
async def public_health_check():
    """Public health check endpoint that doesn't require authentication"""
    return {
        "status": "healthy",
        "version": "1.0.0"
    }

@app.get("/api/debug/proxies")
async def debug_proxies(authorization: str = Depends(token_required)):
    """Debug endpoint to check proxy status"""
    proxy_manager = app.state.proxy_manager
    return {
        "total_proxies": len(proxy_manager.proxies),
        "available_proxies": len(proxy_manager.available_proxies),
        "sample_proxies": [
            {
                "host": proxy_manager.proxies[host]["host"],
                "port": proxy_manager.proxies[host]["port"],
                "last_used": proxy_manager.proxies[host]["last_used"]
            }
            for host in list(proxy_manager.proxies.keys())[:5]
        ]
    }

@app.get("/api/debug/runners")
async def debug_runners(authorization: str = Depends(token_required)):
    """Debug endpoint to check runner status"""
    runner_manager = app.state.runner_manager
    return {
        "active_runners": len(runner_manager.runners),
        "runners": [
            {
                "id": runner_id,
                "url": info["url"],
                "status": info["status"]
            }
            for runner_id, info in runner_manager.runners.items()
        ]
    }

@app.get("/api/debug/test-scrape")
async def test_scrape(authorization: str = Depends(token_required)):
    """Test endpoint to try a scrape operation"""
    try:
        logger.info("Starting test scrape")
        
        # Check if we have runners
        if not app.state.runner_manager.runners:
            logger.error("No runners registered")
            return {
                "status": "error",
                "error": "No runners registered. Please check runner logs."
            }
            
        proxy = await app.state.proxy_manager.get_next_proxy()
        logger.info(f"Got proxy: {proxy[0]}:{proxy[1]}")
        
        task_data = {
            "url": "https://example.com",
            "proxy": proxy,
            "method": "simple",
            "stealth": False,
            "cache": True
        }
        
        result = await app.state.runner_manager.distribute_task(task_data)
        logger.info("Test scrape completed successfully")
        
        return {
            "status": "success",
            "proxy_used": f"{proxy[0]}:{proxy[1]}",
            "result": result,
            "runners_available": len(app.state.runner_manager.runners)
        }
    except Exception as e:
        logger.error(f"Test scrape failed: {e}")
        return {
            "status": "error",
            "error": str(e),
            "runners_available": len(app.state.runner_manager.runners)
        }
