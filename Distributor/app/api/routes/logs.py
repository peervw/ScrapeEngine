from fastapi import APIRouter, HTTPException, Depends, Query
from ...core.security import token_required
from ...db.crud import logs as logs_crud

router = APIRouter(prefix="/api/logs", tags=["logs"])

@router.get("")
async def get_scrape_logs(
    authorization: str = Depends(token_required), 
    limit: int = Query(50, ge=1, le=1000),
    offset: int = Query(0, ge=0)
):
    """Get recent scraping logs with pagination"""
    return logs_crud.get_logs(limit, offset)

@router.delete("")
async def delete_all_logs(authorization: str = Depends(token_required)):
    """Delete all scraping logs from the database"""
    try:
        logs_crud.delete_all_logs()
        return {"status": "success", "message": "All logs deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to delete logs")

@router.delete("/{log_id}")
async def delete_log(log_id: int, authorization: str = Depends(token_required)):
    """Delete a specific log entry by ID"""
    try:
        if logs_crud.delete_log(log_id):
            return {"status": "success", "message": f"Log {log_id} deleted successfully"}
        raise HTTPException(status_code=404, detail="Log entry not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to delete log") 