from pydantic_settings import BaseSettings
from functools import lru_cache
import multiprocessing
import os
from pydantic import ConfigDict

class Settings(BaseSettings):
    # Environment
    ENV: str = "development"
    DEBUG: bool = True
    
    # API Settings
    AUTH_TOKEN: str
    HOST: str = "0.0.0.0"
    PORT: int = 8080
    
    # Proxy Settings
    WEBSHARE_TOKEN: str
    PROXY_UPDATE_INTERVAL: int = 3600  # seconds
    
    # Scraper Settings
    MAX_WORKERS: int = multiprocessing.cpu_count() * 2
    SCRAPER_TIMEOUT: int = 30
    CACHE_TTL: int = 14400
    CACHE_MAX_SIZE: int = 32
    
    # File Paths
    PROXIES_FILE: str = "app/static/proxies.txt"
    SCRAPER_FILE: str = "app/static/scraper.txt"
    
    model_config = ConfigDict(
        env_file=f".env.{os.getenv('ENV', 'development')}",
        case_sensitive=True
    )

@lru_cache()
def get_settings() -> Settings:
    return Settings() 