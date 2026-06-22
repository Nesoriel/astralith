from backend.app.core.database import SessionLocal
from backend.app.services.task_service import TaskService
from backend.app.workers.celery_app import celery_app


@celery_app.task(name="astralith.execute_operation_task")
def execute_operation_task(task_id: int) -> dict[str, int | str]:
    """Celery 异步任务入口。"""
    db = SessionLocal()
    try:
        task = TaskService(db).execute_task(task_id)
        return {"task_id": task.id, "status": task.status}
    finally:
        db.close()
