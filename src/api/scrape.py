from fastapi import APIRouter, HTTPException, Depends
from src.scraping.schemas import ScrapeRequest, ScrapeResponse
from src.scraping.services.scraping_service import ScrapingService

router = APIRouter(tags=["scrape"])


def get_scraping_service():
    return ScrapingService()

@router.post("/scrape", response_model=ScrapeResponse)
async def scrape_data(
    request: ScrapeRequest,
    
    service: ScrapingService = Depends(get_scraping_service)
):
    try:
        return await service.start(request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error starting scraping task: {str(e)}")

@router.get("/scrape/{task_id}", response_model=ScrapeResponse)
async def get_scrape_status(
    task_id: str,
    service: ScrapingService = Depends(get_scraping_service)
):
    task = await service.get_status(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task