from pydantic import BaseModel
from typing import Tuple, Optional

class ScrapeRequest(BaseModel):
    url: str
    stealth: bool = False
    render: bool = False
    parse: bool = True

class ScrapeResponse(BaseModel):
    url: str
    stealth: bool
    render: bool
    parse: bool
    proxy_used: str
    runner_used: str
    method_used: str
    content: dict
