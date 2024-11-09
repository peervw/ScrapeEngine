from typing import Dict, Any, Tuple, List
import aiohttp
import logging
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright, Browser, Page
import random
import json
from tenacity import retry, stop_after_attempt, wait_exponential
import asyncio
import time

logger = logging.getLogger(__name__)

class WebScraper:
    # Base browser configurations to build upon
    BROWSER_BASES = {
        'chrome': {
            'name': 'Chrome',
            'versions': ['120.0.0.0', '119.0.0.0', '118.0.0.0'],
            'build_ids': ['6099', '5735', '5993', '6045'],
        },
        'firefox': {
            'name': 'Firefox',
            'versions': ['121.0', '120.0', '119.0'],
            'build_ids': ['20231211', '20231130', '20231201'],
        },
        'safari': {
            'name': 'Safari',
            'versions': ['17.1', '17.0', '16.6'],
            'build_ids': ['14.1.2', '14.1.1', '14.1.0'],
        }
    }

    def _generate_dynamic_fingerprint(self) -> Dict[str, str]:
        """Generate a random but realistic fingerprint for each request"""
        # Randomly select browser type
        browser_type = random.choice(list(self.BROWSER_BASES.keys()))
        browser = self.BROWSER_BASES[browser_type]
        
        # Random device characteristics
        is_mobile = random.random() < 0.2
        is_mac = random.random() < 0.3
        
        # Generate platform-specific details
        if is_mobile:
            if random.random() < 0.7:  # iOS
                platform = 'iPhone'
                os_version = f'iOS {random.randint(14,17)}_{random.randint(0,6)}'
                webkit_version = f'{600+random.randint(1,5)}.{random.randint(1,9)}.{random.randint(1,15)}'
            else:  # Android
                platform = 'Android'
                os_version = f'{random.randint(10,14)}.0.0'
                webkit_version = f'537.36'
        else:
            if is_mac:
                platform = 'MacIntel'
                os_version = f'10_{random.randint(14,15)}_{random.randint(0,7)}'
            else:
                platform = 'Win64'
                os_version = f'10.0.{random.randint(19041,19045)}.0'

        # Generate dynamic screen properties
        if is_mobile:
            width = random.choice([375, 390, 414, 428])
            height = random.choice([667, 736, 812, 844, 896, 926])
            pixel_ratio = random.choice([2, 3])
        else:
            width = random.randint(1024, 1920)
            height = random.randint(768, 1080)
            pixel_ratio = random.choice([1, 1.25, 1.5, 2])

        return {
            'browser': browser_type,
            'version': random.choice(browser['versions']),
            'build_id': random.choice(browser['build_ids']),
            'platform': platform,
            'os_version': os_version,
            'webkit_version': webkit_version if is_mobile else '537.36',
            'is_mobile': is_mobile,
            'width': width,
            'height': height,
            'pixel_ratio': pixel_ratio,
            'languages': [
                random.choice(['en-US', 'en-GB', 'en-CA']),
                random.choice(['en;q=0.9', 'es;q=0.8', 'fr;q=0.7'])
            ],
            'color_depth': random.choice([24, 30, 32]),
            'cores': random.choice([4, 6, 8, 12, 16]),
            'memory': random.choice([4, 8, 16, 32]),
            'touch_points': 5 if is_mobile else 0,
        }

    async def scrape_with_aiohttp(self, url: str) -> str:
        """Enhanced aiohttp scraping with dynamic fingerprinting"""
        # Generate new fingerprint for each request
        fingerprint = self._generate_dynamic_fingerprint()
        
        # Build user agent
        if fingerprint['is_mobile']:
            if 'iPhone' in fingerprint['platform']:
                user_agent = (
                    f'Mozilla/5.0 (iPhone; CPU {fingerprint["platform"]} OS {fingerprint["os_version"]} like Mac OS X) '
                    f'AppleWebKit/{fingerprint["webkit_version"]} (KHTML, like Gecko) '
                    f'Version/{fingerprint["version"]} Mobile/15E148 Safari/{fingerprint["webkit_version"]}'
                )
            else:
                user_agent = (
                    f'Mozilla/5.0 (Linux; Android {fingerprint["os_version"]}; K) '
                    f'AppleWebKit/{fingerprint["webkit_version"]} (KHTML, like Gecko) '
                    f'Chrome/{fingerprint["version"]} Mobile Safari/{fingerprint["webkit_version"]}'
                )
        else:
            user_agent = (
                f'Mozilla/5.0 ({fingerprint["platform"]}; '
                f'{"Mac OS X" if "Mac" in fingerprint["platform"] else "Windows NT"} {fingerprint["os_version"]}) '
                f'AppleWebKit/537.36 (KHTML, like Gecko) '
                f'Chrome/{fingerprint["version"]} Safari/537.36'
            )

        # Dynamic headers based on fingerprint
        headers = {
            'User-Agent': user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': ','.join(fingerprint['languages']),
            'Accept-Encoding': 'gzip, deflate, br',
            'Sec-CH-UA-Platform': f'"{fingerprint["platform"]}"',
            'Sec-CH-UA-Mobile': '?1' if fingerprint['is_mobile'] else '?0',
            'Viewport-Width': str(fingerprint['width']),
            'DPR': str(fingerprint['pixel_ratio']),
        }

        if self.stealth:
            # Add dynamic anti-bot headers
            headers.update({
                'DNT': str(random.randint(0, 1)),
                'Sec-Fetch-Dest': random.choice(['document', 'empty']),
                'Sec-Fetch-Mode': random.choice(['navigate', 'cors']),
                'Sec-Fetch-Site': random.choice(['none', 'same-origin']),
                'Sec-Fetch-User': '?1',
                'X-Requested-With': 'XMLHttpRequest' if random.random() < 0.3 else None,
                'Priority': random.choice(['u=0', 'u=1', 'u=3']),
                'Connection': random.choice(['keep-alive', 'close']),
            })

            # Generate dynamic cookies
            cookies = {
                f'_id_{random.randint(100,999)}': f'{random.randbytes(16).hex()}',
                f'_sess_{random.randint(100,999)}': f'{random.randbytes(8).hex()}',
                '_v': f'{int(time.time()-random.randint(100000,999999))}',
            }

        async with aiohttp.ClientSession(cookie_jar=aiohttp.CookieJar()) as session:
            if self.stealth:
                # Random pre-request behavior
                if random.random() < 0.3:  # 30% chance of referrer
                    referrer = random.choice([
                        'https://www.google.com/search?q=' + '+'.join(url.split('/')[2].split('.')),
                        'https://duckduckgo.com/',
                        None
                    ])
                    if referrer:
                        headers['Referer'] = referrer
                        await session.get(referrer, proxy=self.proxy_url, ssl=False)
                        await asyncio.sleep(random.uniform(0.5, 2))

            async with session.get(
                url,
                proxy=self.proxy_url,
                headers=headers,
                cookies=cookies if self.stealth else None,
                timeout=aiohttp.ClientTimeout(total=30),
                allow_redirects=True,
                ssl=False if self.stealth else True,
            ) as response:
                content = await response.text()
                
                # Random post-request delay
                if self.stealth:
                    await asyncio.sleep(random.uniform(0.1, 1.0))
                
                return content

@retry(stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=4))
async def scrape(args: Dict[str, Any]) -> Dict[str, Any]:
    """Main scraping function with method selection"""
    url = str(args['url'])
    proxy = args['proxy']
    full_content = args['full_content']
    stealth = args.get('stealth', False)
    method = args.get('method', 'aiohttp')
    
    start_time = time.time()
    scraper = WebScraper(proxy, stealth)
    
    try:
        if method == 'playwright':
            html = await scraper.scrape_with_playwright(url)
        else:
            html = await scraper.scrape_with_aiohttp(url)
            
        soup = BeautifulSoup(html, 'html.parser')
        
        result = {
            "url": url,
            "title": soup.title.string if soup.title else None,
            "success": True,
            "method_used": method,
            "stealth_mode": stealth,
            "scrape_time": round(time.time() - start_time, 2)
        }
        
        if full_content == "yes":
            result.update({
                "content": html,
                "text_content": soup.get_text(separator='\n', strip=True),
                "meta": {
                    tag['name']: tag['content']
                    for tag in soup.find_all('meta', attrs={'name': True, 'content': True})
                }
            })
            
        return result
        
    except Exception as e:
        logger.error(f"Scraping failed: {str(e)}")
        raise