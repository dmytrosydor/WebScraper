import uuid
from src.scraping.schemas import ScrapeRequest, ScrapeResponse

class ScrapingService:
    async def start(self, request):
        return {
            "task_id": str(uuid.uuid4()),
            "status": "pending"
        }