from typing import Any, Literal

from pydantic import BaseModel, Field

# 任务状态必须与 AGENTS.md 中约定的状态机保持一致。
TaskStatus = Literal["pending", "running", "success", "partial_success", "failed", "cancelled"]


class TaskCreate(BaseModel):
    """创建执行任务时前端提交的请求体。"""

    name: str = Field(min_length=1, max_length=100)
    module_key: str
    module_task_key: str
    target_type: Literal["hosts", "host_groups"]
    target_ids: list[int]
    parameters: dict[str, Any] = Field(default_factory=dict)


class TaskRead(BaseModel):
    """返回给前端展示的任务基础信息。"""

    id: int
    name: str
    module_key: str
    module_task_key: str
    status: TaskStatus
