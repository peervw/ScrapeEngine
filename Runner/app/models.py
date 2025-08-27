from pydantic import BaseModel
from typing import Dict, Any, Optional, Literal

class ScrapeRequest(BaseModel):
    url: str
    method: Optional[Literal["aiohttp", "playwright"]] = "aiohttp"
    full_content: Optional[bool] = False
    stealth: Optional[bool] = False
    parse: Optional[bool] = True
    infinite_scroll: Optional[bool] = False
    scroll_count: Optional[int] = 5
    
    class Config:
        extra = "ignore"