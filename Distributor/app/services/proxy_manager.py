from typing import List, Tuple, Dict
import aiohttp
import logging
import os
from datetime import datetime
import asyncio
from fastapi import HTTPException

logger = logging.getLogger(__name__)

class ProxyManager:
    def __init__(self):
        self.webshare_token = os.getenv('WEBSHARE_TOKEN')
        self.proxies: Dict[str, dict] = {}  # host -> proxy_data
        self.available_proxies: List[str] = []  # list of hosts
        
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
            "success_rate": 1.0
        }
        self.available_proxies.append(host)
        logger.debug(f"Added proxy {host}")
        
    async def get_next_proxy(self) -> Tuple[str, str, str, str]:
        """Get next available proxy using round-robin"""
        if not self.available_proxies:
            await self.refresh_proxies()
            if not self.available_proxies:
                raise HTTPException(status_code=503, detail="No proxies available")
        
        # Round-robin selection
        host = self.available_proxies.pop(0)
        self.available_proxies.append(host)  # Add back to end
        
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
                await self.refresh_proxies()
                await asyncio.sleep(3600)  # 1 hour
            except Exception as e:
                logger.error(f"Error in proxy maintenance: {e}")
                await asyncio.sleep(60)

    async def mark_proxy_result(self, host: str, success: bool):
        """Mark proxy success/failure for tracking"""
        if host in self.proxies:
            proxy = self.proxies[host]
            if success:
                # Successful request - improve success rate
                proxy["success_rate"] = min(1.0, proxy["success_rate"] + 0.1)
                proxy["failures"] = max(0, proxy["failures"] - 1)
            else:
                # Failed request - decrease success rate and increment failures
                proxy["success_rate"] = max(0.0, proxy["success_rate"] - 0.2)
                proxy["failures"] += 1
                
                # Remove proxy if too many failures or low success rate
                if proxy["failures"] > 5 or proxy["success_rate"] < 0.3:
                    self.proxies.pop(host, None)
                    if host in self.available_proxies:
                        self.available_proxies.remove(host)
                    logger.warning(f"Removed failing proxy {host}")