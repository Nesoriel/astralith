# Architecture

Astralith is a lightweight automated operations platform based on FastAPI and Ansible Runner.

## Technology Choices

- Backend: Python 3.12+, uv, FastAPI, SQLAlchemy, SQLite, Celery, Redis, APScheduler, Ansible Runner, pytest.
- Frontend: Vue 3, Vite, pnpm, Element Plus, Tailwind CSS, TypeScript, vue-i18n.
- Deployment: Docker Compose for backend and Redis in the first version; frontend runs through Vite during early development.

## Core Flow

```text
FastAPI API
  -> service layer
  -> SQLAlchemy / SQLite task records
  -> Celery worker
  -> Ansible Runner
  -> task_results
  -> Vue frontend log display
```

## Responsibilities

- FastAPI handles authentication, validation, and resource APIs.
- Service modules contain business logic.
- Celery executes long-running operations asynchronously.
- Ansible Runner is the only remote execution engine.
- APScheduler only triggers scheduled jobs and must not execute remote operations directly.
- Built-in operation modules describe controlled operations such as system inspection and service management.
- Frontend i18n keeps user-facing labels available in Simplified Chinese and English.

## Scope Control

Astralith intentionally avoids first-version enterprise features such as Kubernetes management, bastion host sessions, web terminals, complex RBAC, and user-uploaded plugins.
