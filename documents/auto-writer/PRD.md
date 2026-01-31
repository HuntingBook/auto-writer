toolName: get_llm_config
            
status: success
          
          

        
            
toolName: file_search
            
status: success
          
file_pattern: **/user_rule.md
          

        
            
toolName: view_files
            
status: success
          
            
filePath: /Users/jack.yan/Downloads/labeleases/stage03/413/user_rule.md
          

        
            
toolName: view_folder
            
status: success
          
/Users/jack.yan/Downloads/labeleases/stage03/413
          
已研读 [user_rule.md](file:///Users/jack.yan/Downloads/labeleases/stage03/413/user_rule.md)。后续会在不与需求冲突的前提下严格遵循（如需冲突，以你的需求优先），并把全部代码与文档放在 `auto-writer/` 目录下。

**Implementation Plan（实施方案）**
- **交付形态（桌面优先 + 可验收运行态）**：核心形态按“桌面软件”设计（后续可用 Tauri/Electron 打包），同时提供 `docker compose up` 一键启动的“同款 Web 运行态”用于验收与调试（与桌面端同一套前端代码/同一套后端 API）。这样既满足桌面诉求，也尽量满足规范中的容器化交付与一键启动。
- **技术栈选择（满意度/成熟度优先）**
  - Frontend：React + Vite + Tailwind + Shadcn/UI（现代审美与组件能力，利于“藏书阁”风格与响应式）。
  - Backend：FastAPI + SQLAlchemy + Alembic（Python 生态里口碑/满意度非常高，适合异步任务与强校验）。
  - DB：PostgreSQL（持久化、事务、并发；配合 `pgvector` 做知识库向量检索）。
  - 异步任务：Celery + Redis（支持暂停/恢复/取消的任务编排；worker 侧做多智能体轮询式逐章生成）。
  - 实时进度与“思考过程”展示：WebSocket（或 SSE）+ 事件日志表（前端实时滚动展示每个智能体的过程与产出片段）。
- **DeepSeek 接入方式**
  - 采用 OpenAI SDK 的兼容模式：后端统一封装 `DeepSeekClient`（可替换 base_url、model、超参），并实现“可重试、限流、超时、断点续写”能力。
  - 密钥管理：密钥只允许来自 UI 设置或运行环境变量（例如 `DEEPSEEK_API_KEY`），不写入仓库、不硬编码；数据库仅保存“已配置/最后更新时间/使用的模型”等非敏感元信息。
- **多智能体矩阵（每一步独立 Agent + 协作）**
  - Orchestrator（编排器）：严格按步骤推进，持久化状态机，保证“只基于最新版本的设定/大纲/章节编排”生成，不串线。
  - 关键 Agents：设定解析 Agent、全书大纲 Agent、书名 Agent、分卷章节编排 Agent、章节大纲 Agent、章节正文生成 Agent、连贯性/一致性审校 Agent、风格润色 Agent、知识库检索 Agent、网络抓取 Agent。
  - “成长/学习”：所有 Agent 强制先走检索（RAG）→再生成；抓取与用户知识库进入同一索引与版本体系，可追溯来源与生效范围。
- **数据模型（真实落库 + 版本化）**
  - Novel（小说主表）、NovelSetting（基础设定/多选枚举）、OutlineVersion、TitleVersion、Volume、Chapter、ChapterPlan（章纲/细纲）、ChapterDraft（正文版本）、GenerationJob（异步任务）、JobStep（步骤状态）、AgentLog（过程日志）、KnowledgeDoc（知识库文档/来源/标签）、Embedding（向量索引）。
  - 任何“可编辑再生成”的对象都采用**版本链**：前端编辑会生成新版本；再生成必须以“最新版本”为输入。
- **工作流（严格按你给的分步骤）**
  1) 输入基础设定 → 2) 生成/编辑/再生成全书大纲（版本化） → 3) 基于最新大纲生成多个书名候选（可编辑/挑选） → 4) 基于设定+最新大纲生成分卷与章节编排 → 5) 逐章生成章节大纲/细纲 → 6) 逐章生成正文（批量也必须内部按章轮询，支持暂停/继续/取消） → 7) 阅读器展示与管理。
- **一致性保证机制（防跑题/防断裂）**
  - “小说圣经（Novel Bible）”固定结构：世界观、人物表、时间线、禁忌清单、风格指南、伏笔与回收清单；每章生成前后都更新。
  - 生成前：检索相关人物/设定/前情摘要 + 强约束提示；生成后：一致性审校 Agent 校验（人物关系、时间线、称呼、设定冲突、文风偏移），不通过则自动修订或回滚重写。
- **UI/UX（藏书阁首页 + 响应式）**
  - 首页：书封卡片墙（藏书阁风格）、搜索/筛选、历史生成管理、新建向导、DeepSeek 密钥设置。
  - 创作页：左侧步骤导航（可回溯）、中间编辑器/版本历史、右侧实时“多智能体过程流”（可过滤 Agent、可折叠）。
  - 阅读器：章节目录树 + 阅读区 + 进度书签；支持不同分辨率布局（Grid/Flex，自适配）。
- **容器化交付（在不冲突前提下做到极致）**
  - `docker-compose.yml`：`db(Postgres+volume)`、`redis(volume)`、`backend(FastAPI)`、`worker(Celery)`、`frontend(Nginx)`；全部服务名互联，不写死 localhost。
  - Seed：提供演示小说与若干章节（真实 DB 数据），保证“开箱即用有内容”。

**Task List（任务清单）**
- 搭建 `auto-writer/` 单体仓库骨架（frontend/backend/infra/docs）与容器编排
- 设计并落地数据库 Schema（含版本化与任务状态机）+ ORM + 迁移
- 实现 DeepSeek 统一调用层（重试/超时/限流/结构化输出约束）
- 实现异步生成系统（Job/Step/可暂停恢复取消/逐章轮询）
- 实现多智能体框架（Orchestrator + 各 Step Agent + 审校闭环）
- 实现知识库（导入/抓取/向量检索/生效范围与版本）
- 实现前端“藏书阁首页 + 新建向导 + 工作流编辑器 + 实时日志面板”
- 实现阅读器与章节管理（目录树/版本切换/书签）
- 全链路错误处理与可观测性（前端 Error Boundary + Toast；后端结构化日志）
- 完成 Seed 数据与一键启动文档（README 严格按规范格式）

**Walkthrough（逻辑梳理）**
- **核心对象**：`Novel`（一部书）+ `Setting`（你的输入设定）+ `Artifact`（每一步产物：大纲/书名/章节编排/章纲/正文，均版本化）+ `Job`（异步生成任务）+ `AgentLog`（过程可视化）
- **核心不变量**
  - 任一步生成只允许读取“最新已确认版本”的上游产物
  - 批量生成也必须“按章节逐一轮询”，每章都可被暂停/继续/取消
  - 所有智能体先检索知识库/前情，再生成；生成后必须一致性审校再落库
- **端到端数据流**
  - 前端提交设定 → 后端落库并创建 `Job` → Worker 驱动 Orchestrator → 每一步产物写入对应 `*Version` 表 → 过程事件写入 `AgentLog` 并推送 WebSocket → 前端实时展示、允许人工编辑产物并生成新版本 → Orchestrator 检测到新版本后从该节点继续推进
- **为什么能保证连贯**
  - “Novel Bible”作为强约束上下文 + 向量检索补全细节 + 审校 Agent 做硬性一致性检查 + 版本链确保引用唯一来源，避免拿旧大纲写新章节

我会先保持待命，不做任何编码或文件变更；你确认上述方案后，我再开始在 `auto-writer/` 目录内落地实现。