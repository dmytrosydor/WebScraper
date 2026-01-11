from pprint import pprint

tasks_db = {}


async def save_task(task_id: str, task_data: dict):
    tasks_db[task_id] = task_data
    print("\n[SAVE TASK]")
    pprint(tasks_db, width=120)


async def get_task(task_id: str):
    print("\n[GET TASK]")
    pprint(tasks_db, width=120)
    return tasks_db.get(task_id)


async def update_task_status(task_id: str, status: str, result=None, error_message=None):
    task = tasks_db.get(task_id)
    if task:
        task['status'] = status
        if result is not None:
            task['result'] = result
        if error_message is not None:
            task['error_message'] = error_message

        tasks_db[task_id] = task

        print("\n[UPDATE TASK]")
        pprint(tasks_db, width=120)




