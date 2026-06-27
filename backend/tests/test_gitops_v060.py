import subprocess
from pathlib import Path

from starlette.testclient import TestClient
from sqlalchemy.orm import Session

from backend.app.models.gitops import DesiredResource, GitOpsRepository, GitOpsSyncRun
from backend.app.schemas.gitops import GitOpsRepositoryCreate
from backend.app.services.gitops_service import GitOpsService


def auth_headers(client: TestClient) -> dict[str, str]:
    """登录测试管理员并返回 Bearer 认证头。"""
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "admin123"},
    )
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def create_desired_state_repo(tmp_path: Path) -> Path:
    """创建一个真实 Git desired-state 仓库用于同步测试。"""
    repo_path = tmp_path / "astralith-infra"
    (repo_path / "hosts").mkdir(parents=True)
    (repo_path / "stacks" / "uptime-kuma").mkdir(parents=True)
    (repo_path / "modules" / "docker_compose_restart").mkdir(parents=True)
    (repo_path / "policies").mkdir(parents=True)
    (repo_path / "hosts" / "proxy-01.yaml").write_text(
        "name: proxy-01\nip_address: 192.0.2.10\nssh_user: root\n",
        encoding="utf-8",
    )
    (repo_path / "stacks" / "uptime-kuma" / "stack.yaml").write_text(
        "name: uptime-kuma\nhost: monitoring-01\ncompose_file: compose.yaml\n",
        encoding="utf-8",
    )
    (repo_path / "modules" / "docker_compose_restart" / "module.yaml").write_text(
        "module_key: docker_compose_restart\ntitle: Restart Docker Compose Stack\n",
        encoding="utf-8",
    )
    (repo_path / "policies" / "compose-security.yaml").write_text(
        "rule_key: no_privileged\nseverity: high\n",
        encoding="utf-8",
    )
    subprocess.run(["git", "init"], cwd=repo_path, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=repo_path, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo_path, check=True)
    subprocess.run(["git", "add", "."], cwd=repo_path, check=True)
    subprocess.run(["git", "commit", "-m", "seed desired state"], cwd=repo_path, check=True, capture_output=True)
    return repo_path


def test_gitops_service_syncs_repository_and_parses_desired_resources(db_session: Session, tmp_path: Path) -> None:
    """GitOps 服务应同步真实 Git 仓库并解析 hosts/stacks/modules/policies。"""
    source_repo = create_desired_state_repo(tmp_path)
    service = GitOpsService(db_session)
    repository = service.create_repository(
        GitOpsRepositoryCreate(
            name="demo infra",
            repo_url=str(source_repo),
            branch="master",
            local_path=str(tmp_path / "checkout"),
            enabled=True,
        )
    )

    sync_run = service.sync_repository(repository.id)

    resources = service.list_desired_resources(repository.id)
    resource_keys = {(item.resource_type, item.resource_key) for item in resources}
    assert sync_run.status == "success"
    assert len(sync_run.commit_sha) == 40
    assert repository.last_sync_at is not None
    assert resource_keys == {
        ("host", "proxy-01"),
        ("stack", "uptime-kuma"),
        ("module", "docker_compose_restart"),
        ("policy", "compose-security"),
    }
    assert resources[0].commit_sha == sync_run.commit_sha


def test_gitops_service_records_sync_failure(db_session: Session, tmp_path: Path) -> None:
    """同步失败时应保存失败记录与错误信息。"""
    service = GitOpsService(db_session)
    repository = service.create_repository(
        GitOpsRepositoryCreate(
            name="missing infra",
            repo_url=str(tmp_path / "missing"),
            branch="main",
            local_path=str(tmp_path / "checkout"),
            enabled=True,
        )
    )

    sync_run = service.sync_repository(repository.id)

    assert sync_run.status == "failed"
    assert "missing" in (sync_run.stderr or "")
    assert db_session.query(GitOpsSyncRun).count() == 1
    assert db_session.query(DesiredResource).count() == 0


def test_gitops_repository_api_syncs_and_returns_desired_resources(client: TestClient, tmp_path: Path) -> None:
    """GitOps API 应支持配置仓库、手动同步并查看 Desired Resources。"""
    source_repo = create_desired_state_repo(tmp_path)
    headers = auth_headers(client)
    create_response = client.post(
        "/api/v1/gitops-repositories",
        headers=headers,
        json={
            "name": "api infra",
            "repo_url": str(source_repo),
            "branch": "master",
            "local_path": str(tmp_path / "api-checkout"),
            "enabled": True,
        },
    )
    assert create_response.status_code == 201
    repository_id = create_response.json()["id"]

    sync_response = client.post(f"/api/v1/gitops-repositories/{repository_id}/sync", headers=headers)

    assert sync_response.status_code == 200
    assert sync_response.json()["status"] == "success"

    resources_response = client.get(f"/api/v1/gitops-repositories/{repository_id}/desired-resources")
    assert resources_response.status_code == 200
    keys = {(item["resource_type"], item["resource_key"]) for item in resources_response.json()}
    assert ("host", "proxy-01") in keys
    assert ("stack", "uptime-kuma") in keys

    list_response = client.get("/api/v1/gitops-repositories")
    assert list_response.status_code == 200
    assert list_response.json()[0]["last_commit_sha"] == sync_response.json()["commit_sha"]
