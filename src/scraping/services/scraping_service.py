import functools
import logging
import asyncio
import uuid
from src.scraping.schemas import ScrapeRequest, ScrapeResponse, ScrapingMode, TaskStatus
from src.database.mem_db import save_task, get_task, update_task_status
from src.scraping.parsers.kinorium import KinoriumParser
from src.utils.decorators import task_monitor

logger = logging.getLogger(__name__)

class ScrapingService:

    def __init__(self):
        self.parser = KinoriumParser()

    async def start(self, request):
        task_id = str(uuid.uuid4())

        logger.info(f"Created a new scraping task with ID: {task_id}, for query: {request.query}")
        
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
        

    async def get_status(self, task_id: str) -> ScrapeResponse | None:
        task = await get_task(task_id)
        if not task:
            return None

        return ScrapeResponse(
            task_id=task["task_id"],
            status=task["status"],
            result=task.get("result"),
            error_message=task.get("error_message")
        )



    @task_monitor
    async def _process_scraping(self, task_id: str, request: ScrapeRequest):
        if request.mode == ScrapingMode.http:
            return await self.parser.scrape_by_genre(request.query)
        
        elif request.mode == ScrapingMode.headless:
            return await self.parser.scrape_movie_details(request.query)
        
        else:
            # Якщо кинути помилку тут, декоратор її зловить і запише в БД
            raise ValueError(f"Unsupported scraping mode: {request.mode}")
