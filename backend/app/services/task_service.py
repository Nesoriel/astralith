import json
from typing import Any, cast

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models.host import Host, HostGroup
from backend.app.models.task import Task, TaskResult
from backend.app.operation_modules.registry import registry
from backend.app.schemas.task import TargetType, TaskCreate, TaskRead, TaskResultRead, TaskStatus


class TaskService:
    """任务业务服务。

    API 层只负责参数校验与响应封装，任务持久化和 Celery 投递应集中在这里。
    """

    def __init__(self, db: Session) -> None:
        self.db = db

    def list_tasks(self) -> list[Task]:
        """按创建顺序倒序返回任务列表。"""
        return list(self.db.scalars(select(Task).order_by(Task.id.desc())))

    def get_task(self, task_id: int) -> Task | None:
        """按 ID 查询任务。"""
        return self.db.get(Task, task_id)

    def list_results(self, task_id: int) -> list[TaskResult]:
        """返回任务下的全部执行结果。"""
        statement = select(TaskResult).where(TaskResult.task_id == task_id).order_by(TaskResult.id)
        return list(self.db.scalars(statement))

    def create_task(self, payload: TaskCreate) -> Task:
        """创建 pending 状态任务记录。"""
        self._validate_module_task(payload.module_key, payload.module_task_key)
        self._validate_targets(payload.target_type, payload.target_ids)
        task = Task(
            name=payload.name,
            module_key=payload.module_key,
            module_task_key=payload.module_task_key,
            status="pending",
            target_type=payload.target_type,
            target_ids_json=json.dumps(payload.target_ids),
            parameters_json=json.dumps(payload.parameters, ensure_ascii=False),
        )
        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)
        return task

    def task_to_schema(self, task: Task) -> TaskRead:
        """把 ORM 任务对象转换为前端友好的响应模型。"""
        status = cast(TaskStatus, task.status)
        target_type = cast(TargetType, task.target_type)
        return TaskRead(
            id=task.id,
            name=task.name,
            module_key=task.module_key,
            module_task_key=task.module_task_key,
            status=status,
            target_type=target_type,
            target_ids=json.loads(task.target_ids_json),
            parameters=json.loads(task.parameters_json or "{}"),
            created_at=task.created_at,
            updated_at=task.updated_at,
            started_at=task.started_at,
            finished_at=task.finished_at,
        )

    def result_to_schema(self, result: TaskResult) -> TaskResultRead:
        """把 ORM 任务结果转换为响应模型。"""
        return TaskResultRead.model_validate(result)

    def _validate_module_task(self, module_key: str, task_key: str) -> None:
        """校验内置模块与任务是否存在。"""
        module = registry.get_module(module_key)
        if module is None or module.get_task(task_key) is None:
            raise ValueError("Operation module task not found")

    def _validate_targets(self, target_type: str, target_ids: list[int]) -> None:
        """校验任务目标是否存在。"""
        model: type[Host] | type[HostGroup]
        model = Host if target_type == "hosts" else HostGroup
        found_ids = set(self.db.scalars(select(model.id).where(model.id.in_(target_ids))))
        missing_ids = set(target_ids) - found_ids
        if missing_ids:
            raise ValueError(f"Target ids not found: {sorted(missing_ids)}")


def serialize_json(value: Any) -> str:
    """序列化 JSON 字段，保留中文内容方便日志与演示查看。"""
    return json.dumps(value, ensure_ascii=False)
