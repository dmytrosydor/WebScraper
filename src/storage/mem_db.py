
tasks_db = {}

def save_task(task_id: str, task_data: dict):
    tasks_db[task_id] = task_data
    
# def get_task(task_id: str) -> dict:
#     if task_id in tasks_db:
#         return tasks_db.get(task_id)
#     return None

    
# def update_task_status(task_id: str,status:str, result: any = None, error_message: str = None):
#     if task_id in tasks_db:
#         tasks_db[task_id]['status'] = status
#         if result is not None:
#             tasks_db[task_id]['result'] = result
#         if error_message is not None:
#             tasks_db[task_id]['error_message'] = error_message