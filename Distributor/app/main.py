from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
import os
import asyncio
import logging
from contextlib import asynccontextmanager

from .config.logging_config import setup_logging
from .services.proxy_manager import ProxyManager
from .services.runner_manager import RunnerManager
from .db.session import init_db, get_db_connection
from .api.routes import api_router
from .core.security import token_required
from .db.crud.events import store_event
from .services.maintenance import MaintenanceService

# Setup logging first
setup_logging()
logger = logging.getLogger(__name__)

# Add constants at top of file
HEALTH_CHECK_INTERVAL = 30  # seconds
MAX_FAILED_CHECKS = 3  # number of failed checks before deregistration

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    # Initialize database
    init_db()
    
    # Initialize managers
    app.state.runner_manager = RunnerManager()
    app.state.proxy_manager = ProxyManager()
    
    # Log startup event
    store_event({
        "title": "System startup",
        "description": "ScrapeEngine Distributor has started",
        "event_type": "system",
        "severity": "info",
        "details": {
            "version": "1.0.0",
            "environment": os.getenv("ENVIRONMENT", "development")
        }
    })
    
    logger.info("Application startup complete")
    
    # Start maintenance service
    maintenance_service = MaintenanceService()
    asyncio.create_task(maintenance_service.start())
    
    yield
    
    # Log shutdown event
    store_event({
        "title": "System shutdown",
        "description": "ScrapeEngine Distributor is shutting down",
        "event_type": "system",
        "severity": "info",
        "details": {
            "active_runners": len(app.state.runner_manager.runners),
            "available_proxies": len(app.state.proxy_manager.available_proxies)
        }
    })
    
    logger.info("Application shutdown complete")

app = FastAPI(
    title="ScrapeEngine Distributor",
    description="Distributed web scraping service with proxy rotation",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("FRONTEND_URL", "http://localhost:3000")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include all routes
app.include_router(api_router)

@app.get("/health")
async def health_check(authorization: str = Depends(token_required)):
    """Internal health check endpoint that requires authentication"""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "active_runners": len(app.state.runner_manager.runners),
        "available_proxies": len(app.state.proxy_manager.available_proxies),
        "runner_ids": list(app.state.runner_manager.runners.keys())
    }

@app.get("/health/public")
async def public_health_check():
    """Public health check endpoint that doesn't require authentication"""
    return {
        "status": "healthy",
        "version": "1.0.0"
    }
