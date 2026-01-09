from fastapi import APIRouter
from src.scraping.schemas import ScrapeRequest, ScrapeResponse
from src.scraping.services.scraping_service import ScrapingService

router = APIRouter(tags=["scrape"])

scraping_service = ScrapingService()

@router.post("/scrape", response_model=ScrapeResponse)
async def scrape_data(request: ScrapeRequest):
    return await scraping_service.start(request)