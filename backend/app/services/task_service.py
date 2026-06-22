from backend.app.schemas.task import TaskCreate


class TaskService:
    def create_task(self, payload: TaskCreate) -> dict[str, object]:
        # TODO: 持久化 Task，并投递 backend.app.workers.tasks.execute_operation_task。
        return payload.model_dump()
