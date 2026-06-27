from datetime import datetime

from sqlalchemy import Boolean, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.core.database import Base
from backend.app.models.common import TimestampMixin


class OperationModule(TimestampMixin, Base):
    """数据库中的内置运维模块元数据。"""

    __tablename__ = "operation_modules"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    module_key: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class OperationModuleTask(TimestampMixin, Base):
    """数据库中的内置运维模块任务元数据。"""

    __tablename__ = "operation_module_tasks"
    __table_args__ = (UniqueConstraint("module_key", "task_key", name="uq_operation_module_task"),)

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    module_key: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    task_key: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    parameter_schema_json: Mapped[str | None] = mapped_column(Text)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class OperationModuleProposal(Base):
    """AI 辅助生成的可复核运维模块提案。"""

    __tablename__ = "operation_module_proposals"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    source_ai_proposal_id: Mapped[int | None] = mapped_column(ForeignKey("ai_proposals.id"))
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    problem_summary: Mapped[str] = mapped_column(Text, nullable=False)
    module_key: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    task_key: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    risk_level: Mapped[str] = mapped_column(String(32), nullable=False, default="medium")
    parameter_schema_json: Mapped[str] = mapped_column(Text, nullable=False)
    runbook: Mapped[str] = mapped_column(Text, nullable=False)
    playbook_json: Mapped[str] = mapped_column(Text, nullable=False)
    test_plan_json: Mapped[str] = mapped_column(Text, nullable=False)
    rollback_notes: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="draft", index=True)
    validation_status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")
    validation_output: Mapped[str | None] = mapped_column(Text)
    dangerous_command_detected: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    review_comment: Mapped[str | None] = mapped_column(Text)
    reviewed_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    reviewed_at: Mapped[datetime | None] = mapped_column()
    created_at: Mapped[datetime] = mapped_column(nullable=False)
