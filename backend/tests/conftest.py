from collections.abc import Generator

import pytest
from starlette.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.core.database import Base, get_db
from backend.app.main import app
from backend.app.services.auth_service import AuthService


@pytest.fixture()
def db_session() -> Generator[Session, None, None]:
    """提供服务层测试使用的独立内存数据库会话。"""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        future=True,
    )
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    AuthService(db).ensure_default_admin()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(autouse=True)
def disable_task_dispatch(monkeypatch: pytest.MonkeyPatch) -> None:
    """API 测试默认不连接 Redis，按需在单个测试中覆盖投递函数。"""
    monkeypatch.setattr("backend.app.api.routes.tasks.dispatch_task", lambda task_id: None)
    monkeypatch.setattr("backend.app.services.schedule_service.dispatch_task", lambda task_id: None)


@pytest.fixture()
def client() -> Generator[TestClient, None, None]:
    """使用独立内存数据库运行 API 测试，避免污染开发环境 SQLite。"""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        future=True,
    )
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    Base.metadata.create_all(bind=engine)
    seed_db = TestingSessionLocal()
    try:
        AuthService(seed_db).ensure_default_admin()
    finally:
        seed_db.close()

    def override_get_db() -> Generator[Session, None, None]:
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()
