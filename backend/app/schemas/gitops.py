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
