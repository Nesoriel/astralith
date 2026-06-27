from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.api.routes.auth import get_current_user
from backend.app.core.database import get_db
from backend.app.models.user import User
from backend.app.schemas.gitops import AiProposalCreate, AiProposalRead, AiProposalReview
from backend.app.services.ai_proposal_service import AiProposalService

router = APIRouter()


def get_ai_proposal_service(db: Session = Depends(get_db)) -> AiProposalService:
    """构造 AI 提案服务，保持路由层薄。"""
    return AiProposalService(db)


@router.get("", response_model=list[AiProposalRead])
def list_proposals(service: AiProposalService = Depends(get_ai_proposal_service)) -> list[AiProposalRead]:
    """查看 AI GitOps 提案列表。"""
    return [service.to_schema(proposal) for proposal in service.list_proposals()]


@router.post("", response_model=AiProposalRead, status_code=status.HTTP_201_CREATED)
def create_proposal(
    payload: AiProposalCreate,
    _current_user: User = Depends(get_current_user),
    service: AiProposalService = Depends(get_ai_proposal_service),
) -> AiProposalRead:
    """创建人工或 AI 辅助提案草稿。"""
    return service.to_schema(service.create_proposal(payload))


@router.post("/{proposal_id}/approve", response_model=AiProposalRead)
def approve_proposal(
    proposal_id: int,
    payload: AiProposalReview,
    current_user: User = Depends(get_current_user),
    service: AiProposalService = Depends(get_ai_proposal_service),
) -> AiProposalRead:
    """人工批准 AI 提案。"""
    try:
        return service.to_schema(
            service.review_proposal(proposal_id, current_user.id, "approved", payload.review_comment)
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/{proposal_id}/reject", response_model=AiProposalRead)
def reject_proposal(
    proposal_id: int,
    payload: AiProposalReview,
    current_user: User = Depends(get_current_user),
    service: AiProposalService = Depends(get_ai_proposal_service),
) -> AiProposalRead:
    """人工拒绝 AI 提案。"""
    try:
        return service.to_schema(
            service.review_proposal(proposal_id, current_user.id, "rejected", payload.review_comment)
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
