# 系统架构文档 (System Architecture)

## 1. 系统概览

Auto Writer 是一个基于大语言模型（DeepSeek）的多智能体协作网文生成系统。它采用前后端分离架构，通过异步任务队列管理复杂的生成流程。

### 核心能力
- **长篇小说创作**：支持分卷、分章的结构化生成。
- **多智能体协作**：大纲、书名、编排、细纲、正文各有独立 Agent。
- **上下文管理**：基于 Knowledge Base (RAG) 和 Novel Bible (世界观一致性) 进行生成。
- **完全可控**：支持生成任务的暂停、继续、取消及实时日志监控。

## 2. 技术栈

### 前端 (Frontend)
- **框架**: React 18, Vite
- **语言**: TypeScript
- **UI 组件库**: Shadcn/UI (基于 Radix UI), Tailwind CSS
- **状态管理**: Zustand
- **通信**: Axios (HTTP), EventSource (SSE 实时日志)

### 后端 (Backend)
- **框架**: FastAPI (Python 3.11)
- **数据库**: PostgreSQL (pgvector 向量支持)
- **ORM**: SQLAlchemy (Async)
- **迁移工具**: Alembic
- **任务队列**: Celery, Redis
- **LLM**: DeepSeek API (OpenAI Compatible)

### 部署 (Deployment)
- **容器化**: Docker, Docker Compose
- **网关**: Nginx (反向代理与静态资源服务)

## 3. 架构设计

### 3.1 系统组件图

```mermaid
graph TD
    Client[前端 (React)] <-->|HTTP/SSE| Nginx
    Nginx <-->|API| Server[API 服务 (FastAPI)]
    Nginx <-->|Static| Static[静态资源]
    
    Server <-->|CRUD| DB[(PostgreSQL)]
    Server -->|Task| Redis[(Redis)]
    
    Worker[Celery Worker] <-->|Pop Task| Redis
    Worker <-->|State/Result| DB
    Worker <-->|Chat| DeepSeek[DeepSeek API]
```

### 3.2 数据流向

1. **用户操作**：用户在前端触发生成任务（如生成大纲）。
2. **任务提交**：API 服务创建 `Run` 记录（Status=queued），并向 Celery 发送任务。
3. **任务执行**：
   - Worker 获取任务。
   - Worker 从 DB 读取 `NovelSetting` 和 `Knowledge`。
   - Worker 组装 Prompt，调用 DeepSeek API。
   - Worker 实时通过 SSE 抛出 `RunEvent`（日志/预览）。
   - Worker 完成生成，更新 DB（如 `OutlineVersion`）。
4. **状态反馈**：前端通过轮询或 SSE 监听 `Run`状态，实时更新 UI。

## 4. 目录结构

```
auto-writer/
├── backend/
│   ├── app/
│   │   ├── api/          # API 路由
│   │   ├── core/         # 配置与基础设施
│   │   ├── db/           # 数据库模型与会话
│   │   ├── llm/          # LLM 客户端
│   │   ├── services/     # 业务逻辑
│   │   ├── workers/      # Celery 任务与 Agent 实现
│   │   └── main.py       # 入口文件
│   └── alembic/          # 数据库迁移
├── frontend/
│   ├── src/
│   │   ├── components/   # UI 组件
│   │   ├── pages/        # 页面视图
│   │   ├── stores/       # 状态管理
│   │   └── utils/        # 工具函数
│   └── vite.config.ts
├── docker-compose.yml    # 容器编排
└── docs/                 # 项目文档
```
