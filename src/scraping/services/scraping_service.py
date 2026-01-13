import functools
import logging
import asyncio
import uuid
from src.scraping.schemas import ScrapeRequest, ScrapeResponse, ScrapingMode, TaskStatus
from src.database.mem_db import save_task, get_task, update_task_status
from src.scraping.parsers.headless_pareser import KinoriumHeadlessParser
from src.scraping.parsers.http_parser import KinoriumHttpParser
from src.scraping.parsers.ui_parser import KinoriumUIParser 
from src.utils.decorators import task_monitor

logger = logging.getLogger(__name__)

class ScrapingService:

    def __init__(self):
        self.parsers = {
            ScrapingMode.http: KinoriumHttpParser(),
            ScrapingMode.headless: KinoriumHeadlessParser(),
            ScrapingMode.ui: KinoriumUIParser(),
        }

    async def start(self, request):
        raw_uuid = str(uuid.uuid4())
        task_id = f"{request.mode.value}_{raw_uuid}" # just for easier identification

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
            logger.warning(f"Client requested non-existent task_id: {task_id}")
            return None

        return ScrapeResponse(
            task_id=task["task_id"],
            status=task["status"],
            result=task.get("result"),
            error_message=task.get("error_message")
        )



    @task_monitor
    async def _process_scraping(self, task_id: str, request: ScrapeRequest):
        parser = self.parsers.get(request.mode)
        if not parser:
            raise ValueError(f"No parser found for mode: {request.mode}")

        return await parser.parse(request.query)
