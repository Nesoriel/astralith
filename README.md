# Astralith

English | [简体中文](./README.zh-CN.md)

Astralith is a lightweight automated operations platform built with FastAPI and Ansible Runner. It is designed for small and medium-sized Linux server environments, with a practical focus on host management, Ansible-based automation, scheduled inspections, execution logs, and built-in operations modules.

Project codename: Astralith

Chinese codename: 星磐

Organization: Nesoriel

Graduation project title:

> Design and Implementation of a Lightweight Automated Operations Platform Based on FastAPI and Ansible

## Goals

Astralith aims to provide a clean, maintainable, and demonstrable operations platform without turning into a large enterprise CMDB, bastion host, Kubernetes platform, or CI/CD system.

Core workflow:

```text
User logs in
  ↓
Adds Linux hosts
  ↓
Tests Ansible connectivity
  ↓
Selects hosts or host groups
  ↓
Chooses an operations task
  ↓
Submits task to backend
  ↓
Celery executes task asynchronously
  ↓
Ansible Runner runs automation on target hosts
  ↓
Execution result is saved to SQLite
  ↓
Frontend displays logs and task status
```

## Technology Stack

### Backend

- Python 3.12+
- uv for dependency and virtual environment management
- FastAPI
- SQLAlchemy
- SQLite
- Ansible Runner
- Celery
- Redis
- APScheduler
- JWT authentication

### Frontend

- Vue 3
- Vite
- pnpm
- Element Plus
- Tailwind CSS
- TypeScript
- vue-i18n for Simplified Chinese and English UI text

### Deployment

- Docker Compose
- SQLite for local and graduation-project deployment
- Redis as the Celery broker

## Core Features

- User login and JWT authentication
- Linux host management
- Host group management
- SSH key-based Ansible connectivity tests
- Built-in operations module registry
- System inspection tasks
- Service management tasks
- Asynchronous task execution through Celery
- Ansible Runner integration
- Execution log storage and display
- Scheduled inspection jobs triggered by APScheduler
- Simplified Chinese and English frontend internationalization

## Built-in Operations Modules

The first version focuses on internal built-in operations modules, not user-uploaded third-party plugins.

Planned modules:

- `system_inspection`
  - `check_disk`
  - `check_memory`
  - `check_load`
  - `check_uptime`
  - `check_logged_users`
- `service_manage`
  - `service_status`
  - `service_start`
  - `service_stop`
  - `service_restart`
  - `service_reload`
- `docker_manage` as a lightweight future extension

## Suggested Project Structure

```text
backend/
├── app/
│   ├── main.py
│   ├── core/
│   ├── models/
│   ├── schemas/
│   ├── api/
│   ├── services/
│   ├── workers/
│   ├── scheduler/
│   └── operation_modules/
├── tests/
└── Dockerfile

frontend/
├── src/
│   ├── api/
│   ├── i18n/
│   ├── router/
│   ├── stores/
│   ├── views/
│   └── components/
├── package.json
├── pnpm-lock.yaml
├── pnpm-workspace.yaml
├── postcss.config.js
├── tailwind.config.ts
├── tsconfig.json
└── vite.config.ts

pyproject.toml
uv.lock
docker-compose.yml
```

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

## Development Roadmap

1. Initialize backend project
2. Initialize frontend project
3. Implement database connection
4. Implement user login
5. Implement host management
6. Implement host grouping
7. Implement Ansible connectivity tests
8. Implement task model and task status management
9. Implement Celery worker
10. Implement Ansible execution service
11. Store and display execution logs
12. Implement system inspection module
13. Implement service management module
14. Implement scheduled jobs
15. Implement basic dashboard
16. Add Docker Compose deployment
17. Improve documentation

## Security Principles

- Do not store managed server SSH passwords.
- Prefer SSH private key paths over raw private key content.
- Do not allow users to upload and execute Python code.
- Do not dynamically install third-party plugins.
- Do not log JWT secrets, private key content, or sensitive environment variables.
- All operations that affect remote hosts must be logged.
- Destructive operations should require explicit confirmation.

## Documentation

Important design and development rules are recorded in [AGENTS.md](./AGENTS.md). More design documents are available in:

- `docs/architecture.md`
- `docs/database-design.md`
- `docs/api-design.md`
- `docs/deployment.md`
- `docs/frontend-i18n.md`
- `docs/graduation-design-notes.md`

## License

This project is released under the license provided in [LICENSE](./LICENSE).
