# Deployment

The first deployment target is a simple Docker Compose environment with the backend, SQLite, and Redis.

## Local Backend with uv

Astralith uses uv as the primary Python project and dependency manager.

```bash
uv sync
uv run uvicorn backend.app.main:app --reload
```

Run backend tests:

```bash
uv run pytest
```

## Local Frontend with pnpm

```bash
cd frontend
pnpm install
pnpm dev
```

Build frontend assets:

```bash
pnpm build
```

The frontend stack is Vue 3, Vite, Element Plus, TypeScript, and Tailwind CSS.

## Docker Compose

```bash
docker compose up --build
```

The current Compose file starts the backend and Redis only. The frontend is intentionally kept as a local Vite development server in this early scaffold:

```bash
cd frontend
pnpm dev
```

A later one-click demonstration setup may add either a `frontend` service or an Nginx/static asset service.

Redis is required for Celery. SQLite is stored as a local file for the first version.

## Security Notes

- Change `ASTRALITH_SECRET_KEY` before production-like deployment.
- Do not mount private SSH keys into containers unless the deployment path is explicitly designed and reviewed.
- Keep `.env` files out of version control.
