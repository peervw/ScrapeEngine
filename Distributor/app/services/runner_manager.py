from typing import Dict
import aiohttp
import logging
import json
from fastapi import HTTPException
from datetime import datetime
import random

logger = logging.getLogger(__name__)

class RunnerManager:
    def __init__(self):
        self.runners: Dict[str, dict] = {}  # runner_id -> runner_info
        logger.info("RunnerManager initialized")
        
    async def register_runner(self, runner_id: str, url: str):
        """Register a new runner"""
        try:
            logger.info(f"Registering runner {runner_id} with URL {url}")
            
            # Test the runner's connection
            async with aiohttp.ClientSession() as session:
                try:
                    health_url = f"{url}/health"
                    logger.info(f"Testing runner health at {health_url}")
                    async with session.get(health_url, timeout=5) as response:
                        if response.status != 200:
                            raise Exception(f"Runner health check failed: {response.status}")
                except Exception as e:
                    logger.error(f"Runner health check failed: {str(e)}")
                    raise HTTPException(
                        status_code=503, 
                        detail=f"Runner health check failed: {str(e)}"
                    )
            
            self.runners[runner_id] = {
                "url": url,
                "status": "active",
                "registered_at": datetime.now().isoformat(),
                "failures": 0  # Track consecutive failures
            }
            logger.info(f"Runner {runner_id} registered successfully. Total runners: {len(self.runners)}")
            logger.info(f"Current runners: {list(self.runners.keys())}")
            
        except Exception as e:
            logger.error(f"Failed to register runner {runner_id}: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))
            
    async def distribute_task(self, task_data: dict):
        """Distribute task to a random available runner"""
        if not self.runners:
            logger.error("No runners available for task distribution")
            raise HTTPException(status_code=503, detail="No runners available")
            
        # Convert runners to list and shuffle for random selection
        runner_items = list(self.runners.items())
        random.shuffle(runner_items)
        
        # Try runners in random order until one succeeds
        last_error = None
        for runner_id, runner_info in runner_items:
            if runner_info.get("failures", 0) >= 3:  # Skip runners with too many failures
                continue
                
            logger.info(f"Attempting to distribute task to runner {runner_id}")
            
            async with aiohttp.ClientSession() as session:
                try:
                    async with session.post(
                        f"{runner_info['url']}/scrape",
                        json=task_data,
                        timeout=30
                    ) as response:
                        if response.status != 200:
                            logger.error(f"Runner {runner_id} failed with status {response.status}")
                            runner_info["failures"] = runner_info.get("failures", 0) + 1
                            if runner_info["failures"] >= 3:
                                self.runners.pop(runner_id, None)
                            continue
                            
                        result = await response.json()
                        logger.info(f"Task completed successfully by runner {runner_id}")
                        runner_info["failures"] = 0  # Reset failure count on success
                        return result
                except Exception as e:
                    logger.error(f"Runner {runner_id} failed with error: {e}")
                    last_error = e
                    runner_info["failures"] = runner_info.get("failures", 0) + 1
                    if runner_info["failures"] >= 3:
                        self.runners.pop(runner_id, None)
                    continue
        
        # If we get here, all runners failed
        error_msg = str(last_error) if last_error else "All runners failed"
        raise HTTPException(status_code=503, detail=error_msg)