from fastapi import Request
from ..services.proxy_manager import ProxyManager
from ..services.runner_manager import RunnerManager

def get_proxy_manager(request: Request) -> ProxyManager:
    """Get the proxy manager from the app state"""
    return request.app.state.proxy_manager

def get_runner_manager(request: Request) -> RunnerManager:
    """Get the runner manager from the app state"""
    return request.app.state.runner_manager 