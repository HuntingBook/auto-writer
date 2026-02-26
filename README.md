# Auto Writer（智能网文生成系统）

Auto Writer 是一个基于 DeepSeek 的多智能体协作网文生成系统，覆盖“设定 → 大纲 → 书名 → 分卷分章编排 → 正文”的完整流程，并提供实时日志与可控的异步任务执行。

## 核心特性

- 多智能体协作：大纲、取名、结构编排、章节大纲、正文生成、小说圣经维护等
- 长篇创作结构：分卷 / 分章标准化结构，支持批量轮询生成
- RAG 知识库：可录入文本或抓取 URL，生成时检索引用，减少设定跑偏
- 小说圣经：自动维护人物表、时间线、禁忌清单、伏笔回收清单
- 实时日志：SSE 推送过程事件，支持暂停 / 继续 / 取消
- 开箱即用：需配置DeepSeek Key

## 服务说明

本项目默认通过 Docker Compose 启动 5 个服务：

- **数据库 (db)**：PostgreSQL + pgvector（本机端口 5413 → 容器 5432），持久化卷 `db_data`
- **缓存 (redis)**：任务状态与临时数据（无对外端口），持久化卷 `redis_data`
- **后端 (backend)**：FastAPI API 服务（本机端口 8413 → 容器 8000）
- **工作节点 (worker)**：Celery Worker（执行生成任务与编排），与 backend 共用同一镜像
- **前端 (frontend)**：静态站点（nginx），本机端口 3413 → 容器 80

数据与产物：

- **产物目录 (artifacts)**：生成结果与中间产物目录（容器内 `/data/artifacts`），持久化卷 `artifacts`

## 快速开始（Docker）

### 1) 前置要求

- Docker 桌面版（或 Docker 引擎）
- Docker Compose

### 2) 配置（必须配置）

你需配置环境变量提供 DeepSeek 密钥。

- 环境变量方式（推荐）：`DEEPSEEK_API_KEY`
- 文件方式（可选）：`DEEPSEEK_API_KEY_FILE`（指向密钥文件路径；容器内也会尝试默认路径）

示例（不把密钥写进仓库）：

- 复制 `.env.example` 为 `.env`，在 `.env` 中填写 `DEEPSEEK_API_KEY=...`

### 3) 启动

```bash
docker compose up -d --build
```

启动后访问：

- Web 前端：http://localhost:3413

### 4) 关闭与清理

- 仅停止：`docker compose down`
- 清空本地数据（会删除数据库/redis/产物）：`docker compose down -v`

## 桌面开发模式 (桌面应用)

如果你希望以桌面软件形式运行前端（基于 Electron），请确保本地已安装 Node.js。

1.  **启动后端服务**（保持 Docker 运行）：

    ```bash
    docker compose up -d db redis backend worker
    ```

2.  **启动桌面应用**：
    ```bash
    cd frontend
    npm install
    npm run electron
    ```
    这将同时启动 Vite 开发服务器和 Electron 窗口。

## 使用提示（上手路径）

建议按以下顺序操作：

1. 新建小说：背景设定写得越具体，生成质量越稳定
2. 生成大纲：可手动微调后保存为新版本
3. 生成书名：从候选中选择一个设为书名
4. 生成编排：生成分卷与章节标题列表
5. 逐章生成 / 批量轮询：生成章节大纲与正文，日志面板会显示进度与状态
6. 知识库：将人物卡、世界观补充、参考资料录入，提升一致性

## 页面截图

参考 `snapshots/`目录截图

## 常见问题

- 生成步骤提示“请先生成大纲/章节编排”：需要先按工作流完成上游步骤
- 日志显示“未连接”：通常是 SSE 连接尚未建立或网络代理影响，稍等或点击“刷新”
- 未配置 DeepSeek 密钥：系统会自动进入演示模式；配置后会自动切回 DeepSeek

## 文档

项目文档在 `docs/` 目录：

- [架构文档 (ARCHITECTURE.md)](docs/ARCHITECTURE.md)
- [设计文档 (design.md)](docs/design.md)
- [开发文档 (development.md)](docs/development.md)
- [测试文档 (testing.md)](docs/testing.md)
- [用户手册 (user_manual.md)](docs/user_manual.md)
