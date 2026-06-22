FROM python:3.12-slim

# 使用官方 uv 镜像复制 uv/uvx，避免在 Dockerfile 中再通过 pip 安装项目管理工具。
COPY --from=ghcr.io/astral-sh/uv:0.9.8 /uv /uvx /bin/

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

COPY pyproject.toml uv.lock README.md /app/
COPY backend /app/backend

# 生产镜像只同步运行依赖，不安装 dev 依赖。
RUN uv sync --frozen --no-dev

CMD ["uv", "run", "uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
