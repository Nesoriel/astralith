from typing import cast

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.api.routes.auth import get_current_user
from backend.app.core.database import get_db
from backend.app.models.task import Task
from backend.app.operation_modules.base import LocalizedText
from backend.app.operation_modules.registry import registry
from backend.app.schemas.operation_module import (
    LocalizedTextRead,
    OperationModuleRead,
    OperationModuleTaskCreateRequest,
    OperationPlaybookPreviewRead,
    OperationPlaybookPreviewRequest,
    OperationTaskRead,
)
from backend.app.schemas.task import TargetType, TaskCreate, TaskRead
from backend.app.services.task_service import TaskService
from backend.app.workers.tasks import execute_operation_task

router = APIRouter()


def get_task_service(db: Session = Depends(get_db)) -> TaskService:
    """构造任务服务。"""
    return TaskService(db)


def _localized_text_to_schema(text: LocalizedText) -> LocalizedTextRead:
    """把内部双语文本转换为 API 响应模型。"""
    return LocalizedTextRead.model_validate({"zh-CN": text.zh_CN, "en-US": text.en_US})


def _module_to_schema(module_key: str) -> OperationModuleRead:
    """把内部模块对象转换为 API 响应模型。"""
    module = registry.get_module(module_key)
    if module is None:
        raise HTTPException(status_code=404, detail="Operation module not found")
    return OperationModuleRead(
        module_key=module.module_key,
        name=_localized_text_to_schema(module.name),
        description=_localized_text_to_schema(module.description),
        tasks=[
            OperationTaskRead(
                task_key=task.task_key,
                name=_localized_text_to_schema(task.name),
                description=_localized_text_to_schema(task.description),
                parameters=task.parameters,
            )
            for task in module.tasks
        ],
    )


@router.get("", response_model=list[OperationModuleRead])
def list_operation_modules() -> list[OperationModuleRead]:
    """列出所有内置运维模块，用于前端任务选择页面。"""
    return [_module_to_schema(module.module_key) for module in registry.list_modules()]


@router.get("/{module_key}", response_model=OperationModuleRead)
def get_operation_module(module_key: str) -> OperationModuleRead:
    """查看单个内置运维模块详情。"""
    return _module_to_schema(module_key)


@router.post("/{module_key}/tasks/{task_key}/preview-playbook", response_model=OperationPlaybookPreviewRead)
def preview_task_playbook(
    module_key: str,
    task_key: str,
    payload: OperationPlaybookPreviewRequest,
    _current_user = Depends(get_current_user),
) -> OperationPlaybookPreviewRead:
    """预览模块任务生成的受控 Ansible Playbook。"""
    task = _get_operation_task(module_key, task_key)
    try:
        playbook = task.build_playbook(payload.parameters)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return OperationPlaybookPreviewRead(module_key=module_key, task_key=task_key, parameters=payload.parameters, playbook=playbook)


@router.get("/{module_key}/recent-tasks", response_model=list[TaskRead])
def list_module_recent_tasks(
    module_key: str,
    service: TaskService = Depends(get_task_service),
) -> list[TaskRead]:
    """查看某个模块最近执行任务。"""
    statement = select(Task).where(Task.module_key == module_key).order_by(Task.id.desc()).limit(10)
    return [service.task_to_schema(task) for task in service.db.scalars(statement)]


@router.post("/{module_key}/tasks/{task_key}/create-task", response_model=TaskRead, status_code=status.HTTP_202_ACCEPTED)
def create_module_task(
    module_key: str,
    task_key: str,
    payload: OperationModuleTaskCreateRequest,
    _current_user = Depends(get_current_user),
    service: TaskService = Depends(get_task_service),
) -> TaskRead:
    """从模块工作台快捷创建执行任务。"""
    _get_operation_task(module_key, task_key)
    try:
        task = service.create_task(TaskCreate(
            name=payload.name,
            module_key=module_key,
            module_task_key=task_key,
            target_type=cast(TargetType, payload.target_type),
            target_ids=payload.target_ids,
            parameters=payload.parameters,
        ))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    dispatch_task(task.id)
    return service.task_to_schema(task)


def dispatch_task(task_id: int) -> None:
    """投递模块快捷任务，保持测试可替换边界。"""
    cast(object, execute_operation_task).delay(task_id)  # type: ignore[attr-defined]


def _get_operation_task(module_key: str, task_key: str):
    """读取内置模块任务。"""
    module = registry.get_module(module_key)
    operation_task = module.get_task(task_key) if module is not None else None
    if operation_task is None:
        raise HTTPException(status_code=404, detail="Operation module task not found")
    return operation_task
