import json
from typing import Any, cast

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.api.routes.auth import get_current_user
from backend.app.core.database import get_db
from backend.app.models.gitops import AiProposal
from backend.app.models.task import EvidencePack, TaskResult
from backend.app.schemas.task import AiAnalysisResultRead, EvidencePackRead, TaskAiProposalCreate, TaskCreate, TaskIncidentContextRead, TaskLogsRead, TaskRead
from backend.app.services.ai_analysis_service import AiAnalysisService
from backend.app.services.ai_proposal_service import AiProposalService
from backend.app.services.task_service import TaskService
from backend.app.workers.tasks import execute_operation_task

router = APIRouter()


def get_task_service(db: Session = Depends(get_db)) -> TaskService:
    """构造任务服务，保持路由层薄。"""
    return TaskService(db)


@router.get("", response_model=list[TaskRead])
def list_tasks(service: TaskService = Depends(get_task_service)) -> list[TaskRead]:
    """列出执行任务。"""
    return [service.task_to_schema(task) for task in service.list_tasks()]


@router.post("", response_model=TaskRead, status_code=status.HTTP_202_ACCEPTED)
def create_task(
    payload: TaskCreate,
    _current_user = Depends(get_current_user),
    service: TaskService = Depends(get_task_service),
) -> TaskRead:
    """创建 pending 状态执行任务。

    v0.1.0 先落库并返回任务记录；真实 Celery + Ansible Runner 执行在 v0.2.0 接入。
    """
    try:
        task = service.create_task(payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    dispatch_task(task.id)
    return service.task_to_schema(task)


def dispatch_task(task_id: int) -> None:
    """把任务投递给 Celery，隔离 Celery 动态 delay 属性。"""
    cast(Any, execute_operation_task).delay(task_id)


@router.get("/{task_id}", response_model=TaskRead)
def get_task(task_id: int, service: TaskService = Depends(get_task_service)) -> TaskRead:
    """读取单个执行任务。"""
    task = service.get_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return service.task_to_schema(task)


@router.get("/{task_id}/logs", response_model=TaskLogsRead)
def get_task_logs(task_id: int, service: TaskService = Depends(get_task_service)) -> TaskLogsRead:
    """读取任务详情与执行日志。"""
    task = service.get_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    analysis_service = AiAnalysisService(service.db)
    return TaskLogsRead(
        task=service.task_to_schema(task),
        results=[service.result_to_schema(result) for result in service.list_results(task_id)],
        ai_analyses=[
            service.ai_analysis_to_schema(analysis)
            for analysis in analysis_service.list_task_analyses(task_id)
        ],
    )


@router.post("/{task_id}/ai-analysis", response_model=AiAnalysisResultRead, status_code=status.HTTP_201_CREATED)
def create_task_ai_analysis(
    task_id: int,
    _current_user = Depends(get_current_user),
    service: TaskService = Depends(get_task_service),
) -> AiAnalysisResultRead:
    """基于任务结果生成 AI 故障分析报告。"""
    try:
        analysis = AiAnalysisService(service.db).analyze_task(task_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return service.ai_analysis_to_schema(analysis)


@router.post("/{task_id}/ai-proposal", status_code=status.HTTP_201_CREATED)
def create_task_ai_proposal(
    task_id: int,
    payload: TaskAiProposalCreate,
    _current_user = Depends(get_current_user),
    service: TaskService = Depends(get_task_service),
) -> dict[str, Any]:
    """从任务 AI 分析生成可审核 Proposal。"""
    from backend.app.models.task import AiAnalysisResult
    from backend.app.schemas.gitops import AiProposalCreate

    task = service.get_task(task_id)
    analysis = service.db.get(AiAnalysisResult, payload.analysis_id)
    if task is None or analysis is None:
        raise HTTPException(status_code=404, detail="Task or analysis not found")
    analysis_schema = service.ai_analysis_to_schema(analysis)
    proposal_service = AiProposalService(service.db)
    proposal = proposal_service.create_proposal(AiProposalCreate(
        proposal_type="runbook",
        title=f"Incident proposal for task {task.id}",
        summary=analysis.summary,
        content={"analysis_id": analysis.id, "task_id": task.id, "analysis": analysis_schema.content},
        risk_level=str(analysis_schema.content.get("risk_level", "medium")),
        source_type="task",
        source_id=task.id,
    ))
    return proposal_service.to_schema(proposal).model_dump(mode="json")


@router.get("/{task_id}/incident-context", response_model=TaskIncidentContextRead)
def get_task_incident_context(task_id: int, service: TaskService = Depends(get_task_service)) -> TaskIncidentContextRead:
    """读取任务故障闭环上下文。"""
    task = service.get_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    results = service.list_results(task_id)
    result_ids = [result.id for result in results]
    evidence = list(service.db.scalars(select(EvidencePack).where(EvidencePack.task_result_id.in_(result_ids)))) if result_ids else []
    proposals = list(service.db.scalars(select(AiProposal).where(AiProposal.source_type == "task", AiProposal.source_id == task_id)))
    proposal_service = AiProposalService(service.db)
    return TaskIncidentContextRead(
        task=service.task_to_schema(task),
        results=[service.result_to_schema(result) for result in results],
        evidence_packs=[EvidencePackRead(id=item.id, task_result_id=item.task_result_id, host_id=item.host_id, content=json.loads(item.content_json), created_at=item.created_at) for item in evidence],
        ai_analyses=[service.ai_analysis_to_schema(analysis) for analysis in AiAnalysisService(service.db).list_task_analyses(task_id)],
        ai_proposals=[proposal_service.to_schema(proposal).model_dump(mode="json") for proposal in proposals],
    )
