from datetime import datetime

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.base import BaseTrigger
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.core.database import SessionLocal
from backend.app.models.scheduled_job import ScheduledJob

scheduler = BackgroundScheduler(timezone="UTC")
SCHEDULER_JOB_ID_PREFIX = "scheduled-job-"


def build_scheduler_job_id(scheduled_job_id: int) -> str:
    """生成 APScheduler 使用的稳定任务 ID。"""

    return f"{SCHEDULER_JOB_ID_PREFIX}{scheduled_job_id}"


def build_trigger(job: ScheduledJob) -> BaseTrigger:
    """根据数据库定时任务配置构造 APScheduler trigger。"""

    if job.schedule_type == "interval":
        if job.interval_seconds is None:
            raise ValueError("interval_seconds is required for interval schedule")
        return IntervalTrigger(seconds=job.interval_seconds, timezone="UTC")

    if job.schedule_type == "cron":
        if not job.cron_expression:
            raise ValueError("cron_expression is required for cron schedule")
        fields = job.cron_expression.split()
        if len(fields) != 5:
            raise ValueError("cron_expression must use five fields: minute hour day month day_of_week")
        minute, hour, day, month, day_of_week = fields
        return CronTrigger(
            minute=minute,
            hour=hour,
            day=day,
            month=month,
            day_of_week=day_of_week,
            timezone="UTC",
        )

    raise ValueError(f"Unsupported schedule type: {job.schedule_type}")


def sync_scheduler_job(db: Session, job: ScheduledJob) -> ScheduledJob:
    """把单条数据库定时任务同步到 APScheduler，并更新 next_run_at。"""

    scheduler_job_id = build_scheduler_job_id(job.id)
    remove_scheduler_job(scheduler_job_id)
    if not job.enabled:
        job.next_run_at = None
        db.commit()
        db.refresh(job)
        return job

    scheduler_job = scheduler.add_job(
        run_scheduled_job_by_id,
        trigger=build_trigger(job),
        id=scheduler_job_id,
        args=[job.id],
        replace_existing=True,
        coalesce=True,
        max_instances=1,
    )
    next_run_time = getattr(scheduler_job, "next_run_time", None)
    job.next_run_at = normalize_scheduler_datetime(next_run_time)
    db.commit()
    db.refresh(job)
    return job


def remove_scheduler_job(scheduler_job_id: str) -> None:
    """从 APScheduler 移除任务；任务不存在时保持幂等。"""

    try:
        scheduler.remove_job(scheduler_job_id)
    except Exception as exc:
        if exc.__class__.__name__ != "JobLookupError":
            raise


def normalize_scheduler_datetime(value: object) -> datetime | None:
    """把 APScheduler 时间归一化为 SQLite 友好的 UTC naive datetime。"""

    if not isinstance(value, datetime):
        return None
    return value.replace(tzinfo=None)


def sync_all_scheduled_jobs() -> None:
    """应用启动时把数据库中的启用任务重新注册到 APScheduler。"""

    db = SessionLocal()
    try:
        for job in db.scalars(select(ScheduledJob).where(ScheduledJob.enabled.is_(True))):
            sync_scheduler_job(db, job)
    finally:
        db.close()


def run_scheduled_job_by_id(scheduled_job_id: int) -> int | None:
    """APScheduler 后台回调入口，使用独立数据库会话触发任务。"""

    db = SessionLocal()
    try:
        return run_scheduled_job_once(db, scheduled_job_id)
    finally:
        db.close()


def run_scheduled_job_once(db: Session, scheduled_job_id: int) -> int | None:
    """执行一次定时任务触发逻辑；禁用或已删除任务不会创建执行任务。"""

    from backend.app.services.schedule_service import ScheduleService

    job = db.get(ScheduledJob, scheduled_job_id)
    if job is None or not job.enabled:
        return None
    return ScheduleService(db).trigger_scheduled_job(job, trigger_source="scheduler")


def start_scheduler() -> None:
    """启动 APScheduler；远程执行仍由 Celery 和 Ansible Runner 完成。"""

    if not scheduler.running:
        scheduler.start()
    sync_all_scheduled_jobs()


def stop_scheduler() -> None:
    """关闭 APScheduler，应用退出时不等待后台调度线程继续运行。"""

    if scheduler.running:
        scheduler.shutdown(wait=False)
