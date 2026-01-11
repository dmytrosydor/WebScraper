import asyncio
import uuid
from src.scraping.schemas import ScrapeRequest, ScrapeResponse, ScrapingMode, TaskStatus
from src.storage.mem_db import save_task, get_task, update_task_status
from src.scraping.parsers.kinorium import KinoriumParser

class ScrapingService:

    def __init__(self):
        self.parser = KinoriumParser()

    async def start(self, request):
        task_id = str(uuid.uuid4())
        
        # 1. Створюємо об'єкт задачі
        task_data = {
            "task_id": task_id,
            "status": TaskStatus.pending,
            "mode": request.mode,
            "query": request.query
        }
        
        await save_task(task_id, task_data) 

        asyncio.create_task(self._process_scraping(task_id, request))

        return ScrapeResponse(
            task_id=task_id,
            status=TaskStatus.pending
        )
        

    async def get_status(self, task_id: str):
        task = await get_task(task_id)
        if task: 
            return task

    async def _process_scraping(self, task_id: str, request: ScrapeRequest):
        try:
            await update_task_status(task_id, TaskStatus.in_progress)

            if request.mode == ScrapingMode.http:
                result = await self.parser.scrape_by_genre(request.query)
            else:
                raise ValueError("Unsupported scraping mode")

            await update_task_status(
                task_id,
                TaskStatus.completed,
                result=result
            )

        except Exception as e:
            await update_task_status(
                task_id,
                TaskStatus.failed,
                error_message=str(e)
            )
