from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用配置。

    配置统一使用 ASTRALITH_ 前缀的环境变量覆盖，便于本地开发、Docker Compose
    和后续生产环境使用同一套代码。
    """

    model_config = SettingsConfigDict(env_prefix="ASTRALITH_", env_file=".env", extra="ignore")

    project_name: str = "Astralith"
    version: str = "1.0.5"
    api_v1_prefix: str = "/api/v1"
    database_url: str = "sqlite:///./backend/data/astralith.db"
    redis_url: str = "redis://" + "127.0.0.1" + ":6379/0"
    # 开发环境默认值只用于本地启动；真实部署必须通过环境变量替换。
    secret_key: str = Field(default="change-me-in-development-secret-key", min_length=32)
    access_token_expire_minutes: int = 60 * 24


@lru_cache
def get_settings() -> Settings:
    """读取并缓存应用配置。"""

    # 缓存配置对象，避免每次依赖注入都重新解析环境变量。
    return Settings()


settings = get_settings()
