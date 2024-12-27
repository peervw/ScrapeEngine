from fastapi import APIRouter, HTTPException, Depends
from ...core.security import token_required
from ...models import ScrapeRequest
from ...db.crud.logs import store_log
from ..dependencies import get_runner_manager, get_proxy_manager
from ...services.runner_manager import RunnerManager
from ...services.proxy_manager import ProxyManager
import logging
from datetime import datetime

router = APIRouter(prefix="/api/scrape", tags=["scrape"])
logger = logging.getLogger(__name__)

@router.post("")
async def scrape_endpoint(
    request: ScrapeRequest,
    runner_manager: RunnerManager = Depends(get_runner_manager),
    proxy_manager: ProxyManager = Depends(get_proxy_manager),
    authorization: str = Depends(token_required)
):
    try:
        start_time = datetime.now()
        try:
            proxy = await proxy_manager.get_next_proxy()
        except Exception as e:
            logger.warning(f"Failed to get proxy: {e}, proceeding without proxy")
            proxy = None
            
        task_data = {
            "url": str(request.url),
            "stealth": request.stealth,
            "render": request.render,
            "parse": request.parse,
            "proxy": proxy,
            "headers": None
        }
        
        result = await runner_manager.distribute_task(task_data)
        end_time = datetime.now()
        response_time = (end_time - start_time).total_seconds()
        
        # Check if the scraping failed
        if result.get("status") == "error":
            if proxy:  # Only update proxy metrics if a proxy was used
                await proxy_manager.update_proxy_metrics(proxy[0], response_time, False)
            # Store error log
            log_data = {
                "timestamp": start_time.isoformat(),
                "runner_id": result.get("runner_id", "unknown"),
                "status": "failed",
                "url": str(request.url),
                "duration": response_time,
                "details": result.get("error", "Scraping failed"),
                "config": {
                    "url": str(request.url),
                    "stealth": request.stealth,
                    "render": request.render,
                    "parse": request.parse,
                    "proxy": f"{proxy[0]}:{proxy[1]}" if proxy else "none"
                },
                "error": result.get("error")
            }
            store_log(log_data)
            raise HTTPException(status_code=500, detail=result.get("error", "Scraping failed"))
            
        # Update proxy metrics with response time if proxy was used
        if proxy:
            await proxy_manager.update_proxy_metrics(proxy[0], response_time, True)
        
        # Store success log
        logger.debug(f"Raw result from runner: {result}")
        
        # Format the response data
        response_data = {
            "url": str(request.url),
            "stealth": request.stealth,
            "render": request.render,
            "parse": request.parse,
            "proxy_used": f"{proxy[0]}:{proxy[1]}" if proxy else "none",
            "runner_used": result.get("runner_id", "unknown"),
            "method_used": result.get("method_used", "aiohttp"),
            "response_time": response_time,
            "content": {
                "raw_content": result.get("raw_content"),
                "text_content": result.get("text_content"),
                "title": result.get("title"),
                "links": result.get("links", []),
                "parse_error": result.get("parse_error")
            }
        }
        
        # Store log with the same format as the response
        log_data = {
            "timestamp": start_time.isoformat(),
            "runner_id": result.get("runner_id", "unknown"),
            "status": "success",
            "url": str(request.url),
            "duration": response_time,
            "details": "Successfully scraped content",
            "config": {
                "url": str(request.url),
                "stealth": request.stealth,
                "render": request.render,
                "parse": request.parse,
                "proxy": f"{proxy[0]}:{proxy[1]}" if proxy else "none"
            },
            "result": {
                "proxy_used": f"{proxy[0]}:{proxy[1]}" if proxy else "none",
                "runner_used": result.get("runner_id", "unknown"),
                "method_used": result.get("method_used", "aiohttp"),
                "response_time": response_time,
                "content": {
                    "raw_content": result.get("raw_content"),
                    "text_content": result.get("text_content"),
                    "title": result.get("title"),
                    "links": result.get("links", []),
                    "parse_error": result.get("parse_error")
                }
            }
        }
        
        logger.debug(f"Storing log data: {log_data}")
        store_log(log_data)
        
        return response_data
            
    except Exception as e:
        logger.error(f"Scrape error: {e}")
        if 'proxy' in locals() and proxy:
            end_time = datetime.now()
            response_time = (end_time - start_time).total_seconds()
            await proxy_manager.update_proxy_metrics(proxy[0], response_time, False)
        # Store error log
        log_data = {
            "timestamp": datetime.now().isoformat(),
            "runner_id": "unknown",
            "status": "failed",
            "url": str(request.url) if 'request' in locals() else "unknown",
            "duration": response_time if 'response_time' in locals() else 0,
            "details": str(e),
            "config": task_data if 'task_data' in locals() else None,
            "error": str(e)
        }
        store_log(log_data)
        raise HTTPException(status_code=500, detail=str(e)) 