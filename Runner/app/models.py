from pydantic import BaseModel, HttpUrl
from typing import Tuple, Optional, Dict, Any, Literal

class ScrapeRequest(BaseModel):
    url: HttpUrl
    stealth: bool = False     # Enable stealth mode
    render: bool = False      # Use Playwright when True
    parse: bool = True       # Parse the content
    proxy: Tuple[str, str, str, str]
    headers: Optional[Dict[str, str]] = None