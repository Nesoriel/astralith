from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.api.routes.auth import get_current_user
from backend.app.core.database import get_db
from backend.app.schemas.gitops import (
    DesiredResourceRead,
    GitOpsRepositoryCreate,
    GitOpsRepositoryRead,
    GitOpsRepositoryUpdate,
    GitOpsSyncRunRead,
)
from backend.app.services.gitops_service import GitOpsService

router = APIRouter()


def get_gitops_service(db: Session = Depends(get_db)) -> GitOpsService:
    """构造 GitOps 服务，保持路由层薄。"""
    return GitOpsService(db)


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
