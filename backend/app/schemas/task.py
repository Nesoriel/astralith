from typing import Any, Literal

from pydantic import BaseModel, Field

TaskStatus = Literal["pending", "running", "success", "partial_success", "failed", "cancelled"]


class TaskCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    module_key: str
    module_task_key: str
    target_type: Literal["hosts", "host_groups"]
    target_ids: list[int]
    parameters: dict[str, Any] = {}


class TaskRead(BaseModel):
    id: int
    name: str
    module_key: str
    module_task_key: str
    status: TaskStatus
