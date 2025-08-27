from typing import Dict, Any, Optional, Tuple, Union, List
import aiohttp
import logging
from bs4 import BeautifulSoup, Tag
from playwright.async_api import async_playwright
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from aiohttp import ClientError, ClientTimeout
import asyncio
import random
import json
from datetime import datetime
import ssl
import os
import base64

# Initialize uvloop for better performance on macOS/Linux
try:
    import uvloop
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
except ImportError:
    pass  # Fall back to default event loop

logger = logging.getLogger(__name__)

# Common headers to rotate
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
]

# Performance constants
MAX_CONCURRENT = 50
MINIMAL_DELAY = 0.05  # Reduced delay

# Global session cache for connection reuse
_session_cache = {}

async def cleanup_sessions():
    """Clean up all cached sessions"""
    global _session_cache
    for session in _session_cache.values():
        if not session.closed:
            await session.close()
    _session_cache.clear()

async def get_cached_session(proxy: Optional[Tuple[str, str, str, str]] = None, stealth: bool = True) -> aiohttp.ClientSession:
    """Reuse sessions for better performance"""
    proxy_key = f"{proxy[0]}:{proxy[1]}" if proxy else "no_proxy"
    
    if proxy_key not in _session_cache or _session_cache[proxy_key].closed:
        headers = await get_enhanced_stealth_headers() if stealth else {
            "User-Agent": USER_AGENTS[0],
            "Accept": "*/*"
        }
        
        connector = aiohttp.TCPConnector(
            limit=200,  # Increased connection pool
            limit_per_host=20,  # More connections per host
            ttl_dns_cache=600,  # Longer DNS cache
            use_dns_cache=True,
            keepalive_timeout=45,  # Keep connections alive
            enable_cleanup_closed=True,  # Enable cleanup
            ssl=False
        )
        
        timeout = ClientTimeout(
            total=45,  # Increased timeout for testing
            connect=15,  # Increased connect timeout
            sock_read=35  # Increased read timeout
        )
        
        _session_cache[proxy_key] = aiohttp.ClientSession(
            headers=headers,
            connector=connector,
            timeout=timeout,
            trust_env=True
        )
    
    return _session_cache[proxy_key]

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

async def parse_html_fast(content: str) -> Dict[str, Any]:
    """Optimized HTML parsing"""
    # Use lxml parser (faster than html.parser)
    try:
        soup = BeautifulSoup(content, 'lxml')
    except:
        # Fallback to html.parser if lxml not available
        soup = BeautifulSoup(content, 'html.parser')
    
    # Parse in parallel using asyncio
    async def get_title():
        return soup.title.string if soup.title else None
    
    async def get_text():
        return ' '.join(soup.stripped_strings)
    
    async def get_links():
        links = []
        try:
            link_elements = soup.find_all('a', href=True, limit=100)
            for a in link_elements:
                if isinstance(a, Tag):
                    href = str(a.get('href', '')) if a.get('href') else None
                    text = str(a.get_text(strip=True))[:100] if a else ''
                    if href and href.strip():
                        links.append({'href': href, 'text': text})
        except Exception:
            pass  # Skip link parsing if it fails
        return links
    
    # Run parsing tasks concurrently
    title, text_content, links = await asyncio.gather(
        get_title(),
        get_text(),
        get_links(),
        return_exceptions=False
    )
    
    return {
        'title': title,
        'text_content': text_content,
        'links': links
    }

async def get_proxy_from_distributor() -> Optional[Tuple[str, str, str, str]]:
    """Get a proxy from the distributor service - works with or without authentication"""
    distributor_url = os.getenv('DISTRIBUTOR_URL', 'http://distributor:8080')
    auth_token = os.getenv('AUTH_TOKEN')
    
    try:
        # Prepare headers - only include auth if token is available
        headers = {}
        if auth_token:
            headers["Authorization"] = f"Bearer {auth_token}"
            logger.debug("Using authentication for proxy request")
        else:
            logger.debug("No AUTH_TOKEN set, requesting proxy without authentication")
        
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{distributor_url}/proxy/next",
                headers=headers,
                timeout=5
            ) as response:
                if response.status == 200:
                    proxy_data = await response.json()
                    # Assuming the response is a tuple/list [host, port, username, password]
                    logger.debug(f"Received proxy from distributor: {proxy_data[0]}:{proxy_data[1]}")
                    return tuple(proxy_data)
                else:
                    logger.warning(f"Failed to get proxy from distributor: {response.status}")
                    return None
    except Exception as e:
        logger.warning(f"Error getting proxy from distributor: {e}")
        return None

async def scrape_with_aiohttp(url: str, stealth: bool = True, max_attempts: int = 3) -> Tuple[str, Optional[str]]:
    """Scrape with automatic proxy rotation on failure"""
    last_exception = None
    used_proxy = None
    
    for attempt in range(max_attempts):
        try:
            # Get a new proxy for each attempt
            proxy = await get_proxy_from_distributor()
            proxy_info = f"{proxy[0]}:{proxy[1]}" if proxy else "No proxy"
            logger.info(f"Attempt {attempt + 1}/{max_attempts} for {url} using proxy: {proxy_info}")
            
            session = await get_cached_session(proxy, stealth)
            
            async with session.get(
                url,
                proxy=f"http://{proxy[0]}:{proxy[1]}" if proxy else None,
                proxy_auth=aiohttp.BasicAuth(proxy[2], proxy[3]) if proxy and len(proxy) == 4 else None,
                allow_redirects=True,
                max_redirects=2,
                ssl=False,
                compress=True
            ) as response:
                if response.status != 200:
                    raise ClientError(f"HTTP {response.status}")
                
                content = await response.text(encoding='utf-8', errors='ignore')
                used_proxy = proxy_info  # Store successful proxy
                logger.info(f"Successfully scraped {url} on attempt {attempt + 1} with proxy: {proxy_info}")
                return content, used_proxy
                
        except Exception as e:
            last_exception = e
            logger.warning(f"Attempt {attempt + 1} failed for {url}: {str(e)}")
            
            # Add small delay between retries
            if attempt < max_attempts - 1:
                await asyncio.sleep(random.uniform(1, 3))
    
    # If all attempts failed, raise the last exception
    logger.error(f"All {max_attempts} attempts failed for {url}")
    raise last_exception

async def scrape_with_playwright(url: str, stealth: bool = True, max_attempts: int = 3) -> Tuple[str, Optional[str]]:
    """Scrape with Playwright for JavaScript rendering with automatic proxy rotation"""
    last_exception = None
    used_proxy = None
    
    url = url.strip()
    
    for attempt in range(max_attempts):
        try:
            # Get a new proxy for each attempt
            proxy = await get_proxy_from_distributor()
            proxy_info = f"{proxy[0]}:{proxy[1]}" if proxy else "No proxy"
            logger.info(f"Playwright attempt {attempt + 1}/{max_attempts} for {url} using proxy: {proxy_info}")
            
            async with async_playwright() as p:
                # Launch browser with stealth settings
                browser_args = [
                    '--no-sandbox',
                    '--disable-blink-features=AutomationControlled',
                    '--disable-web-security',
                    '--disable-features=VizDisplayCompositor'
                ]
                
                if proxy:
                    browser_args.append(f'--proxy-server=http://{proxy[0]}:{proxy[1]}')
                
                browser = await p.chromium.launch(
                    headless=True,
                    args=browser_args
                )
                
                context = await browser.new_context(
                    user_agent=random.choice(USER_AGENTS) if stealth else None,
                    viewport={'width': 1920, 'height': 1080},
                    ignore_https_errors=True,
                    extra_http_headers={
                        'Accept-Language': f"{random.choice(['en-US', 'en-GB', 'en-CA'])},en;q=0.9" if stealth else 'en-US,en;q=0.9'
                    } if stealth else {}
                )
                
                # Set proxy authentication if available
                if proxy and len(proxy) == 4:
                    await context.set_extra_http_headers({
                        'Proxy-Authorization': f'Basic {base64.b64encode(f"{proxy[2]}:{proxy[3]}".encode()).decode()}'
                    })
                
                page = await context.new_page()
                
                # Add stealth scripts
                if stealth:
                    await page.add_init_script("""
                        Object.defineProperty(navigator, 'webdriver', {
                            get: () => undefined,
                        });
                        Object.defineProperty(navigator, 'plugins', {
                            get: () => [1, 2, 3, 4, 5],
                        });
                        Object.defineProperty(navigator, 'languages', {
                            get: () => ['en-US', 'en'],
                        });
                    """)
                
                # Navigate to URL and wait for network idle (JavaScript rendering)
                response = await page.goto(url, wait_until='networkidle', timeout=30000)
                
                if response and response.status != 200:
                    raise Exception(f"HTTP {response.status}")
                
                # Wait a bit more for any remaining JavaScript to execute
                await page.wait_for_timeout(1000)
                
                # Get the rendered HTML content (after JavaScript execution)
                content = await page.content()
                used_proxy = proxy_info
                
                await browser.close()
                
                logger.info(f"Successfully scraped {url} with Playwright on attempt {attempt + 1} using proxy: {proxy_info}")
                return content, used_proxy
                
        except Exception as e:
            last_exception = e
            logger.warning(f"Playwright attempt {attempt + 1} failed for {url}: {str(e)}")
            
            # Add small delay between retries
            if attempt < max_attempts - 1:
                await asyncio.sleep(random.uniform(1, 3))
    
    # If all attempts failed, raise the last exception
    logger.error(f"All {max_attempts} Playwright attempts failed for {url}")
    raise last_exception

async def scrape(task_data: Dict[str, Any]) -> Dict[str, Any]:
    """Optimized main scrape function with optional parsing"""
    url = str(task_data['url'])
        
    stealth = task_data.get('stealth', False)
    should_parse = task_data.get('parse', True)
    method = task_data.get('method', 'aiohttp')
    
    start_time = datetime.now()
    
    try:
        # Choose scraping method based on request
        if method == 'playwright':
            content, used_proxy = await scrape_with_playwright(url, stealth)
            method_used = 'playwright'
        else:
            content, used_proxy = await scrape_with_aiohttp(url, stealth)
            method_used = 'aiohttp'
        
        result = {
            'status': 'success',
            'scrape_time': (datetime.now() - start_time).total_seconds(),
            'method': method_used,
            'proxy_used': used_proxy  # Add the proxy that was used
        }
            
        # Handle different content return scenarios
        if task_data.get('full_content') == True:
            result['html'] = content
            
        if should_parse:
            # Use optimized parsing
            parsed_data = await parse_html_fast(content)
            result.update(parsed_data)
        else:
            # Return minimal parsed content
            result['raw_content'] = content
            
        return result
        
    except Exception as e:
        logger.error(f"Scraping failed for {url}: {str(e)}")
        return {
            'status': 'error',
            'error': str(e),
            'scrape_time': (datetime.now() - start_time).total_seconds(),
            'proxy_used': None  # No proxy was successfully used
        }
