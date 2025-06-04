from typing import Dict
import aiohttp
import logging
import json
from fastapi import HTTPException
from datetime import datetime, timedelta
import random
import asyncio

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
                "last_failure": None,
                "failure_count": 0
            }
            logger.info(f"Runner {runner_id} registered successfully. Total runners: {len(self.runners)}")
            logger.info(f"Current runners: {list(self.runners.keys())}")
            
        except Exception as e:
            logger.error(f"Failed to register runner {runner_id}: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))
    
    def _is_runner_available(self, runner_info: dict) -> bool:
        """Check if runner is available for task distribution"""
        if runner_info["status"] != "active":
            return False
            
        # If runner never failed, it's available
        if not runner_info.get("last_failure"):
            return True
            
        # Check if enough time has passed since last failure (10 seconds)
        last_failure = datetime.fromisoformat(runner_info["last_failure"])
        cooldown_period = timedelta(seconds=10)
        
        return datetime.now() - last_failure > cooldown_period
    
    def _mark_runner_failed(self, runner_id: str):
        """Mark runner as temporarily failed"""
        if runner_id in self.runners:
            self.runners[runner_id]["last_failure"] = datetime.now().isoformat()
            self.runners[runner_id]["failure_count"] = self.runners[runner_id].get("failure_count", 0) + 1
            
            # If runner fails too many times (e.g., 5), remove it permanently
            if self.runners[runner_id]["failure_count"] >= 5:
                logger.warning(f"Runner {runner_id} failed {self.runners[runner_id]['failure_count']} times, removing permanently")
                self.runners.pop(runner_id, None)
            else:
                logger.warning(f"Runner {runner_id} marked as temporarily unavailable (failure #{self.runners[runner_id]['failure_count']})")
    
    def _mark_runner_success(self, runner_id: str):
        """Reset failure count on successful task completion"""
        if runner_id in self.runners:
            self.runners[runner_id]["failure_count"] = 0
            self.runners[runner_id]["last_failure"] = None
        
    async def distribute_task(self, task_data: dict):
        """Distribute task to a random available runner with retry logic"""
        if not self.runners:
            logger.error("No runners available for task distribution")
            raise HTTPException(status_code=503, detail="No runners available")
            
        # Get available runners (not in cooldown)
        available_runners = [
            (runner_id, runner_info) 
            for runner_id, runner_info in self.runners.items() 
            if self._is_runner_available(runner_info)
        ]
        
        if not available_runners:
            logger.warning("No runners currently available (all in cooldown)")
            # Wait a bit and check again
            await asyncio.sleep(2)
            available_runners = [
                (runner_id, runner_info) 
                for runner_id, runner_info in self.runners.items() 
                if self._is_runner_available(runner_info)
            ]
            
            if not available_runners:
                raise HTTPException(status_code=503, detail="No runners available (all in cooldown)")
        
        # Shuffle for random selection
        random.shuffle(available_runners)
        
        # Try runners in random order until one succeeds
        for runner_id, runner_info in available_runners:
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
                            self._mark_runner_failed(runner_id)
                            continue
                        
                        result = await response.json()
                        logger.info(f"Task completed successfully by runner {runner_id}")
                        self._mark_runner_success(runner_id)
                        return result
                        
                except Exception as e:
                    logger.error(f"Runner {runner_id} failed with error: {e}")
                    self._mark_runner_failed(runner_id)
                    continue
        
        # If we get here, all available runners failed
        raise HTTPException(status_code=503, detail="All available runners failed")
    
    def get_runner_status(self) -> dict:
        """Get status of all runners"""
        status = {}
        for runner_id, runner_info in self.runners.items():
            status[runner_id] = {
                "status": runner_info["status"],
                "available": self._is_runner_available(runner_info),
                "failure_count": runner_info.get("failure_count", 0),
                "last_failure": runner_info.get("last_failure")
            }
        return status