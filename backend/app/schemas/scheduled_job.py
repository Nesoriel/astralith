from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from backend.app.schemas.task import TargetType

ScheduleType = Literal["cron", "interval"]


class ScheduledJobBase(BaseModel):
    """定时任务请求与响应共用字段。"""

    name: str = Field(min_length=1, max_length=100)
    module_key: str
    module_task_key: str
    target_type: TargetType
    target_ids: list[int] = Field(min_length=1)
    parameters: dict[str, Any] = Field(default_factory=dict)
    schedule_type: ScheduleType
    cron_expression: str | None = None
    interval_seconds: int | None = Field(default=None, ge=1)
    enabled: bool = True

    @model_validator(mode="after")
    def validate_schedule_value(self) -> "ScheduledJobBase":
        """确保 cron 与 interval 类型只使用对应的调度字段。"""
        if self.schedule_type == "cron" and not self.cron_expression:
            raise ValueError("cron_expression is required for cron schedule")
        if self.schedule_type == "interval" and self.interval_seconds is None:
            raise ValueError("interval_seconds is required for interval schedule")
        return self


class ScheduledJobCreate(ScheduledJobBase):
    """创建定时任务的请求体。"""


class ScheduledJobUpdate(ScheduledJobBase):
    """更新定时任务的请求体。"""


class ScheduledJobRead(ScheduledJobBase):
    """返回给前端展示的定时任务信息。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime
    last_run_at: datetime | None = None
    next_run_at: datetime | None = None


class ScheduledJobTriggerRead(BaseModel):
    """手动触发定时任务后的响应。"""

    scheduled_job_id: int
    task_id: int
