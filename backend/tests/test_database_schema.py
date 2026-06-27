import sqlite3
from pathlib import Path

from sqlalchemy import create_engine, text

from backend.app.core.database import ensure_sqlite_schema


def test_ensure_sqlite_schema_adds_v022_task_target_ids_column(tmp_path: Path) -> None:
    """v0.2.2 启动时应修复旧开发库中缺失的任务目标列。"""
    db_path = tmp_path / "old-astralith.db"
    connection = sqlite3.connect(db_path)
    try:
        connection.execute(
            """
            CREATE TABLE tasks (
                id INTEGER NOT NULL PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                module_key VARCHAR(64) NOT NULL,
                module_task_key VARCHAR(64) NOT NULL,
                status VARCHAR(32) NOT NULL,
                target_type VARCHAR(32) NOT NULL,
                parameters_json TEXT,
                created_by INTEGER,
                started_at DATETIME,
                finished_at DATETIME,
                created_at DATETIME NOT NULL,
                updated_at DATETIME NOT NULL
            )
            """
        )
        connection.commit()
    finally:
        connection.close()

    engine = create_engine(f"sqlite:///{db_path}", future=True)
    ensure_sqlite_schema(engine)

    with engine.connect() as migrated:
        columns = {row[1] for row in migrated.execute(text("PRAGMA table_info(tasks)"))}

    assert "target_ids_json" in columns


def test_ensure_sqlite_schema_adds_v050_ai_analysis_tables(tmp_path: Path) -> None:
    """v0.5.0 启动时应为旧开发库补齐 AI 分析相关表。"""
    db_path = tmp_path / "old-astralith.db"
    connection = sqlite3.connect(db_path)
    try:
        connection.execute(
            """
            CREATE TABLE tasks (
                id INTEGER NOT NULL PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                module_key VARCHAR(64) NOT NULL,
                module_task_key VARCHAR(64) NOT NULL,
                status VARCHAR(32) NOT NULL,
                target_type VARCHAR(32) NOT NULL,
                target_ids_json TEXT NOT NULL,
                parameters_json TEXT,
                created_by INTEGER,
                started_at DATETIME,
                finished_at DATETIME,
                created_at DATETIME NOT NULL,
                updated_at DATETIME NOT NULL
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE task_results (
                id INTEGER NOT NULL PRIMARY KEY,
                task_id INTEGER NOT NULL,
                host_id INTEGER,
                status VARCHAR(32) NOT NULL,
                stdout TEXT,
                stderr TEXT,
                raw_event_data TEXT,
                started_at DATETIME,
                finished_at DATETIME
            )
            """
        )
        connection.commit()
    finally:
        connection.close()

    engine = create_engine(f"sqlite:///{db_path}", future=True)
    ensure_sqlite_schema(engine)

    with engine.connect() as migrated:
        table_names = {row[0] for row in migrated.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))}

    assert "evidence_packs" in table_names
    assert "ai_analysis_results" in table_names


def test_ensure_sqlite_schema_adds_v060_gitops_tables(tmp_path: Path) -> None:
    """v0.6.0 启动时应为旧开发库补齐 GitOps 同步相关表。"""
    db_path = tmp_path / "old-astralith.db"
    connection = sqlite3.connect(db_path)
    try:
        connection.execute(
            """
            CREATE TABLE users (
                id INTEGER NOT NULL PRIMARY KEY,
                username VARCHAR(64) NOT NULL,
                hashed_password VARCHAR(255) NOT NULL,
                role VARCHAR(32) NOT NULL,
                is_active BOOLEAN NOT NULL,
                created_at DATETIME NOT NULL,
                updated_at DATETIME NOT NULL
            )
            """
        )
        connection.commit()
    finally:
        connection.close()

    engine = create_engine(f"sqlite:///{db_path}", future=True)
    ensure_sqlite_schema(engine)

    with engine.connect() as migrated:
        table_names = {row[0] for row in migrated.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))}

    assert "gitops_repositories" in table_names
    assert "gitops_sync_runs" in table_names
    assert "desired_resources" in table_names
