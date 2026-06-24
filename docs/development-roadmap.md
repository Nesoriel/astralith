# Development Roadmap

## Version Strategy

Astralith uses small, demonstrable releases. Each version should be easy to explain in the graduation thesis and defense.

## v0.1.0 — Minimal Demonstration Loop

Goal: provide a runnable local prototype that demonstrates the core automated-operations workflow without pretending to be a full enterprise platform.

### Backend Scope

- Health checks under `/health` and `/api/v1/status`.
- Host CRUD API:
  - `GET /api/v1/hosts`
  - `POST /api/v1/hosts`
  - `GET /api/v1/hosts/{host_id}`
  - `PUT /api/v1/hosts/{host_id}`
  - `DELETE /api/v1/hosts/{host_id}`
  - `POST /api/v1/hosts/{host_id}/test-connection`
- Host group CRUD and membership API:
  - `GET /api/v1/host-groups`
  - `POST /api/v1/host-groups`
  - `GET /api/v1/host-groups/{group_id}`
  - `PUT /api/v1/host-groups/{group_id}`
  - `DELETE /api/v1/host-groups/{group_id}`
  - `POST /api/v1/host-groups/{group_id}/hosts`
  - `DELETE /api/v1/host-groups/{group_id}/hosts/{host_id}`
- Built-in operation module listing for `system_inspection` and `service_manage`.
- Task creation and logs API backed by SQLite records:
  - task creation validates module/task keys and target selection;
  - v0.1.0 records tasks and returns `pending` status;
  - actual long-running execution remains behind the Celery/Ansible service boundary for later versions.
- Scheduled job CRUD and manual trigger API backed by SQLite records.
- Pytest coverage for core API paths.

### Frontend Scope

- Vue 3 + Element Plus shell with Simplified Chinese / English i18n.
- Dashboard summary cards loaded from backend data where practical.
- Hosts page with list, create, delete, and connection-test actions.
- Host groups page with list and create/delete basics.
- Operation modules page with localized module/task metadata.
- Tasks page with module/task selection, target selection, task creation, and task list.
- Scheduled jobs page with create/list/enable/disable/manual trigger basics.

### Explicit Non-goals

- No web terminal.
- No SSH password storage.
- No user-uploaded plugins or dynamic Python execution.
- No complex RBAC.
- No Kubernetes or CI/CD management.
- No real remote execution requirement in automated tests.

## v0.1.1 — Security Maintenance

- Replace `python-jose` with `PyJWT[crypto]` to remove the vulnerable `ecdsa` dependency chain.
- Add JWT encode/decode regression coverage.
- Keep the release small: no feature scope expansion beyond dependency security and documentation.

## v0.2.0 — Real Execution Loop

- Generate Ansible inventory from selected hosts/groups.
- Generate playbooks from controlled built-in operation modules.
- Dispatch task creation to Celery and execute tasks through the worker service boundary.
- Persist per-host `TaskResult` rows with stdout, stderr, raw events, and timestamps.
- Parse Ansible Runner status and host events into task states: `running`, `success`, `partial_success`, and `failed`.
- Display task logs and per-host output in the Vue task page.

## v0.2.1 — Execution Loop Polish

- Add an explicit task status transition guard to prevent terminal-state regression.
- Isolate Ansible Runner working directories as `backend/.runner/task-{id}`.
- Replace Passlib with direct bcrypt hashing to avoid Python 3.13 `crypt` deprecation noise.
- Install `httpx2` for clean Starlette TestClient runs.
- Improve task log UI with loading states, status tags, timestamps, and raw event data.
- Configure Vite/Rolldown chunking and dependency warning handling for clean frontend builds.

## v0.3.0 — Authentication and Defense Polish

- Phase 1: add JSON login, `/api/v1/auth/me`, JWT validation, and an initial local admin user for deployment and demo startup.
- Phase 2: add a frontend login page, token storage, and route guard for the main app shell.
- Phase 3: apply authentication dependencies to write operations first, then evaluate read-route protection for the demo flow.
- Phase 4: improve dashboard cards/charts and task log presentation for graduation defense.
- Phase 5: add Docker Compose quick-start verification notes.

## v0.4.0 — Scheduled Execution and Operational Hardening

- Wire APScheduler persistence to scheduled jobs.
- Trigger Celery execution from scheduler events.
- Add better validation and error messages.
- Add deployment hardening notes.

## Quality Rules

- Code comments and docstrings are Chinese.
- User-facing frontend text goes through locale files.
- Backend tests run with `uv run pytest`.
- Frontend build runs with `pnpm --dir frontend build`.
- Each release should keep the project lightweight and thesis-friendly.
