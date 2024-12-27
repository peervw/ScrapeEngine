from fastapi import APIRouter, Depends
from ...core.security import token_required
from ..dependencies import get_runner_manager
from ...services.runner_manager import RunnerManager
import psutil

router = APIRouter(prefix="/api/metrics", tags=["metrics"])

@router.get("")
async def get_system_metrics(
    runner_manager: RunnerManager = Depends(get_runner_manager),
    authorization: str = Depends(token_required)
):
    """Get system-wide metrics"""
    return {
        "cpu_usage": psutil.cpu_percent(),
        "memory_usage": {
            "used": psutil.virtual_memory().used // (1024 * 1024),  # Convert to MB
            "total": psutil.virtual_memory().total // (1024 * 1024)  # Convert to MB
        },
        "disk_usage": {
            "used": psutil.disk_usage('/').used // (1024 * 1024),  # Convert to MB
            "total": psutil.disk_usage('/').total // (1024 * 1024)  # Convert to MB
        },
        "network": {
            "active_connections": len(runner_manager.runners),
            "throughput": 0.0,  # This would come from actual network monitoring
            "latency": 0.0  # This would come from actual network monitoring
        }
    }