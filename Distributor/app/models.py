from pydantic import BaseModel
from typing import Tuple, Optional, Literal

class ScrapeRequest(BaseModel):
    url: str
    method: Optional[Literal["aiohttp", "playwright"]] = "aiohttp"
    full_content: Optional[bool] = False
    stealth: Optional[bool] = False
    cache: Optional[bool] = True
    parse: Optional[bool] = True

class ScrapeResponse(BaseModel):
    url: str
    method: str
    full_content: bool
    stealth: bool
    cache: bool
    parse: bool
    proxy_used: str
    runner_used: str
    content: dict
