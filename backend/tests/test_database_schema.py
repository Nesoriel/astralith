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
