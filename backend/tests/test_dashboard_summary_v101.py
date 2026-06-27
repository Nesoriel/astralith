import json
from datetime import datetime, timezone

from starlette.testclient import TestClient
from sqlalchemy.orm import Session

from backend.app.models.gitops import AiProposal, ApplyPlan, GitOpsRepository, PolicyResult, ResourceDiff
from backend.app.models.host import Host, HostGroup
from backend.app.models.operation_module import OperationModuleProposal
from backend.app.models.scheduled_job import ScheduledJob
from backend.app.models.task import AiAnalysisResult, EvidencePack, Task, TaskResult


def seed_dashboard_data(db_session: Session) -> None:
    """准备 Dashboard Summary 需要聚合的最小数据。"""
    host = Host(
        name="demo-host",
        ip_address="127.0.0.1",
        ssh_port=22,
        ssh_user="root",
        private_key_path="/tmp/id_rsa",
        description="demo",
    )
    db_session.add(host)
    db_session.add(HostGroup(name="demo-group", description="demo"))
    db_session.add(
        Task(
            name="success task",
            module_key="system_inspection",
            module_task_key="check_disk",
            status="success",
            target_type="hosts",
            target_ids_json="[]",
            parameters_json="{}",
        )
    )
    failed_task = Task(
        name="failed task",
        module_key="service_manage",
        module_task_key="service_status",
        status="failed",
        target_type="hosts",
        target_ids_json="[]",
        parameters_json="{}",
    )
    db_session.add(failed_task)
    db_session.add(
        ScheduledJob(
            name="daily check",
            module_key="system_inspection",
            module_task_key="check_disk",
            target_type="hosts",
            target_ids_json="[]",
            parameters_json="{}",
            schedule_type="interval",
            interval_seconds=3600,
            enabled=True,
        )
    )
    repo = GitOpsRepository(
        name="infra",
        repo_url="/tmp/infra",
        branch="main",
        local_path="/tmp/checkout",
        auth_type="none",
        enabled=True,
    )
    db_session.add(repo)
    db_session.commit()
    db_session.refresh(repo)
    diff = ResourceDiff(
        repository_id=repo.id,
        resource_type="stack",
        resource_key="uptime-kuma",
        diff_type="create",
        before_json=None,
        after_json="{}",
        risk_level="medium",
    )
    db_session.add(diff)
    db_session.commit()
    db_session.refresh(diff)
    plan = ApplyPlan(
        repository_id=repo.id,
        diff_id=diff.id,
        plan_json="{}",
        status="pending_review",
        policy_status="blocked",
    )
    db_session.add(plan)
    db_session.commit()
    db_session.refresh(plan)
    db_session.add(PolicyResult(repository_id=repo.id, plan_id=plan.id, rule_key="no_latest", severity="high", passed=False, message="blocked"))
    db_session.add(AiProposal(proposal_type="runbook", title="proposal", summary="summary", content_json="{}", risk_level="medium", status="draft", created_at=datetime.now(timezone.utc)))
    db_session.add(OperationModuleProposal(title="module proposal", problem_summary="summary", module_key="demo", task_key="task", risk_level="medium", parameter_schema_json="{}", runbook="runbook", playbook_json="{}", test_plan_json="[]", rollback_notes="rollback", status="draft", validation_status="passed", dangerous_command_detected=False, created_at=datetime.now(timezone.utc)))
    db_session.commit()
    db_session.refresh(failed_task)
    task_result = TaskResult(task_id=failed_task.id, host_id=host.id, status="failed", stdout="", stderr="failed", raw_event_data="[]")
    db_session.add(task_result)
    db_session.commit()
    db_session.refresh(task_result)
    evidence = EvidencePack(task_result_id=task_result.id, host_id=host.id, content_json=json.dumps({"stderr": "failed"}), created_at=datetime.now(timezone.utc))
    db_session.add(evidence)
    db_session.commit()
    db_session.refresh(evidence)
    db_session.add(AiAnalysisResult(evidence_pack_id=evidence.id, summary="analysis", content_json="{}", model_name="test", created_at=datetime.now(timezone.utc)))
    db_session.commit()


def test_dashboard_summary_service_counts_platform_metrics(db_session: Session) -> None:
    """Dashboard Summary 服务应聚合平台核心能力指标。"""
    from backend.app.services.dashboard_service import DashboardService

    seed_dashboard_data(db_session)

    summary = DashboardService(db_session).get_summary()

    assert summary.hosts == 1
    assert summary.host_groups == 1
    assert summary.operation_modules >= 2
    assert summary.operation_tasks >= 2
    assert summary.tasks_total == 2
    assert summary.tasks_failed == 1
    assert summary.tasks_success_rate == 0.5
    assert summary.scheduled_jobs == 1
    assert summary.gitops_repositories == 1
    assert summary.resource_diffs == 1
    assert summary.pending_apply_plans == 1
    assert summary.blocked_policy_results == 1
    assert summary.ai_analyses == 1
    assert summary.pending_ai_proposals == 1
    assert summary.pending_module_proposals == 1


def test_dashboard_summary_api_returns_metrics(client: TestClient) -> None:
    """Dashboard Summary API 应返回前端工作台所需指标。"""
    from backend.app.core.database import get_db
    from backend.app.main import app

    db = next(app.dependency_overrides[get_db]())
    try:
        seed_dashboard_data(db)
    finally:
        db.close()

    response = client.get("/api/v1/dashboard/summary")

    assert response.status_code == 200
    body = response.json()
    assert body["hosts"] == 1
    assert body["tasks_total"] == 2
    assert body["tasks_success_rate"] == 0.5
    assert body["pending_apply_plans"] == 1
    assert body["pending_ai_proposals"] == 1
    assert body["pending_module_proposals"] == 1
