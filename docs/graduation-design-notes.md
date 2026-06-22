# Graduation Design Notes

Project title:

> 基于 FastAPI 与 Ansible 的轻量级自动化运维平台设计与实现

## Demonstration Path

```text
Login
  -> Add host
  -> Test Ansible connectivity
  -> Run system inspection
  -> View task status
  -> View execution log
  -> Create scheduled inspection
  -> Show scheduled execution result
```

## Thesis-Friendly Design Decisions

- FastAPI provides clear API structure and automatic OpenAPI documentation.
- Ansible Runner keeps remote execution standardized and explainable.
- Celery separates long-running operations from HTTP requests.
- APScheduler demonstrates scheduled inspection without introducing Celery Beat.
- SQLite keeps deployment simple for a graduation-project environment.
- Built-in operation modules avoid unsafe third-party plugin execution.
