# Astralith

English | [简体中文](./README.zh-CN.md)

Astralith is a lightweight automated operations platform for small Linux server environments. It is built with FastAPI, Ansible Runner, SQLite, Celery, APScheduler, and Vue 3.

Graduation project title:

> Design and Implementation of a Lightweight Automated Operations Platform Based on FastAPI and Ansible

## Current Status

v0.3.0 provides a lightweight authenticated demonstration loop:

- Local admin login with JWT authentication and `/api/v1/auth/me`.
- Frontend login page, token storage, route guard, and logout action.
- JWT protection for backend write operations while keeping read APIs useful for dashboard display.
- Host CRUD and host group management.
- Built-in operation module metadata for `system_inspection` and `service_manage`.
- Celery-dispatched task execution through the service boundary.
- Ansible inventory and playbook generation for controlled built-in tasks.
- SQLite-backed per-host task results with stdout, stderr, and raw event data.
- Scheduled job records with enable, disable, and manual trigger actions.
- Vue 3 task log display with Simplified Chinese and English i18n.
- Clean test/build output for the current v0.3.x toolchain.

The project still intentionally avoids enterprise CMDB, bastion-host, Kubernetes, and user-uploaded plugin scope.

## Quick Start

Backend:

```bash
uv sync
uv run uvicorn backend.app.main:app --reload
```

Frontend:

```bash
cd frontend
pnpm install
pnpm dev
```

Verification:

```bash
uv run pytest
pnpm --dir frontend build
```

Default local login:

```text
username: admin
password: admin123
```

## Core Workflow

```text
Log in
  -> add Linux hosts
  -> select hosts or host groups
  -> choose a built-in operation task
  -> create an execution task
  -> store status and logs in SQLite
  -> inspect results in the frontend
```

## Technology Stack

- Backend: Python 3.12+, uv, FastAPI, SQLAlchemy, SQLite, Celery, Redis, APScheduler, Ansible Runner, pytest.
- Frontend: Vue 3, Vite, pnpm, Element Plus, Tailwind CSS, TypeScript, vue-i18n.
- Deployment: Docker Compose, SQLite, Redis.

## Documentation

- `AGENTS.md` — project scope, coding rules, architecture constraints.
- `docs/development-roadmap.md` — version plan.
- `docs/architecture.md` — architecture overview.
- `docs/api-design.md` — REST API design.
- `docs/database-design.md` — database tables.
- `docs/deployment.md` — deployment notes.
- `docs/frontend-i18n.md` — frontend i18n rules.
- `docs/graduation-design-notes.md` — graduation-project notes.

## Security Boundaries

- Do not store managed server SSH passwords.
- Store SSH private key paths, not raw private key content.
- Do not allow user-uploaded Python plugins or arbitrary code execution.
- Keep remote operations logged and routed through the service layer.

## License

This project is released under the license provided in [LICENSE](./LICENSE).
