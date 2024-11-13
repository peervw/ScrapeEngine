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

# Add more randomized browser fingerprinting data
BROWSER_VERSIONS = {
    'chrome': ['120.0.0.0', '119.0.0.0', '118.0.0.0'],
    'firefox': ['121.0', '120.0', '119.0'],
    'safari': ['17.2', '17.1', '17.0']
}

DEVICE_MEMORY = [2, 4, 8, 16]
HARDWARE_CONCURRENCY = [2, 4, 6, 8, 12]
SCREEN_RESOLUTIONS = [
    (1920, 1080), (1366, 768), (1536, 864),
    (1440, 900), (1280, 720), (2560, 1440)
]

async def get_enhanced_stealth_headers() -> Dict[str, str]:
    """Generate highly randomized headers for enhanced stealth"""
    browser = random.choice(['chrome', 'firefox', 'safari'])
    version = random.choice(BROWSER_VERSIONS[browser])
    resolution = random.choice(SCREEN_RESOLUTIONS)
    
    headers = {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": f"{random.choice(['en-US', 'en-GB', 'en-CA'])},{random.choice(['en;q=0.9', 'en;q=0.8'])}",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": random.choice(["keep-alive", "close"]),
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": random.choice(['none', 'same-origin', 'cross-site']),
        "Sec-Fetch-User": "?1",
        "Sec-CH-UA": f'"Not A(Brand";v="99", "{browser}";v="{version}"',
        "Sec-CH-UA-Mobile": random.choice(["?0", "?1"]),
        "Sec-CH-UA-Platform": f'"{random.choice(["Windows", "macOS", "Linux"])}"',
        "Sec-CH-UA-Arch": random.choice(["x86", "arm"]),
        "Sec-CH-UA-Full-Version": version,
        "Sec-CH-UA-Platform-Version": random.choice(["10.0.0", "11.0.0", "12.0.0"]),
        "Sec-CH-UA-Model": "",
        "Sec-CH-Device-Memory": f"{random.choice(DEVICE_MEMORY)}",
        "Sec-CH-UA-Bitness": random.choice(["64", "32"]),
        "Device-Memory": f"{random.choice(DEVICE_MEMORY)}",
        "Viewport-Width": f"{resolution[0]}",
        "DPR": random.choice(["1", "2", "3"]),
        "Hardware-Concurrency": f"{random.choice(HARDWARE_CONCURRENCY)}",
        "RTT": f"{random.randint(50, 150)}",
        "Downlink": f"{random.randint(5, 15)}",
        "ECT": random.choice(["4g", "3g"]),
    }
    
    # Add random additional headers
    if random.random() > 0.5:
        headers["DNT"] = "1"
    if random.random() > 0.5:
        headers["Save-Data"] = random.choice(["on", "off"])
    if random.random() > 0.5:
        headers["Pragma"] = random.choice(["no-cache", "max-age=0"])
        
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
    """Enhanced stealth aiohttp scraping with proxy support"""
    try:
        # Get enhanced stealth headers
        headers = await get_enhanced_stealth_headers()
        
        # Randomized timeout settings
        timeout = ClientTimeout(
            total=random.uniform(20, 40),
            connect=random.uniform(5, 15),
            sock_read=random.uniform(5, 15)
        )
        
        # Enhanced connector settings
        connector = aiohttp.TCPConnector(
            force_close=True,
            enable_cleanup_closed=True,
            ssl=False,
            limit_per_host=1,
            ttl_dns_cache=300,
            use_dns_cache=False
        )
        
        # Process proxy with random timing
        proxy_url, proxy_auth = None, None
        if proxy and len(proxy) == 4:
            host, port, username, password = proxy
            if all([host, port, username, password]):
                proxy_auth = aiohttp.BasicAuth(username, password)
                proxy_url = f"http://{host}:{port}"
        
        # Random delay before request
        await asyncio.sleep(random.uniform(0.5, 2))
        
        async with aiohttp.ClientSession(
            headers=headers,
            connector=connector,
            timeout=timeout,
            trust_env=True
        ) as session:
            # Random delay between session creation and request
            await asyncio.sleep(random.uniform(0.1, 0.5))
            
            async with session.get(
                url,
                proxy=proxy_url,
                proxy_auth=proxy_auth,
                allow_redirects=True,
                max_redirects=5,
                timeout=timeout,
                verify_ssl=False
            ) as response:
                if response.status != 200:
                    raise ClientError(f"HTTP {response.status}")
                
                # Random delay before reading content
                await asyncio.sleep(random.uniform(0.1, 0.3))
                
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

async def setup_stealth_browser(playwright, proxy: Optional[Tuple[str, str, str, str]] = None):
    """Configure a stealth browser instance with Playwright"""
    # Random browser selection (weighted towards Chrome)
    browser_type = random.choices(
        ['chromium', 'firefox', 'webkit'],
        weights=[0.7, 0.2, 0.1]
    )[0]
    
    # Random device specifications
    resolution = random.choice(SCREEN_RESOLUTIONS)
    device_memory = random.choice(DEVICE_MEMORY)
    hardware_concurrency = random.choice(HARDWARE_CONCURRENCY)
    
    # Browser launch arguments
    browser_args = [
        '--no-sandbox',
        '--disable-setuid-sandbox',
        '--disable-infobars',
        '--window-position=0,0',
        f'--window-size={resolution[0]},{resolution[1]}',
        '--ignore-certifcate-errors',
        '--ignore-certifcate-errors-spki-list',
        f'--device-memory={device_memory}',
        f'--cpu-count={hardware_concurrency}',
    ]
    
    # Proxy configuration
    proxy_settings = None
    if proxy and len(proxy) == 4:
        host, port, username, password = proxy
        if all([host, port, username, password]):
            proxy_settings = {
                "server": f"http://{host}:{port}",
                "username": username,
                "password": password
            }
    
    # Launch browser with stealth settings
    browser = await getattr(playwright, browser_type).launch(
        headless=True,
        args=browser_args,
        proxy=proxy_settings,
        firefox_user_prefs={
            "media.navigator.streams.fake": True,
            "dom.webdriver.enabled": False,
        } if browser_type == 'firefox' else None
    )
    
    # Create context with enhanced stealth
    context = await browser.new_context(
        viewport={'width': resolution[0], 'height': resolution[1]},
        user_agent=random.choice(USER_AGENTS),
        locale=random.choice(['en-US', 'en-GB', 'en-CA']),
        timezone_id=random.choice([
            'America/New_York', 'Europe/London', 'Asia/Tokyo',
            'Australia/Sydney', 'Europe/Paris'
        ]),
        permissions=['geolocation'],
        geolocation={
            'latitude': random.uniform(30, 50),
            'longitude': random.uniform(-120, -70)
        },
        color_scheme=random.choice(['light', 'dark']),
        reduced_motion=random.choice(['reduce', 'no-preference']),
        forced_colors=random.choice(['none', 'active']),
        device_scale_factor=random.choice([1, 2]),
        is_mobile=random.random() < 0.1,  # 10% chance of mobile
        has_touch=random.random() < 0.2,  # 20% chance of touch
        javascript_enabled=True,
    )
    
    # Additional stealth configurations
    await context.add_init_script("""
        Object.defineProperty(navigator, 'webdriver', {
            get: () => false,
        });
        Object.defineProperty(navigator, 'plugins', {
            get: () => [
                { name: 'Chrome PDF Plugin' },
                { name: 'Chrome PDF Viewer' },
                { name: 'Native Client' }
            ],
        });
        window.chrome = {
            runtime: {},
        };
    """)
    
    return browser, context

async def scrape_with_playwright(url: str, proxy: Optional[Tuple[str, str, str, str]] = None) -> str:
    """Enhanced stealth Playwright scraping"""
    async with async_playwright() as playwright:
        browser, context = await setup_stealth_browser(playwright, proxy)
        
        try:
            # Create new page
            page = await context.new_page()
            
            # Randomize navigation behavior
            await page.set_default_navigation_timeout(random.randint(30000, 60000))
            await page.set_default_timeout(random.randint(30000, 60000))
            
            # Random delay before navigation
            await asyncio.sleep(random.uniform(1, 3))
            
            # Navigate with stealth patterns
            response = await page.goto(
                url,
                wait_until=random.choice([
                    'domcontentloaded',
                    'networkidle',
                    'load'
                ])
            )
            
            if not response.ok:
                raise Exception(f"HTTP {response.status}")
                
            # Random scroll behavior
            if random.random() < 0.7:  # 70% chance to scroll
                await page.evaluate("""
                    window.scrollTo({
                        top: document.body.scrollHeight * Math.random(),
                        behavior: 'smooth'
                    });
                """)
                await asyncio.sleep(random.uniform(0.5, 2))
            
            # Random delay before content extraction
            await asyncio.sleep(random.uniform(0.5, 1.5))
            
            content = await page.content()
            
            # Random delay before closing
            await asyncio.sleep(random.uniform(0.3, 1))
            
            return content
            
        except Exception as e:
            logger.error(f"Playwright scraping error: {str(e)}")
            raise
        finally:
            await context.close()
            await browser.close()

async def scrape(task_data: Dict[str, Any]) -> Dict[str, Any]:
    """Main scraping function that handles both methods"""
    url = str(task_data['url'])
    method = task_data.get('method', 'simple')
    proxy = task_data.get('proxy')
    stealth = task_data.get('stealth', True)
    
    logger.info(f"Starting scrape task for {url} using {method} (stealth: {stealth})")
    start_time = datetime.now()
    method_used = method
    
    try:
        if method == 'advanced':
            content = await scrape_with_playwright(url, proxy)
            method_used = 'advanced (playwright)'
        else:
            try:
                content = await scrape_with_aiohttp(url, proxy, stealth=stealth)
                method_used = 'simple (aiohttp)'
            except Exception as e:
                logger.warning(f"aiohttp scraping failed, falling back to playwright: {str(e)}")
                content = await scrape_with_playwright(url, proxy)
                method_used = 'Fallback: advanced (playwright)'
        
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
