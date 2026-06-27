import json
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models.gitops import ApplyPlan, GitOpsApplyRun, GitOpsRepository, ResourceDiff
from backend.app.services.ansible_service import AnsibleService


class GitOpsApplyService:
    """Docker Compose GitOps Apply 服务。

    v0.8.0 只执行已审批且策略通过的 Docker Compose stack plan，并保存执行记录。
    """

    def __init__(self, db: Session, ansible_service: AnsibleService | None = None) -> None:
        self.db = db
        self.ansible_service = ansible_service or AnsibleService()

    def approve_plan(self, plan_id: int, reviewer_id: int) -> ApplyPlan:
        """人工审批 Apply Plan。"""
        plan = self._get_plan(plan_id)
        if plan.policy_status != "passed":
            raise ValueError("Cannot approve plan because policy validation did not pass")
        plan.status = "approved"
        plan.approved_by = reviewer_id
        plan.approved_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(plan)
        return plan

    def execute_plan(self, plan_id: int) -> GitOpsApplyRun:
        """执行已审批的 Docker Compose stack Apply Plan。"""
        plan = self._get_plan(plan_id)
        if plan.status != "approved":
            raise ValueError("Apply plan must be approved before execution")
        if plan.policy_status != "passed":
            raise ValueError("Apply plan policy status must be passed before execution")
        diff = self.db.get(ResourceDiff, plan.diff_id)
        if diff is None:
            raise ValueError("Resource diff not found")
        if diff.resource_type != "stack":
            raise ValueError("v0.8.0 only supports Docker Compose stack apply")
        repository = self.db.get(GitOpsRepository, plan.repository_id)
        if repository is None:
            raise ValueError("GitOps repository not found")
        desired_content = json.loads(diff.after_json or "{}")
        stack_name = str(desired_content.get("name") or diff.resource_key)
        target_path = f"/opt/stacks/{stack_name}"
        started_at = datetime.now(timezone.utc)
        apply_run = GitOpsApplyRun(
            repository_id=plan.repository_id,
            plan_id=plan.id,
            stack_name=stack_name,
            target_path=target_path,
            commit_sha=repository.last_commit_sha,
            status="running",
            rollback_json=json.dumps(
                {
                    "commit_sha": repository.last_commit_sha,
                    "previous_content": json.loads(diff.before_json) if diff.before_json else None,
                    "target_path": target_path,
                },
                ensure_ascii=False,
                sort_keys=True,
            ),
            started_at=started_at,
        )
        self.db.add(apply_run)
        self.db.commit()
        self.db.refresh(apply_run)

        playbook = _build_compose_playbook(stack_name, target_path, desired_content)
        result = self.ansible_service.run_module_task(_local_inventory(), playbook)
        apply_run.status = "success" if result.status in {"successful", "success"} else "failed"
        apply_run.stdout = result.stdout
        apply_run.stderr = result.stderr
        apply_run.raw_event_data = json.dumps(result.raw_events, ensure_ascii=False)
        apply_run.finished_at = datetime.now(timezone.utc)
        plan.status = "applied" if apply_run.status == "success" else "failed"
        self.db.commit()
        self.db.refresh(apply_run)
        return apply_run

    def list_apply_runs(self, repository_id: int) -> list[GitOpsApplyRun]:
        """查看仓库 Apply 执行记录。"""
        statement = (
            select(GitOpsApplyRun)
            .where(GitOpsApplyRun.repository_id == repository_id)
            .order_by(GitOpsApplyRun.id.desc())
        )
        return list(self.db.scalars(statement))

    def _get_plan(self, plan_id: int) -> ApplyPlan:
        """读取 Apply Plan，不存在时抛出业务错误。"""
        plan = self.db.get(ApplyPlan, plan_id)
        if plan is None:
            raise ValueError("Apply plan not found")
        return plan


def _build_compose_playbook(stack_name: str, target_path: str, desired_content: dict[str, Any]) -> list[dict[str, Any]]:
    """构造受控 Docker Compose apply playbook。"""
    compose_content = str(desired_content.get("compose_content") or _default_compose_content(desired_content))
    compose_file = str(desired_content.get("compose_file") or "compose.yaml")
    return [
        {
            "name": f"Apply Docker Compose stack {stack_name}",
            "hosts": "all",
            "become": True,
            "tasks": [
                {"name": "Create stack directory", "ansible.builtin.file": {"path": target_path, "state": "directory", "mode": "0755"}},
                {"name": "Write docker compose file", "ansible.builtin.copy": {"dest": f"{target_path}/{compose_file}", "content": compose_content, "mode": "0644"}},
                {"name": "Validate docker compose config", "ansible.builtin.command": "docker compose config", "args": {"chdir": target_path}},
                {"name": "Pull docker compose images", "ansible.builtin.command": "docker compose pull", "args": {"chdir": target_path}},
                {"name": "Apply docker compose stack", "ansible.builtin.command": "docker compose up -d", "args": {"chdir": target_path}},
            ],
        }
    ]


def _default_compose_content(desired_content: dict[str, Any]) -> str:
    """当 Git 资源没有直接提供 compose_content 时，生成最小演示 compose。"""
    service_name = str(desired_content.get("name") or "app")
    image = str(desired_content.get("image") or "hello-world:latest")
    return f"services:\n  {service_name}:\n    image: {image}\n"


def _local_inventory() -> dict[str, Any]:
    """v0.8.0 演示用本地 inventory；真实主机选择在后续版本接入。"""
    return {"all": {"hosts": {"localhost": {"ansible_connection": "local"}}}}
