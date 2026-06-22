# Database Design

SQLite is the initial database for local development and graduation-project deployment.

## Core Tables

- `users`
- `hosts`
- `host_groups`
- `host_group_members`
- `operation_modules`
- `operation_module_tasks`
- `tasks`
- `task_results`
- `scheduled_jobs`

## Task Status

Allowed task statuses:

- `pending`
- `running`
- `success`
- `partial_success`
- `failed`
- `cancelled`

For multi-host tasks, `partial_success` means at least one target host succeeded and at least one failed or was unreachable.

## Migration Policy

Early prototypes may use SQLAlchemy `metadata.create_all()`. Once the schema stabilizes, the project should introduce Alembic migrations.
