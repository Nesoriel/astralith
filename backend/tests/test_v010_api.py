from fastapi.testclient import TestClient


def create_host(client: TestClient) -> dict[str, object]:
    """创建测试主机并返回响应数据。"""
    response = client.post(
        "/api/v1/hosts",
        json={
            "name": "demo-host",
            "ip_address": "192.0.2.10",
            "ssh_port": 22,
            "ssh_user": "root",
            "private_key_path": "/home/demo/.ssh/id_rsa",
            "description": "demo",
        },
    )
    assert response.status_code == 201
    return response.json()


def test_host_crud_and_connection_placeholder(client: TestClient) -> None:
    """主机 CRUD 与连接测试占位接口可用。"""
    host = create_host(client)

    list_response = client.get("/api/v1/hosts")
    assert list_response.status_code == 200
    assert list_response.json()[0]["name"] == "demo-host"

    update_response = client.put(
        f"/api/v1/hosts/{host['id']}",
        json={
            "name": "updated-host",
            "ip_address": "192.0.2.11",
            "ssh_port": 2222,
            "ssh_user": "deploy",
            "private_key_path": "/home/demo/.ssh/deploy",
            "description": "updated",
        },
    )
    assert update_response.status_code == 200
    assert update_response.json()["ssh_port"] == 2222

    test_response = client.post(f"/api/v1/hosts/{host['id']}/test-connection")
    assert test_response.status_code == 200
    assert test_response.json()["status"] == "pending"

    delete_response = client.delete(f"/api/v1/hosts/{host['id']}")
    assert delete_response.status_code == 204
    assert client.get(f"/api/v1/hosts/{host['id']}").status_code == 404


def test_host_group_membership(client: TestClient) -> None:
    """主机组可以创建并维护成员关系。"""
    host = create_host(client)
    group_response = client.post(
        "/api/v1/host-groups",
        json={"name": "web", "description": "web servers"},
    )
    assert group_response.status_code == 201
    group = group_response.json()

    add_response = client.post(f"/api/v1/host-groups/{group['id']}/hosts", json={"host_id": host["id"]})
    assert add_response.status_code == 200
    assert add_response.json()["host_ids"] == [host["id"]]

    remove_response = client.delete(f"/api/v1/host-groups/{group['id']}/hosts/{host['id']}")
    assert remove_response.status_code == 204


def test_task_creation_and_logs(client: TestClient) -> None:
    """任务创建会校验模块与目标，并可读取日志聚合接口。"""
    host = create_host(client)
    response = client.post(
        "/api/v1/tasks",
        json={
            "name": "Check disk",
            "module_key": "system_inspection",
            "module_task_key": "check_disk",
            "target_type": "hosts",
            "target_ids": [host["id"]],
            "parameters": {},
        },
    )
    assert response.status_code == 202
    task = response.json()
    assert task["status"] == "pending"
    assert task["target_ids"] == [host["id"]]

    logs_response = client.get(f"/api/v1/tasks/{task['id']}/logs")
    assert logs_response.status_code == 200
    assert logs_response.json()["task"]["id"] == task["id"]
    assert logs_response.json()["results"] == []


def test_scheduled_job_manual_trigger(client: TestClient) -> None:
    """定时任务可创建、禁用、启用并手动触发生成任务。"""
    host = create_host(client)
    create_response = client.post(
        "/api/v1/scheduled-jobs",
        json={
            "name": "Daily disk check",
            "module_key": "system_inspection",
            "module_task_key": "check_disk",
            "target_type": "hosts",
            "target_ids": [host["id"]],
            "parameters": {},
            "schedule_type": "interval",
            "interval_seconds": 3600,
            "enabled": True,
        },
    )
    assert create_response.status_code == 201
    job = create_response.json()

    disable_response = client.post(f"/api/v1/scheduled-jobs/{job['id']}/disable")
    assert disable_response.status_code == 200
    assert disable_response.json()["enabled"] is False

    enable_response = client.post(f"/api/v1/scheduled-jobs/{job['id']}/enable")
    assert enable_response.status_code == 200
    assert enable_response.json()["enabled"] is True

    trigger_response = client.post(f"/api/v1/scheduled-jobs/{job['id']}/trigger")
    assert trigger_response.status_code == 200
    assert trigger_response.json()["scheduled_job_id"] == job["id"]
    assert trigger_response.json()["task_id"] > 0
