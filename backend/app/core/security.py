from datetime import datetime, timedelta, timezone

from jose import jwt
from passlib.context import CryptContext

from backend.app.core.config import settings

ALGORITHM = "HS256"

# passlib 统一封装密码哈希算法，后续更换算法时不影响业务代码。
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """生成密码哈希。数据库中只保存哈希，不保存明文密码。"""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """校验用户输入密码与数据库中的哈希是否匹配。"""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(subject: str, expires_delta: timedelta | None = None) -> str:
    """创建 JWT 访问令牌。subject 通常保存用户 ID 或用户名。"""
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.access_token_expire_minutes)
    )
    payload = {"sub": subject, "exp": expire}
    return jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM)
