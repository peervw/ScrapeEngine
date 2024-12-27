from fastapi import APIRouter, HTTPException, Depends
from ...core.security import token_required
from ..dependencies import get_runner_manager, get_proxy_manager
from ...services.runner_manager import RunnerManager
from ...services.proxy_manager import ProxyManager
import psutil
import logging

router = APIRouter(prefix="/api/runners", tags=["runners"])
logger = logging.getLogger(__name__)

@router.post('/register')
async def register_runner(
    request: dict,
    runner_manager: RunnerManager = Depends(get_runner_manager),
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
        await runner_manager.register_runner(runner_id, url)
        logger.info(f"Successfully registered runner {runner_id} at {url}")
        return {
            "status": "registered",
            "runner_id": runner_id,
            "url": url
        }
    except Exception as e:
        logger.error(f"Failed to register runner {runner_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get('/health')
async def get_runners_health(
    runner_manager: RunnerManager = Depends(get_runner_manager),
    authorization: str = Depends(token_required)
):
    """Get health status of all runners"""
    runners = runner_manager.runners
    result = []
    
    for runner_id, info in runners.items():
        runner_data = {
            "id": runner_id,
            "status": "active" if info["status"] == "active" else "offline",
            "cpu_usage": psutil.cpu_percent(),  # This would come from the runner's metrics
            "memory_usage": {
                "used": psutil.virtual_memory().used // (1024 * 1024),  # Convert to MB
                "total": psutil.virtual_memory().total // (1024 * 1024)  # Convert to MB
            },
            "active_jobs": 0,  # This would come from the runner's metrics
            "uptime": 0  # This would come from the runner's metrics
        }
        
        if info["status"] == "offline":
            runner_data["last_seen"] = "15m ago"  # This would be calculated
            runner_data["last_status"] = "Connection lost"
            
        result.append(runner_data)
    
    return result

@router.get('/debug')
async def debug_runners(
    runner_manager: RunnerManager = Depends(get_runner_manager),
    authorization: str = Depends(token_required)
):
    """Debug endpoint to check runner status"""
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

@router.get('/test-scrape')
async def test_scrape(
    runner_manager: RunnerManager = Depends(get_runner_manager),
    proxy_manager: ProxyManager = Depends(get_proxy_manager),
    authorization: str = Depends(token_required)
):
    """Test endpoint to try a scrape operation"""
    try:
        logger.info("Starting test scrape")
        
        # Check if we have runners
        if not runner_manager.runners:
            logger.error("No runners registered")
            return {
                "status": "error",
                "error": "No runners registered. Please check runner logs."
            }
            
        proxy = await proxy_manager.get_next_proxy()
        logger.info(f"Got proxy: {proxy[0]}:{proxy[1]}")
        
        task_data = {
            "url": "https://example.com",
            "proxy": proxy,
            "method": "simple",
            "stealth": False,
            "cache": True
        }
        
        result = await runner_manager.distribute_task(task_data)
        logger.info("Test scrape completed successfully")
        
        return {
            "status": "success",
            "proxy_used": f"{proxy[0]}:{proxy[1]}",
            "result": result,
            "runners_available": len(runner_manager.runners)
        }
    except Exception as e:
        logger.error(f"Test scrape failed: {e}")
        return {
            "status": "error",
            "error": str(e),
            "runners_available": len(runner_manager.runners)
        } 