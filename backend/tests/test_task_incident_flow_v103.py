from datetime import datetime, timezone

from starlette.testclient import TestClient
from sqlalchemy.orm import Session

from backend.app.models.host import Host
from backend.app.models.task import AiAnalysisResult, EvidencePack, Task, TaskResult


def auth_headers(client: TestClient) -> dict[str, str]:
    """登录测试管理员并返回认证头。"""
    response = client.post("/api/v1/auth/login", json={"username": "admin", "password": "admin123"})
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def seed_failed_task_with_analysis(db_session: Session) -> int:
    """准备失败任务、任务结果、Evidence Pack 与 AI 分析。"""
    host = Host(
        name="demo-host",
        ip_address="127.0.0.1",
        ssh_port=22,
        ssh_user="root",
        private_key_path="/tmp/id_rsa",
        description="demo",
    )
    db_session.add(host)
    task = Task(
        name="failed service check",
        module_key="service_manage",
        module_task_key="service_status",
        status="failed",
        target_type="hosts",
        target_ids_json="[]",
        parameters_json='{"service_name":"nginx"}',
    )
    db_session.add(task)
    db_session.commit()
    db_session.refresh(task)
    db_session.refresh(host)
    result = TaskResult(task_id=task.id, host_id=host.id, status="failed", stdout="", stderr="systemctl failed", raw_event_data="[]")
    db_session.add(result)
    db_session.commit()
    db_session.refresh(result)
    evidence = EvidencePack(task_result_id=result.id, host_id=host.id, content_json='{"signals":{"stderr":"systemctl failed"}}', created_at=datetime.now(timezone.utc))
    db_session.add(evidence)
    db_session.commit()
    db_session.refresh(evidence)
    analysis = AiAnalysisResult(
        evidence_pack_id=evidence.id,
        summary="服务检查失败，需要人工复核。",
        content_json='{"risk_level":"medium","key_evidence":["systemctl failed"],"possible_causes":["服务异常"],"recommended_steps":["检查日志"],"review_notes":["必须人工复核"],"source":{"task_id":1}}',
        model_name="test",
        created_at=datetime.now(timezone.utc),
    )
    db_session.add(analysis)
    db_session.commit()
    return task.id


def test_task_incident_context_includes_evidence_and_proposals(client: TestClient) -> None:
    """任务故障上下文应串联日志、Evidence Pack、AI 分析与 AI Proposal。"""
    from backend.app.core.database import get_db
    from backend.app.main import app

    headers = auth_headers(client)
    db = next(app.dependency_overrides[get_db]())
    try:
        task_id = seed_failed_task_with_analysis(db)
    finally:
        db.close()

    proposal_response = client.post(
        f"/api/v1/tasks/{task_id}/ai-proposal",
        headers=headers,
        json={"analysis_id": 1},
    )
    assert proposal_response.status_code == 201

    response = client.get(f"/api/v1/tasks/{task_id}/incident-context")

    assert response.status_code == 200
    body = response.json()
    assert body["task"]["id"] == task_id
    assert len(body["results"]) == 1
    assert len(body["evidence_packs"]) == 1
    assert body["evidence_packs"][0]["content"]["signals"]["stderr"] == "systemctl failed"
    assert len(body["ai_analyses"]) == 1
    assert len(body["ai_proposals"]) == 1
    assert body["ai_proposals"][0]["source_type"] == "task"
