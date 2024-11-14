import logging
import sys
import os

def setup_logging():
    # Remove all handlers associated with the root logger object
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)

    # Get log level from environment variable
    is_debug = os.getenv('DEBUG', 'false').lower() == 'true'
    
    # Base configuration
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        stream=sys.stdout
    )

    if is_debug:
        # Debug mode - verbose logging
        logging.getLogger("uvicorn").setLevel(logging.DEBUG)
        logging.getLogger("fastapi").setLevel(logging.DEBUG)
        logging.getLogger("aiohttp").setLevel(logging.DEBUG)
    else:
        # Production mode - minimal logging but keep API logs
        logging.getLogger("uvicorn.access").setLevel(logging.INFO)
        logging.getLogger("uvicorn.error").setLevel(logging.WARNING)
        logging.getLogger("fastapi").setLevel(logging.WARNING)
        logging.getLogger("aiohttp").setLevel(logging.WARNING)
        
        # Keep app-specific loggers at INFO
        logging.getLogger("app").setLevel(logging.INFO)
        
        # Custom filter for access logs
        uvicorn_access = logging.getLogger("uvicorn.access")
        class APIFilter(logging.Filter):
            def filter(self, record):
                return record.args and (
                    not record.args[2].endswith("/health") and
                    not record.args[2].endswith("/health/public")
                )
        uvicorn_access.addFilter(APIFilter())