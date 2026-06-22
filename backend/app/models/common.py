from datetime import datetime, timezone

from sqlalchemy.orm import Mapped, mapped_column


def utc_now() -> datetime:
    """生成带 UTC 时区的当前时间，避免数据库中混用本地时间。"""
    return datetime.now(timezone.utc)


class TimestampMixin:
    """为核心业务表统一提供创建与更新时间字段。"""

    created_at: Mapped[datetime] = mapped_column(default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(default=utc_now, onupdate=utc_now)
