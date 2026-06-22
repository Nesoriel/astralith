from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.schemas.host import HostConnectionTestRead, HostCreate, HostRead, HostUpdate
from backend.app.services.host_service import HostService

router = APIRouter()


def get_host_service(db: Session = Depends(get_db)) -> HostService:
    """构造主机服务，保持路由函数轻量。"""
    return HostService(db)


@router.get("", response_model=list[HostRead])
def list_hosts(service: HostService = Depends(get_host_service)) -> list[HostRead]:
    """列出全部受管主机。"""
    return [HostRead.model_validate(host) for host in service.list_hosts()]


@router.post("", response_model=HostRead, status_code=status.HTTP_201_CREATED)
def create_host(
    payload: HostCreate,
    service: HostService = Depends(get_host_service),
) -> HostRead:
    """创建受管主机。"""
    return HostRead.model_validate(service.create_host(payload))


@router.get("/{host_id}", response_model=HostRead)
def get_host(host_id: int, service: HostService = Depends(get_host_service)) -> HostRead:
    """读取单台受管主机。"""
    host = service.get_host(host_id)
    if host is None:
        raise HTTPException(status_code=404, detail="Host not found")
    return HostRead.model_validate(host)


@router.put("/{host_id}", response_model=HostRead)
def update_host(
    host_id: int,
    payload: HostUpdate,
    service: HostService = Depends(get_host_service),
) -> HostRead:
    """更新受管主机。"""
    host = service.get_host(host_id)
    if host is None:
        raise HTTPException(status_code=404, detail="Host not found")
    return HostRead.model_validate(service.update_host(host, payload))


@router.delete("/{host_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_host(host_id: int, service: HostService = Depends(get_host_service)) -> Response:
    """删除受管主机。"""
    host = service.get_host(host_id)
    if host is None:
        raise HTTPException(status_code=404, detail="Host not found")
    service.delete_host(host)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{host_id}/test-connection", response_model=HostConnectionTestRead)
def test_host_connection(
    host_id: int,
    service: HostService = Depends(get_host_service),
) -> HostConnectionTestRead:
    """v0.1.0 连接测试占位接口。

    真实 Ansible ping 会在 v0.2.0 接入；当前先验证主机记录存在，并明确返回 pending，
    避免在没有真实 SSH 环境的测试中伪造远程执行结果。
    """
    host = service.get_host(host_id)
    if host is None:
        raise HTTPException(status_code=404, detail="Host not found")
    return HostConnectionTestRead(
        host_id=host.id,
        status="pending",
        message="Ansible connectivity test will run through the execution service in v0.2.0.",
    )
