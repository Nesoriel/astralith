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

## AI-native GitOps Direction

After the v0.4 scheduled-execution loop, Astralith's long-term direction is an AI-native GitOps control plane for personal servers, homelab environments, and small teams. The current platform remains the execution and audit foundation; new capabilities should extend it through controlled GitOps and proposal workflows rather than bypassing it.

```text
Git repository
  -> GitOps Sync Service
  -> Desired State Database
  -> Diff / Plan Engine
  -> Policy Validator
  -> Human Review Center
  -> Ansible Runner / Docker Compose execution
  -> Result, audit, and rollback logs
```

AI participates only through structured Evidence Packs and reviewable proposals:

```text
Task failure or inspection anomaly
  -> Evidence Pack Builder
  -> AI Analysis / Proposal Service
  -> schema validation, policy validation, syntax-check, dry-run/check-mode
  -> human approval or rejection
```

This direction is documented in `docs/gitops-ai-roadmap.md` and must preserve the existing safety boundary: AI can explain, summarize, and propose; it must not directly execute infrastructure changes.

## Responsibilities

- FastAPI handles authentication, validation, and resource APIs.
- Service modules contain business logic.
- Celery executes long-running operations asynchronously.
- Ansible Runner is the only remote execution engine.
- APScheduler registers enabled scheduled jobs and triggers normal task creation.
- Built-in operation modules describe controlled operations such as system inspection and service management.
- Frontend i18n keeps user-facing labels available in Simplified Chinese and English.
- GitOps synchronization will parse desired hosts, stacks, modules, and policies from versioned repositories.
- Policy validation gates risky GitOps changes, Compose files, Ansible playbooks, and AI-generated proposals.
- Human review approves or rejects apply plans and proposals before they affect managed hosts.

## Scope Control

Astralith intentionally avoids first-version enterprise features such as Kubernetes management, bastion host sessions, web terminals, complex RBAC, and user-uploaded plugins. Future GitOps and AI features must not turn the project into a fully autonomous self-modifying system, an arbitrary shell executor, or a user-uploaded plugin marketplace.
