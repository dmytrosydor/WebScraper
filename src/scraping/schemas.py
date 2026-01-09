from pydantic import BaseModel, HttpUrl
from enum import Enum


class ScrapingMode(str, Enum):
    http = "http"
    headless = "headless"
    ui = "ui"

    
class ScrapeRequest(BaseModel):
    url: HttpUrl
    mode: ScrapingMode

    
class ScrapeResponse(BaseModel):
    task_id: str
    status: str