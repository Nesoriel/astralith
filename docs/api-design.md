# API Design

All API routes should use the `/api/v1` prefix.

## v0.9.0 Endpoints

```text
GET    /health
GET    /api/v1/status

POST   /api/v1/auth/login
GET    /api/v1/auth/me

GET    /api/v1/hosts
POST   /api/v1/hosts
GET    /api/v1/hosts/{host_id}
PUT    /api/v1/hosts/{host_id}
DELETE /api/v1/hosts/{host_id}
POST   /api/v1/hosts/{host_id}/test-connection

GET    /api/v1/host-groups
POST   /api/v1/host-groups
GET    /api/v1/host-groups/{group_id}
PUT    /api/v1/host-groups/{group_id}
DELETE /api/v1/host-groups/{group_id}
POST   /api/v1/host-groups/{group_id}/hosts
DELETE /api/v1/host-groups/{group_id}/hosts/{host_id}

GET    /api/v1/operation-modules
GET    /api/v1/operation-modules/{module_key}

GET    /api/v1/tasks
POST   /api/v1/tasks
GET    /api/v1/tasks/{task_id}
GET    /api/v1/tasks/{task_id}/logs
POST   /api/v1/tasks/{task_id}/ai-analysis

GET    /api/v1/scheduled-jobs
POST   /api/v1/scheduled-jobs
GET    /api/v1/scheduled-jobs/{job_id}
PUT    /api/v1/scheduled-jobs/{job_id}
DELETE /api/v1/scheduled-jobs/{job_id}
POST   /api/v1/scheduled-jobs/{job_id}/enable
POST   /api/v1/scheduled-jobs/{job_id}/disable
POST   /api/v1/scheduled-jobs/{job_id}/trigger

GET    /api/v1/gitops-repositories
POST   /api/v1/gitops-repositories
GET    /api/v1/gitops-repositories/{repository_id}
PUT    /api/v1/gitops-repositories/{repository_id}
POST   /api/v1/gitops-repositories/{repository_id}/sync
GET    /api/v1/gitops-repositories/{repository_id}/sync-runs
GET    /api/v1/gitops-repositories/{repository_id}/desired-resources
POST   /api/v1/gitops-repositories/actual-resources
GET    /api/v1/gitops-repositories/actual-resources
POST   /api/v1/gitops-repositories/{repository_id}/diff
GET    /api/v1/gitops-repositories/{repository_id}/diffs
GET    /api/v1/gitops-repositories/{repository_id}/apply-plans
GET    /api/v1/gitops-repositories/{repository_id}/policy-results
POST   /api/v1/gitops-repositories/apply-plans/{plan_id}/approve
POST   /api/v1/gitops-repositories/apply-plans/{plan_id}/execute
GET    /api/v1/gitops-repositories/{repository_id}/apply-runs
POST   /api/v1/gitops-repositories/apply-plans/{plan_id}/ai-proposal

GET    /api/v1/ai-proposals
POST   /api/v1/ai-proposals
POST   /api/v1/ai-proposals/{proposal_id}/approve
POST   /api/v1/ai-proposals/{proposal_id}/reject
```

## Authentication Rules

- `POST /api/v1/auth/login` returns a Bearer JWT for active local users.
- `GET /api/v1/auth/me` requires a valid Bearer JWT.
- Write operations such as creating/updating/deleting hosts, groups, tasks, scheduled jobs, and GitOps repositories require a valid Bearer JWT.
- `POST /api/v1/tasks/{task_id}/ai-analysis` requires a valid Bearer JWT because it creates persisted analysis records.
- `POST /api/v1/gitops-repositories/{repository_id}/sync` requires a valid Bearer JWT because it writes sync logs and Desired Resources.
- `POST /api/v1/gitops-repositories/actual-resources` and `POST /api/v1/gitops-repositories/{repository_id}/diff` require a valid Bearer JWT because they write Actual Resources, diffs, plans, and policy results.
- `POST /api/v1/gitops-repositories/apply-plans/{plan_id}/approve` and `/execute` require a valid Bearer JWT because they approve or execute controlled apply plans.
- AI proposal create, generate, approve, and reject endpoints require a valid Bearer JWT because they write review records.
- Read operations remain available for the lightweight dashboard and graduation demonstration flow.

## AI Analysis Rules

- The AI analysis endpoint analyzes existing `task_results`; it does not connect to remote hosts or execute repair commands.
- The service first persists an Evidence Pack, then stores an AI analysis result linked to that evidence.
- `GET /api/v1/tasks/{task_id}/logs` returns existing AI analyses beside task logs so the frontend can display evidence-based diagnosis reports.
- v0.5.0 uses a deterministic local analysis boundary suitable for tests and graduation demonstration. A real model provider can be added later only behind the same Evidence Pack and human-review boundary.

## GitOps Sync and Diff Rules

- v0.6.0 GitOps sync only clones/fetches a desired-state repository and parses files. It does not apply changes to managed hosts.
- Supported desired resource paths are `hosts/*.yaml`, `stacks/*/stack.yaml`, `modules/*/module.yaml`, and `policies/*.yaml`.
- Sync runs persist status, stdout/stderr, commit SHA, timestamps, and parsed Desired Resources.
- Parsed resource content is stored as JSON for display and later diff/plan work.
- v0.7.0 compares Desired Resources with Actual Resources and generates `create` or `update` diffs.
- Apply Plans are always created in `pending_review`; they are review artifacts, not execution commands.
- Policy Results are deterministic and can block plans, for example when a Docker Compose stack uses an image tagged `latest`.
- v0.8.0 only executes approved and policy-passed Docker Compose stack Apply Plans.
- Docker Compose apply runs go through the Ansible service boundary and persist stdout, stderr, raw events, target path, commit SHA, and rollback metadata.
- v0.9.0 AI proposals are reviewable drafts for GitOps changes, runbooks, operation modules, or rollback plans; they never modify Git repositories or execute infrastructure directly.

## Deferred Endpoints

- Real Ansible connectivity testing for the dedicated host test button is still deferred; task execution already goes through the service/Celery boundary.

## Route Layer Rules

FastAPI route functions should stay thin. Input validation belongs to Pydantic schemas, and business logic belongs to service modules.

## Internationalization

Frontend UI text uses `vue-i18n`. Backend operation module metadata exposes bilingual text because it is directly displayed by the frontend.

Example localized text shape:

```json
{
  "zh-CN": "系统巡检",
  "en-US": "System Inspection"
}
```

Backend API error-message i18n is intentionally deferred until the core task workflow is implemented.
