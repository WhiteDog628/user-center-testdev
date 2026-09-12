# User Center TestDev
基于 **Flask + MySQL + pytest + Docker + GitHub Actions** 搭建的用户中心接口测试与 CI/CD 实践项目。

项目覆盖用户注册、登录、JWT 鉴权和个人信息维护等核心接口，并围绕接口功能、异常参数、边界条件、数据库一致性等场景构建自动化测试。同时通过 Docker Compose、GitHub Actions、GHCR 和 self-hosted Runner 实现从代码提交到 Linux 环境自动部署的完整流水线。

## Tech Stack

| Category | Technology |
| --- | --- |
| Backend | Python, Flask, Flask-SQLAlchemy |
| Authentication | JWT |
| Database | MySQL 8.0 |
| API Testing | pytest, requests |
| DB Validation | PyMySQL, SQL |
| Containerization | Docker, Docker Compose |
| CI/CD | GitHub Actions |
| Image Registry | GitHub Container Registry |
| Deployment | self-hosted Runner, SSH, Ubuntu WSL2 |

## Core APIs

| Method | Endpoint | Description |
| --- | --- | --- |
| GET | `/health` | 服务健康检查 |
| POST | `/api/register` | 用户注册 |
| POST | `/api/login` | 用户登录并获取 JWT |
| GET | `/api/user/profile` | 查询当前用户信息 |
| PUT | `/api/user/profile` | 更新用户名或邮箱 |

## Automated Testing

当前自动化测试共 **40 个 pytest 用例**，主要覆盖：

- 正常注册、登录及用户信息查询/修改
- 缺失字段、非 JSON 请求等异常输入
- 用户名、邮箱唯一性冲突
- 用户名 50/51 字符、邮箱 120/121 字符等边界值
- JWT 缺失等鉴权异常
- 参数化测试减少重复用例代码
- fixture 自动创建并清理测试用户
- SQL 直连数据库校验接口写入结果
- 校验密码以哈希形式持久化，而非明文存储

执行测试：

```bash
python -m pytest -v
```

## Defect Example

在用户名边界测试中发现：

```text
username length = 51
Expected: HTTP 400
Actual:   HTTP 500
```

根因是接口层未限制用户名长度，超过数据库 `VARCHAR(50)` 后由 MySQL 抛出异常，最终表现为服务端 500。

修复方式是在 API 层增加输入长度校验：

```text
len(username) > 50 -> HTTP 400
```

并保留 50/51 字符边界测试作为回归用例。

该案例形成了：

```text
测试设计
   ↓
自动化用例暴露缺陷
   ↓
日志 / 数据库定位
   ↓
接口校验修复
   ↓
自动化回归
```

的完整缺陷闭环。

## Docker

开发环境通过 Docker Compose 启动 Flask 与 MySQL：

```bash
docker compose up -d --build
```

查看服务：

```bash
docker compose ps
```

停止并清理：

```bash
docker compose down -v
```

应用默认访问：

```text
http://127.0.0.1:5000
```

健康检查：

```bash
curl http://127.0.0.1:5000/health
```

## CI/CD Pipeline

代码提交到 `main` 后，GitHub Actions 自动执行：

```text
git push
   │
   ▼
API Test CI
   │
   ├── Build Flask + MySQL test environment
   │
   ├── Wait for MySQL initialization
   │
   ├── Health check
   │
   └── Run 40 pytest tests
   │
   ▼
Build Docker Image
   │
   ├── Build application image
   ├── Tag with latest
   └── Tag with Git commit SHA
   │
   ▼
Push to GHCR
   │
   ▼
Self-hosted Runner
   │
   ▼
SSH to Ubuntu deployment environment
   │
   ▼
Deploy exact SHA image
   │
   ├── Health check
   ├── Register smoke test
   ├── Login smoke test
   ├── Profile smoke test
   └── Clean smoke-test data
   │
   ▼
Deployment Success
```

每个成功部署版本使用 Git Commit SHA 对应 Docker 镜像，例如：

```text
ghcr.io/<owner>/user-center-testdev:<git-sha>
```

从而保证部署版本可追踪。

## Deployment Rollback

部署脚本会保存最近一次成功部署的镜像：

```text
.last_successful_image
```

若新版本在部署、健康检查或 Smoke Test 阶段失败，则自动重新创建应用容器并恢复上一成功版本。

本项目通过故障注入实际验证过跨版本回滚流程：

```text
Version A running successfully
        ↓
Deploy Version B
        ↓
Inject deployment failure
        ↓
Deployment detected as failed
        ↓
Rollback to Version A
        ↓
Health check passed
```

故障解除后重新执行部署，新版本可正常上线。

> 当前部署环境为本地 **WSL2 Ubuntu Linux 测试环境**，用于验证完整 CI/CD 和回滚机制，并非公网生产服务器。

## Project Structure

```text
user-center-testdev/
├── .github/
│   └── workflows/
│       └── ci.yml
├── app/
│   ├── __init__.py
│   ├── extensions.py
│   ├── models.py
│   └── routes.py
├── deploy/
│   ├── .env.example
│   ├── compose.prod.yaml
│   ├── deploy.sh
│   └── init.sql
├── docker/
│   └── mysql/
│       └── init.sql
├── tests/
│   ├── conftest.py
│   ├── test_health.py
│   ├── test_login.py
│   ├── test_profile.py
│   └── test_register.py
├── compose.yaml
├── Dockerfile
├── config.py
├── requirements.txt
└── run.py
```

## What This Project Demonstrates

该项目重点体现测试开发岗位所需的