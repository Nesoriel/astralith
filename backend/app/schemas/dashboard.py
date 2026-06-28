from pydantic import BaseModel, Field


class DashboardActionItemRead(BaseModel):
    """Dashboard 待处理事项。"""

    kind: str
    title: str
    status: str
    target_path: str


class DashboardSummaryRead(BaseModel):
    """Dashboard 工作台聚合指标。"""

    hosts: int
    host_groups: int
    operation_modules: int
    operation_tasks: int
    tasks_total: int
    tasks_failed: int
    tasks_success_rate: float
    scheduled_jobs: int
    gitops_repositories: int
    resource_diffs: int
    pending_apply_plans: int
    blocked_policy_results: int
    ai_analyses: int
    pending_ai_proposals: int
    pending_module_proposals: int
    action_items: list[DashboardActionItemRead] = Field(default_factory=list)
