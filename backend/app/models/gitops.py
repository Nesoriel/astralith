from datetime import datetime

from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.core.database import Base
from backend.app.models.common import TimestampMixin


class GitOpsRepository(TimestampMixin, Base):
    """GitOps 期望状态仓库配置。"""

    __tablename__ = "gitops_repositories"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    repo_url: Mapped[str] = mapped_column(String(500), nullable=False)
    branch: Mapped[str] = mapped_column(String(100), default="main", nullable=False)
    local_path: Mapped[str] = mapped_column(String(500), nullable=False)
    auth_type: Mapped[str] = mapped_column(String(32), default="none", nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_sync_at: Mapped[datetime | None] = mapped_column()
    last_commit_sha: Mapped[str | None] = mapped_column(String(40))


class GitOpsSyncRun(Base):
    """一次 GitOps 仓库同步记录。"""

    __tablename__ = "gitops_sync_runs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    repository_id: Mapped[int] = mapped_column(ForeignKey("gitops_repositories.id"), nullable=False, index=True)
    commit_sha: Mapped[str | None] = mapped_column(String(40))
    status: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    stdout: Mapped[str | None] = mapped_column(Text)
    stderr: Mapped[str | None] = mapped_column(Text)
    started_at: Mapped[datetime] = mapped_column(nullable=False)
    finished_at: Mapped[datetime | None] = mapped_column()


class DesiredResource(Base):
    """从 Git 仓库解析出的期望状态资源。"""

    __tablename__ = "desired_resources"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    repository_id: Mapped[int] = mapped_column(ForeignKey("gitops_repositories.id"), nullable=False, index=True)
    commit_sha: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    resource_type: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    resource_key: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    content_json: Mapped[str] = mapped_column(Text, nullable=False)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
