from fastapi import FastAPI, HTTPException, Depends, Header
from typing import Optional
from .services.proxy_manager import ProxyManager
from .services.runner_manager import RunnerManager
from .models import ScrapeRequest
from .config.logging_config import setup_logging
from .database import DatabaseManager
import logging
import os
import asyncio
from contextlib import asynccontextmanager
from datetime import datetime
import time

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
        app.state.db_manager = DatabaseManager()
        
        logger.info("Starting proxy maintenance task")
        asyncio.create_task(app.state.proxy_manager.start_proxy_maintenance())
        
        # Create periodic stats update task
        async def update_stats_periodically():
            while True:
                try:
                    active_jobs = len(getattr(app.state.runner_manager, 'active_tasks', {}))
                    connected_runners = len(getattr(app.state.runner_manager, 'runners', {}))
                    app.state.db_manager.update_system_stats(active_jobs, connected_runners)
                except Exception as e:
                    logger.error(f"Error updating stats: {e}")
                await asyncio.sleep(60)  # Update every minute
        
        asyncio.create_task(update_stats_periodically())
        logger.info("Startup complete")
    except Exception as e:
        logger.error(f"Startup failed: {e}", exc_info=True)
        raise
    
    yield  # Server is running
    

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
        
        # Check if it's the legacy admin token
        if token == os.getenv("AUTH_TOKEN"):
            return token, "admin"
        
        # Check database for API keys
        is_valid, key_id = app.state.db_manager.validate_api_key(token)
        if not is_valid:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        return token, key_id
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid token format")

# Protected endpoints with authentication
@app.post('/api/scrape')
async def scrape_endpoint(
    request: ScrapeRequest,
    auth_data: tuple = Depends(token_required)
):
    token, key_id = auth_data
    proxy = None
    start_time = time.time()
    scrape_id = None
    
    try:
        proxy = await app.state.proxy_manager.get_next_proxy()
        task_data = {
            "url": str(request.url),
            "method": request.method,
            "full_content": request.full_content,
            "stealth": request.stealth,
            "cache": request.cache,
            "parse": request.parse,
            "proxy": proxy
        }
        
        result = await app.state.runner_manager.distribute_task(task_data)
        await app.state.proxy_manager.mark_proxy_result(proxy[0], True)
        
        # Record successful scrape
        response_time = time.time() - start_time
        content_length = len(str(result)) if result else 0
        scrape_id = app.state.db_manager.record_scrape(
            url=str(request.url),
            method=request.method,
            status="success",
            runner_id=result.get("runner_id", "unknown"),
            proxy_used=f"{proxy[0]}:{proxy[1]}" if proxy else None,
            response_time=response_time,
            content_length=content_length,
            api_key_id=key_id if key_id != "admin" else None
        )
        
        return {
            "url": request.url,
            "method": result.get("method", request.method),
            "full_content": request.full_content,
            "stealth": request.stealth,
            "cache": request.cache,
            "parse": request.parse,
            "proxy_used": f"{proxy[0]}:{proxy[1]}" if proxy else None,
            "runner_used": result.get("runner_id", "unknown"),
            "content": result,
            "scrape_id": scrape_id,
            "response_time": response_time
        }
            
    except Exception as e:
        logger.error(f"Scrape error: {e}")
        if proxy:
            await app.state.proxy_manager.mark_proxy_result(proxy[0], False)
        
        # Record failed scrape
        response_time = time.time() - start_time
        app.state.db_manager.record_scrape(
            url=str(request.url),
            method=request.method,
            status="failed",
            proxy_used=f"{proxy[0]}:{proxy[1]}" if proxy else None,
            response_time=response_time,
            api_key_id=key_id if key_id != "admin" else None,
            error_message=str(e)
        )
        
        raise HTTPException(status_code=500, detail=str(e))

@app.post('/api/runners/register')
async def register_runner(
    request: dict,
    auth_data: tuple = Depends(token_required)
):
    """Register a new runner with the distributor"""
    token, key_id = auth_data
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
async def health_check(auth_data: tuple = Depends(token_required)):
    token, key_id = auth_data
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
async def debug_proxies(auth_data: tuple = Depends(token_required)):
    """Debug endpoint to check proxy status"""
    token, key_id = auth_data
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
async def debug_runners(auth_data: tuple = Depends(token_required)):
    """Debug endpoint to check runner status"""
    token, key_id = auth_data
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
async def test_scrape(auth_data: tuple = Depends(token_required)):
    """Test endpoint to try a scrape operation"""
    token, key_id = auth_data
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

# Frontend API endpoints (no auth required for dashboard)
@app.get("/api/stats")
async def get_stats():
    """Get system statistics for the dashboard"""
    try:
        # Get latest stats from database
        stats = app.state.db_manager.get_latest_stats()
        
        # Get real-time runner info
        runner_manager = app.state.runner_manager
        active_runners = len([r for r in runner_manager.runners.values() if r.get("status") == "active"])
        total_runners = len(runner_manager.runners)
        
        # Get real-time job info (active tasks)
        active_jobs = len(getattr(runner_manager, 'active_tasks', {}))
        
        # Calculate system health based on active runners and recent success rate
        system_health = 100.0 if active_runners > 0 else 0.0
        
        # Override with real-time data
        stats.update({
            "active_jobs": active_jobs,
            "connected_runners": active_runners,
            "total_runners": total_runners,
            "system_health": system_health,
            "timestamp": datetime.now().isoformat()
        })
        
        return stats
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        # Fallback to basic stats
        runner_manager = app.state.runner_manager
        active_runners = len([r for r in runner_manager.runners.values() if r.get("status") == "active"])
        
        return {
            "active_jobs": len(getattr(runner_manager, 'active_tasks', {})),
            "connected_runners": active_runners,
            "total_runners": len(runner_manager.runners),
            "pages_scraped": 0,
            "total_scrapes_today": 0,
            "total_scrapes_all_time": 0,
            "average_response_time": 0.0,
            "system_health": 100.0 if active_runners > 0 else 0.0,
            "error_rate": 0.0,
            "timestamp": datetime.now().isoformat()
        }

@app.get("/api/runners")
async def get_runners():
    """Get all registered runners for the dashboard"""
    runner_manager = app.state.runner_manager
    
    runners = []
    for runner_id, info in runner_manager.runners.items():
        runners.append({
            "id": runner_id,
            "name": runner_id,
            "status": info.get("status", "unknown"),
            "current_job": None,  # We don't track current jobs yet
            "last_heartbeat": info.get("registered_at", datetime.now().isoformat()),
            "cpu_usage": 0,  # Could be added to runner health endpoint
            "memory_usage": 0,  # Could be added to runner health endpoint
            "completed_jobs": 0,  # Could be tracked
            "uptime": "unknown",  # Could be calculated from registered_at
            "version": "1.0.0"
        })
    
    return runners

@app.get("/api/jobs")
async def get_jobs():
    """Get active jobs (for now, return empty as we don't track jobs separately)"""
    # In the future, you could implement job tracking in the runner manager
    return []

@app.get("/api/scrapes")
async def get_scrape_history():
    """Get recent scrape records for the dashboard"""
    try:
        scrapes = app.state.db_manager.get_recent_scrapes(limit=50)
        return scrapes
    except Exception as e:
        logger.error(f"Error getting scrape history: {e}")
        return []

# Admin API endpoints (require authentication)
@app.get("/api/admin/api-keys")
async def get_api_keys(auth_data: tuple = Depends(token_required)):
    """Get all API keys (admin only)"""
    token, key_id = auth_data
    
    # Only allow admin access
    if key_id != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        api_keys = app.state.db_manager.get_api_keys()
        return api_keys
    except Exception as e:
        logger.error(f"Error getting API keys: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/admin/api-keys")
async def create_api_key(request: dict, auth_data: tuple = Depends(token_required)):
    """Create a new API key (admin only)"""
    token, key_id = auth_data
    
    # Only allow admin access
    if key_id != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    name = request.get("name")
    if not name:
        raise HTTPException(status_code=400, detail="Name is required")
    
    try:
        key_id, raw_key = app.state.db_manager.generate_api_key(name)
        return {
            "key_id": key_id,
            "name": name,
            "key": raw_key,
            "message": "API key created successfully. Save this key securely - you won't be able to see it again."
        }
    except Exception as e:
        logger.error(f"Error creating API key: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/admin/api-keys/{key_id}")
async def deactivate_api_key(key_id: str, auth_data: tuple = Depends(token_required)):
    """Deactivate an API key (admin only)"""
    token, user_key_id = auth_data
    
    # Only allow admin access
    if user_key_id != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        success = app.state.db_manager.deactivate_api_key(key_id)
        if success:
            return {"message": "API key deactivated successfully"}
        else:
            raise HTTPException(status_code=404, detail="API key not found")
    except Exception as e:
        logger.error(f"Error deactivating API key: {e}")
        raise HTTPException(status_code=500, detail=str(e))
