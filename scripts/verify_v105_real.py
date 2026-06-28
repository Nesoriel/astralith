from __future__ import annotations

import json, os, subprocess, sys, tempfile, time, urllib.error, urllib.request
from pathlib import Path


def req(method: str, url: str, token: str | None = None, payload: dict | None = None):
    data = json.dumps(payload).encode() if payload is not None else None
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(request, timeout=20) as response:
        body = response.read().decode()
        return response.status, json.loads(body) if body else {}


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


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    with tempfile.TemporaryDirectory(prefix="astralith-v105-") as tmp:
        env = os.environ.copy()
        env["ASTRALITH_DATABASE_URL"] = f"sqlite:///{Path(tmp) / 'real-v105.db'}"
        proc = subprocess.Popen(
            ["uv", "run", "uvicorn", "backend.app.main:app", "--host", "127.0.0.1", "--port", "18105"],
            cwd=root, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
        )
        try:
            base = "http://127.0.0.1:18105"
            wait_health(base)
            _, login = req("POST", f"{base}/api/v1/auth/login", payload={"username": "admin", "password": "admin123"})
            token = login["access_token"]
            _, modules = req("GET", f"{base}/api/v1/operation-modules")
            _, summary = req("GET", f"{base}/api/v1/dashboard/summary")
            _, proposal = req("POST", f"{base}/api/v1/ai-proposals", token=token, payload={
                "proposal_type": "runbook",
                "title": "frontend workbench verification",
                "summary": "verify proposal flow",
                "content": {"steps": ["review", "export"], "rollback_plan": "manual"},
                "risk_level": "low",
            })
            req("POST", f"{base}/api/v1/ai-proposals/{proposal['id']}/approve", token=token, payload={"review_comment": "verified"})
            _, module_proposal = req("POST", f"{base}/api/v1/operation-module-proposals/from-ai-proposals/{proposal['id']}", token=token)
            _, export_draft = req("GET", f"{base}/api/v1/operation-module-proposals/{module_proposal['id']}/export")
            print(json.dumps({
                "status": "ok",
                "modules": len(modules),
                "operation_tasks": summary["operation_tasks"],
                "ai_proposal_status": proposal["status"],
                "module_proposal_status": module_proposal["status"],
                "export_module_key": export_draft["module_key"],
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
