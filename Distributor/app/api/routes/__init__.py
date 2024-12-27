from fastapi import APIRouter
from .logs import router as logs_router
from .proxies import router as proxies_router
from .runners import router as runners_router
from .settings import router as settings_router
from .scrape import router as scrape_router
from .metrics import router as metrics_router
from .events import router as events_router

api_router = APIRouter()

api_router.include_router(logs_router)
api_router.include_router(proxies_router)
api_router.include_router(runners_router)
api_router.include_router(settings_router)
api_router.include_router(scrape_router)
api_router.include_router(metrics_router)
api_router.include_router(events_router) 