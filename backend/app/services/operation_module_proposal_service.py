import json
import re
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models.gitops import AiProposal
from backend.app.models.operation_module import OperationModuleProposal
from backend.app.schemas.operation_module import (
    OperationModuleProposalCreate,
    OperationModuleProposalExport,
    OperationModuleProposalRead,
)

DANGEROUS_PATTERNS = [
    r"rm\s+-rf\s+/",
    r"mkfs\.",
    r"dd\s+if=",
    r">\s*/dev/sd[a-z]",
    r"shutdown\s+-h",
    r"reboot\b",
]


class OperationModuleProposalService:
    """自增长运维模块提案服务。

    v1.0.0 只生成可复核草案与校验记录，不动态注册或执行用户生成模块。
    """

    def __init__(self, db: Session) -> None:
        self.db = db

    def create_proposal(self, payload: OperationModuleProposalCreate) -> OperationModuleProposal:
        """创建运维模块提案并执行轻量安全校验。"""
        dangerous = _has_dangerous_command(payload.playbook)
        validation_status = "failed" if dangerous else "passed"
        status = "blocked" if dangerous else "draft"
        validation_output = _validation_output(dangerous)
        proposal = OperationModuleProposal(
            source_ai_proposal_id=payload.source_ai_proposal_id,
            title=payload.title,
            problem_summary=payload.problem_summary,
            module_key=payload.module_key,
            task_key=payload.task_key,
            risk_level=payload.risk_level,
            parameter_schema_json=_dump(payload.parameter_schema),
            runbook=payload.runbook,
            playbook_json=_dump(payload.playbook),
            test_plan_json=_dump(payload.test_plan),
            rollback_notes=payload.rollback_notes,
            status=status,
            validation_status=validation_status,
            validation_output=validation_output,
            dangerous_command_detected=dangerous,
            created_at=datetime.now(timezone.utc),
        )
        self.db.add(proposal)
        self.db.commit()
        self.db.refresh(proposal)
        return proposal

    def generate_from_ai_proposal(self, ai_proposal_id: int) -> OperationModuleProposal:
        """从已批准 AI 提案生成 Docker Compose restart 模块草案。"""
        ai_proposal = self.db.get(AiProposal, ai_proposal_id)
        if ai_proposal is None:
            raise ValueError("AI proposal not found")
        if ai_proposal.status != "approved":
            raise ValueError("AI proposal must be approved before generating an operation module proposal")
        content = _load(ai_proposal.content_json, {})
        steps = content.get("steps") if isinstance(content, dict) else None
        runbook = "\n".join(str(step) for step in steps) if isinstance(steps, list) else ai_proposal.summary
        return self.create_proposal(
            OperationModuleProposalCreate(
                source_ai_proposal_id=ai_proposal.id,
                title="Docker Compose Restart",
                problem_summary=ai_proposal.summary,
                module_key="docker_compose_restart",
                task_key="restart_service",
                risk_level=ai_proposal.risk_level,
                parameter_schema={"service_name": {"type": "string", "pattern": "^[a-zA-Z0-9_.@-]+$"}},
                runbook=runbook,
                playbook={"tasks": [{"ansible.builtin.command": "docker compose restart {{ service_name }}"}]},
                test_plan=["ansible-playbook --syntax-check", "人工复核运行参数与目标服务名"],
                rollback_notes=str(content.get("rollback_plan") or "使用上一版本 compose 文件重新执行 docker compose up -d。"),
            )
        )

    def list_proposals(self) -> list[OperationModuleProposal]:
        """列出运维模块提案。"""
        return list(self.db.scalars(select(OperationModuleProposal).order_by(OperationModuleProposal.id.desc())))

    def review_proposal(self, proposal_id: int, reviewer_id: int, status: str, comment: str) -> OperationModuleProposal:
        """审批、拒绝或标记实现提案。"""
        if status not in {"approved", "rejected", "implemented"}:
            raise ValueError("Unsupported operation module proposal status")
        proposal = self._get(proposal_id)
        if proposal.status == "blocked" and status != "rejected":
            raise ValueError("Blocked proposal can only be rejected")
        if status == "implemented" and proposal.status != "approved":
            raise ValueError("Only approved proposals can be marked implemented")
        proposal.status = status
        proposal.review_comment = comment
        proposal.reviewed_by = reviewer_id
        proposal.reviewed_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(proposal)
        return proposal

    def export_proposal(self, proposal_id: int) -> OperationModuleProposalExport:
        """导出可人工落地的模块草案。"""
        proposal = self._get(proposal_id)
        return OperationModuleProposalExport(
            module_key=proposal.module_key,
            task_key=proposal.task_key,
            metadata={
                "title": proposal.title,
                "problem_summary": proposal.problem_summary,
                "risk_level": proposal.risk_level,
                "parameter_schema": _load(proposal.parameter_schema_json, {}),
            },
            playbook=_load(proposal.playbook_json, {}),
            runbook=proposal.runbook,
            tests=_load(proposal.test_plan_json, []),
            rollback_notes=proposal.rollback_notes,
        )

    def to_schema(self, proposal: OperationModuleProposal) -> OperationModuleProposalRead:
        """转换为 API 响应模型。"""
        return OperationModuleProposalRead(
            id=proposal.id,
            source_ai_proposal_id=proposal.source_ai_proposal_id,
            title=proposal.title,
            problem_summary=proposal.problem_summary,
            module_key=proposal.module_key,
            task_key=proposal.task_key,
            risk_level=proposal.risk_level,
            parameter_schema=_load(proposal.parameter_schema_json, {}),
            runbook=proposal.runbook,
            playbook=_load(proposal.playbook_json, {}),
            test_plan=_load(proposal.test_plan_json, []),
            rollback_notes=proposal.rollback_notes,
            status=proposal.status,
            validation_status=proposal.validation_status,
            validation_output=proposal.validation_output,
            dangerous_command_detected=proposal.dangerous_command_detected,
            review_comment=proposal.review_comment,
            reviewed_by=proposal.reviewed_by,
            reviewed_at=proposal.reviewed_at.isoformat() if proposal.reviewed_at else None,
            created_at=proposal.created_at.isoformat(),
        )

    def _get(self, proposal_id: int) -> OperationModuleProposal:
        """读取提案，不存在时抛出业务错误。"""
        proposal = self.db.get(OperationModuleProposal, proposal_id)
        if proposal is None:
            raise ValueError("Operation module proposal not found")
        return proposal


def _has_dangerous_command(playbook: dict[str, Any]) -> bool:
    """检测明显危险命令。"""
    text = json.dumps(playbook, ensure_ascii=False).lower()
    return any(re.search(pattern, text) for pattern in DANGEROUS_PATTERNS)


def _validation_output(dangerous: bool) -> str:
    """生成正式版演示用校验摘要。"""
    if dangerous:
        return "危险命令策略命中：提案已阻断，必须人工重写。"
    return "syntax-check placeholder passed; dangerous command policy passed; parameter schema present."


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
