import json
from typing import Any

from starlette.testclient import TestClient
from sqlalchemy.orm import Session

from backend.app.models.host import Host
from backend.app.models.task import Task, TaskResult
from backend.app.services.ai_analysis_service import AiAnalysisService


def test_build_evidence_pack_from_failed_task_result(db_session: Session) -> None:
    """Evidence Pack 应从失败任务结果中提取结构化证据。"""
    host = Host(
        name="proxy-01",
        ip_address="192.0.2.10",
        ssh_port=22,
        ssh_user="root",
        private_key_path="/tmp/key",
    )
    task = Task(
        name="Restart nginx",
        module_key="service_manage",
        module_task_key="service_restart",
        status="failed",
        target_type="hosts",
        target_ids_json="[]",
        parameters_json=json.dumps({"service_name": "nginx"}),
    )
    db_session.add_all([host, task])
    db_session.commit()
    result = TaskResult(
        task_id=task.id,
        host_id=host.id,
        status="failed",
        stdout="",
        stderr="Job for nginx.service failed because the control process exited with error code.",
        raw_event_data=json.dumps([
            {
                "event": "runner_on_failed",
                "event_data": {"host": "proxy-01", "task": "service_restart"},
            }
        ]),
    )
    db_session.add(result)
    db_session.commit()
    db_session.refresh(result)

    evidence_pack = AiAnalysisService(db_session).build_evidence_pack(result.id)

    content = json.loads(evidence_pack.content_json)
    assert evidence_pack.task_result_id == result.id
    assert evidence_pack.host_id == host.id
    assert content["task"]["id"] == task.id
    assert content["host"]["name"] == "proxy-01"
    assert content["signals"]["stderr"] == result.stderr
    assert content["signals"]["ansible_events"][0]["event"] == "runner_on_failed"
    assert content["metadata"]["evidence_warning"] == "AI analysis must cite evidence and require human review."


def test_analyze_task_result_persists_structured_report(db_session: Session) -> None:
    """AI 分析服务应持久化带证据引用和人工复核提示的结构化报告。"""
    task = Task(
        name="Check disk",
        module_key="system_inspection",
        module_task_key="check_disk",
        status="failed",
        target_type="hosts",
        target_ids_json="[]",
        parameters_json="{}",
    )
    db_session.add(task)
    db_session.commit()
    result = TaskResult(
        task_id=task.id,
        host_id=None,
        status="failed",
        stdout="/dev/vda1 100% used",
        stderr="No space left on device",
        raw_event_data=json.dumps([{"event": "runner_on_failed", "event_data": {"task": "check_disk"}}]),
    )
    db_session.add(result)
    db_session.commit()
    db_session.refresh(result)

    analysis = AiAnalysisService(db_session).analyze_task_result(result.id)

    content = json.loads(analysis.content_json)
    assert analysis.evidence_pack_id is not None
    assert analysis.summary == "任务 Check disk 在未知主机上执行失败，主要错误信号：No space left on device"
    assert content["risk_level"] == "medium"
    assert "No space left on device" in content["key_evidence"][0]
    assert any("人工复核" in note for note in content["review_notes"])
    assert content["recommended_steps"]


def auth_headers(client: TestClient) -> dict[str, str]:
    """登录测试管理员并返回 Bearer 认证头。"""
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "admin123"},
    )
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def create_host(client: TestClient) -> dict[str, Any]:
    """创建用于任务分析 API 测试的主机。"""
    response = client.post(
        "/api/v1/hosts",
        headers=auth_headers(client),
        json={
            "name": "api-host",
            "ip_address": "192.0.2.20",
            "ssh_port": 22,
            "ssh_user": "root",
            "private_key_path": "/tmp/key",
            "description": None,
        },
    )
    assert response.status_code == 201
    return response.json()


def test_task_ai_analysis_api_creates_and_returns_analysis(client: TestClient) -> None:
    """任务日志 API 应返回 AI 分析，分析接口应能按任务生成诊断报告。"""
    host = create_host(client)
    task_response = client.post(
        "/api/v1/tasks",
        headers=auth_headers(client),
        json={
            "name": "Analyze task",
            "module_key": "system_inspection",
            "module_task_key": "check_disk",
            "target_type": "hosts",
            "target_ids": [host["id"]],
            "parameters": {},
        },
    )
    assert task_response.status_code == 202
    task_id = task_response.json()["id"]

    # 直接写入失败结果，避免 API 测试连接真实 Celery 或远端主机。
    from backend.app.core.database import get_db
    from backend.app.main import app

    db = next(app.dependency_overrides[get_db]())
    try:
        db.add(
            TaskResult(
                task_id=task_id,
                host_id=host["id"],
                status="failed",
                stdout="",
                stderr="Connection timed out during disk check",
                raw_event_data=json.dumps([
                    {"event": "runner_on_unreachable", "event_data": {"host": "api-host"}}
                ]),
            )
        )
        db.commit()
    finally:
        db.close()

    analysis_response = client.post(
        f"/api/v1/tasks/{task_id}/ai-analysis",
        headers=auth_headers(client),
    )

    assert analysis_response.status_code == 201
    analysis = analysis_response.json()
    assert analysis["summary"].startswith("任务 Analyze task")
    assert analysis["content"]["risk_level"] == "medium"
    assert "Connection timed out" in analysis["content"]["key_evidence"][0]

    logs_response = client.get(f"/api/v1/tasks/{task_id}/logs")
    assert logs_response.status_code == 200
    assert logs_response.json()["ai_analyses"][0]["id"] == analysis["id"]
