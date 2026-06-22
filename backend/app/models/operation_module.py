from sqlalchemy import Boolean, String, Text, UniqueConstraint
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
