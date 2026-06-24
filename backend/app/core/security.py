from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
import jwt

from backend.app.core.config import settings

ALGORITHM = "HS256"


def hash_password(password: str) -> str:
    """生成密码哈希。数据库中只保存哈希，不保存明文密码。"""
    password_bytes = password.encode("utf-8")
    return bcrypt.hashpw(password_bytes, bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """校验用户输入密码与数据库中的哈希是否匹配。"""
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))


def create_access_token(subject: str, expires_delta: timedelta | None = None) -> str:
    """创建 JWT 访问令牌。subject 通常保存用户 ID 或用户名。"""
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.access_token_expire_minutes)
    )
    payload = {"sub": subject, "exp": expire}
    return jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict[str, Any]:
    """解码并校验 JWT 访问令牌。"""
    return jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
