from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.api.routes.auth import get_current_user
from backend.app.core.database import get_db
from backend.app.schemas.gitops import (
    ActualResourceRead,
    ActualResourceUpsert,
    ApplyPlanRead,
    DesiredResourceRead,
    GitOpsRepositoryCreate,
    GitOpsRepositoryRead,
    GitOpsRepositoryUpdate,
    GitOpsSyncRunRead,
    PolicyResultRead,
    ResourceDiffRead,
)
from backend.app.services.gitops_diff_service import GitOpsDiffService
from backend.app.services.gitops_service import GitOpsService

router = APIRouter()


def get_gitops_service(db: Session = Depends(get_db)) -> GitOpsService:
    """构造 GitOps 服务，保持路由层薄。"""
    return GitOpsService(db)


def get_gitops_diff_service(db: Session = Depends(get_db)) -> GitOpsDiffService:
    """构造 GitOps Diff 服务。"""
    return GitOpsDiffService(db)


@router.get("", response_model=list[GitOpsRepositoryRead])
def list_repositories(service: GitOpsService = Depends(get_gitops_service)) -> list[GitOpsRepositoryRead]:
    """列出 GitOps 期望状态仓库。"""
    return [GitOpsRepositoryRead.model_validate(repository) for repository in service.list_repositories()]


@router.post("", response_model=GitOpsRepositoryRead, status_code=status.HTTP_201_CREATED)
def create_repository(
    payload: GitOpsRepositoryCreate,
    _current_user = Depends(get_current_user),
    service: GitOpsService = Depends(get_gitops_service),
) -> GitOpsRepositoryRead:
    """创建 GitOps 仓库配置。"""
    return GitOpsRepositoryRead.model_validate(service.create_repository(payload))


# 固定路径必须放在 /{repository_id} 之前，避免被动态路径误匹配。
@router.post("/actual-resources", response_model=ActualResourceRead, status_code=status.HTTP_201_CREATED)
def upsert_actual_resource(
    payload: ActualResourceUpsert,
    _current_user = Depends(get_current_user),
    service: GitOpsDiffService = Depends(get_gitops_diff_service),
) -> ActualResourceRead:
    """写入或更新 Actual Resource。"""
    return service.actual_resource_to_schema(service.upsert_actual_resource(payload))


@router.get("/actual-resources", response_model=list[ActualResourceRead])
def list_actual_resources(
    service: GitOpsDiffService = Depends(get_gitops_diff_service),
) -> list[ActualResourceRead]:
    """查看 Actual Resources。"""
    return [service.actual_resource_to_schema(actual) for actual in service.list_actual_resources()]


@router.get("/{repository_id}", response_model=GitOpsRepositoryRead)
def get_repository(
    repository_id: int,
    service: GitOpsService = Depends(get_gitops_service),
) -> GitOpsRepositoryRead:
    """读取单个 GitOps 仓库配置。"""
    repository = service.get_repository(repository_id)
    if repository is None:
        raise HTTPException(status_code=404, detail="GitOps repository not found")
    return GitOpsRepositoryRead.model_validate(repository)


@router.put("/{repository_id}", response_model=GitOpsRepositoryRead)
def update_repository(
    repository_id: int,
    payload: GitOpsRepositoryUpdate,
    _current_user = Depends(get_current_user),
    service: GitOpsService = Depends(get_gitops_service),
) -> GitOpsRepositoryRead:
    """更新 GitOps 仓库配置。"""
    repository = service.get_repository(repository_id)
    if repository is None:
        raise HTTPException(status_code=404, detail="GitOps repository not found")
    return GitOpsRepositoryRead.model_validate(service.update_repository(repository, payload))


@router.post("/{repository_id}/sync", response_model=GitOpsSyncRunRead)
def sync_repository(
    repository_id: int,
    _current_user = Depends(get_current_user),
    service: GitOpsService = Depends(get_gitops_service),
) -> GitOpsSyncRunRead:
    """手动同步 GitOps 仓库并解析 Desired Resources。"""
    try:
        return GitOpsSyncRunRead.model_validate(service.sync_repository(repository_id))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/{repository_id}/sync-runs", response_model=list[GitOpsSyncRunRead])
def list_sync_runs(
    repository_id: int,
    service: GitOpsService = Depends(get_gitops_service),
) -> list[GitOpsSyncRunRead]:
    """查看 GitOps 仓库同步记录。"""
    return [GitOpsSyncRunRead.model_validate(sync_run) for sync_run in service.list_sync_runs(repository_id)]


@router.get("/{repository_id}/desired-resources", response_model=list[DesiredResourceRead])
def list_desired_resources(
    repository_id: int,
    service: GitOpsService = Depends(get_gitops_service),
) -> list[DesiredResourceRead]:
    """查看 GitOps 仓库解析出的 Desired Resources。"""
    return [
        service.desired_resource_to_schema(resource)
        for resource in service.list_desired_resources(repository_id)
    ]


@router.post("/{repository_id}/diff", response_model=list[ResourceDiffRead])
def generate_diffs(
    repository_id: int,
    _current_user = Depends(get_current_user),
    service: GitOpsDiffService = Depends(get_gitops_diff_service),
) -> list[ResourceDiffRead]:
    """生成 Desired / Actual 差异、Apply Plan 与 Policy Results。"""
    try:
        return [service.diff_to_schema(diff) for diff in service.generate_diffs(repository_id)]
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/{repository_id}/diffs", response_model=list[ResourceDiffRead])
def list_diffs(
    repository_id: int,
    service: GitOpsDiffService = Depends(get_gitops_diff_service),
) -> list[ResourceDiffRead]:
    """查看资源差异。"""
    return [service.diff_to_schema(diff) for diff in service.list_diffs(repository_id)]


@router.get("/{repository_id}/apply-plans", response_model=list[ApplyPlanRead])
def list_apply_plans(
    repository_id: int,
    service: GitOpsDiffService = Depends(get_gitops_diff_service),
) -> list[ApplyPlanRead]:
    """查看 Apply Plans。"""
    return [service.plan_to_schema(plan) for plan in service.list_apply_plans(repository_id)]


@router.get("/{repository_id}/policy-results", response_model=list[PolicyResultRead])
def list_policy_results(
    repository_id: int,
    service: GitOpsDiffService = Depends(get_gitops_diff_service),
) -> list[PolicyResultRead]:
    """查看 Policy Results。"""
    return [service.policy_result_to_schema(result) for result in service.list_policy_results(repository_id)]
