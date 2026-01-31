# 开发指南 (Development Guide)

## 1. 环境准备

确保本地已安装：
- Docker & Docker Compose
- Node.js 20+ (仅本地开发前端需要)
- Python 3.11+ (仅本地开发后端需要)

## 2. 快速启动 (One-Click Start)

最推荐的开发方式是直接使用 Docker Compose 启动全栈环境。

```bash
# 根目录下执行
docker compose up -d --build
```

访问地址：
- Web UI: http://localhost
- API Docs: http://localhost/api/docs

## 3. 本地开发 (Local Development)

如果需要单独调试前后端，可分别启动。

### 3.1 启动后端
需先启动数据库与 Redis。

```bash
# 启动依赖服务
docker compose up -d db redis

# 进入后端目录
cd backend
# 创建虚拟环境
python -m venv venv
source venv/bin/activate
# 安装依赖
pip install -r requirements.txt
# 设置环境变量
export PYTHONPATH=$PWD
export DATABASE_URL=postgresql+asyncpg://app:app@localhost:5432/app
export REDIS_URL=redis://localhost:6379/0

# 启动 Celery Worker (新终端)
celery -A app.worker worker -l info

# 启动 FastAPI (新终端)
uvicorn app.main:app --reload --port 8000
```

### 3.2 启动前端

```bash
cd frontend
npm install
npm run dev
```
访问 http://localhost:5173

> 注意：本地开发前端需配置 `.env` 或 `vite.config.ts` 中的 proxy 指向本地后端。

## 4. 数据库迁移 (Alembic)

当你修改了 `backend/app/db/models.py` 后，需要生成迁移文件。

```bash
# 在 backend 目录下
alembic revision --autogenerate -m "description of changes"
alembic upgrade head
```
> 在 Docker 环境中，可进入 backend 容器执行上述命令。

## 5. 调试指南

- **日志查看**：
  - 后端/Worker日志：`docker compose logs -f backend worker`
  - 数据库日志：`docker compose logs -f db`
- **Agent 调试**：
  - 在 `app/workers/novel_tasks.py` 中修改 Agent 逻辑。
  - 由于 Celery 的热重载机制有限，修改 Worker 代码后建议重启 Worker 容器：`docker compose restart worker`。

## 6. 添加新依赖

- **Backend**: 修改 `backend/requirements.txt`。
- **Frontend**: 修改 `frontend/package.json`。
- 修改后记得重新构建镜像：`docker compose up -d --build`。
