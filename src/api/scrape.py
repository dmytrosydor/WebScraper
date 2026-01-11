from fastapi import APIRouter, HTTPException
from src.scraping.schemas import ScrapeRequest, ScrapeResponse
from src.scraping.services.scraping_service import ScrapingService

router = APIRouter(tags=["scrape"])

scraping_service = ScrapingService()

@router.post("/scrape", response_model=ScrapeResponse)
async def scrape_data(request: ScrapeRequest):
    return await scraping_service.start(request)


# Get status of a scraping task
@router.get("/scrape/{task_id}", response_model=ScrapeResponse)
async def get_scrape_status(task_id: str):
    task =  await scraping_service.get_status(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    return task
