import json
from types import SimpleNamespace
from typing import Any

from starlette.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models.host import Host, HostGroup, HostGroupMember
from backend.app.models.task import TaskResult
from backend.app.operation_modules.registry import registry
from backend.app.schemas.scheduled_job import ScheduledJobCreate
from backend.app.schemas.task import TaskCreate
from backend.app.services.ansible_service import AnsibleExecutionResult, AnsibleService
from backend.app.services.schedule_service import ScheduleService
from backend.app.services.task_service import TaskService, validate_task_status_transition
from backend.app.workers import tasks as worker_tasks


def test_system_inspection_tasks_generate_command_playbooks() -> None:
    """系统巡检模块任务应生成受控的 Ansible command playbook。"""
    module = registry.get_module("system_inspection")
    assert module is not None

    task = module.get_task("check_disk")
    assert task is not None

    playbook = task.build_playbook({})

    assert playbook == [
        {
            "name": "Run check_disk",
            "hosts": "all",
            "gather_facts": False,
            "tasks": [{"name": "check_disk", "ansible.builtin.command": "df -h"}],
        }
    ]


def test_service_manage_rejects_unsafe_service_name() -> None:
    """服务管理模块必须拒绝不安全的 systemd 服务名。"""
    module = registry.get_module("service_manage")
    assert module is not None
    task = module.get_task("service_status")
    assert task is not None

    try:
        task.build_playbook({"service_name": "nginx; rm -rf /"})
    except ValueError as exc:
        assert "service_name" in str(exc)
    else:
        raise AssertionError("unsafe service name should be rejected")


def test_ansible_service_builds_inventory_from_hosts() -> None:
    """AnsibleService 应把主机记录转换为 Runner 可用的 inventory。"""
    host = Host(
        id=1,
        name="demo",
        ip_address="192.0.2.10",
        ssh_port=2222,
        ssh_user="root",
        private_key_path="/tmp/demo-key",
    )

    inventory = AnsibleService.build_inventory([host])

    assert inventory["all"]["hosts"]["demo"]["ansible_host"] == "192.0.2.10"
    assert inventory["all"]["hosts"]["demo"]["ansible_port"] == 2222
    assert inventory["all"]["hosts"]["demo"]["ansible_ssh_private_key_file"] == "/tmp/demo-key"


def test_ansible_service_parses_runner_events(monkeypatch: Any, tmp_path: Any) -> None:
    """AnsibleService 应调用 ansible_runner.run 并提取状态、stdout 与事件。"""
    captured: dict[str, Any] = {}

    def fake_run(**kwargs: Any) -> SimpleNamespace:
        captured.update(kwargs)
        return SimpleNamespace(
            status="successful",
            rc=0,
            stdout=SimpleNamespace(read=lambda: "ok stdout"),
            stderr=SimpleNamespace(read=lambda: ""),
            events=[{"event": "runner_on_ok", "event_data": {"host": "demo"}}],
        )

    monkeypatch.setattr("backend.app.services.ansible_service.ansible_runner.run", fake_run)
    service = AnsibleService(private_data_dir=tmp_path)

    result = service.run_module_task(
        inventory={"all": {"hosts": {"demo": {"ansible_host": "127.0.0.1"}}}},
        playbook=[{"hosts": "all", "tasks": []}],
    )

    assert captured["private_data_dir"] == str(tmp_path)
    assert captured["inventory"] == {"all": {"hosts": {"demo": {"ansible_host": "127.0.0.1"}}}}
    assert captured["playbook"] == "main.json"
    assert json.loads((tmp_path / "project" / "main.json").read_text()) == [
        {"hosts": "all", "tasks": []}
    ]
    assert result.status == "successful"
    assert result.stdout == "ok stdout"
    assert result.raw_events == [{"event": "runner_on_ok", "event_data": {"host": "demo"}}]


def test_task_service_executes_task_and_persists_success(db_session: Session, monkeypatch: Any) -> None:
    """任务服务应执行任务、写入 per-host 结果并把状态改为 success。"""
    host = Host(
        name="demo",
        ip_address="127.0.0.1",
        ssh_port=22,
        ssh_user="root",
        private_key_path="/tmp/demo-key",
    )
    db_session.add(host)
    db_session.commit()
    db_session.refresh(host)
    task = TaskService(db_session).create_task(
        TaskCreate(
            name="Check disk",
            module_key="system_inspection",
            module_task_key="check_disk",
            target_type="hosts",
            target_ids=[host.id],
            parameters={},
        )
    )

    def fake_run(self: AnsibleService, inventory: dict[str, Any], playbook: list[dict[str, Any]]) -> AnsibleExecutionResult:
        return AnsibleExecutionResult(
            status="successful",
            stdout="disk ok",
            stderr="",
            raw_events=[{"event": "runner_on_ok", "event_data": {"host": "demo"}}],
        )

    monkeypatch.setattr(AnsibleService, "run_module_task", fake_run)

    executed = TaskService(db_session).execute_task(task.id)

    results = list(db_session.scalars(select(TaskResult).where(TaskResult.task_id == task.id)))
    assert executed.status == "success"
    assert executed.started_at is not None
    assert executed.finished_at is not None
    assert len(results) == 1
    assert results[0].host_id == host.id
    assert results[0].status == "success"
    assert results[0].stdout == "disk ok"


def test_task_service_marks_partial_success_from_events(db_session: Session, monkeypatch: Any) -> None:
    """多主机任务中部分成功部分失败时应标记 partial_success。"""
    hosts = [
        Host(name="ok", ip_address="127.0.0.1", ssh_port=22, ssh_user="root", private_key_path="/tmp/key"),
        Host(name="bad", ip_address="127.0.0.2", ssh_port=22, ssh_user="root", private_key_path="/tmp/key"),
    ]
    db_session.add_all(hosts)
    db_session.commit()
    for host in hosts:
        db_session.refresh(host)
    task = TaskService(db_session).create_task(
        TaskCreate(
            name="Check load",
            module_key="system_inspection",
            module_task_key="check_load",
            target_type="hosts",
            target_ids=[host.id for host in hosts],
            parameters={},
        )
    )

    def fake_run(self: AnsibleService, inventory: dict[str, Any], playbook: list[dict[str, Any]]) -> AnsibleExecutionResult:
        return AnsibleExecutionResult(
            status="failed",
            stdout="mixed",
            stderr="bad failed",
            raw_events=[
                {"event": "runner_on_ok", "event_data": {"host": "ok"}},
                {"event": "runner_on_failed", "event_data": {"host": "bad"}},
            ],
        )

    monkeypatch.setattr(AnsibleService, "run_module_task", fake_run)

    executed = TaskService(db_session).execute_task(task.id)

    result_statuses = {result.status for result in db_session.scalars(select(TaskResult))}
    assert executed.status == "partial_success"
    assert result_statuses == {"success", "failed"}


def test_task_status_machine_rejects_terminal_state_regression() -> None:
    """任务状态机必须拒绝终态回退到 running。"""
    try:
        validate_task_status_transition("success", "running")
    except ValueError as exc:
        assert "success -> running" in str(exc)
    else:
        raise AssertionError("terminal task status should not regress")


def test_task_service_uses_task_scoped_runner_directory(
    db_session: Session,
    monkeypatch: Any,
    tmp_path: Any,
) -> None:
    """任务执行应使用 task-{id} Runner 目录隔离运行数据。"""
    host = Host(
        name="runner-demo",
        ip_address="127.0.0.1",
        ssh_port=22,
        ssh_user="root",
        private_key_path="/tmp/key",
    )
    db_session.add(host)
    db_session.commit()
    db_session.refresh(host)
    task = TaskService(db_session).create_task(
        TaskCreate(
            name="Scoped runner",
            module_key="system_inspection",
            module_task_key="check_uptime",
            target_type="hosts",
            target_ids=[host.id],
            parameters={},
        )
    )
    runner_dirs: list[str] = []

    def fake_run(self: AnsibleService, inventory: dict[str, Any], playbook: list[dict[str, Any]]) -> AnsibleExecutionResult:
        _ = inventory, playbook
        runner_dirs.append(str(self.private_data_dir))
        return AnsibleExecutionResult(
            status="successful",
            stdout="ok",
            stderr="",
            raw_events=[{"event": "runner_on_ok", "event_data": {"host": "runner-demo"}}],
        )

    monkeypatch.setattr(AnsibleService, "run_module_task", fake_run)
    monkeypatch.setattr("backend.app.services.task_service.RUNNER_BASE_DIR", tmp_path)

    TaskService(db_session).execute_task(task.id)

    assert runner_dirs == [str(tmp_path / f"task-{task.id}")]


def test_worker_executes_task_with_database_session(client: TestClient, monkeypatch: Any) -> None:
    """Celery worker 入口应复用任务服务完成实际执行。"""
    response = client.post(
        "/api/v1/hosts",
        json={
            "name": "worker-host",
            "ip_address": "127.0.0.1",
            "ssh_port": 22,
            "ssh_user": "root",
            "private_key_path": "/tmp/key",
            "description": None,
        },
    )
    host_id = response.json()["id"]
    task_response = client.post(
        "/api/v1/tasks",
        json={
            "name": "Worker task",
            "module_key": "system_inspection",
            "module_task_key": "check_uptime",
            "target_type": "hosts",
            "target_ids": [host_id],
            "parameters": {},
        },
    )
    task_id = task_response.json()["id"]

    def fake_execute(self: TaskService, task_id: int) -> SimpleNamespace:
        _ = self
        return SimpleNamespace(id=task_id, status="success")

    monkeypatch.setattr(TaskService, "execute_task", fake_execute)

    result = worker_tasks.execute_operation_task(task_id)

    assert result == {"task_id": task_id, "status": "success"}


def test_create_task_dispatches_celery(client: TestClient, monkeypatch: Any) -> None:
    """创建任务后 API 应把任务 ID 投递给 Celery worker。"""
    response = client.post(
        "/api/v1/hosts",
        json={
            "name": "dispatch-host",
            "ip_address": "127.0.0.1",
            "ssh_port": 22,
            "ssh_user": "root",
            "private_key_path": "/tmp/key",
            "description": None,
        },
    )
    dispatched: list[int] = []

    def fake_dispatch(task_id: int) -> None:
        dispatched.append(task_id)

    monkeypatch.setattr("backend.app.api.routes.tasks.dispatch_task", fake_dispatch)
    task_response = client.post(
        "/api/v1/tasks",
        json={
            "name": "Dispatch task",
            "module_key": "system_inspection",
            "module_task_key": "check_disk",
            "target_type": "hosts",
            "target_ids": [response.json()["id"]],
            "parameters": {},
        },
    )

    assert task_response.status_code == 202
    assert dispatched == [task_response.json()["id"]]


def test_scheduled_job_trigger_dispatches_celery(db_session: Session, monkeypatch: Any) -> None:
    """手动触发定时任务后也应把生成的任务投递给 Celery。"""
    host = Host(
        name="scheduled-host",
        ip_address="127.0.0.1",
        ssh_port=22,
        ssh_user="root",
        private_key_path="/tmp/key",
    )
    db_session.add(host)
    db_session.commit()
    db_session.refresh(host)
    job = ScheduleService(db_session).create_job(
        ScheduledJobCreate(
            name="Daily check",
            module_key="system_inspection",
            module_task_key="check_disk",
            target_type="hosts",
            target_ids=[host.id],
            parameters={},
            schedule_type="interval",
            interval_seconds=300,
            enabled=True,
        )
    )
    dispatched: list[int] = []
    monkeypatch.setattr("backend.app.services.schedule_service.dispatch_task", dispatched.append)

    task_id = ScheduleService(db_session).trigger_scheduled_job(job)

    assert dispatched == [task_id]
