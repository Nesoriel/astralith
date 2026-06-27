# Astralith / 星磐

[English](./README.md) | 简体中文

Astralith（星磐）是面向中小型 Linux 服务器环境的轻量级自动化运维平台，基于 FastAPI、Ansible Runner、SQLite、Celery、APScheduler 与 Vue 3 构建。

毕业设计题目：

> 基于 FastAPI 与 Ansible 的轻量级自动化运维平台设计与实现

## 当前状态

v1.0.0 是第一个正式版本，提供带登录认证、定时执行、Evidence Pack AI 故障分析、GitOps 期望状态同步、Desired/Actual Diff 计划生成、受控 Docker Compose Apply 记录、AI GitOps 变更提案与自增长运维模块提案工厂的轻量闭环：

- 本地管理员登录、JWT 认证与 `/api/v1/auth/me`。
- 前端登录页、token 存储、路由守卫与退出登录。
- 后端写操作需要 JWT，读接口保持便于仪表盘展示。
- 主机 CRUD 与主机组管理。
- `system_inspection` 与 `service_manage` 内置运维模块元数据。
- 通过 Celery 边界投递执行任务。
- 为受控内置任务生成 Ansible inventory 与 playbook。
- 基于 SQLite 保存每台主机的 stdout、stderr 与原始事件数据。
- 定时任务记录支持启用、禁用、手动触发、APScheduler 注册与 `next_run_at` 展示。
- 基于任务 stdout、stderr 与原始 Ansible 事件构建 Evidence Pack。
- 保存带证据引用与人工复核提示的 AI 故障分析报告。
- 支持 GitOps 仓库配置、手动同步、最近 commit 记录，以及解析 `hosts`、`stacks`、`modules`、`policies` 期望状态资源。
- 支持 Actual Resource 写入、Desired/Actual Diff 生成、Apply Plan 创建与确定性策略校验。
- 支持人工审批后的 Docker Compose Apply Plan 经由 Ansible 服务边界执行，并保存 Apply Run 与回滚元数据。
- 支持 AI GitOps 变更与 Runbook 提案，并保存人工批准/拒绝评审记录。
- 支持自增长运维模块提案，包含危险命令检测、校验状态、评审意见与可导出模块草案。
- Vue 3 任务日志展示，并支持简体中文与英文 i18n。
- 针对当前 v1.0.x 工具链保持干净的测试与构建输出。

项目仍刻意避免企业 CMDB、堡垒机、Kubernetes 与用户上传插件等过大范围。

## 路线方向

在 v0.4 轻量执行闭环之后，Astralith 的后续路线会演进为面向个人服务器、Homelab 与小团队的 AI-native GitOps 运维控制平面：

- Git 仓库描述主机、Docker Compose Stack、运维模块与策略等期望状态。
- Astralith 同步期望状态，对比实际状态，并生成 Diff 与 Apply Plan。
- 策略校验、语法检查、dry-run / check mode、人工审核、审计日志与回滚信息共同约束变更。
- AI 基于结构化 Evidence Pack 分析故障，并生成可审核的故障报告、Runbook、GitOps 变更提案与运维模块提案。
- AI 不直接执行基础设施变更，也不能绕过受控的 Ansible Runner / Docker Compose 执行链路。

版本计划见 `docs/development-roadmap.md` 与 `docs/gitops-ai-roadmap.md`。

## 快速开始

后端：

```bash
uv sync
uv run uvicorn backend.app.main:app --reload
```

前端：

```bash
cd frontend
pnpm install
pnpm dev
```

验证：

```bash
uv run pytest
pnpm --dir frontend build
```

默认本地登录账号：

```text
用户名：admin
密码：admin123
```

## 核心流程

```text
登录系统
  -> 添加 Linux 主机
  -> 选择主机或主机组
  -> 选择内置运维任务
  -> 创建执行任务
  -> 按需创建定时巡检任务
  -> 状态与日志保存到 SQLite
  -> 前端查看结果
```

## 技术栈

- 后端：Python 3.12+、uv、FastAPI、SQLAlchemy、SQLite、Celery、Redis、APScheduler、Ansible Runner、pytest。
- 前端：Vue 3、Vite、pnpm、Element Plus、Tailwind CSS、TypeScript、vue-i18n。
- 部署：Docker Compose、SQLite、Redis。

## 文档

- `AGENTS.md`：项目边界、编码规则与架构约束。
- `docs/development-roadmap.md`：版本路线。
- `docs/gitops-ai-roadmap.md`：AI-native GitOps 与自成长运维模块路线。
- `docs/architecture.md`：架构概览。
- `docs/api-design.md`：REST API 设计。
- `docs/database-design.md`：数据库表设计。
- `docs/deployment.md`：部署说明。
- `docs/frontend-i18n.md`：前端 i18n 规则。
- `docs/graduation-design-notes.md`：毕业设计说明。

## 安全边界

- 不存储被管理服务器的 SSH 密码。
- 保存 SSH 私钥路径，而不是原始私钥内容。
- 不允许用户上传 Python 插件或执行任意代码。
- 远程操作必须记录日志，并通过服务层封装。

## 许可证

本项目遵循 [LICENSE](./LICENSE) 中声明的许可证。
