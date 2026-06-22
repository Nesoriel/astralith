# Astralith / 星磐

[English](./README.md) | 简体中文

Astralith，中文代号“星磐”，是 Nesoriel 开源组织下的轻量级自动化运维平台。项目基于 FastAPI 与 Ansible Runner 构建，面向中小型 Linux 服务器环境，重点提供主机管理、Ansible 自动化执行、定时巡检、执行日志与内置运维模块能力。

毕业设计题目：

> 基于 FastAPI 与 Ansible 的轻量级自动化运维平台设计与实现

## 项目目标

Astralith 的目标是实现一个实用、可维护、易演示的轻量级自动化运维平台，而不是大型企业 CMDB、堡垒机、Kubernetes 管理平台或完整 CI/CD 系统。

核心业务流程：

```text
用户登录
  ↓
添加 Linux 主机
  ↓
测试 Ansible 连通性
  ↓
选择主机或主机组
  ↓
选择运维任务
  ↓
提交任务到后端
  ↓
Celery 异步执行任务
  ↓
Ansible Runner 在目标主机执行自动化操作
  ↓
执行结果保存到 SQLite
  ↓
前端展示任务状态与执行日志
```

## 技术栈

### 后端

- Python
- FastAPI
- SQLAlchemy
- SQLite
- Ansible Runner
- Celery
- Redis
- APScheduler
- JWT 认证

### 前端

- Vue 3
- Element Plus
- 如果项目初始化支持，优先使用 TypeScript

### 部署

- Docker Compose
- SQLite 用于本地开发和毕业设计部署
- Redis 作为 Celery broker

## 核心功能

- 用户登录与 JWT 认证
- Linux 主机管理
- 主机组管理
- 基于 SSH 密钥的 Ansible 连通性测试
- 内置运维模块注册与查询
- 系统巡检任务
- 服务管理任务
- 基于 Celery 的异步任务执行
- Ansible Runner 执行集成
- 执行日志存储与展示
- APScheduler 触发的定时巡检任务

## 内置运维模块

第一版只实现内部内置运维模块，不实现用户上传插件，也不执行用户上传的 Python 代码。

计划模块：

- `system_inspection`：系统巡检
  - `check_disk`：检查磁盘
  - `check_memory`：检查内存
  - `check_load`：检查系统负载
  - `check_uptime`：检查运行时间
  - `check_logged_users`：检查登录用户
- `service_manage`：服务管理
  - `service_status`：查看服务状态
  - `service_start`：启动服务
  - `service_stop`：停止服务
  - `service_restart`：重启服务
  - `service_reload`：重载服务
- `docker_manage`：Docker 基础管理，可作为后续轻量扩展或演示模块

## 建议项目结构

```text
backend/
├── app/
│   ├── main.py
│   ├── core/
│   ├── models/
│   ├── schemas/
│   ├── api/
│   ├── services/
│   ├── workers/
│   ├── scheduler/
│   └── operation_modules/
├── tests/
├── requirements.txt
└── Dockerfile

frontend/
├── src/
│   ├── api/
│   ├── router/
│   ├── stores/
│   ├── views/
│   └── components/
├── package.json
└── vite.config.ts
```

## 开发路线

1. 初始化后端项目
2. 初始化前端项目
3. 实现数据库连接
4. 实现用户登录
5. 实现主机管理
6. 实现主机分组
7. 实现 Ansible 连通性测试
8. 实现任务模型与任务状态管理
9. 实现 Celery worker
10. 实现 Ansible 执行服务
11. 存储并展示执行日志
12. 实现系统巡检模块
13. 实现服务管理模块
14. 实现定时任务模块
15. 实现基础仪表盘
16. 添加 Docker Compose 部署
17. 完善项目文档

## 安全原则

- 不存储被管理服务器的 SSH 密码。
- 优先保存 SSH 私钥路径，而不是原始私钥内容。
- 不允许用户上传并执行 Python 代码。
- 不实现动态第三方插件安装。
- 不记录 JWT 密钥、私钥内容或敏感环境变量。
- 所有影响远程主机的操作必须记录日志。
- 破坏性操作应在 API 或前端层面要求明确确认。

## 文档

详细的架构约束、代理开发规则与毕业设计边界记录在 [AGENTS.md](./AGENTS.md)。后续可补充：

- `docs/architecture.md`
- `docs/database-design.md`
- `docs/api-design.md`
- `docs/deployment.md`
- `docs/graduation-design-notes.md`

## 许可证

本项目遵循 [LICENSE](./LICENSE) 中声明的许可证。
