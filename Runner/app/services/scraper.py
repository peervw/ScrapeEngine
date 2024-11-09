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

async def get_stealth_headers() -> Dict[str, str]:
    """Generate randomized headers for stealth"""
    # Enhanced headers with more randomization
    languages = ['en-US,en;q=0.9', 'en-GB,en;q=0.9', 'en-CA,en;q=0.9']
    platforms = ['Windows NT 10.0', 'Macintosh; Intel Mac OS X 10_15_7', 'X11; Linux x86_64']
    encodings = ['gzip, deflate, br', 'gzip, deflate', 'br']
    
    headers = {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
        "Accept-Language": random.choice(languages),
        "Accept-Encoding": random.choice(encodings),
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": random.choice(['none', 'same-origin']),
        "Sec-Fetch-User": "?1",
        "Cache-Control": random.choice(['max-age=0', 'no-cache']),
        "Platform": random.choice(platforms),
        "Sec-CH-UA": '"Google Chrome";v="120", "Chromium";v="120", "Not=A?Brand";v="99"',
        "Sec-CH-UA-Mobile": "?0",
        "Sec-CH-UA-Platform": f'"{random.choice(["Windows", "macOS", "Linux"])}"',
    }
    
    # Optionally add headers that might be None
    if random.random() > 0.5:
        headers["DNT"] = "1"
    if random.random() > 0.5:
        headers["Pragma"] = "no-cache"
    if random.random() > 0.5:
        headers["X-Requested-With"] = "XMLHttpRequest"
        
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
async def scrape_with_aiohttp(url: str, proxy: Optional[Tuple[str, str, str, str]] = None, stealth: bool = False) -> str:
    """Basic aiohttp scraping with proxy support"""
    try:
        # Minimal, guaranteed non-None headers
        headers = {
            "User-Agent": random.choice(USER_AGENTS),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
            "Cache-Control": "no-cache",
        }
        
        # Basic timeout settings
        timeout = ClientTimeout(
            total=30,
            connect=10,
            sock_read=10
        )
        
        # Clean proxy setup
        proxy_auth = None
        if proxy and len(proxy) == 4:
            host, port, username, password = proxy
            if all([host, port, username, password]):  # Ensure no None values
                proxy_auth = aiohttp.BasicAuth(username, password)
                proxy_url = f"http://{host}:{port}"
            else:
                proxy_url = None
        else:
            proxy_url = None
        
        # Basic connector with SSL disabled
        connector = aiohttp.TCPConnector(
            force_close=True,
            enable_cleanup_closed=True,
            ssl=False,
            limit_per_host=1
        )
        
        async with aiohttp.ClientSession(
            headers=headers,
            connector=connector,
            timeout=timeout,
            trust_env=True
        ) as session:
            async with session.get(
                url,
                proxy=proxy_url,
                proxy_auth=proxy_auth,
                allow_redirects=True,
                max_redirects=5,
                timeout=timeout
            ) as response:
                if response.status != 200:
                    raise ClientError(f"HTTP {response.status}")
                
                try:
                    content = await response.text()
                    if not content:
                        raise ClientError("Empty response received")
                    return content
                except UnicodeDecodeError:
                    raw_content = await response.read()
                    return raw_content.decode('utf-8', errors='ignore')
                    
    except Exception as e:
        logger.error(f"Scraping error for {url}: {str(e)}")
        raise

async def scrape_with_playwright(url: str, proxy: Optional[tuple[str, str, str, str]] = None) -> str:
    """Advanced scraping using playwright with enhanced stealth features"""
    async with async_playwright() as p:
        browser_args = [
            '--disable-blink-features=AutomationControlled',
            '--disable-dev-shm-usage',
            '--disable-infobars',
            '--disable-background-networking',
            '--disable-default-apps',
            '--disable-extensions',
            '--disable-sync',
            '--disable-translate',
            '--hide-scrollbars',
            '--metrics-recording-only',
            '--mute-audio',
            '--no-first-run',
            '--no-default-browser-check',
        ]
        
        if proxy:
            host, port, username, password = proxy
            browser_args.append(f'--proxy-server={host}:{port}')
        
        browser = await p.chromium.launch(
            headless=True,
            args=browser_args
        )
        
        try:
            # Enhanced context settings
            context = await browser.new_context(
                proxy={
                    'server': f'{proxy[0]}:{proxy[1]}',
                    'username': proxy[2],
                    'password': proxy[3]
                } if proxy else None,
                viewport={'width': random.randint(1280, 1920), 'height': random.randint(800, 1080)},
                user_agent=random.choice(USER_AGENTS),
                java_script_enabled=True,
                has_touch=random.choice([True, False]),
                locale=random.choice(['en-US', 'en-GB', 'en-CA']),
                timezone_id=random.choice(['America/New_York', 'Europe/London', 'Asia/Tokyo']),
                color_scheme=random.choice(['dark', 'light']),
                device_scale_factor=random.choice([1, 2])
            )
            
            page = await context.new_page()
            await page.goto(url, wait_until='networkidle')
            
            # Random delays and human-like behavior
            await asyncio.sleep(random.uniform(1, 3))
            
            # Natural scrolling behavior
            for _ in range(random.randint(2, 4)):
                await page.evaluate(f"""
                    window.scrollTo({{
                        top: {random.randint(500, 1000)},
                        behavior: 'smooth'
                    }});
                """)
                await asyncio.sleep(random.uniform(1, 2))
            
            content = await page.content()
            return content
            
        finally:
            await browser.close()

async def scrape(task_data: Dict[str, Any]) -> Dict[str, Any]:
    """Main scraping function that handles both methods"""
    url = str(task_data['url'])
    method = task_data.get('method', 'aiohttp')
    proxy = task_data.get('proxy')
    stealth = task_data.get('stealth', False)
    
    logger.info(f"Starting scrape task for {url} using {method} (stealth: {stealth})")
    start_time = datetime.now()
    method_used = method
    
    try:
        if method == 'playwright':
            content = await scrape_with_playwright(url, proxy)
            method_used = 'playwright'
        else:
            try:
                content = await scrape_with_aiohttp(url, proxy, stealth=stealth)
                method_used = 'aiohttp'
            except Exception as e:
                logger.warning(f"aiohttp scraping failed, falling back to playwright: {str(e)}")
                content = await scrape_with_playwright(url, proxy)
                method_used = 'playwright'
        
        # Parse content with BeautifulSoup
        soup = BeautifulSoup(content, 'html.parser', from_encoding='utf-8')
        
        # Remove unwanted elements
        for script in soup(['script', 'style']):
            script.decompose()
        
        result = {
            'title': soup.title.string if soup.title else None,
            'text_content': soup.get_text(separator=' ', strip=True),
            'links': [{'href': a.get('href'), 'text': a.text} for a in soup.find_all('a', href=True)],
            'status': 'success',
            'scrape_time': (datetime.now() - start_time).total_seconds(),
            'method_used': method_used
        }
        
        if task_data.get('full_content') == 'yes':
            result['html'] = content
            
        return result
        
    except Exception as e:
        logger.error(f"Scraping failed for {url}: {str(e)}")
        return {
            'status': 'error',
            'error': str(e),
            'scrape_time': (datetime.now() - start_time).total_seconds()
        }
