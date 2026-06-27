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


def request_json(method: str, url: str, token: str | None = None, payload: dict | None = None) -> tuple[int, dict]:
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
            if status == 200 and payload.get("status") == "ok":
                return
        except Exception:
            pass
        time.sleep(0.5)
    raise RuntimeError("FastAPI server did not become healthy")


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    with tempfile.TemporaryDirectory(prefix="astralith-v050-") as tmpdir:
        db_path = Path(tmpdir) / "real-v050.db"
        env = os.environ.copy()
        env["ASTRALITH_DATABASE_URL"] = f"sqlite:///{db_path}"
        env["ASTRALITH_REDIS_URL"] = "redis://127.0.0.1:6379/15"
        process = subprocess.Popen(
            ["uv", "run", "uvicorn", "backend.app.main:app", "--host", "127.0.0.1", "--port", "18050"],
            cwd=repo_root,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        try:
            base_url = "http://127.0.0.1:18050"
            wait_for_health(base_url)

            status, login = request_json(
                "POST",
                f"{base_url}/api/v1/auth/login",
                payload={"username": "admin", "password": "admin123"},
            )
            assert status == 200, login
            token = login["access_token"]

            status, host = request_json(
                "POST",
                f"{base_url}/api/v1/hosts",
                token=token,
                payload={
                    "name": "real-v050-host",
                    "ip_address": "192.0.2.50",
                    "ssh_port": 22,
                    "ssh_user": "root",
                    "private_key_path": "/tmp/key",
                    "description": "real v0.5.0 verification",
                },
            )
            assert status == 201, host

            # 真实服务已启动并连接临时 SQLite；为避免验证环境依赖 Redis/Celery，
            # 这里直接写入一条已经完成的失败任务与结果，再用真实 HTTP API 验证 v0.5.0 分析链路。
            import sqlite3

            connection = sqlite3.connect(db_path)
            try:
                cursor = connection.execute(
                    """
                    INSERT INTO tasks (
                        name, module_key, module_task_key, status, target_type, target_ids_json,
                        parameters_json, created_at, updated_at, started_at, finished_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'), datetime('now'), datetime('now'))
                    """,
                    (
                        "Real v0.5.0 analysis task",
                        "system_inspection",
                        "check_disk",
                        "failed",
                        "hosts",
                        json.dumps([host["id"]]),
                        "{}",
                    ),
                )
                task_id = cursor.lastrowid
                connection.execute(
                    """
                    INSERT INTO task_results (task_id, host_id, status, stdout, stderr, raw_event_data, started_at, finished_at)
                    VALUES (?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
                    """,
                    (
                        task_id,
                        host["id"],
                        "failed",
                        "",
                        "No space left on device while collecting disk facts",
                        json.dumps([
                            {"event": "runner_on_failed", "event_data": {"host": "real-v050-host", "task": "check_disk"}}
                        ]),
                    ),
                )
                connection.commit()
            finally:
                connection.close()

            status, analysis = request_json(
                "POST",
                f"{base_url}/api/v1/tasks/{task_id}/ai-analysis",
                token=token,
            )
            assert status == 201, analysis
            assert analysis["summary"].startswith("任务 Real v0.5.0 analysis task"), analysis
            assert analysis["content"]["risk_level"] == "medium", analysis
            assert "No space left on device" in analysis["content"]["key_evidence"][0], analysis
            assert any("人工复核" in note for note in analysis["content"]["review_notes"]), analysis

            status, logs = request_json("GET", f"{base_url}/api/v1/tasks/{task_id}/logs")
            assert status == 200, logs
            assert logs["ai_analyses"][0]["id"] == analysis["id"], logs

            connection = sqlite3.connect(db_path)
            try:
                evidence_count = connection.execute("SELECT COUNT(*) FROM evidence_packs").fetchone()[0]
                analysis_count = connection.execute("SELECT COUNT(*) FROM ai_analysis_results").fetchone()[0]
            finally:
                connection.close()
            assert evidence_count == 1
            assert analysis_count == 1

            print(json.dumps({
                "status": "ok",
                "task_id": task_id,
                "analysis_id": analysis["id"],
                "summary": analysis["summary"],
                "evidence_count": evidence_count,
                "analysis_count": analysis_count,
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
