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
            limit=100,  # Increased connection pool
            limit_per_host=30,  # More connections per host
            ttl_dns_cache=600,  # Longer DNS cache
            use_dns_cache=True,
            keepalive_timeout=30,  # Keep connections alive
            enable_cleanup_closed=True,  # Enable cleanup
            ssl=False
        )
        
        timeout = ClientTimeout(
            total=30,  # Increased timeout for testing
            connect=5,  # Increased connect timeout
            sock_read=25  # Increased read timeout
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

async def scrape_batch(tasks: List[Dict[str, Any]], max_concurrent: int = MAX_CONCURRENT) -> List[Union[Dict[str, Any], BaseException]]:
    """Process multiple scraping tasks concurrently"""
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def scrape_with_semaphore(task_data):
        async with semaphore:
            return await scrape(task_data)
    
    return await asyncio.gather(*[scrape_with_semaphore(task) for task in tasks], return_exceptions=True)

@retry(
    stop=stop_after_attempt(2),  # Reduced retries
    wait=wait_exponential(multiplier=0.5, min=1, max=3),  # Faster retry
    retry=(
        retry_if_exception_type(ClientError) |
        retry_if_exception_type(asyncio.TimeoutError)
    ),
    before_sleep=lambda retry_state: logger.warning(
        f"Retry attempt {retry_state.attempt_number} for URL after error: {getattr(retry_state.outcome, 'exception', lambda: 'Unknown error')()}"
    )
)
async def scrape_with_aiohttp(url: str, proxy: Optional[Tuple[str, str, str, str]] = None, stealth: bool = True) -> str:
    """Performance-optimized aiohttp scraping with session reuse"""
    try:
        session = await get_cached_session(proxy, stealth)
        
        # Remove artificial delay - let natural network latency handle this
        
        async with session.get(
            url,
            proxy=f"http://{proxy[0]}:{proxy[1]}" if proxy else None,
            proxy_auth=aiohttp.BasicAuth(proxy[2], proxy[3]) if proxy and len(proxy) == 4 else None,
            allow_redirects=True,
            max_redirects=2,
            ssl=False,
            compress=True  # Enable compression
        ) as response:
            if response.status != 200:
                raise ClientError(f"HTTP {response.status}")
            
            return await response.text(encoding='utf-8', errors='ignore')  # Faster text parsing
                    
    except Exception as e:
        logger.error(f"Scraping error for {url}: {str(e)}")
        raise

async def setup_stealth_browser(playwright, proxy: Optional[Tuple[str, str, str, str]] = None):
    """Performance-optimized Playwright setup"""
    browser_type = 'chromium'
    
    browser_args = [
        '--no-sandbox',
        '--disable-setuid-sandbox',
        '--disable-dev-shm-usage',
        '--disable-accelerated-2d-canvas',
        '--disable-gpu',
        '--disable-extensions',
    ]
    
    browser = await playwright.chromium.launch(
        headless=True,
        args=browser_args,
        proxy={
            "server": f"http://{proxy[0]}:{proxy[1]}",
            "username": proxy[2],
            "password": proxy[3]
        } if proxy and len(proxy) == 4 else None
    )
    
    context = await browser.new_context(
        viewport={'width': 1920, 'height': 1080},
        user_agent=random.choice(USER_AGENTS),
        locale='en-US',
        timezone_id='America/New_York',
    )
    
    await context.add_init_script("""
        Object.defineProperty(navigator, 'webdriver', { get: () => false });
    """)
    
    return browser, context

async def scrape_with_playwright(url: str, proxy: Optional[Tuple[str, str, str, str]] = None) -> str:
    """Performance-optimized Playwright scraping"""
    async with async_playwright() as playwright:
        browser, context = await setup_stealth_browser(playwright, proxy)
        
        try:
            page = await context.new_page()
            await page.set_default_navigation_timeout(20000)
            
            await asyncio.sleep(MINIMAL_DELAY)
            
            response = await page.goto(url, wait_until='domcontentloaded')
            
            if not response.ok:
                raise Exception(f"HTTP {response.status}")
            
            content = await page.content()
            return content
            
        finally:
            await context.close()
            await browser.close()

async def scrape(task_data: Dict[str, Any]) -> Dict[str, Any]:
    """Optimized main scrape function with optional parsing"""
    url = str(task_data['url'])
    method = task_data.get('method', 'aiohttp')
    # Map method names from API to internal names
    if method == 'playwright':
        method = 'advanced'
    else:
        method = 'simple'
        
    proxy = task_data.get('proxy')
    stealth = task_data.get('stealth', False)
    should_parse = task_data.get('parse', True)
    
    start_time = datetime.now()
    
    try:
        if method == 'advanced':
            content = await scrape_with_playwright(url, proxy)
            method_used = 'playwright'
        else:
            content = await scrape_with_aiohttp(url, proxy, stealth)
            method_used = 'aiohttp'
        
        result = {
            'status': 'success',
            'scrape_time': (datetime.now() - start_time).total_seconds(),
            'method': method_used,
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
            'scrape_time': (datetime.now() - start_time).total_seconds()
        }

if __name__ == "__main__":
    # Example usage
    loop = asyncio.get_event_loop()
    tasks = [
        {'url': 'https://example.com', 'method': 'simple', 'parse': True},
        {'url': 'https://example.org', 'method': 'advanced', 'stealth': True, 'parse': False}
    ]
    
    results = loop.run_until_complete(scrape_batch(tasks))
    print(json.dumps(results, indent=2))