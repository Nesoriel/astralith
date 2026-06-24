# API Design

All API routes should use the `/api/v1` prefix.

## v0.3.0 Endpoints

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

GET    /api/v1/scheduled-jobs
POST   /api/v1/scheduled-jobs
GET    /api/v1/scheduled-jobs/{job_id}
PUT    /api/v1/scheduled-jobs/{job_id}
DELETE /api/v1/scheduled-jobs/{job_id}
POST   /api/v1/scheduled-jobs/{job_id}/enable
POST   /api/v1/scheduled-jobs/{job_id}/disable
POST   /api/v1/scheduled-jobs/{job_id}/trigger
```

## Authentication Rules

- `POST /api/v1/auth/login` returns a Bearer JWT for active local users.
- `GET /api/v1/auth/me` requires a valid Bearer JWT.
- Write operations such as creating/updating/deleting hosts, groups, tasks, and scheduled jobs require a valid Bearer JWT.
- Read operations remain available for the lightweight dashboard and graduation demonstration flow.

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
