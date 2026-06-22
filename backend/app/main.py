from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from backend.app.api.router import api_router
from backend.app.core.config import settings
from backend.app.core.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """应用生命周期钩子。

    FastAPI 新版本推荐用 lifespan 替代 on_event。这里在应用启动时初始化数据库表，
    退出时暂时没有额外清理逻辑，所以 yield 后不做处理。
    """
    _ = app
    init_db()
    yield


def create_app() -> FastAPI:
    """创建 FastAPI 应用实例。

    这里使用工厂函数，方便后续测试时创建独立 app，也方便未来扩展中间件。
    """
    app = FastAPI(
        title=settings.project_name,
        version=settings.version,
        description="Lightweight FastAPI + Ansible automated operations platform.",
        lifespan=lifespan,
    )

    @app.get("/health", tags=["health"])
    def health_check() -> dict[str, str]:
        """应用根路径下的健康检查接口。"""

        # 顶层健康检查，供 Docker、监控或本地调试快速确认服务存活。
        return {"status": "ok", "service": settings.project_name}

    # 所有业务 API 统一挂载到 /api/v1，避免后续接口版本混乱。
    app.include_router(api_router, prefix=settings.api_v1_prefix)
    return app


app = create_app()
