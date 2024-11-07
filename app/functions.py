import logging
import requests
import time
from requests.exceptions import HTTPError, Timeout, ConnectionError
from tenacity import retry, stop_after_attempt, wait_exponential
from pydantic import BaseModel, field_validator
from typing import Optional, Literal
import logging
import os

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Add at the top of functions.py
PROXY_FILE = 'app/static/proxies.txt'

# Function to read data from the static file
def read_data_from_file(filename):
    data_list = []
    try:
        # Handle both absolute and relative paths
        filepath = filename if os.path.isabs(filename) else os.path.join("app/static", filename)
        logger.debug(f"Attempting to open file: {filepath}")
        with open(filepath, 'r') as file:
            for line in file:
                logger.debug(f"Reading line: {line.strip()}")
                # Assuming the format in the file is: IP:Port:Username:Password
                parts = line.strip().split(':')
                if len(parts) == 4:
                    logger.debug(f"Parsed data - IP: {parts[0]}, Port: {parts[1]}, Username: {parts[2]}, Password: {parts[3]}")
                    data_list.append({
                        "ip": parts[0],
                        "port": parts[1],
                        "username": parts[2],
                        "password": parts[3]
                    })
                elif len(parts) == 3:
                    logger.debug(f"Parsed data - URL: {parts[0]}, Username: {parts[1]}, Password: {parts[2]}")
                    data_list.append({
                        "url": parts[0],
                        "username": parts[1],
                        "password": parts[2]
                    }) 
                else:
                    logger.warning(f"Invalid line format: {line.strip()}")
    except FileNotFoundError:
        logger.error(f"File not found: {filepath}")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
    
    return data_list

class ProxyManager:
    _instance = None
    _proxy_file = PROXY_FILE
    _proxies = None

    @classmethod
    def reset_instance(cls):
        cls._instance = None
        cls._proxies = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ProxyManager, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        try:
            with open(self._proxy_file, 'r') as f:
                self.proxies = [proxy.strip() for proxy in f.readlines()]
            self.proxy_generator = self._create_proxy_generator()
        except FileNotFoundError:
            logger.error(f"Proxy file not found: {self._proxy_file}")
            raise

    @classmethod
    def set_proxy_file(cls, file_path):
        cls._proxy_file = file_path
        cls.reset_instance()

    def _create_proxy_generator(self):
        while True:
            for proxy in self.proxies:
                ip, port, user, password = proxy.split(':')
                yield ip, port, user, password

    def get_next_proxy(self):
        return next(self.proxy_generator)

def get_next_proxy():
    """
    Get the next proxy from the ProxyManager.
    
    Returns
    -------
    tuple : A tuple containing the IP address, port, username, and password of the proxy.
    
    Examples
    --------
    >>> get_next_proxy()
    '192.168.1.:8080:user:password'
    """
    return ProxyManager().get_next_proxy()

##### Scrape

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=4))
def scrape(args):
    logger.info("Scraper started")

    # Extracting arguments
    target_url = str(args.get('url'))
    scraper = args.get('scraper_credentials')
    proxy = args.get('proxy')
    link_or_article = args.get('link_or_article')

    # Validate input arguments
    if not target_url or not scraper:
        error_message = "Invalid arguments provided to scraper. 'url' and 'credentials' are required."
        logger.error(error_message)
        return {
            "status": "failure",
            "error": error_message
        }
    
    request_url = construct_request_url(scraper, target_url, link_or_article, proxy)

    try:
        logger.info(f"Making GET request to {target_url} using {request_url}")
        response = requests.get(
            request_url,
            auth=(scraper['username'], scraper['password']),
            timeout=30
        )
        response.raise_for_status()
        logger.info(f"Successfully fetched data from {request_url}")
        return {
            "used_scraper": scraper,
            "used_proxy": proxy,
            "status": "success",
            "timestamp": time.time(),
            "url": target_url,
            "data": response.text
        }
    except HTTPError as e:
        logger.error(f"HTTP error occurred while fetching data: {e}")
        return {
            "used_scraper": scraper,
            "used_proxy": proxy,
            "status": "failure",
            "timestamp": time.time(),
            "url": target_url,
            "request_url": request_url,
            "error": f"HTTP error: {str(e)}"
        }
    except Timeout as e:
        logger.error(f"Request timed out for URL: {target_url} using {request_url}: {e}")
        return {
            "used_scraper": scraper,
            "used_proxy": proxy,
            "status": "failure",
            "timestamp": time.time(),
            "url": target_url,
            "request_url": request_url,
            "error": f"Request timed out: {str(e)}"
        }
    except ConnectionError as e:
        logger.error(f"Connection error while trying to reach {target_url} using {request_url}: {e}")
        return {
            "used_scraper": scraper,
            "used_proxy": proxy,
            "status": "failure",
            "timestamp": time.time(),
            "url": target_url,
            "request_url": request_url,
            "error": f"Connection error: {str(e)}"
        }
    except Exception as e:
        logger.error(f"An unexpected error occurred: {str(e)}")
        return {
            "used_scraper": scraper,
            "used_proxy": proxy,
            "status": "failure",
            "timestamp": time.time(),
            "url": target_url,
            "request_url": request_url,
            "error": f"Unexpected error: {str(e)}"
        }


def construct_request_url(scraper, target_url, link_or_article, proxy):
    if link_or_article == 'article':
        base_url = f"http://{scraper['url']}/api/article?url={target_url}&stealth=true&cache=false"
    elif link_or_article == 'link':
        base_url = f"http://{scraper['url']}/api/links?url={target_url}&stealth=true&cache=false"
    proxy_part = f"&proxy-server={proxy[0]}:{proxy[1]}&proxy-username={proxy[2]}&proxy-password={proxy[3]}"
    if link_or_article == 'article':
        return f"{base_url}&full-content=yes{proxy_part}"
    elif link_or_article == 'link':
        return f"{base_url}{proxy_part}"
    else:
        raise ValueError("'link_or_article' must be either 'link' or 'article'")


class ScrapeRequest(BaseModel):
    url: str
    link_or_article: Optional[Literal["link", "article"]] = "article"
    other_params: Optional[dict] = None

    @field_validator('url')
    def validate_url(cls, v):
        if not v.startswith(('http://', 'https://')):
            raise ValueError('URL must start with http:// or https://')
        return v


if __name__ == '__main__':
    pass