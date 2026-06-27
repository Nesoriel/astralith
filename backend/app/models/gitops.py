from datetime import datetime

from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.core.database import Base
from backend.app.models.common import TimestampMixin, utc_now


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


class ActualResource(Base):
    """从主机扫描、数据库或人工导入得到的实际状态资源。"""

    __tablename__ = "actual_resources"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    resource_type: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    resource_key: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    source: Mapped[str] = mapped_column(String(100), nullable=False)
    content_json: Mapped[str] = mapped_column(Text, nullable=False)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    scanned_at: Mapped[datetime] = mapped_column(default=utc_now, nullable=False)


class ResourceDiff(Base):
    """Desired State 与 Actual State 的资源差异。"""

    __tablename__ = "resource_diffs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    repository_id: Mapped[int] = mapped_column(ForeignKey("gitops_repositories.id"), nullable=False, index=True)
    resource_type: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    resource_key: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    diff_type: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    before_json: Mapped[str | None] = mapped_column(Text)
    after_json: Mapped[str | None] = mapped_column(Text)
    risk_level: Mapped[str] = mapped_column(String(32), nullable=False, default="low")
    created_at: Mapped[datetime] = mapped_column(default=utc_now, nullable=False)


class ApplyPlan(Base):
    """为消除资源差异生成的受控执行计划。"""

    __tablename__ = "apply_plans"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    repository_id: Mapped[int] = mapped_column(ForeignKey("gitops_repositories.id"), nullable=False, index=True)
    diff_id: Mapped[int] = mapped_column(ForeignKey("resource_diffs.id"), nullable=False, index=True)
    plan_json: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending_review")
    policy_status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")
    ai_summary: Mapped[str | None] = mapped_column(Text)
    approved_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    approved_at: Mapped[datetime | None] = mapped_column()
    created_at: Mapped[datetime] = mapped_column(default=utc_now, nullable=False)


class PolicyResult(Base):
    """Apply Plan 的确定性策略校验结果。"""

    __tablename__ = "policy_results"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    repository_id: Mapped[int] = mapped_column(ForeignKey("gitops_repositories.id"), nullable=False, index=True)
    plan_id: Mapped[int] = mapped_column(ForeignKey("apply_plans.id"), nullable=False, index=True)
    rule_key: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    severity: Mapped[str] = mapped_column(String(32), nullable=False)
    passed: Mapped[bool] = mapped_column(Boolean, nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=utc_now, nullable=False)


class GitOpsApplyRun(Base):
    """一次 Docker Compose GitOps Apply 执行记录。"""

    __tablename__ = "gitops_apply_runs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    repository_id: Mapped[int] = mapped_column(ForeignKey("gitops_repositories.id"), nullable=False, index=True)
    plan_id: Mapped[int] = mapped_column(ForeignKey("apply_plans.id"), nullable=False, index=True)
    stack_name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    target_path: Mapped[str] = mapped_column(String(500), nullable=False)
    commit_sha: Mapped[str | None] = mapped_column(String(40))
    status: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    stdout: Mapped[str | None] = mapped_column(Text)
    stderr: Mapped[str | None] = mapped_column(Text)
    raw_event_data: Mapped[str | None] = mapped_column(Text)
    rollback_json: Mapped[str] = mapped_column(Text, nullable=False)
    started_at: Mapped[datetime] = mapped_column(default=utc_now, nullable=False)
    finished_at: Mapped[datetime | None] = mapped_column()
