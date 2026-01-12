import functools
import logging
from src.database.mem_db import update_task_status  # Ваші функції оновлення БД
from src.scraping.schemas import TaskStatus

# Налаштовуємо логер (або імпортуємо готовий з config)
logger = logging.getLogger(__name__)

def task_monitor(func):
    """
    Декоратор для автоматичного логування та оновлення статусів задач.
    """
    @functools.wraps(func)
    async def wrapper(self, task_id: str, request, *args, **kwargs):
        # self тут є, бо ми декоруємо метод класу, але ми його не використовуємо
        # request - це аргумент функції, яку ми обгорнули
        
        logger.info(f"Task {task_id}: Started processing query='{request.query}'")
        
        try:
            await update_task_status(task_id, TaskStatus.in_progress)
            
            # Виклик оригінальної функції
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
            # Важливо: якщо треба, щоб сервіс знав про помилку далі - можна зробити raise e
            
    return wrapper