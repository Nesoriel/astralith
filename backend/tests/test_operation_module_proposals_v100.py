import json
from datetime import datetime, timezone

from starlette.testclient import TestClient
from sqlalchemy.orm import Session

from backend.app.models.gitops import AiProposal
from backend.app.schemas.operation_module import OperationModuleProposalCreate
from backend.app.services.operation_module_proposal_service import OperationModuleProposalService


def auth_headers(client: TestClient) -> dict[str, str]:
    """登录测试管理员并返回认证头。"""
    response = client.post("/api/v1/auth/login", json={"username": "admin", "password": "admin123"})
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def seed_ai_proposal(db_session: Session) -> AiProposal:
    """准备一个可转化为运维模块提案的 AI Runbook 提案。"""
    proposal = AiProposal(
        proposal_type="runbook",
        title="Docker Compose 服务重启 Runbook",
        summary="容器服务异常时，生成受控 restart 模块草案。",
        content_json=json.dumps(
            {
                "steps": ["检查 compose 配置", "重启指定服务", "检查服务状态"],
                "rollback_plan": "如重启失败，保留原 compose 文件并提示人工检查日志。",
            },
            ensure_ascii=False,
        ),
        risk_level="medium",
        status="approved",
        created_at=datetime.now(timezone.utc),
    )
    db_session.add(proposal)
    db_session.commit()
    db_session.refresh(proposal)
    return proposal


def test_create_operation_module_proposal_validates_safe_playbook(db_session: Session) -> None:
    """服务应创建可复核运维模块提案并保存语法/风险校验记录。"""
    service = OperationModuleProposalService(db_session)
    proposal = service.create_proposal(
        OperationModuleProposalCreate(
            title="Docker Compose Restart",
            problem_summary="服务异常时重启指定 Compose 服务。",
            module_key="docker_compose_restart",
            task_key="restart_service",
            risk_level="medium",
            parameter_schema={"service_name": {"type": "string"}},
            runbook="1. 检查配置；2. 重启服务；3. 查看状态。",
            playbook={"tasks": [{"ansible.builtin.command": "docker compose restart {{ service_name }}"}]},
            test_plan=["ansible-playbook --syntax-check", "check mode dry-run explanation"],
            rollback_notes="再次执行 docker compose up -d 或人工恢复上一版本 compose。",
        )
    )

    assert proposal.status == "draft"
    assert proposal.validation_status == "passed"
    assert proposal.dangerous_command_detected is False
    assert "syntax-check" in proposal.validation_output


def test_dangerous_command_marks_proposal_blocked(db_session: Session) -> None:
    """包含危险命令的模块提案必须被标记为 blocked，不能伪装成安全草案。"""
    proposal = OperationModuleProposalService(db_session).create_proposal(
        OperationModuleProposalCreate(
            title="Unsafe Cleanup",
            problem_summary="危险清理示例。",
            module_key="unsafe_cleanup",
            task_key="delete_root",
            risk_level="high",
            parameter_schema={},
            runbook="不要执行。",
            playbook={"tasks": [{"ansible.builtin.shell": "rm -rf /"}]},
            test_plan=["blocked by policy"],
            rollback_notes="不可安全回滚。",
        )
    )

    assert proposal.status == "blocked"
    assert proposal.validation_status == "failed"
    assert proposal.dangerous_command_detected is True


def test_generate_operation_module_proposal_from_ai_proposal(db_session: Session) -> None:
    """服务应能从已批准 AI 提案生成运维模块提案草案。"""
    ai_proposal = seed_ai_proposal(db_session)

    proposal = OperationModuleProposalService(db_session).generate_from_ai_proposal(ai_proposal.id)

    assert proposal.source_ai_proposal_id == ai_proposal.id
    assert proposal.module_key == "docker_compose_restart"
    assert proposal.task_key == "restart_service"
    assert proposal.status == "draft"
    assert proposal.validation_status == "passed"


def test_operation_module_proposal_api_review_and_export(client: TestClient) -> None:
    """API 应支持创建、审批、标记 implemented 与导出模块草案。"""
    headers = auth_headers(client)
    payload = {
        "title": "Docker Compose Restart",
        "problem_summary": "服务异常时重启指定 Compose 服务。",
        "module_key": "docker_compose_restart",
        "task_key": "restart_service",
        "risk_level": "medium",
        "parameter_schema": {"service_name": {"type": "string"}},
        "runbook": "检查配置并重启指定服务。",
        "playbook": {"tasks": [{"ansible.builtin.command": "docker compose restart {{ service_name }}"}]},
        "test_plan": ["syntax-check", "人工复核"],
        "rollback_notes": "恢复上一版本 compose 后重新 up。",
    }

    create_response = client.post("/api/v1/operation-module-proposals", headers=headers, json=payload)
    assert create_response.status_code == 201
    proposal_id = create_response.json()["id"]

    approve_response = client.post(
        f"/api/v1/operation-module-proposals/{proposal_id}/approve",
        headers=headers,
        json={"review_comment": "正式版审核通过。"},
    )
    assert approve_response.status_code == 200
    assert approve_response.json()["status"] == "approved"

    implement_response = client.post(
        f"/api/v1/operation-module-proposals/{proposal_id}/implement",
        headers=headers,
        json={"review_comment": "已作为模块草案导出。"},
    )
    assert implement_response.status_code == 200
    assert implement_response.json()["status"] == "implemented"

    export_response = client.get(f"/api/v1/operation-module-proposals/{proposal_id}/export")
    assert export_response.status_code == 200
    export_body = export_response.json()
    assert export_body["module_key"] == "docker_compose_restart"
    assert "playbook" in export_body
