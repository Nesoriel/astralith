from fastapi import APIRouter

from backend.app.api.routes import ai_proposals, auth, gitops, health, host_groups, hosts, operation_modules, scheduled_jobs, tasks

api_router = APIRouter()

# /api/v1/status：API 层健康检查。
api_router.include_router(health.router, tags=["health"])
# /api/v1/auth：登录与当前用户信息。
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
# /api/v1/operation-modules：列出内置运维模块与任务。
api_router.include_router(operation_modules.router, prefix="/operation-modules", tags=["operation-modules"])
# /api/v1/hosts：管理受管 Linux 主机。
api_router.include_router(hosts.router, prefix="/hosts", tags=["hosts"])
# /api/v1/host-groups：管理主机组与成员关系。
api_router.include_router(host_groups.router, prefix="/host-groups", tags=["host-groups"])
# /api/v1/tasks：任务创建与后续任务管理入口。
api_router.include_router(tasks.router, prefix="/tasks", tags=["tasks"])
# /api/v1/scheduled-jobs：管理定时巡检任务。
api_router.include_router(scheduled_jobs.router, prefix="/scheduled-jobs", tags=["scheduled-jobs"])
# /api/v1/gitops-repositories：管理 GitOps 期望状态仓库与同步记录。
api_router.include_router(gitops.router, prefix="/gitops-repositories", tags=["gitops"])
# /api/v1/ai-proposals：管理 AI 生成的 GitOps 变更与 Runbook 提案。
api_router.include_router(ai_proposals.router, prefix="/ai-proposals", tags=["ai-proposals"])
