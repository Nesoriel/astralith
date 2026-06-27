from __future__ import annotations

import json, os, subprocess, sys, tempfile, time, urllib.error, urllib.request
from pathlib import Path


def req(url: str):
    request = urllib.request.Request(url, headers={"Content-Type": "application/json"}, method="GET")
    with urllib.request.urlopen(request, timeout=20) as response:
        body = response.read().decode()
        return response.status, json.loads(body) if body else {}


def wait_health(base_url: str) -> None:
    deadline = time.time() + 20
    while time.time() < deadline:
        try:
            status, body = req(f"{base_url}/health")
            if status == 200 and body.get("status") == "ok":
                return
        except Exception:
            pass
        time.sleep(0.5)
    raise RuntimeError("server did not become healthy")


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    with tempfile.TemporaryDirectory(prefix="astralith-v101-") as tmp:
        env = os.environ.copy()
        env["ASTRALITH_DATABASE_URL"] = f"sqlite:///{Path(tmp) / 'real-v101.db'}"
        proc = subprocess.Popen(
            ["uv", "run", "uvicorn", "backend.app.main:app", "--host", "127.0.0.1", "--port", "18101"],
            cwd=root, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
        )
        try:
            base = "http://127.0.0.1:18101"
            wait_health(base)
            status, summary = req(f"{base}/api/v1/dashboard/summary")
            assert status == 200, summary
            expected_keys = {
                "hosts", "host_groups", "operation_modules", "operation_tasks", "tasks_total",
                "tasks_failed", "tasks_success_rate", "scheduled_jobs", "gitops_repositories",
                "resource_diffs", "pending_apply_plans", "blocked_policy_results", "ai_analyses",
                "pending_ai_proposals", "pending_module_proposals",
            }
            assert expected_keys.issubset(summary), summary
            print(json.dumps({"status": "ok", "summary": summary}, ensure_ascii=False, indent=2))
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
