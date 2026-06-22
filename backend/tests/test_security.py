from datetime import timedelta

import jwt

from backend.app.core.config import settings
from backend.app.core.security import ALGORITHM, create_access_token, hash_password, verify_password


def test_password_hash_roundtrip() -> None:
    """密码哈希应能通过 passlib 正确校验。"""
    hashed_password = hash_password("secret-password")

    assert hashed_password != "secret-password"
    assert verify_password("secret-password", hashed_password)
    assert not verify_password("wrong-password", hashed_password)


def test_create_access_token_uses_pyjwt() -> None:
    """JWT 令牌应能由 PyJWT 解码并包含 subject。"""
    token = create_access_token("demo-user", expires_delta=timedelta(minutes=5))

    payload = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])

    assert payload["sub"] == "demo-user"
    assert "exp" in payload
