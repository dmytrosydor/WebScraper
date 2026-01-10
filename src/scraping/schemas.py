from typing import Optional, Any
from pydantic import BaseModel, HttpUrl
from enum import Enum


class ScrapingMode(str, Enum):
    http = "http"         # Search by film
    headless = "headless" # Film details
    ui = "ui"             # Open browser

    
class TaskStatus(str, Enum):
    in_progress = "in_progress"
    pending = "pending"
    failed = "failed"
    completed = "completed"


class ScrapeRequest(BaseModel):
    query: str
    mode: ScrapingMode

    
class ScrapeResponse(BaseModel):
    task_id: str
    status: TaskStatus
    result: Optional[Any] = None
    error_message: Optional[str] = None