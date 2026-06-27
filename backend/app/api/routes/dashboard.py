from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.schemas.dashboard import DashboardSummaryRead
from backend.app.services.dashboard_service import DashboardService

router = APIRouter()


def get_dashboard_service(db: Session = Depends(get_db)) -> DashboardService:
    """构造 Dashboard 聚合服务。"""
    return DashboardService(db)


@router.get("/summary", response_model=DashboardSummaryRead)
def get_dashboard_summary(service: DashboardService = Depends(get_dashboard_service)) -> DashboardSummaryRead:
    """返回 Dashboard 工作台指标。"""
    return service.get_summary()
