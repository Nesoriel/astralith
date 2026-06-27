from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class GitOpsRepositoryCreate(BaseModel):
    """创建 GitOps 仓库配置的请求体。"""

    name: str = Field(min_length=1, max_length=100)
    repo_url: str = Field(min_length=1, max_length=500)
    branch: str = Field(default="main", min_length=1, max_length=100)
    local_path: str = Field(min_length=1, max_length=500)
    auth_type: str = Field(default="none", max_length=32)
    enabled: bool = True


class GitOpsRepositoryUpdate(GitOpsRepositoryCreate):
    """更新 GitOps 仓库配置的请求体。"""


class GitOpsRepositoryRead(BaseModel):
    """返回给前端展示的 GitOps 仓库配置。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    repo_url: str
    branch: str
    local_path: str
    auth_type: str
    enabled: bool
    last_sync_at: datetime | None = None
    last_commit_sha: str | None = None
    created_at: datetime
    updated_at: datetime


class GitOpsSyncRunRead(BaseModel):
    """返回给前端展示的 GitOps 同步记录。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    repository_id: int
    commit_sha: str | None = None
    status: str
    stdout: str | None = None
    stderr: str | None = None
    started_at: datetime
    finished_at: datetime | None = None


class DesiredResourceRead(BaseModel):
    """返回给前端展示的期望状态资源。"""

    id: int
    repository_id: int
    commit_sha: str
    resource_type: str
    resource_key: str
    file_path: str
    content: dict[str, Any]
    content_hash: str


class ActualResourceUpsert(BaseModel):
    """写入或更新 Actual Resource 的请求体。"""

    resource_type: str = Field(min_length=1, max_length=32)
    resource_key: str = Field(min_length=1, max_length=200)
    source: str = Field(default="manual", max_length=100)
    content: dict[str, Any]


class ActualResourceRead(BaseModel):
    """返回给前端展示的实际状态资源。"""

    id: int
    resource_type: str
    resource_key: str
    source: str
    content: dict[str, Any]
    content_hash: str
    scanned_at: datetime


class ResourceDiffRead(BaseModel):
    """返回给前端展示的资源差异。"""

    id: int
    repository_id: int
    resource_type: str
    resource_key: str
    diff_type: str
    before: dict[str, Any] | None = None
    after: dict[str, Any] | None = None
    risk_level: str
    created_at: datetime


class ApplyPlanRead(BaseModel):
    """返回给前端展示的执行计划。"""

    id: int
    repository_id: int
    diff_id: int
    plan: dict[str, Any]
    status: str
    policy_status: str
    ai_summary: str | None = None
    approved_by: int | None = None
    approved_at: datetime | None = None
    created_at: datetime


class PolicyResultRead(BaseModel):
    """返回给前端展示的策略校验结果。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    repository_id: int
    plan_id: int
    rule_key: str
    severity: str
    passed: bool
    message: str
    created_at: datetime
