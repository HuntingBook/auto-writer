# 系统设计文档 (System Design)

## 1. 数据库设计 (Database Schema)

### 1.1 Novel (小说)
| 字段 | 类型 | 说明 |
| :--- | :--- | :--- |
| id | UUID | 主键 |
| title | String | 标题 |
| created_at | DateTime | 创建时间 |
| updated_at | DateTime | 更新时间 |

### 1.2 NovelSetting (小说设定)
| 字段 | 类型 | 说明 |
| :--- | :--- | :--- |
| novel_id | UUID | 外键 -> Novel |
| genres | ARRAY(String) | 类型标签 |
| style_tags | ARRAY(String) | 风格标签 |
| target_readers | ARRAY(String) | 目标读者 |
| total_words | Integer | 预计字数 |
| min_chapter_words | Integer | 单章最少字数 |
| background | Text | 世界观背景 |
| deepseek_key_configured | Boolean | 是否配置 Key |

### 1.3 Chapter (章节)
| 字段 | 类型 | 说明 |
| :--- | :--- | :--- |
| id | UUID | 主键 |
| novel_id | UUID | 外键 -> Novel |
| volume_no | Integer | 卷号 |
| chapter_no | Integer | 章号 |
| title | String | 章节标题 |
| outline | Text | 章节大纲 |
| fine_outline | Text | 章节细纲 (Beat Sheet) |
| content | Text | 正文内容 |
| status | Enum | pending, generating, done, failed |

### 1.4 Versioning Models (版本控制)
- `OutlineVersion` (大纲版本)
- `TitleVersion` (书名候选版本)
- `PlanVersion` (编排版本)
- `NovelBibleVersion` (圣经/设定版本)

### 1.5 Run (运行任务)
| 字段 | 类型 | 说明 |
| :--- | :--- | :--- |
| id | UUID | 主键 |
| novel_id | UUID | 关联小说 |
| kind | Enum | outline, titles, plan, chapter, chapters |
| status | Enum | queued, running, paused, canceled, succeeded, failed |
| current_step | String | 当前步骤 |

## 2. 接口设计 (API Design)

### 小说管理
- `GET /api/novels`: 列表
- `GET /api/novels/{id}`: 详情（包含大纲、设定、章节列表）
- `POST /api/novels`: 创建
- `DELETE /api/novels/{id}`: 删除

### 创作工作流
- `PUT /api/novels/{id}/outline`: 保存大纲
- `PUT /api/novels/{id}/titles/selection`: 保存书名选择
- `PUT /api/novels/{id}/deepseek`: 配置 API Key

### 任务运行
- `POST /api/runs/novels/{id}/{kind}`: 启动任务 (kind: outline/titles/plan)
- `POST /api/runs/novels/{id}/chapter/{chapter_id}`: 启动单章生成
- `POST /api/runs/novels/{id}/chapters/batch`: 启动批量生成
- `POST /api/runs/{id}/pause`: 暂停
- `POST /api/runs/{id}/resume`: 继续
- `GET /api/runs/{id}`: 获取状态
- `GET /api/runs/{id}/events`: 获取日志流 (SSE)

## 3. UI/UX 设计

### 风格指南
- **配色**: 靛青色 (Indigo) 为主色调，Slate 为中性色。
- **字体**: Inter, Noto Sans SC
- **布局**: 响应式设计，桌面端采用分栏布局（左侧工作流，右侧日志），移动端堆叠。

### 关键组件
- **WorkflowSteps**: 步骤条 + 各阶段编辑器/预览器。
- **RunLogPanel**: 实时日志面板，支持自动滚动、连接状态显示、进度条。
- **DeepSeekModal**: API Key 配置弹窗。
- **KnowledgeModal**: 知识库管理弹窗。

## 4. 智能体设计 (Agent Design)

系统采用 Chain of Agents 模式，各 Agent 职责单一，通过上下文串联。

1. **Outline Agent**: 负责全书大纲。
2. **Title Agent**: 负责书名生成。
3. **Plan Agent**: 负责分卷与章节拆分 (JSON Output)。
4. **Chapter Outline Agent**: 负责单章大纲 (RAG + Bible)。
5. **Fine Outline Agent**: 负责单章细纲 (Beat Sheet)。
6. **Chapter Writer**: 负责正文生成的“推土机”。
7. **Bible Agent**: 负责维护全局设定一致性 (Create/Update)。

各 Agent 均集成 RAG (Retrieval-Augmented Generation) 能力，自动检索 Knowledge Base 中的相关资料。
