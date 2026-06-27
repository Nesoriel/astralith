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

## Planned GitOps and AI Tables

The AI-native GitOps roadmap adds tables only when the corresponding release starts. Keep these tables reviewable and SQLite-friendly; do not introduce a separate storage system unless the lightweight scope is explicitly changed.

```text
gitops_repositories
- id, name, repo_url, branch, local_path, auth_type, enabled, last_sync_at

gitops_sync_runs
- id, repository_id, commit_sha, status, stdout, stderr, started_at, finished_at

desired_resources
- id, repository_id, commit_sha, resource_type, resource_key, file_path, content_json, content_hash

actual_resources
- id, resource_type, resource_key, source, content_json, content_hash, scanned_at

resource_diffs
- id, sync_run_id, resource_type, resource_key, diff_type, before_json, after_json, risk_level

apply_plans
- id, diff_id, plan_json, status, policy_status, ai_summary, approved_by, approved_at

policy_results
- id, plan_id, rule_key, severity, passed, message

evidence_packs
- id, task_result_id, host_id, content_json, created_at

ai_analysis_results
- id, evidence_pack_id, summary, content_json, model_name, created_at

ai_proposals
- id, evidence_pack_id, proposal_type, title, content_json, status, risk_level

operation_module_proposals
- id, source_proposal_id, module_key, title, problem_summary, parameters_schema, runbook, generated_playbook, test_plan, status, risk_level
```

These tables support desired-state sync, actual-state scanning, diff generation, policy-gated apply plans, structured Evidence Packs, AI analysis, and reviewable proposals. AI-generated content should be stored as proposals or analysis results, not treated as automatically trusted execution input.
