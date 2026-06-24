from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from backend.app.api.routes.auth import get_current_user
from backend.app.core.database import get_db
from backend.app.models.host import HostGroup
from backend.app.schemas.host import HostGroupCreate, HostGroupMemberCreate, HostGroupRead, HostGroupUpdate
from backend.app.services.host_service import HostService

router = APIRouter()


def get_host_service(db: Session = Depends(get_db)) -> HostService:
    """构造主机服务，供主机组路由复用。"""
    return HostService(db)


def group_to_schema(service: HostService, group: HostGroup) -> HostGroupRead:
    """把 ORM 主机组转换为包含成员 ID 的响应模型。"""
    data = HostGroupRead.model_validate(group).model_dump()
    data["host_ids"] = service.list_group_host_ids(group.id)
    return HostGroupRead.model_validate(data)


@router.get("", response_model=list[HostGroupRead])
def list_host_groups(service: HostService = Depends(get_host_service)) -> list[HostGroupRead]:
    """列出全部主机组。"""
    return [group_to_schema(service, group) for group in service.list_groups()]


@router.post("", response_model=HostGroupRead, status_code=status.HTTP_201_CREATED)
def create_host_group(
    payload: HostGroupCreate,
    _current_user = Depends(get_current_user),
    service: HostService = Depends(get_host_service),
) -> HostGroupRead:
    """创建主机组。"""
    return group_to_schema(service, service.create_group(payload))


@router.get("/{group_id}", response_model=HostGroupRead)
def get_host_group(group_id: int, service: HostService = Depends(get_host_service)) -> HostGroupRead:
    """读取单个主机组。"""
    group = service.get_group(group_id)
    if group is None:
        raise HTTPException(status_code=404, detail="Host group not found")
    return group_to_schema(service, group)


@router.put("/{group_id}", response_model=HostGroupRead)
def update_host_group(
    group_id: int,
    payload: HostGroupUpdate,
    _current_user = Depends(get_current_user),
    service: HostService = Depends(get_host_service),
) -> HostGroupRead:
    """更新主机组。"""
    group = service.get_group(group_id)
    if group is None:
        raise HTTPException(status_code=404, detail="Host group not found")
    return group_to_schema(service, service.update_group(group, payload))


@router.delete("/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_host_group(
    group_id: int,
    _current_user = Depends(get_current_user),
    service: HostService = Depends(get_host_service),
) -> Response:
    """删除主机组。"""
    group = service.get_group(group_id)
    if group is None:
        raise HTTPException(status_code=404, detail="Host group not found")
    service.delete_group(group)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{group_id}/hosts", response_model=HostGroupRead)
def add_host_to_group(
    group_id: int,
    payload: HostGroupMemberCreate,
    _current_user = Depends(get_current_user),
    service: HostService = Depends(get_host_service),
) -> HostGroupRead:
    """向主机组添加主机。"""
    group = service.get_group(group_id)
    if group is None:
        raise HTTPException(status_code=404, detail="Host group not found")
    host = service.get_host(payload.host_id)
    if host is None:
        raise HTTPException(status_code=404, detail="Host not found")
    service.add_host_to_group(group, host)
    return group_to_schema(service, group)


@router.delete("/{group_id}/hosts/{host_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_host_from_group(
    group_id: int,
    host_id: int,
    _current_user = Depends(get_current_user),
    service: HostService = Depends(get_host_service),
) -> Response:
    """从主机组移除主机。"""
    group = service.get_group(group_id)
    if group is None:
        raise HTTPException(status_code=404, detail="Host group not found")
    removed = service.remove_host_from_group(group_id, host_id)
    if not removed:
        raise HTTPException(status_code=404, detail="Host group member not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
