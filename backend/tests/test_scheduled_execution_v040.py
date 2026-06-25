from datetime import datetime, timezone
from typing import Any

import pytest
from sqlalchemy.orm import Session

from backend.app.models.host import Host
from backend.app.scheduler import scheduler as scheduler_module
from backend.app.schemas.scheduled_job import ScheduledJobCreate, ScheduledJobUpdate
from backend.app.services.schedule_service import ScheduleService


def _create_host(db_session: Session) -> Host:
    """创建一个定时任务测试用主机。"""
    host = Host(
        name="v040-host",
        ip_address="127.0.0.1",
        ssh_port=22,
        ssh_user="root",
        private_key_path="/tmp/key",
    )
    db_session.add(host)
    db_session.commit()
    db_session.refresh(host)
    return host


@pytest.fixture(autouse=True)
def clear_scheduler_jobs() -> None:
    """隔离 APScheduler 全局实例，避免不同测试之间残留任务。"""
    scheduler_module.scheduler.remove_all_jobs()


@pytest.fixture()
def frozen_next_run(monkeypatch: pytest.MonkeyPatch) -> datetime:
    """固定调度器返回的下一次执行时间，便于断言数据库字段。"""
    next_run_at = datetime(2026, 1, 1, 0, 5, tzinfo=timezone.utc)

    class FakeSchedulerJob:
        def __init__(self, job_id: str) -> None:
            self.id = job_id
            self.next_run_time = next_run_at

    def fake_add_job(*args: Any, **kwargs: Any) -> FakeSchedulerJob:
        return FakeSchedulerJob(str(kwargs["id"]))

    monkeypatch.setattr(scheduler_module.scheduler, "add_job", fake_add_job)
    monkeypatch.setattr(scheduler_module.scheduler, "remove_job", lambda job_id: None)
    return next_run_at


def _interval_payload(host_id: int, *, enabled: bool = True) -> ScheduledJobCreate:
    """生成最小 interval 定时任务请求。"""
    return ScheduledJobCreate(
        name="Every five minutes",
        module_key="system_inspection",
        module_task_key="check_disk",
        target_type="hosts",
        target_ids=[host_id],
        parameters={},
        schedule_type="interval",
        interval_seconds=300,
        enabled=enabled,
    )


def test_create_enabled_job_registers_scheduler_and_next_run(
    db_session: Session,
    frozen_next_run: datetime,
) -> None:
    """创建启用的定时任务时，应注册 APScheduler 并持久化 next_run_at。"""
    host = _create_host(db_session)

    job = ScheduleService(db_session).create_job(_interval_payload(host.id))

    assert job.next_run_at == frozen_next_run.replace(tzinfo=None)


def test_disable_update_and_delete_remove_scheduler_job(
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """禁用、更新为禁用和删除时，应从 APScheduler 移除对应任务。"""
    host = _create_host(db_session)
    removed_job_ids: list[str] = []
    monkeypatch.setattr(scheduler_module.scheduler, "add_job", lambda *args, **kwargs: None)
    monkeypatch.setattr(scheduler_module.scheduler, "remove_job", removed_job_ids.append)

    service = ScheduleService(db_session)
    job = service.create_job(_interval_payload(host.id))
    removed_job_ids.clear()

    service.set_enabled(job, False)
    assert removed_job_ids == ["scheduled-job-1"]

    removed_job_ids.clear()
    service.update_job(job, ScheduledJobUpdate(**_interval_payload(host.id, enabled=False).model_dump()))
    assert removed_job_ids == ["scheduled-job-1"]

    removed_job_ids.clear()
    service.delete_job(job)
    assert removed_job_ids == ["scheduled-job-1"]


def test_scheduler_callback_creates_task_only_for_enabled_jobs(
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """APScheduler 回调只触发仍处于启用状态的数据库任务。"""
    host = _create_host(db_session)
    dispatched: list[int] = []
    monkeypatch.setattr("backend.app.services.schedule_service.dispatch_task", dispatched.append)

    service = ScheduleService(db_session)
    job = service.create_job(_interval_payload(host.id, enabled=False))

    task_id = scheduler_module.run_scheduled_job_once(db_session, job.id)

    assert task_id is None
    assert dispatched == []

    service.set_enabled(job, True)
    task_id = scheduler_module.run_scheduled_job_once(db_session, job.id)

    assert task_id is not None
    assert dispatched == [task_id]


def test_cron_schedule_accepts_standard_five_field_expression(
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """cron 定时任务应接受标准五段 crontab 表达式并注册调度器。"""
    host = _create_host(db_session)
    captured: dict[str, Any] = {}

    def fake_add_job(*args: Any, **kwargs: Any) -> None:
        captured.update(kwargs)

    monkeypatch.setattr(scheduler_module.scheduler, "add_job", fake_add_job)
    monkeypatch.setattr(scheduler_module.scheduler, "remove_job", lambda job_id: None)

    ScheduleService(db_session).create_job(
        ScheduledJobCreate(
            name="Nightly cron",
            module_key="system_inspection",
            module_task_key="check_disk",
            target_type="hosts",
            target_ids=[host.id],
            parameters={},
            schedule_type="cron",
            cron_expression="5 0 * * *",
            enabled=True,
        )
    )

    assert captured["id"] == "scheduled-job-1"
    assert captured["replace_existing"] is True
