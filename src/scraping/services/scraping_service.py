import logging
import asyncio
import uuid
from src.scraping.schemas import ScrapeRequest, ScrapeResponse, ScrapingMode, TaskStatus
from src.storage.mem_db import save_task, get_task, update_task_status
from src.scraping.parsers.kinorium import KinoriumParser

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


    async def _process_scraping(self, task_id: str, request: ScrapeRequest):
        logger.info(f"Processing scraping task ID: {task_id} for query: {request.query}")
        try:
            await update_task_status(task_id, TaskStatus.in_progress)

            if request.mode == ScrapingMode.http:
                result = await self.parser.scrape_by_genre(request.query)
            else:
                logger.warning(f"Task {task_id}: Unsupported scraping mode: {request.mode}")
                raise ValueError("Unsupported scraping mode: {request.mode}")

            await update_task_status(
                task_id,
                TaskStatus.completed,
                result=result
            )
            logger.info(f"Task {task_id} completed successfully")

        except TimeoutError as e:
            logger.error(f"Task {task_id} failed due to timeout: {str(e)}")
            await update_task_status(
                task_id,
                TaskStatus.failed,
                error_message=f"Timeout: {str(e)}"
            )

        except ConnectionError as e:
            logger.error(f"Task {task_id} failed due to connection error: {str(e)}")
            await update_task_status(
                task_id,
                TaskStatus.failed,
                error_message=f"Connection error: {str(e)}"
            )
        
        except Exception as e:
            logger.error(f"Task {task_id} failed with error: {str(e)}")
            await update_task_status(
                task_id,
                TaskStatus.failed,
                error_message=f"Error: {str(e)}"
            )
            
