from collections.abc import Generator
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from backend.app.core.config import settings


class Base(DeclarativeBase):
    """所有 SQLAlchemy ORM 模型的基类。"""


# SQLite 默认禁止跨线程使用连接；FastAPI 测试和开发场景需要关闭这个限制。
connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
engine = create_engine(settings.database_url, connect_args=connect_args, future=True)

# SessionLocal 是每个请求中使用的数据库会话工厂。
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def init_db() -> None:
    """初始化数据库。

    当前阶段为了快速搭建毕业设计原型，使用 create_all 创建表；当表结构稳定后，
    应按照 AGENTS.md 的约束切换到 Alembic 迁移。
    """
    if settings.database_url.startswith("sqlite:///"):
        db_path = Path(settings.database_url.removeprefix("sqlite:///"))
        db_path.parent.mkdir(parents=True, exist_ok=True)

    # 导入 models 包以注册所有 ORM 模型，否则 Base.metadata 不知道有哪些表。
    from backend.app import models  # noqa: F401

    Base.metadata.create_all(bind=engine)


def get_db() -> Generator[Session, None, None]:
    """FastAPI 依赖：为每个请求提供一个数据库会话并在结束后关闭。"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
