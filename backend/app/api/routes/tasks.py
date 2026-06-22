from typing import Any, cast

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.schemas.task import TaskCreate, TaskLogsRead, TaskRead
from backend.app.services.task_service import TaskService
from backend.app.workers.tasks import execute_operation_task

router = APIRouter()


def get_task_service(db: Session = Depends(get_db)) -> TaskService:
    """构造任务服务，保持路由层薄。"""
    return TaskService(db)


@router.get("", response_model=list[TaskRead])
def list_tasks(service: TaskService = Depends(get_task_service)) -> list[TaskRead]:
    """列出执行任务。"""
    return [service.task_to_schema(task) for task in service.list_tasks()]


@router.post("", response_model=TaskRead, status_code=status.HTTP_202_ACCEPTED)
def create_task(
    payload: TaskCreate,
    service: TaskService = Depends(get_task_service),
) -> TaskRead:
    """创建 pending 状态执行任务。

    v0.1.0 先落库并返回任务记录；真实 Celery + Ansible Runner 执行在 v0.2.0 接入。
    """
    try:
        task = service.create_task(payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    dispatch_task(task.id)
    return service.task_to_schema(task)


def dispatch_task(task_id: int) -> None:
    """把任务投递给 Celery，隔离 Celery 动态 delay 属性。"""
    cast(Any, execute_operation_task).delay(task_id)


@router.get("/{task_id}", response_model=TaskRead)
def get_task(task_id: int, service: TaskService = Depends(get_task_service)) -> TaskRead:
    """读取单个执行任务。"""
    task = service.get_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return service.task_to_schema(task)


@router.get("/{task_id}/logs", response_model=TaskLogsRead)
def get_task_logs(task_id: int, service: TaskService = Depends(get_task_service)) -> TaskLogsRead:
    """读取任务详情与执行日志。"""
    task = service.get_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return TaskLogsRead(
        task=service.task_to_schema(task),
        results=[service.result_to_schema(result) for result in service.list_results(task_id)],
    )
