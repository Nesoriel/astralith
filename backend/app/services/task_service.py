from backend.app.schemas.task import TaskCreate


class TaskService:
    """任务业务服务。

    API 层只负责参数校验与响应封装，任务持久化和 Celery 投递应集中在这里。
    """

    def create_task(self, payload: TaskCreate) -> dict[str, object]:
        """创建任务记录并返回任务基础信息的临时骨架。"""

        # TODO: 持久化 Task，并投递 backend.app.workers.tasks.execute_operation_task。
        return payload.model_dump()
