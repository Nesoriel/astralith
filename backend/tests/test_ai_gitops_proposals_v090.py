import json
from datetime import datetime, timezone

from starlette.testclient import TestClient
from sqlalchemy.orm import Session

from backend.app.models.gitops import ApplyPlan, DesiredResource, GitOpsRepository, ResourceDiff
from backend.app.schemas.gitops import AiProposalCreate
from backend.app.services.ai_proposal_service import AiProposalService


def auth_headers(client: TestClient) -> dict[str, str]:
    """登录测试管理员并返回 Bearer 认证头。"""
    response = client.post("/api/v1/auth/login", json={"username": "admin", "password": "admin123"})
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def seed_stack_plan(db_session: Session) -> ApplyPlan:
    """创建一个可用于生成 AI GitOps 提案的 stack plan。"""
    repository = GitOpsRepository(
        name="proposal infra",
        repo_url="/tmp/infra",
        branch="main",
        local_path="/tmp/checkout",
        auth_type="none",
        enabled=True,
        last_commit_sha="e" * 40,
        last_sync_at=datetime.now(timezone.utc),
    )
    db_session.add(repository)
    db_session.commit()
    db_session.refresh(repository)
    content = {"name": "uptime-kuma", "host": "monitoring-01", "image": "louislam/uptime-kuma:1"}
    db_session.add(
        DesiredResource(
            repository_id=repository.id,
            commit_sha=repository.last_commit_sha or "e" * 40,
            resource_type="stack",
            resource_key="uptime-kuma",
            file_path="stacks/uptime-kuma/stack.yaml",
            content_json=json.dumps(content, ensure_ascii=False, sort_keys=True),
            content_hash="proposal-stack-hash",
        )
    )
    diff = ResourceDiff(
        repository_id=repository.id,
        resource_type="stack",
        resource_key="uptime-kuma",
        diff_type="create",
        before_json=None,
        after_json=json.dumps(content, ensure_ascii=False, sort_keys=True),
        risk_level="medium",
    )
    db_session.add(diff)
    db_session.commit()
    db_session.refresh(diff)
    plan = ApplyPlan(
        repository_id=repository.id,
        diff_id=diff.id,
        plan_json=json.dumps({"resource_type": "stack", "resource_key": "uptime-kuma", "steps": ["review compose"]}, ensure_ascii=False),
        status="pending_review",
        policy_status="passed",
        ai_summary="Plan to create docker compose stack uptime-kuma.",
    )
    db_session.add(plan)
    db_session.commit()
    db_session.refresh(plan)
    return plan


def test_generate_gitops_change_proposal_from_apply_plan(db_session: Session) -> None:
    """AI 提案服务应从 Apply Plan 生成可复核 GitOps Change Proposal。"""
    plan = seed_stack_plan(db_session)
    service = AiProposalService(db_session)

    proposal = service.generate_from_apply_plan(plan.id)

    assert proposal.proposal_type == "gitops_change"
    assert proposal.status == "draft"
    assert proposal.source_type == "apply_plan"
    assert proposal.source_id == plan.id
    assert "uptime-kuma" in proposal.title
    content = json.loads(proposal.content_json)
    assert content["resource_key"] == "uptime-kuma"
    assert content["rollback_plan"]
    assert "人工复核" in content["review_notes"][0]


def test_create_manual_runbook_proposal(db_session: Session) -> None:
    """服务应支持创建手工 runbook 提案，便于毕业设计演示。"""
    proposal = AiProposalService(db_session).create_proposal(
        AiProposalCreate(
            proposal_type="runbook",
            title="磁盘空间排查 Runbook",
            summary="整理磁盘空间不足的排查步骤。",
            content={"steps": ["df -h", "du -sh /var/*"], "rollback_plan": "不直接修改文件。"},
            risk_level="low",
        )
    )

    assert proposal.id is not None
    assert proposal.status == "draft"
    assert proposal.proposal_type == "runbook"


def test_ai_proposal_api_generates_and_reviews_proposal(client: TestClient) -> None:
    """AI Proposal API 应支持生成、列表、批准和拒绝。"""
    headers = auth_headers(client)
    from backend.app.core.database import get_db
    from backend.app.main import app

    db = next(app.dependency_overrides[get_db]())
    try:
        plan = seed_stack_plan(db)
        plan_id = plan.id
    finally:
        db.close()

    generate_response = client.post(
        f"/api/v1/gitops-repositories/apply-plans/{plan_id}/ai-proposal",
        headers=headers,
    )
    assert generate_response.status_code == 201
    proposal_id = generate_response.json()["id"]

    list_response = client.get("/api/v1/ai-proposals")
    assert list_response.status_code == 200
    assert list_response.json()[0]["id"] == proposal_id

    approve_response = client.post(
        f"/api/v1/ai-proposals/{proposal_id}/approve",
        headers=headers,
        json={"review_comment": "同意作为 GitOps 变更草案继续评审。"},
    )
    assert approve_response.status_code == 200
    assert approve_response.json()["status"] == "approved"

    reject_response = client.post(
        f"/api/v1/ai-proposals/{proposal_id}/reject",
        headers=headers,
        json={"review_comment": "重新检查风险。"},
    )
    assert reject_response.status_code == 200
    assert reject_response.json()["status"] == "rejected"
