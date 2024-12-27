from pydantic import BaseModel, HttpUrl

class ScrapeRequest(BaseModel):
    url: HttpUrl
    stealth: bool = False
    render: bool = False
    parse: bool = True 