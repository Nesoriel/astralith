# AI-native GitOps Roadmap

This document summarizes the long-term roadmap tracked in GitHub issue #1:

<https://github.com/Nesoriel/astralith/issues/1>

## Positioning

Astralith should remain a lightweight automated operations platform, but its post-v0.4 roadmap evolves toward an AI-native GitOps control plane for personal servers, homelab environments, and small teams.

```text
Astralith
= GitOps Reconciler
+ Ansible Executor
+ Docker Compose Stack Manager
+ Evidence-based AI Incident Analyzer
+ Policy-gated Operation Module Factory
```

The goal is not an unrestricted AI chat bot for servers. The goal is a controlled operations loop where Git describes desired state, Astralith compares desired and actual state, deterministic policy checks gate risk, humans approve changes, and AI only prepares evidence-based proposals.

## Target Scenarios

- PVE / homelab VM and container management.
- Docker Compose stack management across multiple Linux hosts.
- Lightweight automation for small teams.
- Ansible task execution and audit logging.
- Turning incident experience into reusable runbooks and operation module proposals.
- Using Git as the versioned source of infrastructure desired state.

## Core Principles

1. Git is the source of desired state for hosts, stacks, modules, and policies.
2. AI generates proposals only; it must not directly change production infrastructure.
3. Execution remains routed through Ansible Runner, Docker Compose, and controlled built-in operation modules.
4. User-uploaded Python plugins and arbitrary uploaded code execution remain out of scope.
5. High-risk operations require human approval.
6. Changes must be traceable, auditable, and rollback-aware.
7. Safety cannot rely only on LLM judgment; schema validation, allowlists, policy rules, syntax checks, and dry-run/check-mode validation are mandatory.
8. Early versions should persist proposals in SQLite first; exporting patches or PR drafts can come later.
9. Docker Compose and Ansible are first-class targets; Kubernetes management remains outside the near-term scope.

## Controlled GitOps Loop

```text
Git repository declares desired state
  -> Astralith syncs and parses hosts / stacks / modules / policies
  -> Desired State is compared with Actual State
  -> Diff and Apply Plan are generated
  -> Policy-as-Code validation and risk rating run
  -> Human reviewer approves or rejects
  -> Ansible Runner / Docker Compose executes approved operations
  -> Execution result, audit data, and rollback metadata are saved
```

## AI-assisted Incident Loop

```text
Task failure / inspection anomaly / user problem description
  -> Evidence Pack is built
  -> AI generates a diagnosis based on structured evidence
  -> Astralith checks whether existing modules cover the scenario
  -> AI proposes a runbook, operation module, GitOps change, or rollback plan
  -> Schema validation, policy validation, syntax-check, and dry-run/check-mode run
  -> Human reviewer approves or rejects
  -> Approved work is stored as controlled documentation, module drafts, or GitOps PR drafts
```

## Desired State Repository Shape

A typical desired-state repository may look like this:

```text
astralith-infra/
├── hosts/
│   ├── proxy-01.yaml
│   ├── monitoring-01.yaml
│   └── dev-01.yaml
├── stacks/
│   ├── uptime-kuma/
│   │   ├── stack.yaml
│   │   ├── compose.yaml
│   │   └── .env.example
│   └── nginx-proxy-manager/
│       ├── stack.yaml
│       ├── compose.yaml
│       └── .env.example
├── modules/
│   ├── system_inspection/
│   │   ├── module.yaml
│   │   ├── playbook.yaml
│   │   └── runbook.md
│   └── docker_compose_restart/
│       ├── module.yaml
│       ├── playbook.yaml
│       └── runbook.md
├── policies/
│   ├── compose-security.yaml
│   ├── ansible-risk-rules.yaml
│   └── operation-risk.yaml
└── README.md
```

## Key Concepts

### Desired / Actual Diff

Astralith should distinguish three concepts clearly:

```text
Desired State: target resources declared in Git.
Actual State: resources observed from the database, host scans, Docker status, and task results.
Diff: differences between desired and actual state.
Apply Plan: controlled steps required to reconcile the diff.
```

### Evidence Pack

AI analysis must use structured evidence rather than free-form guessing. An Evidence Pack can include task stdout/stderr, Ansible events, host facts, Docker status, systemd status, journal logs, port probes, disk usage, recent Git commits, and previous incidents.

AI reports should cite the evidence that supports each conclusion, such as the failing stderr line, abnormal container state, failed port probe, or related GitOps change.

### Policy-as-Code

Initial policy validation can be a lightweight built-in rules engine. OPA / Conftest can be evaluated later only if the project still stays lightweight.

Example Docker Compose policy checks:

- Block or flag `privileged: true` unless explicitly exempted.
- Block dangerous mounts such as `/`, `/etc`, and `/var/run/docker.sock` unless explicitly marked high-risk.
- Discourage `latest` image tags outside experimental environments.
- Require public ports to declare risk metadata.
- Require persistent volumes for database-like services.
- Reject real `.env`, private keys, and tokens.

Example Ansible policy checks:

- Block dangerous shell commands such as destructive root deletion, disk formatting, or mass deletion of critical directories.
- Restrict `shell` / `command` module usage.
- Force human approval for SSH, firewall, OpenWrt, database, and volume changes.
- Require check-mode support or a dry-run explanation when practical.

### AI Proposals

AI output should become reviewable objects instead of unstructured advice.

Supported proposal types:

```text
Incident Report
Runbook Proposal
Operation Module Proposal
GitOps Change Proposal
Policy Explanation
Rollback Plan Proposal
```

A GitOps Change Proposal should include target, affected hosts/stacks, evidence chain, change summary, risk level, validation steps, rollback plan, and whether a PR draft should be generated.

### Controlled Operation Module DSL

AI must not generate executable Python plugins. It may propose controlled module metadata or DSL that Astralith maps to existing safe actions, such as Docker Compose status, pull, up, logs, or Ansible playbooks passing validation.

## Recommended Architecture

```text
                 Git Repository
        hosts / stacks / modules / policies
                         │
                         ▼
              GitOps Sync Service
                         │
                         ▼
             Desired State Database
                         │
                         ▼
                Diff / Plan Engine
                         │
        ┌────────────────┴────────────────┐
        ▼                                 ▼
Policy Validator                  Evidence Pack Builder
        │                                 │
        ▼                                 ▼
Risk Report                  AI Analysis / Proposal
        │                                 │
        └────────────────┬────────────────┘
                         ▼
                 Human Review Center
                         │
                         ▼
              Ansible Runner Executor
                         │
                         ▼
             Result / Audit / Rollback Log
```

## Version Roadmap

### v0.5.0 — Evidence Pack + AI Incident Analysis MVP

Goal: generate structured Chinese incident reports from task evidence.

Scope:

- Add an AI analysis service boundary.
- Add Evidence Pack data structures.
- Build base evidence from task stdout, stderr, and raw events.
- Optionally include host facts, systemd status, Docker status, disk status, and port probes.
- Output summary, key evidence, likely causes, troubleshooting steps, and risk notes.
- Save AI analysis results to SQLite.
- Show AI analysis on the frontend task detail page.
- Do not perform automatic repair or generate executable modules.

Acceptance:

- A failed task can be selected and analyzed into a structured Chinese diagnosis.
- The report contains evidence references and human-review warnings.
- AI output cannot bypass the Evidence Pack and request dangerous commands directly.

### v0.6.0 — GitOps Repository Sync MVP

Goal: introduce Git repositories as desired-state sources.

Scope:

- Add `gitops_repositories` and `gitops_sync_runs` tables.
- Configure repository URL, branch, local path, and enabled state.
- Support manual sync and save latest commit SHA.
- Parse `hosts/*.yaml`, `stacks/*/stack.yaml`, `modules/*/module.yaml`, and `policies/*.yaml`.
- Show desired resources in the frontend.

Acceptance:

- Astralith can pull and parse a configured repository.
- The frontend can display Git-declared hosts, stacks, modules, and policies.
- Sync failures save error logs.

### v0.7.0 — Desired / Actual Diff + Policy Validation

Goal: compare desired and actual state, then generate controlled execution plans.

Scope:

- Add `desired_resources`, `actual_resources`, `resource_diffs`, `apply_plans`, and `policy_results` tables.
- Implement diff types for create, update, and delete.
- Generate Apply Plans.
- Validate Docker Compose files and Ansible playbook syntax.
- Run policy validation for risky fields.
- Add Diff Center and Apply Plan frontend pages.

Acceptance:

- A new stack committed to Git is detected as a diff and converted into a deployment plan.
- Dangerous compose/playbook content is flagged or blocked.
- Plans failing policy validation cannot be executed directly.

### v0.8.0 — Docker Compose GitOps Apply

Goal: deploy Docker Compose stacks through controlled approval and Ansible Runner execution.

Scope:

- Create `/opt/stacks/<stack_name>` on target hosts through Ansible Runner.
- Sync compose files and metadata.
- Run `docker compose config`, `pull`, and `up -d`.
- Verify container state, healthcheck, and ports.
- Save commit SHA, execution logs, stack state, and rollback metadata.
- Support rollback to compose content from a previous commit.

Acceptance:

- A Git-declared `uptime-kuma` stack can be detected, approved, and deployed.
- The frontend shows plan, logs, validation result, and rollback information.

### v0.9.0 — AI GitOps Change Proposal

Goal: generate reviewable GitOps change proposals from incident evidence.

Scope:

- Add `ai_proposals` table.
- Support incident_report, runbook, operation_module, gitops_change, and rollback_plan proposal types.
- Generate compose, module, or runbook modification suggestions from Evidence Packs.
- Support patch draft export.
- Optionally generate GitHub PR drafts instead of writing directly to the main branch.
- Add Proposal Review frontend page.

Acceptance:

- For a container incident, AI can generate a GitOps Change Proposal with an evidence chain.
- The proposal includes impact scope, risk level, change summary, validation steps, and rollback plan.
- Proposals require human approval and must not auto-execute.

### v1.0.0 — Self-growing Operation Module Factory

Goal: turn incident experience into reviewable, verifiable, reusable controlled operation module proposals.

Scope:

- Add `operation_module_proposals` table.
- Include title, problem summary, module key, task key, risk level, parameter schema, runbook, generated playbook, test plan, and status.
- Generate module proposals from task results, Evidence Packs, and incident reports.
- Support statuses: draft, reviewing, approved, rejected, implemented.
- Add safety validators for dangerous commands, Ansible module allowlists, parameter validation, and risk prompts.
- Run Ansible syntax-check on generated playbooks.
- Save dry-run/check-mode validation records.
- Allow admins to approve or reject with review comments.
- Export approved proposals as module drafts, documentation, tests, examples, and rollback notes.

Acceptance:

- A service anomaly or inspection failure can produce a module proposal.
- The proposal includes runbook, playbook draft, parameter notes, risk level, and test plan.
- Dangerous commands or missing validation are flagged as high-risk or validation failures.
- Approved proposals can be exported as reviewable module drafts.

## Frontend Workbench Productization — v1.0.x

GitHub issue #3 shifts the immediate 1.0.x focus from adding more backend primitives to making existing capabilities visible as product workflows.

```text
v1.0.1 Dashboard Summary Workbench
  -> real platform metrics and navigation cards
v1.0.2 Operation Module Workbench
  -> module details, parameter schemas, playbook preview, quick execution
v1.0.3 Task Incident Flow
  -> logs, Evidence Pack, AI analysis, and proposal actions in one flow
v1.0.4 GitOps Workbench
  -> sync, desired, actual, diff, plan, policy, approve, execute, apply run
v1.0.5 Proposal Review Workbench
  -> AI and module proposals with filters, review state, validation, export
```

Principles:

1. Reuse existing APIs first; add small aggregation endpoints only where they clearly improve the UX.
2. Each page should show the user's next operation, not just database rows.
3. Workbench pages should make the graduation defense flow visually obvious.
4. Do not introduce complex RBAC, Kubernetes UI, plugin marketplaces, or large enterprise dashboards.

## Database Extension Draft

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

## Frontend Pages

```text
GitOps Repositories: repository URL, branch, latest commit, sync status, sync logs.
Desired Resources: Git-declared hosts, stacks, modules, and policies.
Diff Center: desired/actual differences.
Apply Plan: planned actions, affected hosts, risk level, validation steps, rollback path.
Policy Results: passed, blocking, and review-required rules.
Evidence Pack: evidence used by AI analysis.
AI Analysis: structured incident report.
Proposal Review: review AI runbook/module/GitOps proposals.
Audit Log: commits, approvals, execution records, rollback records.
```

## Non-goals

- No fully autonomous self-modifying system.
- No arbitrary shell execution by an Agent.
- No user-uploaded plugin marketplace.
- No near-term Kubernetes management platform.
- No enterprise CMDB, bastion host, or complete CI/CD platform expansion.
- No complex multi-tenant permission model.
- No commercial-scale AIOps big-data platform.
- No unconditional auto-remediation; prefer semi-automatic, reviewable, rollback-aware operations.

## Graduation and Career Value

This roadmap turns Astralith from a normal CRUD plus task execution platform into a thesis-friendly DevOps/SRE platform prototype:

- GitOps: versioned infrastructure desired state.
- DevOps: change plan, execution, validation, and rollback loop.
- AIOps: evidence-based incident analysis instead of free chat.
- Security engineering: policy validation, risk rating, human approval, audit logs.
- Platform engineering: reusable operation capabilities distilled from real incidents.
