from pydantic import BaseSettings
from functools import lru_cache
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
    PROXY_UPDATE_INTERVAL: int = 3600
    PROXY_MAX_FAILURES: int = 3
    PROXY_TIMEOUT: int = 30
    
    # Runner Settings
    RUNNER_TIMEOUT: int = 30
    RUNNER_REGISTRATION_RETRY: int = 5
    
    # Health Check Settings
    HEALTH_CHECK_INTERVAL: int = 60
    
    model_config = ConfigDict(
        case_sensitive=True,
        extra="ignore"
    )

@lru_cache()
def get_settings() -> Settings:
    env = os.getenv("ENV", "development")
    return Settings(_env_file=f".env.{env}") 