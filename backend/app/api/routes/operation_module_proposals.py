from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.api.routes.auth import get_current_user
from backend.app.core.database import get_db
from backend.app.models.user import User
from backend.app.schemas.operation_module import (
    OperationModuleProposalCreate,
    OperationModuleProposalExport,
    OperationModuleProposalRead,
    OperationModuleProposalReview,
)
from backend.app.services.operation_module_proposal_service import OperationModuleProposalService

router = APIRouter()


def get_proposal_service(db: Session = Depends(get_db)) -> OperationModuleProposalService:
    """构造运维模块提案服务。"""
    return OperationModuleProposalService(db)


@router.get("", response_model=list[OperationModuleProposalRead])
def list_proposals(service: OperationModuleProposalService = Depends(get_proposal_service)) -> list[OperationModuleProposalRead]:
    """查看运维模块提案列表。"""
    return [service.to_schema(proposal) for proposal in service.list_proposals()]


@router.post("", response_model=OperationModuleProposalRead, status_code=status.HTTP_201_CREATED)
def create_proposal(
    payload: OperationModuleProposalCreate,
    _current_user: User = Depends(get_current_user),
    service: OperationModuleProposalService = Depends(get_proposal_service),
) -> OperationModuleProposalRead:
    """创建运维模块提案。"""
    return service.to_schema(service.create_proposal(payload))


@router.post("/from-ai-proposals/{ai_proposal_id}", response_model=OperationModuleProposalRead, status_code=status.HTTP_201_CREATED)
def generate_from_ai_proposal(
    ai_proposal_id: int,
    _current_user: User = Depends(get_current_user),
    service: OperationModuleProposalService = Depends(get_proposal_service),
) -> OperationModuleProposalRead:
    """从已批准 AI 提案生成运维模块提案。"""
    try:
        return service.to_schema(service.generate_from_ai_proposal(ai_proposal_id))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/{proposal_id}/approve", response_model=OperationModuleProposalRead)
def approve_proposal(
    proposal_id: int,
    payload: OperationModuleProposalReview,
    current_user: User = Depends(get_current_user),
    service: OperationModuleProposalService = Depends(get_proposal_service),
) -> OperationModuleProposalRead:
    """批准运维模块提案。"""
    try:
        return service.to_schema(service.review_proposal(proposal_id, current_user.id, "approved", payload.review_comment))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/{proposal_id}/reject", response_model=OperationModuleProposalRead)
def reject_proposal(
    proposal_id: int,
    payload: OperationModuleProposalReview,
    current_user: User = Depends(get_current_user),
    service: OperationModuleProposalService = Depends(get_proposal_service),
) -> OperationModuleProposalRead:
    """拒绝运维模块提案。"""
    try:
        return service.to_schema(service.review_proposal(proposal_id, current_user.id, "rejected", payload.review_comment))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/{proposal_id}/implement", response_model=OperationModuleProposalRead)
def mark_implemented(
    proposal_id: int,
    payload: OperationModuleProposalReview,
    current_user: User = Depends(get_current_user),
    service: OperationModuleProposalService = Depends(get_proposal_service),
) -> OperationModuleProposalRead:
    """将已批准提案标记为 implemented。"""
    try:
        return service.to_schema(service.review_proposal(proposal_id, current_user.id, "implemented", payload.review_comment))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/{proposal_id}/export", response_model=OperationModuleProposalExport)
def export_proposal(
    proposal_id: int,
    service: OperationModuleProposalService = Depends(get_proposal_service),
) -> OperationModuleProposalExport:
    """导出模块草案，供人工复制到内置模块目录。"""
    try:
        return service.export_proposal(proposal_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
