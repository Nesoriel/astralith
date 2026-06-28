from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.app.models.gitops import AiProposal, ApplyPlan, GitOpsRepository, PolicyResult, ResourceDiff
from backend.app.models.host import Host, HostGroup
from backend.app.models.operation_module import OperationModuleProposal
from backend.app.models.scheduled_job import ScheduledJob
from backend.app.models.task import AiAnalysisResult, Task
from backend.app.operation_modules.registry import registry
from backend.app.schemas.dashboard import DashboardActionItemRead, DashboardSummaryRead


class DashboardService:
    """Dashboard 工作台聚合服务。"""

    def __init__(self, db: Session) -> None:
        self.db = db

    def get_summary(self) -> DashboardSummaryRead:
        """统计平台核心能力指标。"""
        tasks_total = self._count(Task)
        tasks_failed = self._count_where(Task, Task.status == "failed")
        tasks_success = self._count_where(Task, Task.status == "success")
        success_rate = round(tasks_success / tasks_total, 3) if tasks_total else 0.0
        modules = registry.list_modules()
        return DashboardSummaryRead(
            hosts=self._count(Host),
            host_groups=self._count(HostGroup),
            operation_modules=len(modules),
            operation_tasks=sum(len(module.tasks) for module in modules),
            tasks_total=tasks_total,
            tasks_failed=tasks_failed,
            tasks_success_rate=success_rate,
            scheduled_jobs=self._count(ScheduledJob),
            gitops_repositories=self._count(GitOpsRepository),
            resource_diffs=self._count(ResourceDiff),
            pending_apply_plans=self._count_where(ApplyPlan, ApplyPlan.status.in_(["pending_review", "approved"])),
            blocked_policy_results=self._count_where(PolicyResult, PolicyResult.passed.is_(False)),
            ai_analyses=self._count(AiAnalysisResult),
            pending_ai_proposals=self._count_where(AiProposal, AiProposal.status == "draft"),
            pending_module_proposals=self._count_where(OperationModuleProposal, OperationModuleProposal.status.in_(["draft", "reviewing"])),
            action_items=self._action_items(),
        )

    def _action_items(self) -> list[DashboardActionItemRead]:
        """返回首页最需要处理的事项。"""
        items: list[DashboardActionItemRead] = []
        for task in self.db.scalars(select(Task).where(Task.status == "failed").order_by(Task.id.desc()).limit(5)):
            items.append(DashboardActionItemRead(kind="failed_task", title=task.name, status=task.status, target_path=f"/tasks?task_id={task.id}"))
        for plan in self.db.scalars(select(ApplyPlan).where(ApplyPlan.status == "pending_review").order_by(ApplyPlan.id.desc()).limit(5)):
            items.append(DashboardActionItemRead(kind="pending_apply_plan", title=f"Apply Plan #{plan.id}", status=plan.status, target_path=f"/gitops-diff?plan_id={plan.id}"))
        for proposal in self.db.scalars(select(AiProposal).where(AiProposal.status == "draft").order_by(AiProposal.id.desc()).limit(5)):
            items.append(DashboardActionItemRead(kind="pending_ai_proposal", title=proposal.title, status=proposal.status, target_path=f"/ai-proposals?id={proposal.id}"))
        for proposal in self.db.scalars(select(OperationModuleProposal).where(OperationModuleProposal.status.in_(["draft", "reviewing"])).order_by(OperationModuleProposal.id.desc()).limit(5)):
            items.append(DashboardActionItemRead(kind="pending_module_proposal", title=proposal.title, status=proposal.status, target_path=f"/operation-module-proposals?id={proposal.id}"))
        return items[:10]

    def _count(self, model: type) -> int:
        """统计表记录数。"""
        return int(self.db.scalar(select(func.count()).select_from(model)) or 0)

    def _count_where(self, model: type, criterion) -> int:
        """按条件统计表记录数。"""
        return int(self.db.scalar(select(func.count()).select_from(model).where(criterion)) or 0)
