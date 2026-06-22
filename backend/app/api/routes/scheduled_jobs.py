from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.schemas.scheduled_job import (
    ScheduledJobCreate,
    ScheduledJobRead,
    ScheduledJobTriggerRead,
    ScheduledJobUpdate,
)
from backend.app.services.schedule_service import ScheduleService

router = APIRouter()


def get_schedule_service(db: Session = Depends(get_db)) -> ScheduleService:
    """构造定时任务服务，保持路由层薄。"""
    return ScheduleService(db)


@router.get("", response_model=list[ScheduledJobRead])
def list_scheduled_jobs(
    service: ScheduleService = Depends(get_schedule_service),
) -> list[ScheduledJobRead]:
    """列出定时任务。"""
    return [service.job_to_schema(job) for job in service.list_jobs()]


@router.post("", response_model=ScheduledJobRead, status_code=status.HTTP_201_CREATED)
def create_scheduled_job(
    payload: ScheduledJobCreate,
    service: ScheduleService = Depends(get_schedule_service),
) -> ScheduledJobRead:
    """创建定时任务。"""
    try:
        job = service.create_job(payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return service.job_to_schema(job)


@router.get("/{job_id}", response_model=ScheduledJobRead)
def get_scheduled_job(
    job_id: int,
    service: ScheduleService = Depends(get_schedule_service),
) -> ScheduledJobRead:
    """读取单个定时任务。"""
    job = service.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Scheduled job not found")
    return service.job_to_schema(job)


@router.put("/{job_id}", response_model=ScheduledJobRead)
def update_scheduled_job(
    job_id: int,
    payload: ScheduledJobUpdate,
    service: ScheduleService = Depends(get_schedule_service),
) -> ScheduledJobRead:
    """更新定时任务。"""
    job = service.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Scheduled job not found")
    try:
        updated_job = service.update_job(job, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return service.job_to_schema(updated_job)


@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_scheduled_job(
    job_id: int,
    service: ScheduleService = Depends(get_schedule_service),
) -> Response:
    """删除定时任务。"""
    job = service.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Scheduled job not found")
    service.delete_job(job)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{job_id}/enable", response_model=ScheduledJobRead)
def enable_scheduled_job(
    job_id: int,
    service: ScheduleService = Depends(get_schedule_service),
) -> ScheduledJobRead:
    """启用定时任务。"""
    job = service.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Scheduled job not found")
    return service.job_to_schema(service.set_enabled(job, True))


@router.post("/{job_id}/disable", response_model=ScheduledJobRead)
def disable_scheduled_job(
    job_id: int,
    service: ScheduleService = Depends(get_schedule_service),
) -> ScheduledJobRead:
    """禁用定时任务。"""
    job = service.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Scheduled job not found")
    return service.job_to_schema(service.set_enabled(job, False))


@router.post("/{job_id}/trigger", response_model=ScheduledJobTriggerRead)
def trigger_scheduled_job(
    job_id: int,
    service: ScheduleService = Depends(get_schedule_service),
) -> ScheduledJobTriggerRead:
    """手动触发定时任务并创建一条执行任务记录。"""
    job = service.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Scheduled job not found")
    try:
        task_id = service.trigger_scheduled_job(job)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return ScheduledJobTriggerRead(scheduled_job_id=job.id, task_id=task_id)
