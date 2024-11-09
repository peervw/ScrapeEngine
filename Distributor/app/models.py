from pydantic import BaseModel
from typing import Tuple, Optional

class ScrapeRequest(BaseModel):
    url: str
    full_content: str
    stealth: Optional[bool] = False
    cache: Optional[bool] = True

class ScrapeResponse(BaseModel):
    url: str
    full_content: str
    stealth: bool
    cache: bool
    content: dict
    proxy_used: str
    runner_used: str