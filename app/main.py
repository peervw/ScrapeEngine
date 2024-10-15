from flask import Flask, jsonify, request, abort
import os
import logging
from functions import *
from webshare_proxy import *
import threading
import asyncio
from concurrent.futures import ThreadPoolExecutor
import time

app = Flask(__name__)
stop_event = threading.Event()

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Executor for running scrapers concurrently
executor = ThreadPoolExecutor(max_workers=5)

# Authentication setup
API_TOKEN = os.getenv('AUTH_TOKEN')

# Read scraper credentials
credentials_list = read_data_from_file('scraper.txt')
if not credentials_list:
    logger.error("No credentials found in scraper.txt")
else:
    logger.info(f"Loaded {len(credentials_list)} credentials for scraping")

# Index and lock for round-robin credential usage
credentials_index = 0
credentials_lock = threading.Lock()  # To safely access the shared credentials index

def token_required(f):
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token or token not in API_TOKEN:
            logger.warning("Unauthorized access attempt.")
            abort(401, description="Unauthorized: Invalid or missing token.")
        return f(*args, **kwargs)
    decorated.__name__ = f.__name__
    return decorated

async def route_to_scraper(args):
    global credentials_index
    with credentials_lock:
        # Get the next set of credentials in a round-robin fashion
        if not credentials_list:
            raise Exception("No credentials available for scraping")
        
        credentials = credentials_list[credentials_index]
        credentials_index = (credentials_index + 1) % len(credentials_list)

    # Add credentials to the args
    args['scraper_credentials'] = credentials
    
    # get next proxy
    args['proxy'] = get_next_proxy()

    # Run the scraper using the executor to avoid blocking the event loop
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(executor, scrape, args)
    return result

@app.route('/api/scrape', methods=['GET'])
@token_required
async def scrape_endpoint():
    # Get JSON arguments
    args = request.get_json()

    # Validate that the target URL is provided
    target_url = args.get('url')
    if not target_url:
        logger.error("No target URL provided in request")
        return jsonify({"error": "No target URL provided"}), 400

    # Route to the next available scraper with appropriate credentials
    try:
        result = await route_to_scraper(args)
        return jsonify(result)
    except Exception as e:
        logger.error(f"An error occurred while scraping: {str(e)}")
        return jsonify({"error": str(e)}), 500

# Route to return JSON runners data
@app.route('/api/runners_json', methods=['GET'])
@token_required
def get_runners_data():
    logger.info("/api/runners_json endpoint was called")
    data = read_data_from_file("scraper.txt")
    logger.debug(f"Data to be returned: {data}")
    return data

# Route to return JSON proxy data
@app.route('/api/proxies_json', methods=['GET'])
@token_required
def get_proxies_data():
    logger.info("/api/proxies_json endpoint was called")
    data = read_data_from_file("proxies.txt")
    logger.debug(f"Data to be returned: {data}")
    return data

# Proxy manager
def main_proxy_updater():
    while not stop_event.is_set():
        try:
            master_webshare_get_proxies()
            logging.info("Proxies updated.")
        except Exception as e:
            logging.error(f"An error occurred in proxy_updater: {str(e)}")
        time.sleep(3600)

if __name__ == '__main__':
    # Start the proxy updater thread
    threads = []
    threads.append(threading.Thread(target=main_proxy_updater, daemon=True))
    for thread in threads:
        thread.start()

    logger.info("Starting scrape engine...")
    # Running the app with an async-friendly server like hypercorn or gunicorn
    app.run(debug=True, host='0.0.0.0', port=4000)
