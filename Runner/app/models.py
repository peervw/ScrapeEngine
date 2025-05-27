from pydantic import BaseModel, HttpUrl, Field, validator
from typing import Tuple, Optional, Dict, Any, Literal, Union

class ScrapeRequest(BaseModel):
    url: Union[HttpUrl, str]
    full_content: bool = True
    method: Literal["aiohttp", "playwright"] = "aiohttp"
    stealth: bool = False
    cache: bool = True
    parse: bool = True
    proxy: Optional[Tuple[str, str, str, str]] = None
    headers: Optional[Dict[str, str]] = None
        
    class Config:
        extra = "ignore"