import functools
import logging
from src.database.mem_db import update_task_status  
from src.scraping.schemas import TaskStatus

logger = logging.getLogger(__name__)

# Decorator to monitor scraping tasks
def task_monitor(func):
    @functools.wraps(func)
    async def wrapper(self, task_id: str, request, *args, **kwargs):
        # request -  argument that contains the scraping request details
        
        logger.info(f"Task {task_id}: Started processing query='{request.query}'")
        
        try:
            await update_task_status(task_id, TaskStatus.in_progress)
            
            # Original function call
            result = await func(self, task_id, request, *args, **kwargs)
            
            await update_task_status(task_id, TaskStatus.completed, result=result)
            logger.info(f"Task {task_id}: Completed successfully")
            return result

        except (TimeoutError, ConnectionError) as e:
            error_msg = f"Network error: {str(e)}"
            logger.warning(f"Task {task_id}: {error_msg}")
            await update_task_status(task_id, TaskStatus.failed, error_message=error_msg)

        except Exception as e:
            logger.exception(f"Task {task_id}: CRITICAL FAILURE")
            await update_task_status(task_id, TaskStatus.failed, error_message=f"Internal error: {str(e)}")
            raise e
    return wrapper