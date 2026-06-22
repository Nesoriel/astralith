import json
from datetime import datetime, timezone
from typing import cast

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models.scheduled_job import ScheduledJob
from backend.app.schemas.scheduled_job import (
    ScheduleType,
    ScheduledJobCreate,
    ScheduledJobRead,
    ScheduledJobUpdate,
)
from backend.app.schemas.task import TargetType, TaskCreate
from backend.app.services.task_service import TaskService


class ScheduleService:
    """定时任务业务服务，负责把 APScheduler 触发转换为平台任务。"""

    def __init__(self, db: Session) -> None:
        self.db = db

    def list_jobs(self) -> list[ScheduledJob]:
        """按创建顺序倒序返回定时任务列表。"""
        return list(self.db.scalars(select(ScheduledJob).order_by(ScheduledJob.id.desc())))

    def get_job(self, scheduled_job_id: int) -> ScheduledJob | None:
        """按 ID 查询定时任务。"""
        return self.db.get(ScheduledJob, scheduled_job_id)

    def create_job(self, payload: ScheduledJobCreate) -> ScheduledJob:
        """创建定时任务配置。"""
        TaskService(self.db)._validate_module_task(payload.module_key, payload.module_task_key)
        job = ScheduledJob(
            name=payload.name,
            module_key=payload.module_key,
            module_task_key=payload.module_task_key,
            target_type=payload.target_type,
            target_ids_json=json.dumps(payload.target_ids),
            parameters_json=json.dumps(payload.parameters, ensure_ascii=False),
            schedule_type=payload.schedule_type,
            cron_expression=payload.cron_expression,
            interval_seconds=payload.interval_seconds,
            enabled=payload.enabled,
        )
        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)
        return job

    def update_job(self, job: ScheduledJob, payload: ScheduledJobUpdate) -> ScheduledJob:
        """更新定时任务配置。"""
        TaskService(self.db)._validate_module_task(payload.module_key, payload.module_task_key)
        job.name = payload.name
        job.module_key = payload.module_key
        job.module_task_key = payload.module_task_key
        job.target_type = payload.target_type
        job.target_ids_json = json.dumps(payload.target_ids)
        job.parameters_json = json.dumps(payload.parameters, ensure_ascii=False)
        job.schedule_type = payload.schedule_type
        job.cron_expression = payload.cron_expression
        job.interval_seconds = payload.interval_seconds
        job.enabled = payload.enabled
        self.db.commit()
        self.db.refresh(job)
        return job

    def delete_job(self, job: ScheduledJob) -> None:
        """删除定时任务配置。"""
        self.db.delete(job)
        self.db.commit()

    def set_enabled(self, job: ScheduledJob, enabled: bool) -> ScheduledJob:
        """启用或禁用定时任务。"""
        job.enabled = enabled
        self.db.commit()
        self.db.refresh(job)
        return job

    def trigger_scheduled_job(self, job: ScheduledJob) -> int:
        """手动触发定时任务，并创建一条 pending 执行任务。"""
        target_type = job.target_type
        if target_type not in ("hosts", "host_groups"):
            raise ValueError("Invalid scheduled job target type")
        typed_target_type = cast(TargetType, target_type)
        payload = TaskCreate(
            name=f"{job.name} manual trigger",
            module_key=job.module_key,
            module_task_key=job.module_task_key,
            target_type=typed_target_type,
            target_ids=json.loads(job.target_ids_json),
            parameters=json.loads(job.parameters_json or "{}"),
        )
        task = TaskService(self.db).create_task(payload)
        job.last_run_at = datetime.now(timezone.utc)
        self.db.commit()
        return task.id

    def job_to_schema(self, job: ScheduledJob) -> ScheduledJobRead:
        """把 ORM 定时任务转换为前端友好的响应模型。"""
        target_type = cast(TargetType, job.target_type)
        schedule_type = cast(ScheduleType, job.schedule_type)
        return ScheduledJobRead(
            id=job.id,
            name=job.name,
            module_key=job.module_key,
            module_task_key=job.module_task_key,
            target_type=target_type,
            target_ids=json.loads(job.target_ids_json),
            parameters=json.loads(job.parameters_json or "{}"),
            schedule_type=schedule_type,
            cron_expression=job.cron_expression,
            interval_seconds=job.interval_seconds,
            enabled=job.enabled,
            created_at=job.created_at,
            updated_at=job.updated_at,
            last_run_at=job.last_run_at,
            next_run_at=job.next_run_at,
        )
