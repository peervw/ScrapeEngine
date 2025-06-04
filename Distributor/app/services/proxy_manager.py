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
        self.available_proxies.append(host)
        
        proxy_data = self.proxies[host]
        proxy_data["last_used"] = datetime.now().isoformat()
        
        return (
            proxy_data["host"],
            proxy_data["port"],
            proxy_data["username"],
            proxy_data["password"]
        )

    async def refresh_proxies(self):
        """Refresh proxy list from Webshare - fetch all pages"""
        try:
            # Clear existing proxies
            self.proxies.clear()
            self.available_proxies.clear()
            
            page = 1
            page_size = 250  # Maximum page size
            total_proxies = 0
            
            async with aiohttp.ClientSession() as session:
                while True:
                    logger.info(f"Fetching proxy page {page}")
                    
                    async with session.get(
                        f'https://proxy.webshare.io/api/v2/proxy/list/?mode=direct&page={page}&page_size={page_size}',
                        headers={'Authorization': f'Token {self.webshare_token}'}
                    ) as response:
                        if response.status != 200:
                            error_text = await response.text()
                            logger.error(f"Failed to fetch proxies page {page}: Status {response.status}, Response: {error_text}")
                            raise Exception(f"Failed to fetch proxies: {response.status}, {error_text}")
                        
                        data = await response.json()
                        proxies = data.get('results', [])
                        count = data.get('count', 0)
                        next_page = data.get('next')
                        
                        logger.info(f"Page {page}: Fetched {len(proxies)} proxies out of {count} total")
                        
                        # Process each proxy on this page
                        for proxy in proxies:
                            try:
                                proxy_data = (
                                    proxy['proxy_address'],
                                    str(proxy['port']),  # Convert port to string
                                    proxy['username'],
                                    proxy['password']
                                )
                                await self.add_proxy(proxy_data)
                                total_proxies += 1
                                logger.debug(f"Added proxy: {proxy['proxy_address']}:{proxy['port']}")
                            except Exception as e:
                                logger.error(f"Error processing proxy: {e}, Data: {proxy}")
                                continue
                        
                        # Check if there are more pages
                        if not next_page or len(proxies) == 0:
                            logger.info(f"No more pages. Finished fetching all proxies.")
                            break
                        
                        page += 1
                        
                        # Add small delay between requests to be respectful
                        await asyncio.sleep(0.1)
                    
            logger.info(f"Successfully refreshed {total_proxies} proxies from {page} pages")
                    
        except Exception as e:
            logger.error(f"Error refreshing proxies: {e}")
            raise

    async def start_proxy_maintenance(self):
        """Background task to refresh proxies periodically"""
        while True:
            try:
                logger.info("Starting proxy maintenance cycle")
                await self.refresh_proxies()
                logger.info(f"Proxy maintenance completed. Next refresh in 1 hour. Current proxy count: {len(self.available_proxies)}")
                await asyncio.sleep(3600)  # 1 hour
            except Exception as e:
                logger.error(f"Error in proxy maintenance: {e}")
                logger.info("Retrying proxy maintenance in 5 minutes")
                await asyncio.sleep(300)  # 5 minutes on error

    async def mark_proxy_result(self, host: str, success: bool):
        """Mark proxy success/failure for tracking"""
        if host in self.proxies:
            proxy = self.proxies[host]
            if success:
                # Successful request - improve success rate
                proxy["success_rate"] = min(1.0, proxy["success_rate"] + 0.1)
                proxy["failures"] = max(0, proxy["failures"] - 1)
                logger.debug(f"Proxy {host} success - success_rate: {proxy['success_rate']:.2f}")
            else:
                # Failed request - decrease success rate and increment failures
                proxy["success_rate"] = max(0.0, proxy["success_rate"] - 0.2)
                proxy["failures"] += 1
                logger.warning(f"Proxy {host} failed - failures: {proxy['failures']}, success_rate: {proxy['success_rate']:.2f}")
                
                # Remove proxy if too many failures or low success rate
                if proxy["failures"] > 5 or proxy["success_rate"] < 0.3:
                    self.proxies.pop(host, None)
                    if host in self.available_proxies:
                        self.available_proxies.remove(host)
                    logger.warning(f"Removed failing proxy {host} (failures: {proxy['failures']}, success_rate: {proxy['success_rate']:.2f})")

    def get_proxy_stats(self) -> dict:
        """Get proxy statistics"""
        total_proxies = len(self.proxies)
        available_proxies = len(self.available_proxies)
        
        if total_proxies == 0:
            return {
                "total_proxies": 0,
                "available_proxies": 0,
                "average_success_rate": 0.0,
                "failed_proxies": 0
            }
        
        avg_success_rate = sum(p["success_rate"] for p in self.proxies.values()) / total_proxies
        failed_proxies = sum(1 for p in self.proxies.values() if p["failures"] > 0)
        
        return {
            "total_proxies": total_proxies,
            "available_proxies": available_proxies,
            "average_success_rate": round(avg_success_rate, 3),
            "failed_proxies": failed_proxies
        }