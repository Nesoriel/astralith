from __future__ import annotations

import json, os, subprocess, sys, tempfile, time, urllib.error, urllib.request
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


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    with tempfile.TemporaryDirectory(prefix="astralith-v100-") as tmp:
        env = os.environ.copy()
        env["ASTRALITH_DATABASE_URL"] = f"sqlite:///{Path(tmp) / 'real-v100.db'}"
        proc = subprocess.Popen(
            ["uv", "run", "uvicorn", "backend.app.main:app", "--host", "127.0.0.1", "--port", "18100"],
            cwd=root, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
        )
        try:
            base = "http://127.0.0.1:18100"
            wait_health(base)
            status, login = req("POST", f"{base}/api/v1/auth/login", payload={"username": "admin", "password": "admin123"})
            assert status == 200, login
            token = login["access_token"]
            payload = {
                "title": "Docker Compose Restart",
                "problem_summary": "容器服务异常时生成可复核重启模块。",
                "module_key": "docker_compose_restart",
                "task_key": "restart_service",
                "risk_level": "medium",
                "parameter_schema": {"service_name": {"type": "string", "pattern": "^[a-zA-Z0-9_.@-]+$"}},
                "runbook": "检查 compose 配置，重启指定服务，复核状态。",
                "playbook": {"tasks": [{"ansible.builtin.command": "docker compose restart {{ service_name }}"}]},
                "test_plan": ["syntax-check", "manual review"],
                "rollback_notes": "恢复上一版本 compose 后重新 up。",
            }
            status, created = req("POST", f"{base}/api/v1/operation-module-proposals", token=token, payload=payload)
            assert status == 201 and created["validation_status"] == "passed", created
            proposal_id = created["id"]
            status, approved = req("POST", f"{base}/api/v1/operation-module-proposals/{proposal_id}/approve", token=token, payload={"review_comment": "正式版验证通过。"})
            assert status == 200 and approved["status"] == "approved", approved
            status, exported = req("GET", f"{base}/api/v1/operation-module-proposals/{proposal_id}/export")
            assert status == 200 and exported["module_key"] == "docker_compose_restart", exported
            status, implemented = req("POST", f"{base}/api/v1/operation-module-proposals/{proposal_id}/implement", token=token, payload={"review_comment": "导出草案完成。"})
            assert status == 200 and implemented["status"] == "implemented", implemented
            print(json.dumps({
                "status": "ok", "proposal_id": proposal_id,
                "validation_status": created["validation_status"],
                "final_status": implemented["status"],
                "export_module_key": exported["module_key"],
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
