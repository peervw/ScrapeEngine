from typing import List, Tuple, Dict, Optional
import aiohttp
import logging
from datetime import datetime
import asyncio
from fastapi import HTTPException
import random
from ..db.crud.events import store_event

logger = logging.getLogger(__name__)

class ProxyManager:
    def __init__(self):
        self.webshare_token = None
        self.proxies: Dict[str, dict] = {}  # host -> proxy_data
        self.available_proxies: List[str] = []  # list of hosts
        self.performance_window = 50  # Number of requests to calculate average response time
        
    async def initialize(self, db_connection):
        """Initialize proxy manager with settings from database"""
        try:
            cursor = db_connection.cursor()
            cursor.execute('SELECT value FROM settings WHERE key = %s', ('webshare_token',))
            result = cursor.fetchone()
            if result and result[0]:
                await self.set_webshare_token(result[0])
            cursor.close()
        except Exception as e:
            logger.error(f"Error initializing proxy manager: {e}")
            raise
        
    async def add_proxy(self, proxy: Tuple[str, str, str, str]):
        """Add a proxy to memory with metadata"""
        host = proxy[0]
        self.proxies[host] = {
            "host": proxy[0],
            "port": proxy[1],
            "username": proxy[2],
            "password": proxy[3],
            "last_used": None,
            "failures": 0,
            "success_rate": 1.0,
            "response_times": [],  # Track last N response times
            "avg_response_time": None
        }
        self.available_proxies.append(host)
        logger.debug(f"Added proxy {host}")
        
    async def get_next_proxy(self) -> Optional[Tuple[str, str, str, str]]:
        """Get next available proxy using performance-based selection, returns None if no proxies available"""
        if not self.available_proxies:
            logger.info("No proxies available, proceeding without proxy")
            return None
        
        # Sort proxies by performance score (combination of success rate and speed)
        sorted_proxies = sorted(
            self.available_proxies,
            key=lambda x: (
                self.proxies[x]["success_rate"],
                -1 * (self.proxies[x]["avg_response_time"] or float("inf"))
            ),
            reverse=True
        )
        
        # Select from top 20% of proxies randomly to prevent overuse
        selection_pool = sorted_proxies[:max(1, len(sorted_proxies) // 5)]
        host = random.choice(selection_pool)
        
        proxy_data = self.proxies[host]
        proxy_data["last_used"] = datetime.now().isoformat()
        
        return (
            proxy_data["host"],
            proxy_data["port"],
            proxy_data["username"],
            proxy_data["password"]
        )

    async def refresh_proxies(self):
        """Refresh proxy list from Webshare"""
        if not self.webshare_token:
            logger.info("No Webshare token configured, skipping proxy refresh")
            return

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    'https://proxy.webshare.io/api/v2/proxy/list/?mode=direct&page=1&page_size=1000',
                    headers={'Authorization': f'Token {self.webshare_token}'}
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"Failed to fetch proxies: Status {response.status}, Response: {error_text}")
                        raise Exception(f"Failed to fetch proxies: {response.status}, {error_text}")
                    
                    data = await response.json()
                    proxies = data.get('results', [])
                    logger.info(f"Fetched {len(proxies)} proxies")
                    
                    # Clear existing proxies
                    self.proxies.clear()
                    self.available_proxies.clear()
                    
                    # Process each proxy
                    for proxy in proxies:
                        try:
                            proxy_data = (
                                proxy['proxy_address'],
                                str(proxy['port']),  # Convert port to string
                                proxy['username'],
                                proxy['password']
                            )
                            await self.add_proxy(proxy_data)
                            logger.debug(f"Added proxy: {proxy['proxy_address']}:{proxy['port']}")
                        except Exception as e:
                            logger.error(f"Error processing proxy: {e}, Data: {proxy}")
                            continue
                    
                    logger.info(f"Successfully refreshed {len(proxies)} proxies")
                    
        except Exception as e:
            logger.error(f"Error refreshing proxies: {e}")
            raise

    async def start_proxy_maintenance(self):
        while True:
            try:
                if self.webshare_token:
                    await self.refresh_proxies()
                await asyncio.sleep(3600)  # 1 hour
            except Exception as e:
                logger.error(f"Error in proxy maintenance: {e}")
                await asyncio.sleep(60)

    async def update_proxy_metrics(self, host: str, response_time: float, success: bool):
        """Update proxy performance metrics"""
        if not host or host not in self.proxies:
            return
            
        proxy = self.proxies[host]
        
        # Update response times
        proxy["response_times"].append(response_time)
        if len(proxy["response_times"]) > self.performance_window:
            proxy["response_times"].pop(0)
        
        # Update average response time
        proxy["avg_response_time"] = sum(proxy["response_times"]) / len(proxy["response_times"])
        
        # Update success metrics
        if success:
            proxy["success_rate"] = min(1.0, proxy["success_rate"] + 0.1)
            proxy["failures"] = max(0, proxy["failures"] - 1)
        else:
            proxy["success_rate"] = max(0.0, proxy["success_rate"] - 0.2)
            proxy["failures"] += 1
            
        # Remove proxy if too many failures or low success rate
        if proxy["failures"] > 5 or proxy["success_rate"] < 0.3:
            self.proxies.pop(host, None)
            if host in self.available_proxies:
                self.available_proxies.remove(host)
            logger.warning(f"Removed failing proxy {host}")

    def get_proxy_stats(self) -> List[dict]:
        """Get statistics for all proxies"""
        return [
            {
                "host": proxy_data["host"],
                "port": proxy_data["port"],
                "last_used": proxy_data["last_used"],
                "success_rate": proxy_data["success_rate"],
                "avg_response_time": proxy_data["avg_response_time"],
                "failures": proxy_data["failures"]
            }
            for proxy_data in self.proxies.values()
        ]

    async def set_webshare_token(self, token: str):
        """Set the Webshare API token and refresh proxies"""
        self.webshare_token = token
        if token:
            await self.refresh_proxies()
        else:
            self.proxies.clear()
            self.available_proxies.clear()

    async def add_manual_proxy(self, host: str, port: str, username: Optional[str] = None, password: Optional[str] = None):
        """Add a proxy manually"""
        proxy_str = f"{host}:{port}"
        if proxy_str in self.proxies:
            logger.warning(f"Proxy {proxy_str} already exists")
            return

        self.proxies[host] = {
            "port": port,
            "username": username,
            "password": password,
            "last_used": None,
            "success_rate": 0.0,
            "total_requests": 0,
            "successful_requests": 0,
            "failures": 0,
            "avg_response_time": None,
            "total_response_time": 0.0
        }
        self.available_proxies.append((host, port))
        logger.info(f"Added proxy {proxy_str}")

        # Log event
        store_event({
            "title": "New proxy added",
            "description": f"Manual proxy added: {host}:{port}",
            "event_type": "proxy",
            "severity": "info",
            "details": {
                "host": host,
                "port": port,
                "has_auth": bool(username and password)
            }
        })

    async def delete_proxy(self, host: str):
        """Delete a proxy by host"""
        if host in self.proxies:
            self.proxies.pop(host)
            if host in self.available_proxies:
                self.available_proxies.remove(host)
            logger.info(f"Deleted proxy {host}")

    def get_webshare_token(self) -> Optional[str]:
        """Get the current Webshare API token"""
        return self.webshare_token