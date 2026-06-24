from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class LoginRequest(BaseModel):
    """登录请求体。"""

    username: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=1, max_length=128)


class TokenRead(BaseModel):
    """登录成功后返回的访问令牌。"""

    access_token: str
    token_type: str = "bearer"


class UserRead(BaseModel):
    """返回给前端展示的当前用户信息。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    role: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
