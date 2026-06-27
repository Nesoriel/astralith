from __future__ import annotations

import json, os, sqlite3, subprocess, sys, tempfile, time, urllib.error, urllib.request
from pathlib import Path


def req(method: str, url: str, token: str | None = None, payload: dict | None = None):
    data = json.dumps(payload).encode() if payload is not None else None
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            body = response.read().decode()
            return response.status, json.loads(body) if body else {}
    except urllib.error.HTTPError as exc:
        body = exc.read().decode()
        return exc.code, json.loads(body) if body else {}


def wait_health(base_url: str) -> None:
    deadline = time.time() + 20
    while time.time() < deadline:
        try:
            status, body = req("GET", f"{base_url}/health")
            if status == 200 and body.get("status") == "ok":
                return
        except Exception:
            pass
        time.sleep(0.5)
    raise RuntimeError("server did not become healthy")


def seed_plan(db_path: Path, repository_id: int) -> int:
    content = {"name": "uptime-kuma", "host": "monitoring-01", "image": "louislam/uptime-kuma:1"}
    payload = json.dumps(content, ensure_ascii=False, sort_keys=True)
    conn = sqlite3.connect(db_path)
    try:
        conn.execute("UPDATE gitops_repositories SET last_commit_sha=? WHERE id=?", ("f" * 40, repository_id))
        cursor = conn.execute(
            """
            INSERT INTO resource_diffs (repository_id, resource_type, resource_key, diff_type, before_json, after_json, risk_level, created_at)
            VALUES (?, 'stack', 'uptime-kuma', 'create', NULL, ?, 'medium', datetime('now'))
            """,
            (repository_id, payload),
        )
        diff_id = cursor.lastrowid
        cursor = conn.execute(
            """
            INSERT INTO apply_plans (repository_id, diff_id, plan_json, status, policy_status, ai_summary, created_at)
            VALUES (?, ?, ?, 'pending_review', 'passed', 'Plan to create docker compose stack uptime-kuma.', datetime('now'))
            """,
            (repository_id, diff_id, json.dumps({"resource_type": "stack", "resource_key": "uptime-kuma"})),
        )
        plan_id = cursor.lastrowid
        conn.commit()
        assert plan_id is not None
        return int(plan_id)
    finally:
        conn.close()


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    with tempfile.TemporaryDirectory(prefix="astralith-v090-") as tmp:
        db_path = Path(tmp) / "real-v090.db"
        env = os.environ.copy()
        env["ASTRALITH_DATABASE_URL"] = f"sqlite:///{db_path}"
        proc = subprocess.Popen(
            ["uv", "run", "uvicorn", "backend.app.main:app", "--host", "127.0.0.1", "--port", "18090"],
            cwd=root, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
        )
        try:
            base = "http://127.0.0.1:18090"
            wait_health(base)
            status, login = req("POST", f"{base}/api/v1/auth/login", payload={"username": "admin", "password": "admin123"})
            assert status == 200, login
            token = login["access_token"]
            status, repo = req("POST", f"{base}/api/v1/gitops-repositories", token=token, payload={
                "name": "real v0.9.0 proposal repo", "repo_url": "/tmp/infra", "branch": "main",
                "local_path": str(Path(tmp) / "checkout"), "auth_type": "none", "enabled": True,
            })
            assert status == 201, repo
            plan_id = seed_plan(db_path, repo["id"])
            status, proposal = req("POST", f"{base}/api/v1/gitops-repositories/apply-plans/{plan_id}/ai-proposal", token=token)
            assert status == 201 and proposal["proposal_type"] == "gitops_change", proposal
            proposal_id = proposal["id"]
            status, proposals = req("GET", f"{base}/api/v1/ai-proposals")
            assert status == 200 and len(proposals) == 1, proposals
            status, approved = req("POST", f"{base}/api/v1/ai-proposals/{proposal_id}/approve", token=token, payload={"review_comment": "真实服务验证通过。"})
            assert status == 200 and approved["status"] == "approved", approved
            print(json.dumps({
                "status": "ok", "repository_id": repo["id"], "plan_id": plan_id,
                "proposal_id": proposal_id, "proposal_type": proposal["proposal_type"],
                "proposal_status": approved["status"], "proposal_count": len(proposals),
            }, ensure_ascii=False, indent=2))
            return 0
        finally:
            proc.terminate()
            try:
                output, _ = proc.communicate(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill(); output, _ = proc.communicate(timeout=5)
            if proc.returncode not in {0, -15, None}:
                print(output, file=sys.stderr)


if __name__ == "__main__":
    raise SystemExit(main())
