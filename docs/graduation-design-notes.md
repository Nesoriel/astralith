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

## Extended Innovation Direction

After the basic demonstration path is stable, the roadmap in `docs/gitops-ai-roadmap.md` gives Astralith a clearer innovation story for graduation defense and internships:

- GitOps: Git stores versioned desired state for hosts, Docker Compose stacks, operation modules, and policies.
- DevOps loop: Astralith generates diffs, apply plans, execution logs, validation results, and rollback metadata.
- AIOps: AI analysis is based on structured Evidence Packs instead of free-form chat.
- Security engineering: schema validation, policy rules, risk ratings, human review, and audit logs gate proposed changes.
- Platform engineering: recurring incident experience can become reviewable runbooks and controlled operation module proposals.

This direction should be presented as a controlled, semi-automatic operations platform. It is not a fully autonomous self-healing system, not a Kubernetes platform, and not a user-uploaded plugin marketplace.
