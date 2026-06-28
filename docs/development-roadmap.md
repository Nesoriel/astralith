# Development Roadmap

## Version Strategy

Astralith uses small, demonstrable releases. Each version should be easy to explain in the graduation thesis and defense.

The v0.1.0 to v0.4.0 releases establish the lightweight FastAPI + Ansible automated-operations loop. Starting from v0.5.0, the roadmap follows GitHub issue #1 and evolves Astralith toward an AI-native GitOps control plane. The earlier AI-assisted operation module factory direction is preserved as the v1.0.0 self-growing module factory milestone. The detailed long-term design is maintained in `docs/gitops-ai-roadmap.md`.

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

- Register enabled scheduled jobs with APScheduler during app startup and job create/update/enable/disable/delete operations.
- Trigger normal task creation from APScheduler events, then dispatch execution through Celery.
- Persist `next_run_at` for scheduled jobs when APScheduler provides the next run time.
- Support interval schedules and five-field cron expressions.
- Guard disabled or deleted jobs from stale scheduler callbacks.
- Add focused tests for scheduler registration, callback behavior, and cron/interval handling.
- Add deployment notes for secrets, default admin password, Redis reachability, SQLite persistence, and SSH key mounts.

## v0.5.0 — Evidence Pack + AI Incident Analysis MVP

Goal: generate structured Chinese incident reports from controlled task evidence without allowing AI to execute repairs.

- Add an AI analysis service boundary.
- Add Evidence Pack data structures based on task stdout, stderr, and raw Ansible events.
- Optionally enrich evidence with host facts, systemd status, Docker status, disk status, and port probes.
- Persist AI analysis results in SQLite.
- Display AI analysis on the frontend task detail page.
- Require evidence references and human-review warnings in reports.
- Keep automatic repair, executable module generation, and arbitrary shell execution out of scope.

## v0.6.0 — GitOps Repository Sync MVP

Goal: introduce Git repositories as the desired-state source for hosts, stacks, modules, and policies.

- Add `gitops_repositories` and `gitops_sync_runs` tables.
- Support repository URL, branch, local path, enabled state, manual sync, and latest commit SHA tracking.
- Parse `hosts/*.yaml`, `stacks/*/stack.yaml`, `modules/*/module.yaml`, and `policies/*.yaml`.
- Store sync errors and expose desired resources in the frontend.

## v0.7.0 — Desired / Actual Diff + Policy Validation

Goal: compare Git-declared desired state with observed actual state and generate controlled execution plans.

- Add `desired_resources`, `actual_resources`, `resource_diffs`, `apply_plans`, and `policy_results` tables.
- Implement create/update/delete diff types and Apply Plan generation.
- Validate Docker Compose files and Ansible playbook syntax.
- Add deterministic policy validation for high-risk fields and operations.
- Add Diff Center and Apply Plan frontend pages.
- Block direct execution when policy validation fails.

## v0.8.0 — Docker Compose GitOps Apply

Goal: deploy Docker Compose stacks through human-approved plans and Ansible Runner execution.

- Create `/opt/stacks/<stack_name>` on target hosts.
- Sync compose files and metadata.
- Run `docker compose config`, `docker compose pull`, and `docker compose up -d` through controlled Ansible tasks.
- Verify container state, healthcheck, and ports after deployment.
- Save commit SHA, execution logs, stack state, and rollback metadata.
- Support rollback to compose content from a previous commit.

## v0.9.0 — AI GitOps Change Proposal

Goal: generate reviewable GitOps change proposals from structured incident evidence.

- Add `ai_proposals` table.
- Support incident report, runbook, operation module, GitOps change, and rollback plan proposal types.
- Generate compose, module, or runbook modification suggestions from Evidence Packs.
- Support patch draft export and optional GitHub PR drafts.
- Add Proposal Review frontend page.
- Require human approval before any proposal affects managed infrastructure.

## v1.0.0 — Self-growing Operation Module Factory

Goal: turn incident experience into reviewable, verifiable, reusable controlled operation module proposals.

- Add `operation_module_proposals` table.
- Store title, problem summary, module key, task key, risk level, parameter schema, runbook, generated playbook, test plan, status, review comments, and rollback notes.
- Generate module proposals from task results, Evidence Packs, and incident reports.
- Support `draft`, `reviewing`, `approved`, `rejected`, and `implemented` statuses.
- Add dangerous-command detection, Ansible module allowlists, parameter validation, and risk prompts.
- Run Ansible syntax-check and save dry-run/check-mode validation records.
- Require human review before a proposal can be marked implemented.
- Export approved proposals as reviewable module drafts, documentation, tests, examples, and rollback notes.

## v1.0.x — Frontend Workbench Productization

Goal: turn the v1.0.0 backend capabilities into clear, workflow-oriented frontend workbenches so the platform feels like an automated operations console rather than separate CRUD pages.

### v1.0.1 — Dashboard Summary Workbench

- Add `GET /api/v1/dashboard/summary` as a lightweight aggregation API.
- Show real counts for hosts, host groups, operation modules, module tasks, tasks, scheduled jobs, GitOps repositories, diffs, pending apply plans, blocked policy results, AI analyses, AI proposals, and operation module proposals.
- Group cards into operations execution, GitOps reconciliation, AI/proposal review, and safety/policy sections.
- Cards should guide the next click into the relevant workbench.

### v1.0.2 — Operation Module Workbench

- Replace the simple module-card page with a module workbench.
- Show module details, task details, parameter schemas, example parameters, playbook preview, quick task creation, and recent execution history.
- Make `check_disk` and `service_status` executable from the module page without forcing the user to switch to the generic Tasks page first.

### v1.0.3 — Task Incident Flow

- Upgrade the task log drawer/page into an incident workflow.
- Present task metadata, per-host results, stdout/stderr/raw events, Evidence Pack, AI Incident Analysis, and proposal actions in one flow.
- Let failed tasks lead naturally to AI Proposal review rather than stopping at log inspection.

### v1.0.4 — GitOps Workbench

- Consolidate GitOps repository sync, Desired Resources, Actual Resources, Diff Center, Apply Plans, Policy Results, and Apply Runs into a clearer reconciliation workbench.
- Use tabs or step indicators to express `sync -> desired -> actual -> diff -> plan -> policy -> approve -> execute -> apply run`.
- Keep the first implementation lightweight by reusing existing APIs before adding aggregation endpoints.

### v1.0.5 — Proposal Review Workbench

- Turn AI Proposal and Operation Module Proposal pages into a review center.
- Add status filters for draft, approved, rejected, implemented, and blocked proposals.
- Show source, risk, content preview, validation output, test plan, rollback notes, review comments, and export actions.
- Allow approved AI Proposals to generate Operation Module Proposals from the frontend.

### v1.0.6 — Workbench Flow and Error Handling Fixes

- Operation Module quick execution should immediately open or deep-link to the created task feedback loop.
- Recent module tasks should provide a visible log/incident action.
- Task Incident Flow should show Proposal cards with review navigation instead of raw JSON only.
- JSON textarea fallbacks must use safe parse handling with user-visible errors.
- Shared status/risk tag utilities should keep colors consistent across pages.

### v1.0.7 — Unified GitOps Workbench

- Combine repository sync, Desired Resources, Actual Resources, Diff, Apply Plans, Policy Results, and Apply Runs into one user flow.
- Keep the current repository as the shared workbench context.
- Make manual Actual Resource entry clearly marked as demo/manual state until issue #2 introduces real scanning.
- Add confirmation before executing Apply Plans.

### v1.0.8 — Dashboard Action Items and Deep Links

- Dashboard should show pending action lists, not only counters.
- Support useful query-parameter deep links such as `/tasks?task_id=123`, `/ai-proposals?id=5`, and `/operation-module-proposals?id=8`.
- Add focused workflow tests for the new workbench links and guards.
- Keep i18n keys synchronized and avoid new hardcoded user-facing strings.

### v1.0.9 — Issue #3 Final Quality Polish

- Use schema-driven operation module parameter forms with an advanced JSON fallback.
- Add Operation Module Proposal detail drawers and deep links.
- Unify JSON parse error handling and status/risk tag mapping across workbenches.
- Treat v1.0.9 as the issue #3 closure pass; move larger GitOps Apply, scanner, and orchestration features to issue #2.

## Quality Rules

- Code comments and docstrings are Chinese.
- User-facing frontend text goes through locale files.
- Backend tests run with `uv run pytest`.
- Frontend build runs with `pnpm --dir frontend build`.
- Each release should keep the project lightweight and thesis-friendly.
- AI and GitOps features must remain evidence-based, policy-gated, human-approved, and rollback-aware.
- AI-generated operation module proposals must include risk notes, test plans, rollback notes, and human review records before implementation.
