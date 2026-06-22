# Astralith / 星磐

[English](./README.md) | 简体中文

Astralith（星磐）是面向中小型 Linux 服务器环境的轻量级自动化运维平台，基于 FastAPI、Ansible Runner、SQLite、Celery、APScheduler 与 Vue 3 构建。

毕业设计题目：

> 基于 FastAPI 与 Ansible 的轻量级自动化运维平台设计与实现

## 当前状态

v0.2.0 提供轻量真实执行闭环：

- 主机 CRUD 与主机组管理。
- `system_inspection` 与 `service_manage` 内置运维模块元数据。
- 通过 Celery 边界投递执行任务。
- 为受控内置任务生成 Ansible inventory 与 playbook。
- 基于 SQLite 保存每台主机的 stdout、stderr 与原始事件数据。
- 定时任务记录支持启用、禁用与手动触发。
- Vue 3 任务日志展示，并支持简体中文与英文 i18n。

项目仍刻意避免企业 CMDB、堡垒机、Kubernetes 与用户上传插件等过大范围。

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

## 核心流程

```text
添加 Linux 主机
  -> 选择主机或主机组
  -> 选择内置运维任务
  -> 创建执行任务
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
