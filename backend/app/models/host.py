from sqlalchemy import ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.core.database import Base
from backend.app.models.common import TimestampMixin


class Host(TimestampMixin, Base):
    """受管 Linux 主机。

    只保存管理员提供的 SSH 私钥路径，不保存服务器 SSH 密码或私钥内容。
    """

    __tablename__ = "hosts"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    ip_address: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    ssh_port: Mapped[int] = mapped_column(Integer, default=22, nullable=False)
    ssh_user: Mapped[str] = mapped_column(String(64), nullable=False)
    private_key_path: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)


class HostGroup(TimestampMixin, Base):
    """主机分组，用于批量选择执行目标。"""

    __tablename__ = "host_groups"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    members: Mapped[list["HostGroupMember"]] = relationship(cascade="all, delete-orphan")


class HostGroupMember(Base):
    """主机与主机组的成员关系表。"""

    __tablename__ = "host_group_members"
    __table_args__ = (UniqueConstraint("group_id", "host_id", name="uq_host_group_member"),)

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("host_groups.id"), nullable=False)
    host_id: Mapped[int] = mapped_column(ForeignKey("hosts.id"), nullable=False)
