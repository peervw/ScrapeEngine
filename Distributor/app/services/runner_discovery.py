from typing import Dict
import aiohttp
import logging
import os
from runner_manager import RunnerManager
from datetime import datetime

logger = logging.getLogger(__name__)

class RunnerDiscovery:
    def __init__(self):
        self.known_runners: Dict[str, dict] = {}  # Track previously known runners
        
    def add_known_runner(self, runner_id: str, url: str):
        """Add a runner to the known runners list"""
        self.known_runners[runner_id] = {
            "url": url,
            "last_seen": datetime.now().isoformat(),
            "ping_attempts": 0
        }
        
    async def ping_known_runners(self, runner_manager: RunnerManager) -> int:
        """Ping all known runners to re-register"""
        if not self.known_runners:
            logger.info("No known runners to ping")
            return 0
            
        successful_pings = 0
        
        for runner_id, runner_info in list(self.known_runners.items()):
            try:
                await self._ping_runner(runner_id, runner_info["url"])
                successful_pings += 1
                logger.info(f"Successfully pinged runner {runner_id}")
            except Exception as e:
                logger.warning(f"Failed to ping runner {runner_id}: {e}")
                runner_info["ping_attempts"] += 1
                
                # Remove runner from known list after too many failed pings
                if runner_info["ping_attempts"] > 5:
                    logger.info(f"Removing runner {runner_id} from known runners after {runner_info['ping_attempts']} failed pings")
                    self.known_runners.pop(runner_id, None)
                    
        return successful_pings
        
    async def _ping_runner(self, runner_id: str, runner_url: str):
        """Send a ping to a specific runner"""
        try:
            timeout = aiohttp.ClientTimeout(total=10)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(
                    f"{runner_url}/api/ping",
                    json={"action": "re_register", "distributor_url": os.getenv("DISTRIBUTOR_URL", "http://distributor:8080")},
                    timeout=5
                ) as response:
                    if response.status == 200:
                        logger.debug(f"Ping successful for runner {runner_id}")
                    else:
                        raise Exception(f"Ping failed with status {response.status}")
        except Exception as e:
            logger.warning(f"Ping failed for runner {runner_id} at {runner_url}: {e}")
            raise

