from fastapi import APIRouter, HTTPException
from src.scraping.schemas import ScrapeRequest, ScrapeResponse, ScrapingMode
from src.scraping.services.scraping_service import ScrapingService
from src.config.scraping import GENRES_MAP
router = APIRouter(tags=["scrape"])

scraping_service = ScrapingService()

@router.post("/scrape", response_model=ScrapeResponse)
async def scrape_data(request: ScrapeRequest):
    if request.mode == ScrapingMode.http and request.query not in GENRES_MAP:
        available_genres = list(GENRES_MAP.keys())

        raise HTTPException(
            status_code=400,
            detail=f"Invalid genre '{request.query}'. Available genres: {available_genres}",
        )
    
    try:
        return await scraping_service.start(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error starting scraping task: {str(e)}")


# Get status of a scraping task  
@router.get("/scrape/{task_id}", response_model=ScrapeResponse)
async def get_scrape_status(task_id: str):
    task =  await scraping_service.get_status(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    return task
