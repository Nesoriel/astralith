from collections.abc import Generator
from pathlib import Path

from typing import cast

from sqlalchemy import Table, create_engine, inspect, text
from sqlalchemy.engine import Engine
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
    ensure_sqlite_schema(engine)
    seed_default_admin()


def seed_default_admin() -> None:
    """初始化本地管理员账号，保证毕业设计演示可以直接登录。"""
    from backend.app.services.auth_service import AuthService

    db = SessionLocal()
    try:
        AuthService(db).ensure_default_admin()
    finally:
        db.close()


def ensure_sqlite_schema(database_engine: Engine) -> None:
    """补齐原型阶段 SQLite 开发库中缺失的兼容列。

    v0.2.0 引入任务目标 ID 持久化字段后，旧开发库只靠 create_all 不会自动变更
    已存在表结构。这里先做极小范围的 SQLite 兼容迁移，避免前端任务列表读取旧库时报
    no such column；表结构稳定后应迁移到正式 Alembic 版本管理。
    """
    if database_engine.dialect.name != "sqlite":
        return

    inspector = inspect(database_engine)
    # v0.6.0 新增 GitOps 同步表；旧 SQLite 开发库启动时需要补齐这些表。
    from backend.app.models.gitops import (
        ActualResource,
        AiProposal,
        ApplyPlan,
        DesiredResource,
        GitOpsApplyRun,
        GitOpsRepository,
        GitOpsSyncRun,
        PolicyResult,
        ResourceDiff,
    )

    gitops_tables = [
        cast(Table, GitOpsRepository.__table__),
        cast(Table, GitOpsSyncRun.__table__),
        cast(Table, DesiredResource.__table__),
        cast(Table, ActualResource.__table__),
        cast(Table, AiProposal.__table__),
        cast(Table, ResourceDiff.__table__),
        cast(Table, ApplyPlan.__table__),
        cast(Table, PolicyResult.__table__),
        cast(Table, GitOpsApplyRun.__table__),
    ]
    Base.metadata.create_all(bind=database_engine, tables=gitops_tables)

    # v1.0.0 新增自增长运维模块提案表；旧库即使尚未创建 tasks 表也要补齐。
    from backend.app.models.operation_module import OperationModuleProposal

    Base.metadata.create_all(bind=database_engine, tables=[cast(Table, OperationModuleProposal.__table__)])

    if not inspector.has_table("tasks"):
        return

    task_columns = {column["name"] for column in inspector.get_columns("tasks")}
    if "target_ids_json" not in task_columns:
        with database_engine.begin() as connection:
            connection.execute(text("ALTER TABLE tasks ADD COLUMN target_ids_json TEXT"))
            # 旧原型任务没有目标 ID 信息时统一置为空列表，保证列表页和日志页可读。
            connection.execute(text("UPDATE tasks SET target_ids_json = '[]' WHERE target_ids_json IS NULL"))

    # v0.5.0 新增 AI 分析表；旧 SQLite 开发库启动时需要补齐这两个表。
    from backend.app.models.task import AiAnalysisResult, EvidencePack

    ai_analysis_tables = [cast(Table, EvidencePack.__table__), cast(Table, AiAnalysisResult.__table__)]
    Base.metadata.create_all(bind=database_engine, tables=ai_analysis_tables)



def get_db() -> Generator[Session, None, None]:
    """FastAPI 依赖：为每个请求提供一个数据库会话并在结束后关闭。"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
