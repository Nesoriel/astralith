from datetime import datetime

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.core.database import Base
from backend.app.models.common import TimestampMixin


class Task(TimestampMixin, Base):
    """一次用户触发或定时触发的运维执行任务。"""

    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    module_key: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    module_task_key: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(32), default="pending", nullable=False, index=True)
    target_type: Mapped[str] = mapped_column(String(32), nullable=False)
    target_ids_json: Mapped[str] = mapped_column(Text, nullable=False)
    parameters_json: Mapped[str | None] = mapped_column(Text)
    created_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    started_at: Mapped[datetime | None] = mapped_column()
    finished_at: Mapped[datetime | None] = mapped_column()


class TaskResult(Base):
    """单台目标主机上的任务执行结果与日志。"""

    __tablename__ = "task_results"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("tasks.id"), nullable=False, index=True)
    host_id: Mapped[int | None] = mapped_column(ForeignKey("hosts.id"))
    status: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    stdout: Mapped[str | None] = mapped_column(Text)
    stderr: Mapped[str | None] = mapped_column(Text)
    raw_event_data: Mapped[str | None] = mapped_column(Text)
    started_at: Mapped[datetime | None] = mapped_column()
    finished_at: Mapped[datetime | None] = mapped_column()


class EvidencePack(Base):
    """AI 故障分析使用的结构化证据包。"""

    __tablename__ = "evidence_packs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    task_result_id: Mapped[int] = mapped_column(ForeignKey("task_results.id"), nullable=False, index=True)
    host_id: Mapped[int | None] = mapped_column(ForeignKey("hosts.id"))
    content_json: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, nullable=False)


class AiAnalysisResult(Base):
    """基于 Evidence Pack 生成的 AI 诊断报告。"""

    __tablename__ = "ai_analysis_results"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    evidence_pack_id: Mapped[int] = mapped_column(ForeignKey("evidence_packs.id"), nullable=False, index=True)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    content_json: Mapped[str] = mapped_column(Text, nullable=False)
    model_name: Mapped[str | None] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, nullable=False)
