from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models.host import Host, HostGroup, HostGroupMember
from backend.app.schemas.host import HostCreate, HostGroupCreate, HostGroupUpdate, HostUpdate


class HostService:
    """主机与主机组业务服务。"""

    def __init__(self, db: Session) -> None:
        self.db = db

    def list_hosts(self) -> list[Host]:
        """按创建顺序返回全部主机。"""
        return list(self.db.scalars(select(Host).order_by(Host.id)))

    def get_host(self, host_id: int) -> Host | None:
        """按 ID 查询单台主机。"""
        return self.db.get(Host, host_id)

    def create_host(self, payload: HostCreate) -> Host:
        """创建受管主机记录。"""
        host = Host(**payload.model_dump())
        self.db.add(host)
        self.db.commit()
        self.db.refresh(host)
        return host

    def update_host(self, host: Host, payload: HostUpdate) -> Host:
        """更新受管主机记录。"""
        for key, value in payload.model_dump().items():
            setattr(host, key, value)
        self.db.commit()
        self.db.refresh(host)
        return host

    def delete_host(self, host: Host) -> None:
        """删除主机，并清理它在主机组中的成员关系。"""
        self.db.query(HostGroupMember).filter(HostGroupMember.host_id == host.id).delete()
        self.db.delete(host)
        self.db.commit()

    def list_groups(self) -> list[HostGroup]:
        """按创建顺序返回全部主机组。"""
        return list(self.db.scalars(select(HostGroup).order_by(HostGroup.id)))

    def get_group(self, group_id: int) -> HostGroup | None:
        """按 ID 查询主机组。"""
        return self.db.get(HostGroup, group_id)

    def create_group(self, payload: HostGroupCreate) -> HostGroup:
        """创建主机组。"""
        group = HostGroup(**payload.model_dump())
        self.db.add(group)
        self.db.commit()
        self.db.refresh(group)
        return group

    def update_group(self, group: HostGroup, payload: HostGroupUpdate) -> HostGroup:
        """更新主机组。"""
        for key, value in payload.model_dump().items():
            setattr(group, key, value)
        self.db.commit()
        self.db.refresh(group)
        return group

    def delete_group(self, group: HostGroup) -> None:
        """删除主机组及其成员关系。"""
        self.db.delete(group)
        self.db.commit()

    def list_group_host_ids(self, group_id: int) -> list[int]:
        """返回主机组中的主机 ID 列表。"""
        statement = select(HostGroupMember.host_id).where(HostGroupMember.group_id == group_id)
        return list(self.db.scalars(statement))

    def add_host_to_group(self, group: HostGroup, host: Host) -> HostGroupMember:
        """把主机加入主机组；已存在时直接返回原成员关系。"""
        statement = select(HostGroupMember).where(
            HostGroupMember.group_id == group.id,
            HostGroupMember.host_id == host.id,
        )
        existing = self.db.scalar(statement)
        if existing is not None:
            return existing
        member = HostGroupMember(group_id=group.id, host_id=host.id)
        self.db.add(member)
        self.db.commit()
        self.db.refresh(member)
        return member

    def remove_host_from_group(self, group_id: int, host_id: int) -> bool:
        """从主机组移除主机；返回是否实际删除了成员关系。"""
        statement = select(HostGroupMember).where(
            HostGroupMember.group_id == group_id,
            HostGroupMember.host_id == host_id,
        )
        member = self.db.scalar(statement)
        if member is None:
            return False
        self.db.delete(member)
        self.db.commit()
        return True
