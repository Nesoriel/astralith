from fastapi import APIRouter

from backend.app.api.routes import health, operation_modules, tasks

api_router = APIRouter()

# /api/v1/status：API 层健康检查。
api_router.include_router(health.router, tags=["health"])
# /api/v1/operation-modules：列出内置运维模块与任务。
api_router.include_router(operation_modules.router, prefix="/operation-modules", tags=["operation-modules"])
# /api/v1/tasks：任务创建与后续任务管理入口。
api_router.include_router(tasks.router, prefix="/tasks", tags=["tasks"])
