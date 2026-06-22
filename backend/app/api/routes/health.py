from fastapi import APIRouter

router = APIRouter()


@router.get("/status")
def api_status() -> dict[str, str]:
    """API 前缀下的健康检查接口。"""

    return {"status": "ok"}
