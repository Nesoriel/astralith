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
- Change the default local admin password before any shared demonstration or production-like deployment.
- Ensure the backend and Celery worker can both reach the same Redis broker URL.
- Persist the SQLite database file on a durable volume when using Docker Compose.
- Do not mount private SSH keys into containers unless the deployment path is explicitly designed and reviewed.
- If SSH keys are mounted, mount only administrator-controlled key paths as read-only and never expose key content through API responses or logs.
- Keep `.env` files out of version control.
