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
            total=10,
            connect=3,
            sock_read=7
        )
        
        # Connector settings optimized for proxy rotation and stealth
        connector = aiohttp.TCPConnector(
            force_close=True,        # Important for proxy rotation
            enable_cleanup_closed=True,
            ssl=False,
            limit_per_host=5,
            use_dns_cache=True,
            ttl_dns_cache=300
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
            async with session.get(
                url,
                proxy=f"http://{proxy[0]}:{proxy[1]}" if proxy else None,
                proxy_auth=aiohttp.BasicAuth(proxy[2], proxy[3]) if proxy and len(proxy) == 4 else None,
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
    method = task_data.get('method', 'simple')
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
            'method_used': method_used,
        }
            
        # Handle different content return scenarios
        if task_data.get('full_content') == 'yes':
            result['html'] = content
            
        if should_parse:
            # Only parse if explicitly requested
            soup = BeautifulSoup(content, 'html.parser')
            result.update({
                'title': soup.title.string if soup.title else None,
                'text_content': ' '.join(soup.stripped_strings),
                'links': [{'href': a.get('href'), 'text': a.text} 
                         for a in soup.find_all('a', href=True)]
            })
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
