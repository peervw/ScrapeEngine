from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class SystemEvent(BaseModel):
    id: int
    timestamp: datetime
    title: str
    description: str
    event_type: str
    severity: str  # info, warning, error
    details: Optional[dict] = None 