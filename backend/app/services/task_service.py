import json
from datetime import datetime, timezone
from typing import Any, cast

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from backend.app.models.host import Host, HostGroup, HostGroupMember
from backend.app.models.task import Task, TaskResult
from backend.app.operation_modules.registry import registry
from backend.app.schemas.task import TargetType, TaskCreate, TaskRead, TaskResultRead, TaskStatus
from backend.app.services.ansible_service import AnsibleExecutionResult, AnsibleService


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

    def execute_task(self, task_id: int) -> Task:
        """执行任务并保存每台主机的结果。"""
        task = self.get_task(task_id)
        if task is None:
            raise ValueError("Task not found")
        if task.status not in {"pending", "running"}:
            return task

        started_at = datetime.now(timezone.utc)
        task.status = "running"
        task.started_at = started_at
        task.finished_at = None
        self.db.execute(delete(TaskResult).where(TaskResult.task_id == task.id))
        self.db.commit()

        hosts = self._resolve_target_hosts(task)
        try:
            module_task = self._get_operation_task(task.module_key, task.module_task_key)
            parameters = json.loads(task.parameters_json or "{}")
            playbook = module_task.build_playbook(parameters)
            inventory = AnsibleService.build_inventory(hosts)
            result = AnsibleService().run_module_task(inventory, playbook)
            final_status = self._persist_host_results(task, hosts, result, started_at)
            task.status = final_status
        except Exception as exc:
            task.status = "failed"
            self.db.add(
                TaskResult(
                    task_id=task.id,
                    host_id=None,
                    status="failed",
                    stdout="",
                    stderr=str(exc),
                    raw_event_data=serialize_json({"error": str(exc)}),
                    started_at=started_at,
                    finished_at=datetime.now(timezone.utc),
                )
            )
        finally:
            task.finished_at = datetime.now(timezone.utc)
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
        self._get_operation_task(module_key, task_key)

    def _validate_targets(self, target_type: str, target_ids: list[int]) -> None:
        """校验任务目标是否存在。"""
        model: type[Host] | type[HostGroup]
        model = Host if target_type == "hosts" else HostGroup
        found_ids = set(self.db.scalars(select(model.id).where(model.id.in_(target_ids))))
        missing_ids = set(target_ids) - found_ids
        if missing_ids:
            raise ValueError(f"Target ids not found: {sorted(missing_ids)}")

    def _get_operation_task(self, module_key: str, task_key: str) -> Any:
        """查找内置模块任务定义。"""
        module = registry.get_module(module_key)
        operation_task = module.get_task(task_key) if module is not None else None
        if operation_task is None:
            raise ValueError("Operation module task not found")
        return operation_task

    def _resolve_target_hosts(self, task: Task) -> list[Host]:
        """根据任务目标类型解析主机列表。"""
        target_ids = json.loads(task.target_ids_json)
        if task.target_type == "hosts":
            statement = select(Host).where(Host.id.in_(target_ids)).order_by(Host.id)
        else:
            statement = (
                select(Host)
                .join(HostGroupMember, HostGroupMember.host_id == Host.id)
                .where(HostGroupMember.group_id.in_(target_ids))
                .order_by(Host.id)
            )
        hosts = list(self.db.scalars(statement).unique())
        if not hosts:
            raise ValueError("Task has no target hosts")
        return hosts

    def _persist_host_results(
        self,
        task: Task,
        hosts: list[Host],
        result: AnsibleExecutionResult,
        started_at: datetime,
    ) -> str:
        """按主机保存结果并返回任务最终状态。"""
        host_statuses = _extract_host_statuses(result.raw_events)
        statuses: list[str] = []
        finished_at = datetime.now(timezone.utc)
        for host in hosts:
            host_status = host_statuses.get(host.name, _status_from_runner(result.status))
            statuses.append(host_status)
            self.db.add(
                TaskResult(
                    task_id=task.id,
                    host_id=host.id,
                    status=host_status,
                    stdout=result.stdout,
                    stderr=result.stderr,
                    raw_event_data=serialize_json(result.raw_events),
                    started_at=started_at,
                    finished_at=finished_at,
                )
            )
        return _aggregate_task_status(statuses)


def _extract_host_statuses(events: list[dict[str, Any]]) -> dict[str, str]:
    """从 Runner 事件中提取每台主机的执行状态。"""
    statuses: dict[str, str] = {}
    for event in events:
        event_name = str(event.get("event", ""))
        event_data = event.get("event_data") or {}
        host = event_data.get("host")
        if not host:
            continue
        if event_name in {"runner_on_ok", "runner_on_skipped"}:
            statuses[str(host)] = "success"
        elif event_name in {"runner_on_failed", "runner_on_unreachable"}:
            statuses[str(host)] = "failed"
    return statuses


def _status_from_runner(status: str) -> str:
    """把 Runner 总体状态映射为单主机结果状态。"""
    return "success" if status in {"successful", "success"} else "failed"


def _aggregate_task_status(statuses: list[str]) -> str:
    """根据多主机结果聚合任务状态。"""
    if statuses and all(status == "success" for status in statuses):
        return "success"
    if any(status == "success" for status in statuses) and any(status != "success" for status in statuses):
        return "partial_success"
    return "failed"


def serialize_json(value: Any) -> str:
    """序列化 JSON 字段，保留中文内容方便日志与演示查看。"""
    return json.dumps(value, ensure_ascii=False)
