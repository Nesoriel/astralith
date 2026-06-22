# AGENTS.md

## Project Identity

This repository is part of the **Nesoriel** open-source organization.

Project codename: **Astralith**
Chinese codename: **星磐**

Astralith is a lightweight automated operations platform built with **FastAPI** and **Ansible Runner**. It is designed for small and medium-sized Linux server environments and focuses on host management, Ansible-based automation, scheduled inspections, execution logs, and extensible built-in operations modules.

The graduation project title is:

> 基于 FastAPI 与 Ansible 的轻量级自动化运维平台设计与实现

## Core Goal

Build a practical, maintainable, lightweight automated operations platform.

The system should support the following core workflow:

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

* Python 3.12+
* uv for Python dependency and virtual environment management
* FastAPI
* SQLAlchemy
* SQLite
* Ansible Runner
* Celery
* Redis
* APScheduler
* JWT authentication
* pytest for automated backend tests

### Frontend

* Vue 3
* Vite
* pnpm
* Element Plus
* Tailwind CSS
* TypeScript
* vue-i18n for Simplified Chinese and English UI text

### Deployment

* Docker Compose
* SQLite for local and graduation-project deployment
* Redis for Celery broker

## Architectural Principles

### 1. Keep the Platform Lightweight

This project is not intended to be a large enterprise CMDB, bastion host, Kubernetes platform, or full CI/CD system.

Avoid unnecessary complexity.

Do not introduce microservices unless there is a clear reason.

### 2. Separate Platform Capabilities from Operations Capabilities

The core platform is responsible for common infrastructure capabilities:

* User authentication
* Host management
* Host grouping
* Task creation
* Task scheduling
* Task execution status management
* Execution log storage
* Ansible Runner integration
* Celery task dispatching
* APScheduler scheduled triggering
* Built-in module registration

Operations capabilities should be implemented as built-in operations modules.

Examples:

* System inspection module
* Service management module
* Docker basic management module
* Future log analysis module
* Future database backup module

### 3. Built-in Operation Modules, Not Unsafe Third-party Plugins

The project may use the term “plugin” in historical notes or broad documentation, but the first version should implement **built-in operation modules**.

Prefer the code-level name `operation_modules` or `modules` over `plugins` for new backend code, APIs, and database tables. The word `plugin` must not imply user-uploaded code, dynamic installation, or arbitrary Python execution.

Do not implement user-uploaded Python plugins.

Do not implement dynamic third-party plugin installation.

Do not execute arbitrary uploaded code.

The operation module mechanism should be lightweight and internal.

Recommended structure:

```text
backend/app/operation_modules/
├── base.py
├── registry.py
├── system_inspection/
├── service_manage/
└── docker_manage/
```

## Confirmed Scope

The following decisions are already confirmed and should not be changed without explicit instruction:

1. The project title is based on **FastAPI + Ansible**.
2. The platform mainly manages **Linux hosts**.
3. Remote execution must use **Ansible Runner**.
4. SSH authentication should use **SSH key-based authentication**.
5. The platform should not store server SSH passwords.
6. SQLite is used as the initial database.
7. APScheduler triggers scheduled jobs.
8. Celery executes background tasks.
9. Redis is used as the Celery broker.
10. Vue 3 + Element Plus is used for the frontend.
11. Frontend UI text should support Simplified Chinese and English.
12. Built-in operation module extensibility should be reserved for future Docker, log, database, or Kubernetes-related features.

## Out of Scope for the First Version

Do not implement these unless explicitly requested:

* Kubernetes cluster management
* Web terminal
* Bastion host session recording
* Complex approval workflow
* Complex RBAC with per-host or per-button permission
* User-uploaded plugin system
* Dynamic Python code execution from users
* Full CI/CD pipeline platform
* Full Docker Compose deployment management
* Container image build platform
* Multi-tenant enterprise permission model
* Distributed agent installed on every host

These can be mentioned as future extensions in documentation, but they should not become first-version requirements.

## Recommended Modules

### 1. User Authentication Module

Responsibilities:

* User login
* JWT token generation
* Current user information
* Basic role distinction

Recommended roles:

```text
admin
user
```

Avoid complex permission systems in the first version.

### 2. Host Management Module

Responsibilities:

* Add host
* Edit host
* Delete host
* View host list
* Test Ansible connectivity
* Store host metadata

Suggested host fields:

```text
id
name
ip_address
ssh_port
ssh_user
private_key_path
description
created_at
updated_at
```

Do not store SSH passwords.

### 3. Host Group Module

Responsibilities:

* Create host group
* Edit host group
* Delete host group
* Add hosts to group
* Remove hosts from group

### 4. Ansible Execution Module

Responsibilities:

* Generate temporary Ansible inventory
* Invoke Ansible Runner
* Capture stdout
* Capture stderr or event data
* Save execution result
* Return task status to frontend

All remote execution should go through this module.

Do not add Paramiko as the primary execution mechanism.

### 5. Task Management Module

Responsibilities:

* Create execution task
* Track task state
* Store task metadata
* Associate task with selected hosts or host groups
* Associate task with selected built-in module task

Task states should include:

```text
pending
running
success
failed
partial_success
cancelled
```

Allowed task state transitions:

```text
pending -> running
pending -> cancelled
running -> success
running -> partial_success
running -> failed
running -> cancelled
```

Do not silently move terminal states (`success`, `partial_success`, `failed`, `cancelled`) back to `running`.

For multi-host tasks:

* Use `success` only when all targeted hosts complete successfully.
* Use `partial_success` when at least one host succeeds and at least one host fails or is unreachable.
* Use `failed` when all targeted hosts fail, the task cannot be dispatched, or execution crashes before meaningful host results are produced.

Celery worker exceptions must update the task status to `failed` and persist enough error information for troubleshooting. Ansible Runner non-zero status, unreachable hosts, and module failures must be reflected in `task_results`.

### 6. Execution Log Module

Responsibilities:

* Store execution output
* Store execution status
* Store start time and end time
* Store target host result
* Display logs in frontend

Logs should be detailed enough for troubleshooting and graduation-project demonstration.

### 7. Scheduled Job Module

Responsibilities:

* Create scheduled inspection job
* Enable or disable scheduled job
* Trigger task using APScheduler
* Submit actual execution to Celery
* Save scheduled task execution result

Important rule:

```text
APScheduler decides when to run.
Celery performs the actual execution.
Ansible Runner performs the remote operation.
```

Do not introduce Celery Beat unless explicitly requested.

### 8. Built-in Operations Module System

Responsibilities:

* Register built-in operations modules
* List available module tasks
* Provide task metadata
* Provide task parameters
* Generate Ansible execution content

Recommended built-in modules:

```text
system_inspection
service_manage
docker_manage
```

First version must implement:

```text
system_inspection
service_manage
```

Docker management can be a lightweight extension or demonstration module.

## Recommended Built-in Operations Modules

### System Inspection Module

Module key:

```text
system_inspection
```

Suggested tasks:

```text
check_disk
check_memory
check_load
check_uptime
check_logged_users
```

Example commands:

```bash
df -h
free -m
uptime
who
```

### Service Management Module

Module key:

```text
service_manage
```

Suggested tasks:

```text
service_status
service_start
service_stop
service_restart
service_reload
```

The service name must be passed as a parameter.

Example commands:

```bash
systemctl status nginx --no-pager
systemctl restart nginx
```

### Docker Basic Management Module

Module key:

```text
docker_manage
```

Suggested lightweight tasks:

```text
docker_status
list_containers
list_images
```

Avoid complex container creation, deletion, image building, or Compose management in the first version.

## Suggested Backend Directory Structure

```text
backend/
├── app/
│   ├── main.py
│   ├── core/
│   │   ├── config.py
│   │   ├── security.py
│   │   └── database.py
│   ├── models/
│   │   ├── user.py
│   │   ├── host.py
│   │   ├── group.py
│   │   ├── task.py
│   │   ├── result.py
│   │   └── scheduled_job.py
│   ├── schemas/
│   ├── api/
│   │   ├── auth.py
│   │   ├── hosts.py
│   │   ├── groups.py
│   │   ├── tasks.py
│   │   ├── logs.py
│   │   ├── schedules.py
│   │   └── operation_modules.py
│   ├── services/
│   │   ├── ansible_service.py
│   │   ├── task_service.py
│   │   ├── schedule_service.py
│   │   └── operation_module_service.py
│   ├── workers/
│   │   ├── celery_app.py
│   │   └── tasks.py
│   ├── scheduler/
│   │   └── scheduler.py
│   └── operation_modules/
│       ├── base.py
│       ├── registry.py
│       ├── system_inspection/
│       └── service_manage/
├── tests/
└── Dockerfile

pyproject.toml
uv.lock
docker-compose.yml
```

## Suggested Frontend Directory Structure

```text
frontend/
├── src/
│   ├── api/
│   ├── i18n/
│   ├── router/
│   ├── stores/
│   ├── views/
│   │   ├── Login.vue
│   │   ├── Dashboard.vue
│   │   ├── Hosts.vue
│   │   ├── HostGroups.vue
│   │   ├── OperationModules.vue
│   │   ├── Tasks.vue
│   │   ├── TaskLogs.vue
│   │   └── ScheduledJobs.vue
│   ├── components/
│   └── main.ts
├── package.json
├── pnpm-lock.yaml
├── pnpm-workspace.yaml
├── postcss.config.js
├── tailwind.config.ts
├── tsconfig.json
└── vite.config.ts
```

## Database Tables

Recommended tables:

```text
users
hosts
host_groups
host_group_members
operation_modules
operation_module_tasks
tasks
task_results
scheduled_jobs
```

The most important tables are:

```text
hosts
tasks
task_results
scheduled_jobs
```

Recommended minimal fields:

```text
users:
  id, username, hashed_password, role, is_active, created_at, updated_at

hosts:
  id, name, ip_address, ssh_port, ssh_user, private_key_path,
  description, created_at, updated_at

host_groups:
  id, name, description, created_at, updated_at

host_group_members:
  id, group_id, host_id, created_at

operation_modules:
  id, module_key, name, description, enabled, created_at, updated_at

operation_module_tasks:
  id, module_key, task_key, name, description, parameter_schema_json,
  enabled, created_at, updated_at

tasks:
  id, name, module_key, module_task_key, status, target_type,
  parameters_json, created_by, created_at, started_at, finished_at

task_results:
  id, task_id, host_id, status, stdout, stderr, raw_event_data,
  started_at, finished_at

scheduled_jobs:
  id, name, module_key, module_task_key, target_type, target_ids_json,
  parameters_json, schedule_type, cron_expression, interval_seconds,
  enabled, last_run_at, next_run_at, created_at, updated_at
```

For early prototypes, SQLAlchemy `metadata.create_all()` is acceptable. Once database tables stabilize, prefer Alembic migrations. Do not scatter ad-hoc SQL table-creation scripts across the project as the primary migration mechanism.

## API Design Rules

Use a versioned REST-style API prefix:

```text
/api/v1
```

Resource names should be plural and consistent.

Recommended endpoints:

```text
Authentication:
  POST /api/v1/auth/login
  GET  /api/v1/auth/me

Hosts:
  GET    /api/v1/hosts
  POST   /api/v1/hosts
  GET    /api/v1/hosts/{host_id}
  PUT    /api/v1/hosts/{host_id}
  DELETE /api/v1/hosts/{host_id}
  POST   /api/v1/hosts/{host_id}/test-connection

Host groups:
  GET    /api/v1/host-groups
  POST   /api/v1/host-groups
  GET    /api/v1/host-groups/{group_id}
  PUT    /api/v1/host-groups/{group_id}
  DELETE /api/v1/host-groups/{group_id}
  POST   /api/v1/host-groups/{group_id}/hosts
  DELETE /api/v1/host-groups/{group_id}/hosts/{host_id}

Operation modules:
  GET /api/v1/operation-modules
  GET /api/v1/operation-modules/{module_key}/tasks

Tasks:
  GET  /api/v1/tasks
  POST /api/v1/tasks
  GET  /api/v1/tasks/{task_id}
  GET  /api/v1/tasks/{task_id}/logs

Scheduled jobs:
  GET  /api/v1/scheduled-jobs
  POST /api/v1/scheduled-jobs
  PUT  /api/v1/scheduled-jobs/{job_id}
  POST /api/v1/scheduled-jobs/{job_id}/enable
  POST /api/v1/scheduled-jobs/{job_id}/disable
  POST /api/v1/scheduled-jobs/{job_id}/trigger
```

Keep FastAPI route functions thin. Validate input with Pydantic schemas, call service-layer functions, and return response schemas. Do not place Ansible Runner, Celery dispatch, or database-heavy business logic directly in route files.

## Security Rules

1. Do not store server SSH passwords.
2. Prefer SSH private key path over raw private key content.
3. Do not allow users to upload and execute arbitrary Python code.
4. Do not expose raw system paths unnecessarily in API responses.
5. Do not log JWT secrets, private key content, or sensitive environment variables.
6. Operations that affect remote hosts must be logged.
7. Destructive operations should require explicit confirmation at the API or frontend level.
8. Do not directly concatenate untrusted user input into shell commands.
9. Validate operation module parameters before generating Ansible tasks.
10. `service_manage` service names must be restricted to a safe format such as `[a-zA-Z0-9_.@-]+`.
11. `private_key_path` should point to an administrator-controlled or explicitly allowed path; never expose private key content through API responses or logs.
12. Prefer Ansible built-in modules such as `service`, `systemd`, `command`, or `shell` with carefully controlled arguments over arbitrary raw shell strings.

## Coding Style

### Python

* Prefer clear and simple code.
* Use type hints where practical.
* Add clear Chinese comments around important architecture, workflow, and learning points.
* Do not comment every trivial line; comments should explain intent, boundaries, or non-obvious design choices.
* Python triple-quoted strings should be used only for real module, class, or function docstrings. Ordinary implementation notes must use `#` comments.
* Code comments and docstrings should be written in Chinese for learning and review consistency.
* Keep FastAPI route functions thin.
* Put business logic in service modules.
* Do not place complex logic directly inside API route files.
* Use Pydantic schemas for request and response models.
* Use SQLAlchemy models for database tables.
* Use meaningful function names.

### Frontend

* Keep pages simple and clear.
* Use Element Plus components.
* Use Tailwind CSS for lightweight layout and spacing utilities.
* Use vue-i18n for user-facing UI text.
* The first version should support Simplified Chinese (`zh-CN`) and English (`en-US`).
* User-facing UI text should go through locale message files instead of being hardcoded directly in Vue templates.
* Avoid over-designed UI.
* Prioritize usability for graduation-project demonstration.
* API calls should be placed under `src/api/`.
* Route configuration should be placed under `src/router/`.

## Frontend UX Priorities

The frontend should serve the graduation-project demonstration path first.

Recommended page responsibilities:

* `Dashboard`: show host count, task count, recent task results, and scheduled job status.
* `Hosts`: list hosts, create/edit/delete hosts, and provide a visible connection test action.
* `HostGroups`: manage host groups and group membership.
* `OperationModules`: list available built-in modules and their task metadata.
* `Tasks`: create execution tasks, filter by status, and open task details.
* `TaskLogs`: show stdout, stderr, per-host result, status, start time, and finish time.
* `ScheduledJobs`: create scheduled inspections, enable/disable jobs, and manually trigger jobs for demonstration.

Do not over-invest in decorative UI before the core demonstration workflow is complete.

## Ansible Runner Rules

All Ansible execution should be wrapped by the backend service layer.

Recommended service:

```text
backend/app/services/ansible_service.py
```

The service should handle:

* Inventory generation
* Runner working directory creation
* Command or playbook execution
* Result parsing
* Error handling
* Log extraction

Do not call Ansible Runner directly from API routes.

## Celery Rules

Celery should be used for long-running operations.

Examples:

* Batch host inspection
* Service restart on multiple hosts
* Scheduled inspection job
* Docker status query on multiple hosts

Do not block FastAPI requests while waiting for long remote operations.

API should create a task and return task information quickly.

## APScheduler Rules

APScheduler should only trigger scheduled jobs.

It should not directly perform remote execution.

Correct flow:

```text
APScheduler trigger
  ↓
Create task record
  ↓
Submit Celery task
  ↓
Celery calls Ansible Runner
  ↓
Save result
```

## Testing Requirements

Backend tests should use `pytest`.

Python dependencies and test commands should be managed through `uv` from the repository root. Do not reintroduce `requirements.txt` unless a deployment target explicitly requires it.

Recommended backend testing scope:

* Service-layer unit tests for host management, task creation, operation module registration, and scheduling logic.
* FastAPI route tests using `TestClient` for key API paths.
* Temporary SQLite databases for database tests.
* Mock Ansible Runner in normal automated tests; do not require real remote hosts for unit tests.
* Mock Celery dispatch where appropriate, but verify that API calls create task records and request asynchronous execution.

Frontend testing can remain lightweight in the first version, but all frontend changes should keep the project buildable.

Verification expectations:

* After backend changes, run relevant `uv run pytest` tests when the test suite exists.
* After frontend changes, run the package manager's build or type-check command when the frontend project exists.
* If a test or build cannot be run because the project is not initialized yet, state that explicitly in the final response.

## Documentation Requirements

When adding or changing major features, update relevant documentation.

Recommended documentation files:

```text
README.md
docs/architecture.md
docs/database-design.md
docs/api-design.md
docs/deployment.md
docs/graduation-design-notes.md
```

README should explain:

* What Astralith is
* Technology stack
* Quick start
* Core features
* Project structure
* Development plan

Maintain both English and Simplified Chinese README files when project-level documentation changes:

```text
README.md
README.zh-CN.md
```

The two README files do not need to be literal translations, but they should describe the same scope, architecture, and development status.

## Graduation Project Requirements

This project is not only an open-source project but also a graduation design project.

When making design decisions, prefer choices that are:

* Easy to explain in a thesis
* Easy to demonstrate during defense
* Stable enough to finish
* Not unnecessarily complex
* Clearly related to automated operations

The most important demonstration path is:

```text
Login
  ↓
Add host
  ↓
Test connectivity
  ↓
Run system inspection
  ↓
View task status
  ↓
View execution log
  ↓
Create scheduled inspection
  ↓
Show scheduled execution result
```

## Do Not Change These Without Explicit Approval

Do not change the following core decisions without explicit user approval:

* FastAPI as backend framework
* SQLite as initial database
* Ansible Runner as remote execution engine
* Celery + Redis as async task system
* APScheduler as scheduled job trigger
* Vue 3 + Element Plus as frontend stack
* SSH key-based authentication for managed hosts
* Built-in operations module design
* Lightweight graduation-project scope

## Preferred Development Order

Recommended implementation order:

1. Initialize backend project
2. Initialize frontend project
3. Implement database connection
4. Implement user login
5. Implement host management
6. Implement host grouping
7. Implement Ansible connectivity test
8. Implement task model
9. Implement Celery worker
10. Implement Ansible execution task
11. Implement execution log storage
12. Implement system inspection module
13. Implement service management module
14. Implement scheduled job module
15. Implement basic dashboard
16. Add Docker Compose deployment
17. Improve documentation

## Final Reminder for Agents

Do not turn Astralith into a large enterprise platform.

The goal is a clean, understandable, demonstrable, lightweight automated operations platform.

Prioritize:

```text
clear architecture
stable core workflow
readable code
complete logs
simple deployment
graduation-project explainability
safe controlled automation
```

Avoid:

```text
scope creep
overengineering
unsafe plugin execution
complex permission systems
premature Kubernetes management
unnecessary microservices
```
