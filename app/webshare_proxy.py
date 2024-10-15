import requests
import dotenv
import os
import logging

dotenv.load_dotenv("app/.env")

logging.basicConfig(level=logging.INFO)

def master_webshare_get_proxies():
    """
    Get the list of proxies from the Webshare API and save them to a file
    """
    try:
        TOKEN = os.getenv("WEBSHARE_TOKEN")
        response = requests.get(
            "https://proxy.webshare.io/api/v2/proxy/list/?mode=direct&page=1&page_size=1000",
            headers={"Authorization": "Token " + TOKEN}
        )
        data = response.json()
        
        # check if proxies are in the response
        if "results" not in data:
            print("No proxies found in the response.")
        else:
            # delete the existing proxies file
            try:
                os.remove("app/static/proxies.txt")
            except FileNotFoundError:
                pass
        
        # Open the file to write the proxies
        with open("app/static/proxies.txt", "w") as f:
            # Iterate through each proxy in the results
            for proxy in data["results"]:
                # Format the proxy information as "ip:port:username:password"
                proxy_entry = f"{proxy['proxy_address']}:{proxy['port']}:{proxy['username']}:{proxy['password']}\n"
                # Write the formatted string to the file
                f.write(proxy_entry)
        logging.info("Proxies saved to proxies.txt")
    except Exception as e:
        logging.error(f"Error getting proxies: {e}")

master_webshare_get_proxies()