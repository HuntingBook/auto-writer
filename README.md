# Auto Writer（智能网文生成系统）

Auto Writer 是一个基于 DeepSeek 的多智能体协作网文生成系统，覆盖“设定 → 大纲 → 书名 → 分卷分章编排 → 正文”的完整流程，并提供实时日志与可控的异步任务执行。

## 核心特性

- 多智能体协作：大纲、取名、结构编排、章节大纲、正文生成、小说圣经维护等
- 长篇创作结构：分卷 / 分章标准化结构，支持批量轮询生成
- RAG 知识库：可录入文本或抓取 URL，生成时检索引用，减少设定跑偏
- 小说圣经：自动维护人物表、时间线、禁忌清单、伏笔回收清单
- 实时日志：SSE 推送过程事件，支持暂停 / 继续 / 取消
- 开箱即用：未配置 DeepSeek Key 也可运行（自动进入演示模式）；配置 Key 后自动使用 DeepSeek

## 服务说明（Docker Compose）

本项目默认通过 Docker Compose 启动 5 个服务：

- db：PostgreSQL + pgvector（本机端口 5413 → 容器 5432），持久化卷 `db_data`
- redis：任务状态与临时数据（无对外端口），持久化卷 `redis_data`
- backend：FastAPI API 服务（本机端口 8413 → 容器 8000）
- worker：Celery Worker（执行生成任务与编排），与 backend 共用同一镜像
- frontend：静态站点（nginx），本机端口 3413 → 容器 80

数据与产物：
- artifacts：生成结果与中间产物目录（容器内 `/data/artifacts`），持久化卷 `artifacts`

## 快速开始（Docker）

### 1) 前置要求

- Docker Desktop（或 Docker Engine）
- Docker Compose

### 2) 配置（可选）

你可以不配置 Key 直接启动（演示模式），也可以通过环境变量提供 DeepSeek Key。

- 环境变量方式（推荐）：`DEEPSEEK_API_KEY`
- 文件方式（可选）：`DEEPSEEK_API_KEY_FILE`（指向 Key 文件路径；容器内也会尝试默认路径）

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

## 桌面软件（安装与启动）

本项目默认是 Web 应用。你可以将 Web 前端“安装”为桌面应用（PWA/浏览器应用壳），获得更接近桌面软件的使用体验。

### Windows / macOS / Linux（Chrome 或 Edge）

1. 确保服务已启动，并在浏览器打开：http://localhost:3413
2. 在地址栏右侧点击“安装应用 / Install”按钮（或菜单：应用 / Apps → 安装此站点为应用）
3. 安装完成后从桌面/开始菜单启动

说明：
- 桌面应用只是“前端壳”，后端服务仍需要保持运行（Docker Compose 不要关闭）

### macOS（Safari）

1. 打开 http://localhost:3413
2. 选择“文件 → 添加到程序坞”

## 使用提示（上手路径）

建议按以下顺序操作：

1. 新建小说：背景设定写得越具体，生成质量越稳定
2. 生成大纲：可手动微调后保存为新版本
3. 生成书名：从候选中选择一个设为书名
4. 生成编排：生成分卷与章节标题列表
5. 逐章生成 / 批量轮询：生成章节大纲与正文，日志面板会显示进度与状态
6. 知识库：将人物卡、世界观补充、参考资料录入，提升一致性

## 常见问题

- 生成步骤提示“请先生成大纲/章节编排”：需要先按工作流完成上游步骤
- 日志显示“未连接”：通常是 SSE 连接尚未建立或网络代理影响，稍等或点击“刷新”
- 未配置 DeepSeek Key：系统会自动进入演示模式；配置后会自动切回 DeepSeek

## 文档

项目文档在 `docs/` 目录：
- [ARCHITECTURE.md](docs/ARCHITECTURE.md)
- [design.md](docs/design.md)
- [development.md](docs/development.md)
- [testing.md](docs/testing.md)
- [user_manual.md](docs/user_manual.md)
- [walkthrough.md](docs/walkthrough.md)

## 许可证

MIT License
