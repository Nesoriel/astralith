# API Design

All API routes should use the `/api/v1` prefix.

## v0.1.0 Endpoints

```text
GET    /health
GET    /api/v1/status

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

## Deferred Endpoints

- `/api/v1/auth` is planned for a later release with JWT-protected routes.
- Real Ansible connectivity testing and execution are planned for v0.2.0 through the service/Celery boundary.

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
