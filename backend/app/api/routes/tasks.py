from fastapi import APIRouter, status

from backend.app.schemas.task import TaskCreate

router = APIRouter()


@router.post("", status_code=status.HTTP_202_ACCEPTED)
def create_task(payload: TaskCreate) -> dict[str, object]:
    """创建执行任务的占位接口。

    后续完整实现时，这里应当：
    1. 校验内置模块与任务是否存在；
    2. 创建 pending 状态的 Task 记录；
    3. 投递 Celery 异步任务；
    4. 立即返回任务信息，而不是阻塞等待 Ansible 执行结束。
    """
    return {
        "message": "Task creation endpoint scaffolded. Persistence and Celery dispatch are pending.",
        "task": payload.model_dump(),
    }
