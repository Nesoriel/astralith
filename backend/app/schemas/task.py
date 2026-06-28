from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

# 任务状态必须与 AGENTS.md 中约定的状态机保持一致。
TaskStatus = Literal["pending", "running", "success", "partial_success", "failed", "cancelled"]
TargetType = Literal["hosts", "host_groups"]


class TaskCreate(BaseModel):
    """创建执行任务时前端提交的请求体。"""

    name: str = Field(min_length=1, max_length=100)
    module_key: str
    module_task_key: str
    target_type: TargetType
    target_ids: list[int] = Field(min_length=1)
    parameters: dict[str, Any] = Field(default_factory=dict)


class TaskRead(BaseModel):
    """返回给前端展示的任务基础信息。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    module_key: str
    module_task_key: str
    status: TaskStatus
    target_type: TargetType
    target_ids: list[int] = Field(default_factory=list)
    parameters: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime
    started_at: datetime | None = None
    finished_at: datetime | None = None


class TaskResultRead(BaseModel):
    """返回给前端展示的单主机执行日志。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    task_id: int
    host_id: int | None = None
    status: str
    stdout: str | None = None
    stderr: str | None = None
    raw_event_data: str | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None


class AiAnalysisResultRead(BaseModel):
    """返回给前端展示的 AI 故障分析结果。"""

    id: int
    evidence_pack_id: int
    summary: str
    content: dict[str, Any]
    model_name: str | None = None
    created_at: datetime


class TaskLogsRead(BaseModel):
    """任务详情与日志聚合响应。"""

    task: TaskRead
    results: list[TaskResultRead]
    ai_analyses: list[AiAnalysisResultRead] = Field(default_factory=list)


class EvidencePackRead(BaseModel):
    """任务故障上下文中的 Evidence Pack。"""

    id: int
    task_result_id: int
    host_id: int | None = None
    content: dict[str, Any]
    created_at: datetime


class TaskAiProposalCreate(BaseModel):
    """从任务故障分析生成 AI Proposal 的请求体。"""

    analysis_id: int


class TaskIncidentContextRead(BaseModel):
    """任务故障分析工作流聚合响应。"""

    task: TaskRead
    results: list[TaskResultRead]
    evidence_packs: list[EvidencePackRead] = Field(default_factory=list)
    ai_analyses: list[AiAnalysisResultRead] = Field(default_factory=list)
    ai_proposals: list[dict[str, Any]] = Field(default_factory=list)
