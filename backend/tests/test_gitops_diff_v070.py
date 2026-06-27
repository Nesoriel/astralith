import json
from datetime import datetime, timezone

from starlette.testclient import TestClient
from sqlalchemy.orm import Session

from backend.app.models.gitops import ActualResource, DesiredResource, GitOpsRepository
from backend.app.schemas.gitops import ActualResourceUpsert
from backend.app.services.gitops_diff_service import GitOpsDiffService


def auth_headers(client: TestClient) -> dict[str, str]:
    """登录测试管理员并返回 Bearer 认证头。"""
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "admin123"},
    )
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def seed_repository_with_desired_stack(db_session: Session, *, image: str = "louislam/uptime-kuma:1") -> GitOpsRepository:
    """写入一个已同步的 desired stack 资源。"""
    repository = GitOpsRepository(
        name="diff infra",
        repo_url="/tmp/infra",
        branch="main",
        local_path="/tmp/checkout",
        auth_type="none",
        enabled=True,
        last_commit_sha="a" * 40,
        last_sync_at=datetime.now(timezone.utc),
    )
    db_session.add(repository)
    db_session.commit()
    db_session.refresh(repository)
    content = {"name": "uptime-kuma", "host": "monitoring-01", "image": image}
    db_session.add(
        DesiredResource(
            repository_id=repository.id,
            commit_sha=repository.last_commit_sha or "a" * 40,
            resource_type="stack",
            resource_key="uptime-kuma",
            file_path="stacks/uptime-kuma/stack.yaml",
            content_json=json.dumps(content, ensure_ascii=False, sort_keys=True),
            content_hash="desired-hash",
        )
    )
    db_session.commit()
    return repository


def test_generate_diff_creates_apply_plan_for_missing_actual_resource(db_session: Session) -> None:
    """当 Desired 中存在但 Actual 不存在时，应生成 create diff、apply plan 与 policy 结果。"""
    repository = seed_repository_with_desired_stack(db_session)

    diffs = GitOpsDiffService(db_session).generate_diffs(repository.id)

    assert len(diffs) == 1
    diff = diffs[0]
    assert diff.diff_type == "create"
    assert diff.resource_type == "stack"
    assert diff.resource_key == "uptime-kuma"
    assert diff.risk_level == "medium"

    plans = GitOpsDiffService(db_session).list_apply_plans(repository.id)
    assert len(plans) == 1
    assert plans[0].status == "pending_review"
    assert plans[0].policy_status == "passed"
    assert "docker compose" in plans[0].ai_summary

    policy_results = GitOpsDiffService(db_session).list_policy_results(repository.id)
    assert policy_results
    assert all(result.passed for result in policy_results)


def test_generate_diff_blocks_dangerous_latest_image_policy(db_session: Session) -> None:
    """策略校验应阻断使用 latest 镜像的 stack apply plan。"""
    repository = seed_repository_with_desired_stack(db_session, image="louislam/uptime-kuma:latest")

    diffs = GitOpsDiffService(db_session).generate_diffs(repository.id)

    assert diffs[0].risk_level == "high"
    plans = GitOpsDiffService(db_session).list_apply_plans(repository.id)
    policy_results = GitOpsDiffService(db_session).list_policy_results(repository.id)
    assert plans[0].policy_status == "blocked"
    assert any(result.rule_key == "compose_no_latest_image" and not result.passed for result in policy_results)


def test_generate_diff_detects_update_against_actual_resource(db_session: Session) -> None:
    """Actual 与 Desired 内容 hash 不一致时应生成 update diff。"""
    repository = seed_repository_with_desired_stack(db_session)
    service = GitOpsDiffService(db_session)
    service.upsert_actual_resource(
        ActualResourceUpsert(
            resource_type="stack",
            resource_key="uptime-kuma",
            source="manual-scan",
            content={"name": "uptime-kuma", "host": "monitoring-01", "image": "old/image:1"},
        )
    )

    diffs = service.generate_diffs(repository.id)

    assert len(diffs) == 1
    assert diffs[0].diff_type == "update"
    assert json.loads(diffs[0].before_json or "{}")["image"] == "old/image:1"
    assert json.loads(diffs[0].after_json or "{}")["image"] == "louislam/uptime-kuma:1"


def test_gitops_diff_api_generates_and_returns_plans(client: TestClient) -> None:
    """Diff API 应能基于已落库 Desired/Actual 生成差异、计划和策略结果。"""
    headers = auth_headers(client)
    create_response = client.post(
        "/api/v1/gitops-repositories",
        headers=headers,
        json={
            "name": "api diff repo",
            "repo_url": "/tmp/infra",
            "branch": "main",
            "local_path": "/tmp/checkout",
            "auth_type": "none",
            "enabled": True,
        },
    )
    assert create_response.status_code == 201
    repository_id = create_response.json()["id"]

    # 直接写入 desired resource，API 测试聚焦 diff/plan/policy 链路，不重复 Git 同步逻辑。
    from backend.app.core.database import get_db
    from backend.app.main import app

    db = next(app.dependency_overrides[get_db]())
    try:
        content = {"name": "uptime-kuma", "host": "monitoring-01", "image": "louislam/uptime-kuma:1"}
        db.add(
            DesiredResource(
                repository_id=repository_id,
                commit_sha="b" * 40,
                resource_type="stack",
                resource_key="uptime-kuma",
                file_path="stacks/uptime-kuma/stack.yaml",
                content_json=json.dumps(content, ensure_ascii=False, sort_keys=True),
                content_hash="desired-hash",
            )
        )
        db.commit()
    finally:
        db.close()

    diff_response = client.post(f"/api/v1/gitops-repositories/{repository_id}/diff", headers=headers)
    assert diff_response.status_code == 200
    assert diff_response.json()[0]["diff_type"] == "create"

    plans_response = client.get(f"/api/v1/gitops-repositories/{repository_id}/apply-plans")
    assert plans_response.status_code == 200
    assert plans_response.json()[0]["policy_status"] == "passed"

    policies_response = client.get(f"/api/v1/gitops-repositories/{repository_id}/policy-results")
    assert policies_response.status_code == 200
    assert policies_response.json()[0]["passed"] is True
