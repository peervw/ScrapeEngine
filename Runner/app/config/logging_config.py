import logging
import sys
import os

def setup_logging():
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)

    is_debug = os.getenv('DEBUG', 'false').lower() == 'true'
    
    logging.basicConfig(
        level=logging.DEBUG if is_debug else logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        stream=sys.stdout
    )

    if is_debug:
        logging.getLogger("uvicorn").setLevel(logging.DEBUG)
        logging.getLogger("fastapi").setLevel(logging.DEBUG)
        logging.getLogger("aiohttp").setLevel(logging.DEBUG)
    else:
        logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
        logging.getLogger("uvicorn.error").setLevel(logging.WARNING)
        logging.getLogger("fastapi").setLevel(logging.WARNING)
        logging.getLogger("aiohttp").setLevel(logging.WARNING)
        
        # Filter access logs
        uvicorn_access = logging.getLogger("uvicorn.access")
        class APIFilter(logging.Filter):
            def filter(self, record):
                # Only show logs for non-health endpoints
                return record.args and (
                    not record.args[2].endswith("/health") and
                    not record.args[2].endswith("/health/public")
                )
        uvicorn_access.addFilter(APIFilter())