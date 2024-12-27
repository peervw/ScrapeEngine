from fastapi import APIRouter, Depends, Query
from ...core.security import token_required
from ...db.crud import events as events_crud
from typing import Optional

router = APIRouter(prefix="/api/events", tags=["events"])

@router.get("")
async def get_system_events(
    authorization: str = Depends(token_required),
    limit: int = Query(50, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    event_type: Optional[str] = None
):
    """Get recent system events with pagination and filtering"""
    return events_crud.get_events(limit, offset, event_type) 