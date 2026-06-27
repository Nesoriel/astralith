import hashlib
import json
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from backend.app.models.gitops import (
    ActualResource,
    ApplyPlan,
    DesiredResource,
    GitOpsRepository,
    PolicyResult,
    ResourceDiff,
)
from backend.app.schemas.gitops import (
    ActualResourceRead,
    ActualResourceUpsert,
    ApplyPlanRead,
    PolicyResultRead,
    ResourceDiffRead,
)


class GitOpsDiffService:
    """Desired / Actual Diff、Apply Plan 与 Policy 校验服务。

    v0.7.0 只生成可审核计划与策略结果，不执行任何远端变更。
    """

    def __init__(self, db: Session) -> None:
        self.db = db

    def upsert_actual_resource(self, payload: ActualResourceUpsert) -> ActualResource:
        """写入或更新 Actual Resource，用于后续与 Desired Resource 对账。"""
        content_json = _serialize_json(payload.content)
        content_hash = _hash_content(content_json)
        statement = select(ActualResource).where(
            ActualResource.resource_type == payload.resource_type,
            ActualResource.resource_key == payload.resource_key,
        )
        actual = self.db.scalar(statement)
        if actual is None:
            actual = ActualResource(
                resource_type=payload.resource_type,
                resource_key=payload.resource_key,
                source=payload.source,
                content_json=content_json,
                content_hash=content_hash,
                scanned_at=datetime.now(timezone.utc),
            )
            self.db.add(actual)
        else:
            actual.source = payload.source
            actual.content_json = content_json
            actual.content_hash = content_hash
            actual.scanned_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(actual)
        return actual

    def list_actual_resources(self) -> list[ActualResource]:
        """返回全部 Actual Resources。"""
        return list(self.db.scalars(select(ActualResource).order_by(ActualResource.resource_type, ActualResource.resource_key)))

    def generate_diffs(self, repository_id: int) -> list[ResourceDiff]:
        """基于某仓库的 Desired Resources 与全局 Actual Resources 生成差异。"""
        repository = self.db.get(GitOpsRepository, repository_id)
        if repository is None:
            raise ValueError("GitOps repository not found")
        desired_resources = list(
            self.db.scalars(select(DesiredResource).where(DesiredResource.repository_id == repository_id))
        )
        actual_resources = {
            (item.resource_type, item.resource_key): item
            for item in self.db.scalars(select(ActualResource))
        }

        self.db.execute(delete(PolicyResult).where(PolicyResult.repository_id == repository_id))
        self.db.execute(delete(ApplyPlan).where(ApplyPlan.repository_id == repository_id))
        self.db.execute(delete(ResourceDiff).where(ResourceDiff.repository_id == repository_id))
        self.db.flush()

        diffs: list[ResourceDiff] = []
        for desired in desired_resources:
            key = (desired.resource_type, desired.resource_key)
            actual = actual_resources.get(key)
            if actual is None:
                diff = _build_diff(repository_id, desired, None, "create")
            elif actual.content_hash != desired.content_hash:
                diff = _build_diff(repository_id, desired, actual, "update")
            else:
                continue
            self.db.add(diff)
            self.db.flush()
            plan = _build_apply_plan(repository_id, diff)
            self.db.add(plan)
            self.db.flush()
            policy_results = _validate_policy(repository_id, plan, diff)
            plan.policy_status = "blocked" if any(not result.passed for result in policy_results) else "passed"
            diff.risk_level = "high" if plan.policy_status == "blocked" else diff.risk_level
            self.db.add_all(policy_results)
            diffs.append(diff)

        self.db.commit()
        for diff in diffs:
            self.db.refresh(diff)
        return diffs

    def list_diffs(self, repository_id: int) -> list[ResourceDiff]:
        """返回资源差异列表。"""
        statement = (
            select(ResourceDiff)
            .where(ResourceDiff.repository_id == repository_id)
            .order_by(ResourceDiff.id)
        )
        return list(self.db.scalars(statement))

    def list_apply_plans(self, repository_id: int) -> list[ApplyPlan]:
        """返回 Apply Plan 列表。"""
        statement = select(ApplyPlan).where(ApplyPlan.repository_id == repository_id).order_by(ApplyPlan.id)
        return list(self.db.scalars(statement))

    def list_policy_results(self, repository_id: int) -> list[PolicyResult]:
        """返回策略校验结果。"""
        statement = (
            select(PolicyResult)
            .where(PolicyResult.repository_id == repository_id)
            .order_by(PolicyResult.id)
        )
        return list(self.db.scalars(statement))

    def actual_resource_to_schema(self, actual: ActualResource) -> ActualResourceRead:
        """转换 Actual Resource 响应。"""
        return ActualResourceRead(
            id=actual.id,
            resource_type=actual.resource_type,
            resource_key=actual.resource_key,
            source=actual.source,
            content=json.loads(actual.content_json),
            content_hash=actual.content_hash,
            scanned_at=actual.scanned_at,
        )

    def diff_to_schema(self, diff: ResourceDiff) -> ResourceDiffRead:
        """转换 Resource Diff 响应。"""
        return ResourceDiffRead(
            id=diff.id,
            repository_id=diff.repository_id,
            resource_type=diff.resource_type,
            resource_key=diff.resource_key,
            diff_type=diff.diff_type,
            before=json.loads(diff.before_json) if diff.before_json else None,
            after=json.loads(diff.after_json) if diff.after_json else None,
            risk_level=diff.risk_level,
            created_at=diff.created_at,
        )

    def plan_to_schema(self, plan: ApplyPlan) -> ApplyPlanRead:
        """转换 Apply Plan 响应。"""
        return ApplyPlanRead(
            id=plan.id,
            repository_id=plan.repository_id,
            diff_id=plan.diff_id,
            plan=json.loads(plan.plan_json),
            status=plan.status,
            policy_status=plan.policy_status,
            ai_summary=plan.ai_summary,
            approved_by=plan.approved_by,
            approved_at=plan.approved_at,
            created_at=plan.created_at,
        )

    def policy_result_to_schema(self, result: PolicyResult) -> PolicyResultRead:
        """转换 Policy Result 响应。"""
        return PolicyResultRead.model_validate(result)


def _build_diff(
    repository_id: int,
    desired: DesiredResource,
    actual: ActualResource | None,
    diff_type: str,
) -> ResourceDiff:
    """构造资源差异对象。"""
    after = desired.content_json
    before = actual.content_json if actual is not None else None
    risk_level = "medium" if desired.resource_type == "stack" else "low"
    return ResourceDiff(
        repository_id=repository_id,
        resource_type=desired.resource_type,
        resource_key=desired.resource_key,
        diff_type=diff_type,
        before_json=before,
        after_json=after,
        risk_level=risk_level,
        created_at=datetime.now(timezone.utc),
    )


def _build_apply_plan(repository_id: int, diff: ResourceDiff) -> ApplyPlan:
    """为资源差异生成可审核执行计划。"""
    steps = _plan_steps(diff)
    plan = {
        "resource_type": diff.resource_type,
        "resource_key": diff.resource_key,
        "diff_type": diff.diff_type,
        "steps": steps,
        "rollback": "restore previous desired resource content and regenerate the plan",
    }
    return ApplyPlan(
        repository_id=repository_id,
        diff_id=diff.id,
        plan_json=_serialize_json(plan),
        status="pending_review",
        policy_status="pending",
        ai_summary=_plan_summary(diff),
        created_at=datetime.now(timezone.utc),
    )


def _plan_steps(diff: ResourceDiff) -> list[str]:
    """按资源类型生成展示用计划步骤。"""
    if diff.resource_type == "stack":
        return [
            "validate Docker Compose metadata",
            "run docker compose config before apply",
            "prepare controlled Ansible Runner execution",
            "require human approval before docker compose up",
        ]
    return [
        "validate desired resource schema",
        "compare desired and actual resource content",
        "require human approval before applying changes",
    ]


def _plan_summary(diff: ResourceDiff) -> str:
    """生成演示友好的计划摘要。"""
    if diff.resource_type == "stack":
        return f"Plan to {diff.diff_type} docker compose stack {diff.resource_key}."
    return f"Plan to {diff.diff_type} {diff.resource_type} {diff.resource_key}."


def _validate_policy(repository_id: int, plan: ApplyPlan, diff: ResourceDiff) -> list[PolicyResult]:
    """执行确定性策略校验。"""
    results = [
        PolicyResult(
            repository_id=repository_id,
            plan_id=plan.id,
            rule_key="human_review_required",
            severity="medium",
            passed=True,
            message="Apply plan requires human review before execution.",
            created_at=datetime.now(timezone.utc),
        )
    ]
    after = json.loads(diff.after_json or "{}")
    image = str(after.get("image", ""))
    if diff.resource_type == "stack" and image.endswith(":latest"):
        results.append(
            PolicyResult(
                repository_id=repository_id,
                plan_id=plan.id,
                rule_key="compose_no_latest_image",
                severity="high",
                passed=False,
                message="Docker Compose stack images must not use the latest tag.",
                created_at=datetime.now(timezone.utc),
            )
        )
    elif diff.resource_type == "stack":
        results.append(
            PolicyResult(
                repository_id=repository_id,
                plan_id=plan.id,
                rule_key="compose_no_latest_image",
                severity="high",
                passed=True,
                message="Docker Compose stack image tag is pinned.",
                created_at=datetime.now(timezone.utc),
            )
        )
    return results


def _serialize_json(value: Any) -> str:
    """稳定序列化 JSON，用于内容 hash 与展示。"""
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def _hash_content(content_json: str) -> str:
    """计算资源内容 hash。"""
    return hashlib.sha256(content_json.encode("utf-8")).hexdigest()
