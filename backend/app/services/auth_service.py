from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.core.security import hash_password, verify_password
from backend.app.models.user import User

DEFAULT_ADMIN_USERNAME = "admin"
DEFAULT_ADMIN_PASSWORD = "admin123"


class AuthService:
    """认证业务服务，集中处理用户校验与本地管理员初始化。"""

    def __init__(self, db: Session) -> None:
        self.db = db

    def get_user_by_username(self, username: str) -> User | None:
        """按用户名查询用户。"""
        return self.db.scalar(select(User).where(User.username == username))

    def authenticate_user(self, username: str, password: str) -> User | None:
        """校验用户名、密码与启用状态。"""
        user = self.get_user_by_username(username)
        if user is None or not user.is_active:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user

    def ensure_default_admin(self) -> User:
        """确保本地开发环境存在一个初始管理员账号。"""
        existing_admin = self.get_user_by_username(DEFAULT_ADMIN_USERNAME)
        if existing_admin is not None:
            return existing_admin
        admin = User(
            username=DEFAULT_ADMIN_USERNAME,
            hashed_password=hash_password(DEFAULT_ADMIN_PASSWORD),
            role="admin",
            is_active=True,
        )
        self.db.add(admin)
        self.db.commit()
        self.db.refresh(admin)
        return admin
