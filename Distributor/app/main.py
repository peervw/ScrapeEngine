from fastapi import FastAPI, HTTPException, Depends, Header, Request
from typing import Optional, List, Dict
from .services.proxy_manager import ProxyManager
from .services.runner_manager import RunnerManager
from .services.runner_discovery import RunnerDiscovery
from .models import ScrapeRequest
from .config.logging_config import setup_logging
import logging
import os
import asyncio
import aiohttp
from contextlib import asynccontextmanager

# Setup logging first
setup_logging()
logger = logging.getLogger(__name__)

_auth_status_logged = False

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    logger.info("Starting Distributor service...")
    
    # Log authentication status once at startup
    auth_token = os.getenv("AUTH_TOKEN")
    if auth_token:
        logger.info("Authentication enabled - AUTH_TOKEN is set")
    else:
        logger.info("Authentication disabled - AUTH_TOKEN not set")
    
    # Startup
    logger.debug("Starting up distributor service...")
    try:
        app.state.runner_manager = RunnerManager()
        app.state.proxy_manager = ProxyManager()
        app.state.runner_discovery = RunnerDiscovery()
        
        logger.info("Starting proxy maintenance task")
        asyncio.create_task(app.state.proxy_manager.start_proxy_maintenance())
        
        logger.info("Starting runner monitoring task")
        asyncio.create_task(monitor_runners(app))
        
        logger.info("Startup complete")
    except Exception as e:
        logger.error(f"Startup failed: {e}", exc_info=True)
        raise
    
    yield  # Server is running

async def monitor_runners(app: FastAPI):
    """Background task to monitor and ping runners"""
    await asyncio.sleep(30)  # Wait 30 seconds after startup
    
    while True:
        try:
            await asyncio.sleep(60)  # Check every minute
            
            active_runners = len(app.state.runner_manager.runners)
            logger.debug(f"Runner monitor: {active_runners} active runners")
            
            if active_runners == 0:
                logger.warning("No active runners found, attempting to ping known runners")
                pinged = await app.state.runner_discovery.ping_known_runners(app.state.runner_manager)
                logger.info(f"Pinged {pinged} known runners for re-registration")
                
                # If still no runners after pinging, try to discover via Docker/network
                if len(app.state.runner_manager.runners) == 0:
                    await discover_runners_via_network(app)
                    
        except Exception as e:
            logger.error(f"Error in runner monitoring: {e}")

async def discover_runners_via_network(app: FastAPI):
    """Try to discover runners via common Docker network patterns"""
    try:
        # Common Docker service names for runners
        potential_runners = [
            "http://runner:8000",
            "http://runner-1:8000",
            "http://runner-2:8000",
            "http://runner-3:8000",
            "http://scrape-runner:8000",
            "http://scrape-runner-1:8000",
            "http://scrape-runner-2:8000"
        ]
        
        for runner_url in potential_runners:
            try:
                timeout = aiohttp.ClientTimeout(total=5)
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    # Try to ping the health endpoint
                    async with session.get(f"{runner_url}/health") as response:
                        if response.status == 200:
                            logger.info(f"Discovered potential runner at {runner_url}")
                            # Send ping to trigger re-registration
                            await app.state.runner_discovery._ping_runner(f"discovered-{runner_url.split('/')[-1]}", runner_url)
            except Exception:
                continue  # Ignore failed discovery attempts
                
    except Exception as e:
        logger.error(f"Error in network discovery: {e}")

app = FastAPI(
    title="ScrapeEngine Distributor",
    description="Distributed web scraping service with proxy rotation",
    version="1.0.0",
    lifespan=lifespan
)

def verify_auth(auth_header: Optional[str]) -> bool:
    """Verify authentication header"""
    if not auth_header:
        return False
    try:
        scheme, token = auth_header.split()
        return scheme.lower() == 'bearer' and token == os.getenv("AUTH_TOKEN")
    except:
        return False

def optional_token_required(authorization: Optional[str] = Header(None)):
    """Optional authentication - only required if AUTH_TOKEN is set"""
    global _auth_status_logged
    auth_token = os.getenv("AUTH_TOKEN")
    
    # If no AUTH_TOKEN is set, skip authentication
    if not auth_token:
        if not _auth_status_logged:
            logger.info("AUTH_TOKEN not set - running without authentication")
            _auth_status_logged = True
        return None
    
    # If AUTH_TOKEN is set, require proper authentication
    if not authorization:
        raise HTTPException(status_code=401, detail="No authorization token provided")
    
    try:
        # Extract token from "Bearer <token>"
        scheme, token = authorization.split()
        if scheme.lower() != 'bearer':
            raise HTTPException(status_code=401, detail="Invalid authentication scheme")
        if token != auth_token:
            raise HTTPException(status_code=401, detail="Invalid token")
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid token format")
    
    return authorization

# Protected endpoints with optional authentication
@app.post('/api/scrape')
async def scrape_endpoint(
    request: ScrapeRequest,
    authorization: str = Depends(optional_token_required)
):
    proxy = None
    try:
        task_data = {
            "url": str(request.url),
            "method": request.method,
            "full_content": request.full_content,
            "stealth": request.stealth,
            "cache": request.cache,
            "parse": request.parse,
        }
        
        result = await app.state.runner_manager.distribute_task(task_data)
        
        return {
            "url": request.url,
            "method": result.get("method", request.method),
            "full_content": request.full_content,
            "stealth": request.stealth,
            "cache": request.cache,
            "parse": request.parse,
            "runner_used": result.get("runner_id", "unknown"),
            "content": result,
        }
            
    except Exception as e:
        logger.error(f"Scrape error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post('/api/runners/register')
async def register_runner(
    request: dict,
    authorization: str = Depends(optional_token_required)
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
        
        # Add to known runners for future pinging
        app.state.runner_discovery.add_known_runner(runner_id, url)
        
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
async def health_check(authorization: str = Depends(optional_token_required)):
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
async def debug_proxies(authorization: str = Depends(optional_token_required)):
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
async def debug_runners(authorization: str = Depends(optional_token_required)):
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
async def test_scrape(authorization: str = Depends(optional_token_required)):
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

@app.get("/api/proxy/next")
async def get_next_proxy(authorization: str = Depends(optional_token_required)):
    """Get the next available proxy from the proxy manager"""
    proxy = await app.state.proxy_manager.get_next_proxy()
    if not proxy:
        raise HTTPException(status_code=503, detail="No proxies available")
    return proxy

@app.get("/api/runners/status")
async def get_runner_status(authorization: str = Depends(optional_token_required)):
    """Get status of all registered runners"""
    return app.state.runner_manager.get_runner_status()

@app.post("/api/runners/ping-all")
async def ping_all_runners(authorization: str = Depends(optional_token_required)):
    """Manually trigger pinging of all known runners"""
    try:
        pinged = await app.state.runner_discovery.ping_known_runners(app.state.runner_manager)
        return {
            "status": "success",
            "runners_pinged": pinged,
            "known_runners": len(app.state.runner_discovery.known_runners),
            "active_runners": len(app.state.runner_manager.runners)
        }
    except Exception as e:
        logger.error(f"Error pinging runners: {e}")
        raise HTTPException(status_code=500, detail=str(e))