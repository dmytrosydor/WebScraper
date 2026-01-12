from typing import Optional, Any, List
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

class MovieShort(BaseModel):
    title: str
    link: HttpUrl

class MovieDetails(BaseModel):
    title: str
    original_title: Optional[str]
    year: Optional[int]
    rating: Optional[float]
    genres: List[str] = []
    countries: List[str] =[]
    duration_minutes: Optional[int] = None
    description: Optional[str] = None
    production_studios: List[str] = []
    actors: List[str] = []
    poster_url: Optional[str] = None
    kinorium_url: HttpUrl


class ScrapeRequest(BaseModel):
    query: str
    mode: ScrapingMode

    
class ScrapeResponse(BaseModel):
    task_id: str
    status: TaskStatus
    result: Optional[List[Any]] = None
    error_message: Optional[str] = None
