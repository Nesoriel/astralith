import json
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models.gitops import AiProposal, ApplyPlan, ResourceDiff
from backend.app.schemas.gitops import AiProposalCreate, AiProposalRead


class AiProposalService:
    """AI GitOps Change Proposal 服务。

    v0.9.0 生成的是可复核提案，不直接修改 Git 仓库或执行基础设施变更。
    """

    def __init__(self, db: Session) -> None:
        self.db = db

    def create_proposal(self, payload: AiProposalCreate) -> AiProposal:
        """创建人工或 AI 辅助提案草稿。"""
        proposal = AiProposal(
            proposal_type=payload.proposal_type,
            title=payload.title,
            summary=payload.summary,
            content_json=_dump(payload.content),
            risk_level=payload.risk_level,
            status="draft",
            source_type=payload.source_type,
            source_id=payload.source_id,
            created_at=datetime.now(timezone.utc),
        )
        self.db.add(proposal)
        self.db.commit()
        self.db.refresh(proposal)
        return proposal

    def generate_from_apply_plan(self, plan_id: int) -> AiProposal:
        """从 Apply Plan 生成 GitOps 变更提案。"""
        plan = self.db.get(ApplyPlan, plan_id)
        if plan is None:
            raise ValueError("Apply plan not found")
        diff = self.db.get(ResourceDiff, plan.diff_id)
        if diff is None:
            raise ValueError("Resource diff not found")
        after = _load(diff.after_json, {})
        content = {
            "resource_type": diff.resource_type,
            "resource_key": diff.resource_key,
            "diff_type": diff.diff_type,
            "desired_change": after,
            "patch_draft": _build_patch_draft(diff, after),
            "rollback_plan": "如变更失败，回退到上一 commit 的 desired resource 内容并重新生成 Apply Plan。",
            "test_plan": [
                "运行 GitOps sync 解析变更后的 desired resources。",
                "重新生成 diff 并确认策略校验通过。",
                "人工复核 Apply Plan 后再执行。",
            ],
            "review_notes": [
                "人工复核必需：该提案只作为 GitOps 变更草案，不会自动修改仓库或执行远端操作。",
            ],
        }
        title = f"GitOps change proposal for {diff.resource_key}"
        summary = plan.ai_summary or f"Generate GitOps change proposal for {diff.resource_type} {diff.resource_key}."
        return self.create_proposal(
            AiProposalCreate(
                proposal_type="gitops_change",
                title=title,
                summary=summary,
                content=content,
                risk_level=diff.risk_level,
                source_type="apply_plan",
                source_id=plan.id,
            )
        )

    def list_proposals(self) -> list[AiProposal]:
        """返回 AI 提案列表。"""
        return list(self.db.scalars(select(AiProposal).order_by(AiProposal.id.desc())))

    def review_proposal(self, proposal_id: int, reviewer_id: int, status: str, comment: str) -> AiProposal:
        """审批或拒绝提案。"""
        if status not in {"approved", "rejected"}:
            raise ValueError("Unsupported proposal review status")
        proposal = self.db.get(AiProposal, proposal_id)
        if proposal is None:
            raise ValueError("AI proposal not found")
        proposal.status = status
        proposal.review_comment = comment
        proposal.reviewed_by = reviewer_id
        proposal.reviewed_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(proposal)
        return proposal

    def to_schema(self, proposal: AiProposal) -> AiProposalRead:
        """转换响应模型。"""
        return AiProposalRead(
            id=proposal.id,
            proposal_type=proposal.proposal_type,
            title=proposal.title,
            summary=proposal.summary,
            content=_load(proposal.content_json, {}),
            risk_level=proposal.risk_level,
            status=proposal.status,
            source_type=proposal.source_type,
            source_id=proposal.source_id,
            review_comment=proposal.review_comment,
            reviewed_by=proposal.reviewed_by,
            reviewed_at=proposal.reviewed_at,
            created_at=proposal.created_at,
        )


def _build_patch_draft(diff: ResourceDiff, after: dict[str, Any]) -> dict[str, Any]:
    """生成结构化 patch 草案，避免输出不可控命令。"""
    return {
        "target": f"{diff.resource_type}:{diff.resource_key}",
        "operation": diff.diff_type,
        "desired_content": after,
    }


def _dump(value: Any) -> str:
    """稳定序列化 JSON。"""
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def _load(raw: str | None, fallback: Any) -> Any:
    """安全解析 JSON。"""
    if not raw:
        return fallback
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return fallback
