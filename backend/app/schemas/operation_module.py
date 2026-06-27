from typing import Any

from pydantic import BaseModel, Field


class OperationModuleProposalCreate(BaseModel):
    """创建可复核运维模块提案的请求体。"""

    source_ai_proposal_id: int | None = None
    title: str = Field(min_length=1, max_length=200)
    problem_summary: str
    module_key: str = Field(min_length=1, max_length=64)
    task_key: str = Field(min_length=1, max_length=64)
    risk_level: str = Field(default="medium", max_length=32)
    parameter_schema: dict[str, Any]
    runbook: str
    playbook: dict[str, Any]
    test_plan: list[str]
    rollback_notes: str


class OperationModuleProposalReview(BaseModel):
    """评审运维模块提案的请求体。"""

    review_comment: str = Field(default="", max_length=1000)


class OperationModuleProposalRead(BaseModel):
    """返回给前端展示的运维模块提案。"""

    id: int
    source_ai_proposal_id: int | None = None
    title: str
    problem_summary: str
    module_key: str
    task_key: str
    risk_level: str
    parameter_schema: dict[str, Any]
    runbook: str
    playbook: dict[str, Any]
    test_plan: list[str]
    rollback_notes: str
    status: str
    validation_status: str
    validation_output: str | None = None
    dangerous_command_detected: bool
    review_comment: str | None = None
    reviewed_by: int | None = None
    reviewed_at: str | None = None
    created_at: str


class OperationModuleProposalExport(BaseModel):
    """导出的运维模块草案。"""

    module_key: str
    task_key: str
    metadata: dict[str, Any]
    playbook: dict[str, Any]
    runbook: str
    tests: list[str]
    rollback_notes: str


class LocalizedTextRead(BaseModel):
    """API 响应中的中英文双语文本。"""

    zh_CN: str = Field(alias="zh-CN")
    en_US: str = Field(alias="en-US")


class OperationTaskRead(BaseModel):
    """内置运维模块下的单个任务元数据。"""

    task_key: str
    name: LocalizedTextRead
    description: LocalizedTextRead
    parameters: dict[str, Any] = Field(default_factory=dict)


class OperationModuleRead(BaseModel):
    """内置运维模块及其任务列表的 API 响应模型。"""

    module_key: str
    name: LocalizedTextRead
    description: LocalizedTextRead
    tasks: list[OperationTaskRead]
