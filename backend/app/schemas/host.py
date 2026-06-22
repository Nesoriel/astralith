from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class HostBase(BaseModel):
    """主机请求与响应共用字段。"""

    name: str = Field(min_length=1, max_length=100)
    ip_address: str = Field(min_length=1, max_length=64)
    ssh_port: int = Field(default=22, ge=1, le=65535)
    ssh_user: str = Field(min_length=1, max_length=64)
    private_key_path: str = Field(min_length=1, max_length=255)
    description: str | None = None


class HostCreate(HostBase):
    """创建主机的请求体。"""


class HostUpdate(HostBase):
    """更新主机的请求体。"""


class HostRead(HostBase):
    """返回给前端展示的主机信息。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime


class HostConnectionTestRead(BaseModel):
    """主机连接测试结果。"""

    host_id: int
    status: str
    message: str


class HostGroupBase(BaseModel):
    """主机组请求与响应共用字段。"""

    name: str = Field(min_length=1, max_length=100)
    description: str | None = None


class HostGroupCreate(HostGroupBase):
    """创建主机组的请求体。"""


class HostGroupUpdate(HostGroupBase):
    """更新主机组的请求体。"""


class HostGroupRead(HostGroupBase):
    """返回给前端展示的主机组信息。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime
    host_ids: list[int] = Field(default_factory=list)


class HostGroupMemberCreate(BaseModel):
    """向主机组添加主机时使用的请求体。"""

    host_id: int
