# API Design

All API routes should use the `/api/v1` prefix.

## Initial Endpoints

```text
GET  /health
GET  /api/v1/status
GET  /api/v1/operation-modules
GET  /api/v1/operation-modules/{module_key}
POST /api/v1/tasks
```

## Planned Resources

- `/api/v1/auth`
- `/api/v1/hosts`
- `/api/v1/host-groups`
- `/api/v1/operation-modules`
- `/api/v1/tasks`
- `/api/v1/scheduled-jobs`

FastAPI route functions should stay thin. Input validation belongs to Pydantic schemas, and business logic belongs to service modules.

## Internationalization

Frontend UI text uses `vue-i18n`. Backend operation module metadata should expose bilingual text where it is directly displayed by the frontend.

Example localized text shape:

```json
{
  "zh-CN": "系统巡检",
  "en-US": "System Inspection"
}
```

Backend API error-message i18n is intentionally deferred until the core task workflow is implemented.
