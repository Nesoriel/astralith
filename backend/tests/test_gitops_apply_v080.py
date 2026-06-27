import json
from datetime import datetime, timezone

from starlette.testclient import TestClient
from sqlalchemy.orm import Session

from backend.app.models.gitops import ApplyPlan, DesiredResource, GitOpsRepository, ResourceDiff
from backend.app.services.gitops_apply_service import GitOpsApplyService


def auth_headers(client: TestClient) -> dict[str, str]:
    """登录测试管理员并返回 Bearer 认证头。"""
    response = client.post("/api/v1/auth/login", json={"username": "admin", "password": "admin123"})
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def seed_stack_plan(db_session: Session, *, policy_status: str = "passed", approved: bool = False) -> ApplyPlan:
    """创建一个 Docker Compose stack Apply Plan。"""
    repository = GitOpsRepository(
        name="apply infra",
        repo_url="/tmp/infra",
        branch="main",
        local_path="/tmp/checkout",
        auth_type="none",
        enabled=True,
        last_commit_sha="c" * 40,
        last_sync_at=datetime.now(timezone.utc),
    )
    db_session.add(repository)
    db_session.commit()
    db_session.refresh(repository)
    content = {
        "name": "uptime-kuma",
        "host": "monitoring-01",
        "compose_file": "compose.yaml",
        "compose_content": "services:\n  uptime-kuma:\n    image: louislam/uptime-kuma:1\n",
    }
    db_session.add(
        DesiredResource(
            repository_id=repository.id,
            commit_sha=repository.last_commit_sha or "c" * 40,
            resource_type="stack",
            resource_key="uptime-kuma",
            file_path="stacks/uptime-kuma/stack.yaml",
            content_json=json.dumps(content, ensure_ascii=False, sort_keys=True),
            content_hash="stack-hash",
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
        plan_json=json.dumps({"resource_type": "stack", "resource_key": "uptime-kuma"}, ensure_ascii=False),
        status="approved" if approved else "pending_review",
        policy_status=policy_status,
        ai_summary="Plan to create docker compose stack uptime-kuma.",
        approved_by=1 if approved else None,
        approved_at=datetime.now(timezone.utc) if approved else None,
    )
    db_session.add(plan)
    db_session.commit()
    db_session.refresh(plan)
    return plan


class FakeAnsibleService:
    """记录 playbook 并返回成功结果的 Ansible 替身。"""

    def __init__(self) -> None:
        self.inventory: dict | None = None
        self.playbook: list[dict] | None = None

    def run_module_task(self, inventory: dict, playbook: list[dict]):
        from backend.app.services.ansible_service import AnsibleExecutionResult

        self.inventory = inventory
        self.playbook = playbook
        return AnsibleExecutionResult(
            status="successful",
            stdout="compose up ok",
            stderr="",
            raw_events=[{"event": "runner_on_ok"}],
        )


def test_approve_apply_plan_records_reviewer(db_session: Session) -> None:
    """人工审批应记录 reviewer 并把计划置为 approved。"""
    plan = seed_stack_plan(db_session)

    approved = GitOpsApplyService(db_session).approve_plan(plan.id, reviewer_id=1)

    assert approved.status == "approved"
    assert approved.approved_by == 1
    assert approved.approved_at is not None


def test_execute_approved_stack_plan_runs_controlled_ansible_and_records_apply_run(db_session: Session) -> None:
    """已审批且策略通过的 stack plan 应通过 AnsibleService 执行并保存 apply run。"""
    plan = seed_stack_plan(db_session, approved=True)
    fake_ansible = FakeAnsibleService()

    apply_run = GitOpsApplyService(db_session, ansible_service=fake_ansible).execute_plan(plan.id)

    assert apply_run.status == "success"
    assert apply_run.stack_name == "uptime-kuma"
    assert apply_run.target_path == "/opt/stacks/uptime-kuma"
    assert apply_run.stdout == "compose up ok"
    assert json.loads(apply_run.rollback_json)["commit_sha"] == "c" * 40
    assert fake_ansible.playbook is not None
    task_names = [task["name"] for task in fake_ansible.playbook[0]["tasks"]]
    assert "Validate docker compose config" in task_names
    assert "Apply docker compose stack" in task_names


def test_execute_plan_blocks_unapproved_or_policy_blocked_plan(db_session: Session) -> None:
    """未审批或策略阻断的计划不能执行。"""
    pending_plan = seed_stack_plan(db_session)
    blocked_plan = seed_stack_plan(db_session, policy_status="blocked", approved=True)
    service = GitOpsApplyService(db_session, ansible_service=FakeAnsibleService())

    try:
        service.execute_plan(pending_plan.id)
    except ValueError as exc:
        assert "approved" in str(exc)
    else:
        raise AssertionError("pending plan should not execute")

    try:
        service.execute_plan(blocked_plan.id)
    except ValueError as exc:
        assert "policy" in str(exc)
    else:
        raise AssertionError("policy blocked plan should not execute")


def test_gitops_apply_api_approves_and_executes_plan(client: TestClient, monkeypatch) -> None:
    """Apply API 应支持审批计划并触发受控执行记录。"""
    headers = auth_headers(client)
    create_response = client.post(
        "/api/v1/gitops-repositories",
        headers=headers,
        json={
            "name": "api apply repo",
            "repo_url": "/tmp/infra",
            "branch": "main",
            "local_path": "/tmp/checkout",
            "auth_type": "none",
            "enabled": True,
        },
    )
    assert create_response.status_code == 201
    repository_id = create_response.json()["id"]

    from backend.app.core.database import get_db
    from backend.app.main import app

    db = next(app.dependency_overrides[get_db]())
    try:
        plan = seed_stack_plan(db, approved=False)
        plan_id = plan.id
        repository_id = plan.repository_id
    finally:
        db.close()

    fake_ansible = FakeAnsibleService()
    monkeypatch.setattr("backend.app.api.routes.gitops.AnsibleService", lambda: fake_ansible)

    approve_response = client.post(f"/api/v1/gitops-repositories/apply-plans/{plan_id}/approve", headers=headers)
    assert approve_response.status_code == 200
    assert approve_response.json()["status"] == "approved"

    execute_response = client.post(f"/api/v1/gitops-repositories/apply-plans/{plan_id}/execute", headers=headers)
    assert execute_response.status_code == 200
    assert execute_response.json()["status"] == "success"

    runs_response = client.get(f"/api/v1/gitops-repositories/{repository_id}/apply-runs")
    assert runs_response.status_code == 200
    assert runs_response.json()[0]["stack_name"] == "uptime-kuma"
