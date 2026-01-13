import logging
import json
import aiofiles
from pathlib import Path


DATA_DIR = Path("storage")
(DATA_DIR / "http").mkdir(parents=True, exist_ok=True)
(DATA_DIR / "headless").mkdir(parents=True, exist_ok=True)
(DATA_DIR / "ui").mkdir(parents=True, exist_ok=True)

logger = logging.getLogger(__name__)

async def _get_file_path(task_id: str) -> Path:
    
    try:
        mode, _ = task_id.split("_", 1)
    except ValueError:
        return DATA_DIR / f"{task_id}.json"


    if mode in ["http", "headless", "ui"]:
        return DATA_DIR / mode / f"{task_id}.json"
    
    return DATA_DIR / f"{task_id}.json"


def json_serializer(obj):
    if hasattr(obj, 'model_dump'):
        return obj.model_dump()
    if hasattr(obj, 'dict'):
        return obj.dict()
    return str(obj)

async def save_task(task_id: str, task_data: dict):
    file_path = await _get_file_path(task_id)
    async with aiofiles.open(file_path, mode='w', encoding='utf-8') as f:
        await f.write(json.dumps(task_data, default=json_serializer, indent=4, ensure_ascii=False))

async def get_task(task_id: str):
    file_path = await _get_file_path(task_id)
    if not file_path.exists():
        return None
    
    async with aiofiles.open(file_path, mode='r', encoding='utf-8') as f:
        content = await f.read()
        return json.loads(content)

async def update_task_status(task_id: str, status: str, result=None, error_message=None):
    current_data = await get_task(task_id)
    if not current_data:
        logger.error(f"Task {task_id} not found in DB during update attempt")
        return
    
    current_data['status'] = status
    if result is not None:
        current_data['result'] = result
    if error_message is not None:
        current_data['error_message'] = error_message

    await save_task(task_id, current_data)

