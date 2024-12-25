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
import time

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
    _browser = None
    _playwright = None
    _lock = asyncio.Lock()
    _context_pool = []
    _max_contexts = 3  # Maximum number of concurrent contexts
    _last_cleanup = time.time()
    _cleanup_interval = 3600  # Cleanup every hour
    _context_max_age = 1800   # Max context age in seconds (30 minutes)
    _browser_max_age = 7200   # Max browser age in seconds (2 hours)
    _browser_created_at = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @staticmethod
    def _get_stealth_args():
        """Get browser arguments for stealth mode"""
        return [
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-infobars',
            '--window-position=0,0',
            '--ignore-certifcate-errors',
            '--ignore-certifcate-errors-spki-list',
            '--disable-plugins-discovery',
            '--disable-blink-features=AutomationControlled',
            '--disable-web-security',
        ]
    
    @staticmethod
    def _get_normal_args():
        """Get browser arguments for normal mode"""
        return [
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-dev-shm-usage',
            '--disable-gpu',
        ]
    
    async def _periodic_cleanup(self):
        """Perform periodic cleanup of old contexts and browser"""
        current_time = time.time()
        
        # Only run cleanup if enough time has passed
        if current_time - self._last_cleanup < self._cleanup_interval:
            return

        try:
            # Remove old contexts
            old_contexts = [
                ctx for ctx in self._context_pool 
                if current_time - ctx['created_at'] > self._context_max_age
            ]
            
            for ctx in old_contexts:
                try:
                    await ctx['context'].close()
                    self._context_pool.remove(ctx)
                except Exception as e:
                    logger.error(f"Error closing old context: {str(e)}")

            # Restart browser if it's too old
            if (self._browser_created_at and 
                current_time - self._browser_created_at > self._browser_max_age):
                logger.info("Performing periodic browser restart")
                await self.cleanup()
                await self._create_browser()

            self._last_cleanup = current_time
            
        except Exception as e:
            logger.error(f"Error during periodic cleanup: {str(e)}")

    async def _create_browser(self, stealth: bool = False):
        """Create a new browser instance"""
        if not self._playwright:
            self._playwright = await async_playwright().start()
        
        args = self._get_stealth_args() if stealth else self._get_normal_args()
        
        self._browser = await self._playwright.chromium.launch(
            headless=True,
            args=args
        )
        
        self._browser_created_at = time.time()  # Track browser creation time
        logger.info(f"Created new browser instance (stealth: {stealth})")
        return self._browser
    
    async def _setup_stealth_context(self, context):
        """Apply additional stealth measures to context"""
        for page in context.pages:
            await page.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5]
                });
                window.chrome = {
                    runtime: {}
                };
            """)
    
    async def _get_context_from_pool(self, stealth: bool, proxy: Optional[Tuple[str, str, str, str]] = None):
        """Get an existing context from pool or create new one"""
        try:
            # Remove closed contexts from pool
            self._context_pool = [ctx for ctx in self._context_pool if not ctx['context'].is_closed()]
            
            # Try to find matching context in pool
            for ctx_data in self._context_pool:
                if ctx_data['stealth'] == stealth and ctx_data['proxy'] == proxy:
                    return ctx_data['context']
            
            # Create new context if pool isn't full
            if len(self._context_pool) < self._max_contexts:
                context_options = {
                    'viewport': {'width': 1920, 'height': 1080},
                    'user_agent': random.choice(USER_AGENTS),
                    'locale': 'en-US',
                    'timezone_id': 'America/New_York',
                    'bypass_csp': True,
                }
                
                if proxy and len(proxy) >= 2:
                    context_options['proxy'] = {
                        'server': f'http://{proxy[0]}:{proxy[1]}',
                        **({"username": proxy[2], "password": proxy[3]} if len(proxy) == 4 else {})
                    }
                
                context = await self._browser.new_context(**context_options)
                
                if stealth:
                    await self._setup_stealth_context(context)
                
                self._context_pool.append({
                    'context': context,
                    'stealth': stealth,
                    'proxy': proxy,
                    'created_at': time.time()
                })
                
                return context
            
            # If pool is full, reuse oldest context
            oldest_ctx = min(self._context_pool, key=lambda x: x['created_at'])
            await oldest_ctx['context'].close()
            self._context_pool.remove(oldest_ctx)
            return await self._get_context_from_pool(stealth, proxy)
        except Exception as e:
            logger.error(f"Error in context pool management: {str(e)}")
            # Clear the problematic contexts and try again
            self._context_pool = []
            return await self._create_new_context(stealth, proxy)

    async def get_page(self, stealth: bool = False, proxy: Optional[Tuple[str, str, str, str]] = None):
        """Get a configured page for scraping"""
        async with self._lock:
            try:
                # Run periodic cleanup
                await self._periodic_cleanup()
                
                if not self._browser or not self._browser.is_connected():
                    await self._create_browser(stealth)
                
                context = await self._get_context_from_pool(stealth, proxy)
                page = await context.new_page()
                
                if stealth:
                    await page.route("**/*", lambda route: route.continue_())
                
                return page, context
                
            except Exception as e:
                logger.error(f"Error getting page: {str(e)}")
                await self.cleanup()
                raise
    
    async def cleanup(self):
        """Cleanup resources"""
        try:
            if self._browser:
                await self._browser.close()
                self._browser = None
            if self._playwright:
                await self._playwright.stop()
                self._playwright = None
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")
            self._browser = None
            self._playwright = None

    async def shutdown(self):
        """Graceful shutdown method"""
        logger.info("Initiating graceful shutdown of PlaywrightManager")
        try:
            # Close all contexts
            for ctx in self._context_pool:
                try:
                    await ctx['context'].close()
                except Exception as e:
                    logger.error(f"Error closing context during shutdown: {str(e)}")
            
            self._context_pool = []
            await self.cleanup()
            
        except Exception as e:
            logger.error(f"Error during shutdown: {str(e)}")

    async def health_check(self) -> bool:
        """Check if the browser instance is healthy"""
        try:
            if not self._browser or not self._browser.is_connected():
                return False
                
            # Check if we can create a new page
            context = await self._get_context_from_pool(stealth=False)
            page = await context.new_page()
            await page.close()
            
            return True
            
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            return False

# Initialize the singleton
playwright_manager = PlaywrightManager()

async def scrape_with_playwright(url: str, proxy: Optional[Tuple[str, str, str, str]] = None, stealth: bool = False) -> str:
    """Scrape with Playwright using persistent browser instance"""
    page = None
    context = None
    
    try:
        # Get configured page
        page, context = await playwright_manager.get_page(stealth=stealth, proxy=proxy)
        
        # Configure timeout and navigation
        page.set_default_timeout(30000)
        
        # Navigate with retry logic
        for attempt in range(2):
            try:
                response = await page.goto(
                    url,
                    wait_until='networkidle',
                    timeout=30000
                )
                
                if not response or not response.ok:
                    raise Exception(f"Navigation failed with status {response.status if response else 'no response'}")
                
                # Wait for any dynamic content
                await asyncio.sleep(1)
                
                # Get content
                content = await page.content()
                if not content:
                    raise Exception("Failed to get page content")
                
                return content
                
            except Exception as e:
                if attempt == 1:  # Last attempt
                    raise
                logger.warning(f"Navigation attempt {attempt + 1} failed: {str(e)}")
                await asyncio.sleep(1)
        
    except Exception as e:
        logger.error(f"Playwright scraping error for {url}: {str(e)}")
        raise
        
    finally:
        # Cleanup resources
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
                    content = await scrape_with_playwright(url, proxy, stealth=stealth)
                    method_used = 'playwright'
                except Exception as e:
                    logger.error(f"Playwright scraping failed (attempt {attempt + 1}/{retries + 1}): {str(e)}")
                    last_error = e
                    if attempt < retries:
                        await asyncio.sleep(random.uniform(1, 3))  # Random backoff
                        continue
                    raise
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
