from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path


def request_json(method: str, url: str, token: str | None = None, payload: dict | None = None) -> tuple[int, dict | list]:
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            body = response.read().decode("utf-8")
            return response.status, json.loads(body) if body else {}
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8")
        return exc.code, json.loads(body) if body else {}


def wait_for_health(base_url: str) -> None:
    deadline = time.time() + 20
    while time.time() < deadline:
        try:
            status, payload = request_json("GET", f"{base_url}/health")
            if status == 200 and isinstance(payload, dict) and payload.get("status") == "ok":
                return
        except Exception:
            pass
        time.sleep(0.5)
    raise RuntimeError("FastAPI server did not become healthy")


def create_source_repo(root: Path) -> Path:
    repo_path = root / "infra"
    (repo_path / "hosts").mkdir(parents=True)
    (repo_path / "stacks" / "uptime-kuma").mkdir(parents=True)
    (repo_path / "modules" / "docker_compose_restart").mkdir(parents=True)
    (repo_path / "policies").mkdir(parents=True)
    (repo_path / "hosts" / "proxy-01.yaml").write_text("name: proxy-01\nip_address: 192.0.2.10\n", encoding="utf-8")
    (repo_path / "stacks" / "uptime-kuma" / "stack.yaml").write_text("name: uptime-kuma\nhost: monitoring-01\n", encoding="utf-8")
    (repo_path / "modules" / "docker_compose_restart" / "module.yaml").write_text("module_key: docker_compose_restart\n", encoding="utf-8")
    (repo_path / "policies" / "compose-security.yaml").write_text("rule_key: no_latest\nseverity: medium\n", encoding="utf-8")
    subprocess.run(["git", "init"], cwd=repo_path, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Verify"], cwd=repo_path, check=True)
    subprocess.run(["git", "config", "user.email", "verify@example.com"], cwd=repo_path, check=True)
    subprocess.run(["git", "add", "."], cwd=repo_path, check=True)
    subprocess.run(["git", "commit", "-m", "seed desired state"], cwd=repo_path, check=True, capture_output=True)
    return repo_path


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    with tempfile.TemporaryDirectory(prefix="astralith-v060-") as tmpdir:
        tmp_root = Path(tmpdir)
        db_path = tmp_root / "real-v060.db"
        source_repo = create_source_repo(tmp_root)
        env = os.environ.copy()
        env["ASTRALITH_DATABASE_URL"] = f"sqlite:///{db_path}"
        process = subprocess.Popen(
            ["uv", "run", "uvicorn", "backend.app.main:app", "--host", "127.0.0.1", "--port", "18060"],
            cwd=repo_root,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        try:
            base_url = "http://127.0.0.1:18060"
            wait_for_health(base_url)
            status, login = request_json(
                "POST",
                f"{base_url}/api/v1/auth/login",
                payload={"username": "admin", "password": "admin123"},
            )
            assert status == 200 and isinstance(login, dict), login
            token = str(login["access_token"])
            status, repository = request_json(
                "POST",
                f"{base_url}/api/v1/gitops-repositories",
                token=token,
                payload={
                    "name": "real v0.6.0 infra",
                    "repo_url": str(source_repo),
                    "branch": "master",
                    "local_path": str(tmp_root / "checkout"),
                    "auth_type": "none",
                    "enabled": True,
                },
            )
            assert status == 201 and isinstance(repository, dict), repository
            repository_id = repository["id"]
            status, sync_run = request_json(
                "POST",
                f"{base_url}/api/v1/gitops-repositories/{repository_id}/sync",
                token=token,
            )
            assert status == 200 and isinstance(sync_run, dict), sync_run
            assert sync_run["status"] == "success", sync_run
            status, resources = request_json(
                "GET",
                f"{base_url}/api/v1/gitops-repositories/{repository_id}/desired-resources",
            )
            assert status == 200 and isinstance(resources, list), resources
            keys = {(item["resource_type"], item["resource_key"]) for item in resources}
            assert keys == {
                ("host", "proxy-01"),
                ("stack", "uptime-kuma"),
                ("module", "docker_compose_restart"),
                ("policy", "compose-security"),
            }, keys
            print(json.dumps({
                "status": "ok",
                "repository_id": repository_id,
                "sync_run_id": sync_run["id"],
                "commit_sha": sync_run["commit_sha"],
                "resource_count": len(resources),
                "resource_keys": sorted([f"{kind}:{key}" for kind, key in keys]),
            }, ensure_ascii=False, indent=2))
            return 0
        finally:
            process.terminate()
            try:
                output, _ = process.communicate(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                output, _ = process.communicate(timeout=5)
            if process.returncode not in {0, -15, None}:
                print(output, file=sys.stderr)


if __name__ == "__main__":
    raise SystemExit(main())
