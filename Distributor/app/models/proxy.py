from pydantic import BaseModel
from typing import Optional

class ProxyCreate(BaseModel):
    host: str
    port: str
    username: Optional[str] = None
    password: Optional[str] = None

class WebshareToken(BaseModel):
    token: str

class ProxyStats(BaseModel):
    host: str
    port: str
    username: Optional[str] = None
    password: Optional[str] = None
    success_rate: float = 0.0
    average_response_time: float = 0.0
    last_used: Optional[str] = None
    total_requests: int = 0
    failed_requests: int = 0 