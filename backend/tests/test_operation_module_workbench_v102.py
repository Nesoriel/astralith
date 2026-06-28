from starlette.testclient import TestClient
from sqlalchemy.orm import Session

from backend.app.models.host import Host
from backend.app.models.task import Task


def auth_headers(client: TestClient) -> dict[str, str]:
    """登录测试管理员并返回认证头。"""
    response = client.post("/api/v1/auth/login", json={"username": "admin", "password": "admin123"})
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def seed_host_and_task(db_session: Session) -> None:
    """准备模块工作台最近执行记录。"""
    host = Host(
        name="demo-host",
        ip_address="127.0.0.1",
        ssh_port=22,
        ssh_user="root",
        private_key_path="/tmp/id_rsa",
        description="demo",
    )
    db_session.add(host)
    db_session.add(
        Task(
            name="recent disk check",
            module_key="system_inspection",
            module_task_key="check_disk",
            status="success",
            target_type="hosts",
            target_ids_json="[]",
            parameters_json="{}",
        )
    )
    db_session.commit()


def test_operation_module_preview_playbook(client: TestClient) -> None:
    """模块工作台应能预览受控 Playbook。"""
    headers = auth_headers(client)

    response = client.post(
        "/api/v1/operation-modules/system_inspection/tasks/check_disk/preview-playbook",
        headers=headers,
        json={"parameters": {}},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["module_key"] == "system_inspection"
    assert body["task_key"] == "check_disk"
    assert body["playbook"][0]["tasks"][0]["ansible.builtin.command"] == "df -h"


def test_operation_module_recent_tasks(client: TestClient) -> None:
    """模块工作台应能展示模块最近任务。"""
    from backend.app.core.database import get_db
    from backend.app.main import app

    db = next(app.dependency_overrides[get_db]())
    try:
        seed_host_and_task(db)
    finally:
        db.close()

    response = client.get("/api/v1/operation-modules/system_inspection/recent-tasks")

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["module_key"] == "system_inspection"
    assert body[0]["module_task_key"] == "check_disk"


def test_operation_module_create_task_shortcut(client: TestClient) -> None:
    """模块工作台应能从模块任务直接创建执行任务。"""
    from backend.app.core.database import get_db
    from backend.app.main import app

    headers = auth_headers(client)
    db = next(app.dependency_overrides[get_db]())
    try:
        host = Host(
            name="demo-host",
            ip_address="127.0.0.1",
            ssh_port=22,
            ssh_user="root",
            private_key_path="/tmp/id_rsa",
            description="demo",
        )
        db.add(host)
        db.commit()
        db.refresh(host)
        host_id = host.id
    finally:
        db.close()

    response = client.post(
        "/api/v1/operation-modules/system_inspection/tasks/check_disk/create-task",
        headers=headers,
        json={"name": "quick disk check", "target_type": "hosts", "target_ids": [host_id], "parameters": {}},
    )

    assert response.status_code == 202
    body = response.json()
    assert body["name"] == "quick disk check"
    assert body["module_key"] == "system_inspection"
    assert body["module_task_key"] == "check_disk"
