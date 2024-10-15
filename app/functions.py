import os
import logging
import requests
import json

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Function to read data from the static file
def read_data_from_file(filename):
    data_list = []
    try:
        logger.debug(f"Attempting to open file: static/{filename}")
        with open(f"app/static/{filename}", 'r') as file:
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
                if len(parts) == 3:
                    logger.debug(f"Parsed data - URL: {parts[0]}, Username: {parts[1]}, Password: {parts[2]}")
                    data_list.append({
                        "url": parts[0],
                        "username": parts[1],
                        "password": parts[2]
                    }) 
                else:
                    logger.warning(f"Invalid line format: {line.strip()}")
    except FileNotFoundError:
        logger.error(f"File not found: static/{filename}")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
    
    return json.dumps(data_list, indent=4)

# Proxy manager
def import_proxies():
    with open('app/static/proxies.txt', 'r') as f:
        proxies = f.readlines()
    return [proxy.strip() for proxy in proxies]  # Remove any extra whitespace or newline characters

class ProxyManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ProxyManager, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        self.proxies = import_proxies()
        self.proxy_generator = self._create_proxy_generator()

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

def scrape(args):
    """
    Scrape functions that takes in args and performs scraping using scraper network.
    Args should include:
    - 'url': The target URL to which we want to send a request.
    - 'link_or_article': A string that specifies whether links or the complete content should be scraped.
    - 'credentials': A dictionary containing 'url', 'username', 'password' for the scraper endpoint.
    - 'proxies': A dictionary containing 'url', 'username', 'password' for the proxy connection.

    The scraper will use these credentials to make an authenticated GET request to the provided URL.
    """
    logger.info("Scraper started")

    # Extracting arguments
    target_url = args.get('url')
    scraper = args.get('scraper_credentials')
    proxy = args.get('proxy')
    link_or_article = args.get('link_or_article')

    if not target_url or not scraper:
        error_message = "Invalid arguments provided to scraper. 'url' and 'credentials' are required."
        logger.error(error_message)
        return {"error": error_message}
    
    if link_or_article == 'article':
        request_url = f"{scraper["url"]}?url={target_url}&stealth=true&cache=false&full-content=yes&proxy-server={proxy["ip"]}:{proxy["port"]}&proxy-username={proxy["username"]}&proxy-password={proxy["password"]}"
    elif link_or_article == 'link':
        request_url = f"{scraper["url"]}?url={target_url}&stealth=true&cache=false&proxy-server={proxy["ip"]}:{proxy["port"]}&proxy-username={proxy["username"]}&proxy-password={proxy["password"]}"
    else:
        error_message = "Invalid arguments provided to scraper. 'link_or_article' must be either 'link' or 'article'."
        logger.error(error_message)
        return {"error": error_message}
    
    try:
        logger.info(f"Making GET request to {target_url} using {request_url}")
        response = requests.get(
            request_url,
            auth=(scraper['username'], scraper['password']),
            timeout=10
        )
        response.raise_for_status()
        logger.info(f"Successfully fetched data from {request_url}")
        return {
            "used_scraper": scraper['url'],
            "used_proxy": proxy['url'],
            "status": "success",
            "data": response.text
        }
    except requests.RequestException as e:
        logger.error(f"Failed to fetch data from {target_url} using {scraper['url']}: {str(e)}")
        return {
            "credential_url": scraper['url'],
            "status": "failure",
            "error": str(e)
        }

if __name__ == '__main__':
    pass