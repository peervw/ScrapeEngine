from typing import Dict, Any, Optional, Tuple
import aiohttp
import logging
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from aiohttp import ClientError, ClientTimeout
import asyncio
import random
import json
from datetime import datetime
import ssl

logger = logging.getLogger(__name__)

# Common headers to rotate
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
]

MINIMAL_DELAY = 0.1

async def get_enhanced_stealth_headers() -> Dict[str, str]:
    """Optimized stealth headers - only essential ones"""
    headers = {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": f"{random.choice(['en-US', 'en-GB', 'en-CA'])},en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": random.choice(['none', 'same-origin']),
        "Sec-CH-UA-Platform": f'"{random.choice(["Windows", "macOS", "Linux"])}"',
    }
    
    if random.random() > 0.5:
        headers["DNT"] = "1"
    
    return headers

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    retry=(
        retry_if_exception_type(ClientError) |
        retry_if_exception_type(asyncio.TimeoutError) |
        retry_if_exception_type(Exception)
    ),
    before_sleep=lambda retry_state: logger.warning(
        f"Retry attempt {retry_state.attempt_number} for URL after error: {retry_state.outcome.exception()}"
    )
)
async def scrape_with_aiohttp(url: str, proxy: Optional[Tuple[str, str, str, str]] = None, stealth: bool = True) -> str:
    """Performance-optimized aiohttp scraping with focus on stealth and proxy rotation"""
    try:
        headers = await get_enhanced_stealth_headers() if stealth else {
            "User-Agent": USER_AGENTS[0],
            "Accept": "*/*"
        }
        
        # Reduced timeout values
        timeout = ClientTimeout(
            total=15,
            connect=5,
            sock_read=10
        )
        
        # Connector settings optimized for proxy rotation and stealth
        connector = aiohttp.TCPConnector(
            force_close=True,
            enable_cleanup_closed=True,
            ssl=False,
            limit_per_host=5,
            use_dns_cache=True,
            ttl_dns_cache=300,
            resolver=aiohttp.AsyncResolver()
        )
        
        # Minimal delay only if stealth is enabled
        if stealth:
            await asyncio.sleep(MINIMAL_DELAY)
        
        async with aiohttp.ClientSession(
            headers=headers,
            connector=connector,
            timeout=timeout,
            trust_env=True
        ) as session:
            # Try without proxy first if proxy is failing
            if proxy:
                try:
                    async with session.get(
                        url,
                        proxy=f"http://{proxy[0]}:{proxy[1]}",
                        proxy_auth=aiohttp.BasicAuth(proxy[2], proxy[3]) if len(proxy) == 4 else None,
                        allow_redirects=True,
                        max_redirects=2,
                        timeout=timeout,
                        verify_ssl=False
                    ) as response:
                        if response.status != 200:
                            raise ClientError(f"HTTP {response.status}")
                        
                        return await response.text()
                except Exception as e:
                    logger.error(f"Proxy scraping failed, trying without proxy: {str(e)}")
            
            # Try without proxy as fallback
            async with session.get(
                url,
                allow_redirects=True,
                max_redirects=2,
                timeout=timeout,
                verify_ssl=False
            ) as response:
                if response.status != 200:
                    raise ClientError(f"HTTP {response.status}")
                
                return await response.text()
                    
    except Exception as e:
        logger.error(f"Scraping error for {url}: {str(e)}")
        raise

class PlaywrightManager:
    """Singleton class to manage Playwright browser instances"""
    _instance = None
    _initialized = False
    _lock = asyncio.Lock()
    _browser = None
    _playwright = None
    _context_lock = asyncio.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    async def initialize(self):
        """Initialize Playwright if not already initialized"""
        if not self._initialized:
            async with self._lock:
                if not self._initialized:  # Double check pattern
                    try:
                        self._playwright = await async_playwright().start()
                        if not self._playwright:
                            raise Exception("Failed to initialize Playwright")
                            
                        # Launch persistent browser with minimal args
                        self._browser = await self._playwright.chromium.launch(
                            headless=True,
                            args=[
                                '--no-sandbox',
                                '--disable-setuid-sandbox',
                                '--disable-dev-shm-usage',
                                '--disable-gpu',
                                '--single-process',
                                '--disable-web-security',
                                '--disable-features=site-per-process',
                                '--no-zygote'
                            ]
                        )
                        if not self._browser:
                            raise Exception("Failed to launch browser")
                            
                        # Create a test context and page to verify everything works
                        try:
                            async with self._context_lock:
                                test_context = await self._browser.new_context(
                                    viewport={'width': 1920, 'height': 1080},
                                    user_agent=USER_AGENTS[0]
                                )
                                test_page = await test_context.new_page()
                                await test_page.goto('about:blank', wait_until='domcontentloaded')
                                await test_page.close()
                                await test_context.close()
                        except Exception as e:
                            logger.error(f"Browser verification failed: {str(e)}")
                            await self.cleanup()
                            raise
                            
                        self._initialized = True
                        logger.info("Playwright manager initialized successfully")
                    except Exception as e:
                        logger.error(f"Failed to initialize Playwright manager: {str(e)}")
                        await self.cleanup()  # Clean up any partially initialized resources
                        raise
    
    async def get_context(self, proxy: Optional[Tuple[str, str, str, str]] = None):
        """Get a new browser context with optional proxy"""
        await self.initialize()  # Ensure initialization
        
        if not self._browser:
            raise Exception("Browser not initialized")
        
        async with self._context_lock:
            context_options = {
                'viewport': {'width': 1920, 'height': 1080},
                'user_agent': random.choice(USER_AGENTS),
                'locale': 'en-US',
                'timezone_id': 'America/New_York',
                'bypass_csp': True
            }
            
            if proxy and len(proxy) >= 2:
                proxy_config = {
                    "server": f"http://{proxy[0]}:{proxy[1]}"
                }
                if len(proxy) == 4:
                    proxy_config.update({
                        "username": proxy[2],
                        "password": proxy[3]
                    })
                context_options["proxy"] = proxy_config
                
            try:
                context = await self._browser.new_context(**context_options)
                if not context:
                    raise Exception("Failed to create browser context")
                return context
            except Exception as e:
                logger.error(f"Failed to create context: {str(e)}")
                # Try to reinitialize if context creation fails
                await self.cleanup()
                await self.initialize()
                context = await self._browser.new_context(**context_options)
                if not context:
                    raise Exception("Failed to create browser context after reinitialization")
                return context
    
    async def cleanup(self):
        """Cleanup Playwright resources"""
        async with self._lock:
            try:
                if self._browser:
                    await self._browser.close()
                    self._browser = None
                if self._playwright:
                    await self._playwright.stop()
                    self._playwright = None
                self._initialized = False
            except Exception as e:
                logger.error(f"Error during Playwright cleanup: {str(e)}")
                # Reset state even if cleanup fails
                self._browser = None
                self._playwright = None
                self._initialized = False

# Initialize the singleton
playwright_manager = PlaywrightManager()

async def scrape_with_playwright(url: str, proxy: Optional[Tuple[str, str, str, str]] = None) -> str:
    """Performance-optimized Playwright scraping"""
    context = None
    page = None
    
    try:
        # Get browser context
        context = await playwright_manager.get_context(proxy)
        if not context:
            raise Exception("Failed to create browser context")
        
        # Create page
        page = await context.new_page()
        if not page:
            raise Exception("Failed to create new page")
        
        # Configure page settings
        await page.set_default_navigation_timeout(30000)  # Increased timeout
        await asyncio.sleep(MINIMAL_DELAY)
        
        # Navigate and get content
        try:
            response = await page.goto(url, wait_until='networkidle', timeout=30000)
            if not response:
                raise Exception("Navigation failed with no response")
            if not response.ok:
                raise Exception(f"Navigation failed with status {response.status}")
            
            # Wait for any dynamic content
            await asyncio.sleep(1)
            
            content = await page.content()
            if not content:
                raise Exception("Failed to get page content")
            
            return content
        except Exception as e:
            logger.error(f"Navigation error for {url}: {str(e)}")
            raise
            
    except Exception as e:
        logger.error(f"Playwright scraping error for {url}: {str(e)}")
        raise
        
    finally:
        # Cleanup resources in reverse order
        if page:
            try:
                await page.close()
            except Exception as e:
                logger.error(f"Error closing page: {str(e)}")
        
        if context:
            try:
                await context.close()
            except Exception as e:
                logger.error(f"Error closing context: {str(e)}")

async def scrape(task_data: Dict[str, Any]) -> Dict[str, Any]:
    """Optimized main scrape function with optional parsing"""
    url = str(task_data['url'])
    proxy = task_data.get('proxy')
    stealth = task_data.get('stealth', False)
    render = task_data.get('render', False)
    should_parse = task_data.get('parse', True)
    
    start_time = datetime.now()
    retries = 2
    last_error = None
    
    for attempt in range(retries + 1):
        try:
            # Only use playwright if render is true
            if render:
                try:
                    # Initialize Playwright manager first
                    await playwright_manager.initialize()
                    content = await scrape_with_playwright(url, proxy)
                    method_used = 'playwright'
                except Exception as e:
                    logger.error(f"Playwright scraping failed (attempt {attempt + 1}/{retries + 1}): {str(e)}")
                    raise  # Always raise for Playwright as it's required for rendering
            else:
                try:
                    # Use aiohttp with stealth mode only when stealth is True
                    content = await scrape_with_aiohttp(url, proxy, stealth=stealth)
                    method_used = 'aiohttp'
                except Exception as e:
                    logger.error(f"Aiohttp scraping failed (attempt {attempt + 1}/{retries + 1}): {str(e)}")
                    last_error = e
                    if attempt < retries:
                        await asyncio.sleep(random.uniform(1, 3))  # Random backoff
                        continue
                    raise

            result = {
                'status': 'success',
                'scrape_time': (datetime.now() - start_time).total_seconds(),
                'method_used': method_used,
            }
                
            # Always include raw content
            result['raw_content'] = content
                
            if should_parse:
                try:
                    # Only parse if explicitly requested
                    soup = BeautifulSoup(content, 'html.parser')
                    result.update({
                        'title': soup.title.string if soup.title else None,
                        'text_content': ' '.join(soup.stripped_strings),
                        'links': [{'href': a.get('href'), 'text': a.text} 
                                 for a in soup.find_all('a', href=True)]
                    })
                except Exception as e:
                    logger.error(f"Parsing failed: {str(e)}")
                    result['parse_error'] = str(e)
                
            return result
                
        except Exception as e:
            last_error = e
            if attempt < retries:
                logger.warning(f"Scraping attempt {attempt + 1}/{retries + 1} failed, retrying...")
                await asyncio.sleep(random.uniform(1, 3))  # Random backoff
                continue
            
    logger.error(f"All scraping attempts failed for {url}: {str(last_error)}")
    raise last_error
