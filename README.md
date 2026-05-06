# YaeTeaching

![Phase](https://img.shields.io/badge/Phase-1_MVP_Completed-green)
![Frontend](https://img.shields.io/badge/Frontend-Next.js_16-blue)
![Backend](https://img.shields.io/badge/Backend-FastAPI-Python-yellow)
![License](https://img.shields.io/badge/License-MIT-purple)

**一句话生成教案、视频、语音、PPT 的智能教学平台**

只需输入简单的提示词（学科、年级、主题、时长），AI 自动生成完整的教学内容：
- 📝 结构化教案（JSON 格式，支持编辑）
- 🔊 教学语音（按章节分段合成）
- 📊 教学 PPT（多风格模板自动匹配）
- 🎬 教学视频（规划中）

---

## 目录

- [功能特性](#功能特性)
- [项目架构](#项目架构)
- [技术栈](#技术栈)
- [快速开始](#快速开始)
- [API 文档](#api-文档)
- [前端组件](#前端组件)
- [后端服务](#后端服务)
- [测试覆盖](#测试覆盖)
- [部署指南](#部署指南)
- [开发团队](#开发团队)
- [路线图](#路线图)
- [贡献指南](#贡献指南)

---

## 功能特性

### Phase 1 MVP (已完成)

| 功能 | 状态 | 描述 |
|------|------|------|
| 教案生成 | ✅ | LLM 自动生成结构化教案 JSON，支持多学科适配 |
| 语音合成 | ✅ | ChatTTS 分段合成，按自然段切分保持语义完整 |
| PPT 生成 | ✅ | python-pptx 生成，5 种教学模板自动匹配 |
| 前端界面 | ✅ | Next.js 响应式界面，实时进度展示 |
| 教案编辑 | ✅ | 富文本编辑器，支持二次生成和版本管理 |
| WebSocket | ✅ | 实时推送任务进度，四通道并发状态 |
| 单元测试 | ✅ | pytest + Vitest，覆盖率 ≥80% |

### 核心流程

```
用户输入 → LLM 生成教案 → 语音合成 → PPT生成 → 产物下载
    ↓
WebSocket 实时进度反馈
    ↓
教案编辑 → 增量重生成（修改部分）
```

---

## 项目架构

```
yaeteaching/
├── frontend/                    # Next.js 前端
│   ├── src/
│   │   ├── app/                 # App Router 页面
│   │   ├── components/          # React 组件
│   │   │   ├── GenerateForm.tsx       # 输入表单
│   │   │   ├── ProgressDisplay.tsx    # 进度展示
│   │   │   ├── LessonPlanEditor.tsx   # 教案编辑器
│   │   │   ├── LessonPreview.tsx      # 教案预览
│   │   │   ├── VersionHistory.tsx     # 版本历史
│   │   │   └── ProductDownload.tsx    # 产物下载
│   │   ├── hooks/               # 自定义 Hooks
│   │   │   ├── useWebSocket.ts        # WebSocket 连接
│   │   │   ├── useLessonVersions.ts   # 版本管理
│   │   ├── lib/                 # API 客户端
│   │   └── types/               # TypeScript 类型
│   ├── public/                  # 静态资源
│   └── tests/                   # 前端测试
│
├── backend/                     # FastAPI 后端
│   ├── app/
│   │   ├── main.py              # FastAPI 入口
│   │   ├── router.py            # REST API 路由
│   │   ├── websocket.py         # WebSocket 处理
│   ├── services/
│   │   ├── lesson.py            # 教案生成服务
│   │   ├── voice.py             # 语音合成服务
│   │   ├── ppt.py               # PPT 生成服务
│   ├── models/
│   │   ├── lesson.py            # 教案 JSON Schema
│   │   ├── job.py               # 任务状态模型
│   │   ├── request.py           # 请求/响应模型
│   ├── celery/
│   │   ├── tasks.py             # Celery 异步任务
│   │   ├── config.py            # Celery 配置
│   ├── config/
│   │   └ettings.py              # 应用配置
│   └── tests/                   # 后端测试
│
├── docs/                        # 项目文档
├── AGENTS.md                    # Agent 工作指南
└── README.md                    # 本文档
```

---

## 技术栈

### 前端 (Next.js 16)

| 技术 | 版本 | 用途 |
|------|------|------|
| Next.js | 16.2.4 | App Router、服务端渲染 |
| React | 19.2.4 | UI 组件框架 |
| TypeScript | 5.x | 类型安全 |
| Tailwind CSS | 4.x | 响应式样式 |
| WebSocket | - | 实时通信 |

### 后端 (Python 3.11+)

| 技术 | 版本 | 用途 |
|------|------|------|
| FastAPI | 0.100+ | REST API + WebSocket |
| Celery | 5.3+ | 异步任务队列 |
| Redis | 4.5+ | 任务队列 + 缓存 |
| pydantic | 2.0+ | 数据验证 |
| python-pptx | 0.6.21 | PPT 生成 |
| httpx | 0.24+ | HTTP 客户端 |
| minio | 7.1+ | 对象存储 |

---

## 快速开始

### 环境要求

- Node.js 18+
- Python 3.11+
- Redis 7+
- PostgreSQL 15+ (可选，Phase 1 使用内存存储)

### 前端启动

```bash
cd frontend
npm install

# 配置环境变量（连接后端 API）
cp .env.local.example .env.local

npm run dev
# 访问 http://localhost:3000
```

### 后端启动

```bash
cd backend
pip install -r requirements.txt

# 启动 Redis（必需）
redis-server

# 启动 Celery Worker
celery -A celery.tasks worker --loglevel=info

# 启动 FastAPI
uvicorn app.main:app --reload --port 8000
# API 地址 http://localhost:8000
```

### 环境变量

```bash
# frontend/.env.local
NEXT_PUBLIC_API_URL=http://localhost:8000

# backend/.env
DEEPSEEK_API_KEY=your_api_key
REDIS_URL=redis://localhost:6379/0
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
```

---

## API 文档

### REST API

| 端点 | 方法 | 描述 |
|------|------|------|
| `/api/generate` | POST | 创建生成任务 |
| `/api/job/{job_id}/status` | GET | 查询任务状态 |
| `/api/download/{type}/{job_id}` | GET | 获取下载链接 |
| `/health` | GET | 健康检查 |

### 请求示例

```bash
curl -X POST http://localhost:8000/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "subject": "数学",
    "grade": "7年级",
    "topic": "一元一次方程",
    "duration": 45
  }'
```

### WebSocket

```
ws://localhost:8000/ws/job/{job_id}
```

消息格式：
```json
{
  "job_id": "uuid",
  "task_type": "lesson",
  "status": "in_progress",
  "progress": 50,
  "message": "正在生成教案..."
}
```

---

## 前端组件

### 主要组件

| 组件 | 文件 | 功能 |
|------|------|------|
| GenerateForm | `GenerateForm.tsx` | 提示词输入表单 |
| ProgressDisplay | `ProgressDisplay.tsx` | 四通道进度条 |
| LessonPlanEditor | `LessonPlanEditor.tsx` | 富文本编辑器 |
| LessonPreview | `LessonPreview.tsx` | Markdown 教案预览 |
| VersionHistory | `VersionHistory.tsx` | 版本历史管理（最多3版本） |
| ProductDownload | `ProductDownload.tsx` | 下载按钮组 |
| RegenerationProgress | `RegenerationProgress.tsx` | 增量重生成进度 |

### 自定义 Hooks

```typescript
// WebSocket 实时连接
const { status, progress, message } = useWebSocket(jobId);

// 版本管理
const { versions, current, save, restore } = useLessonVersions(jobId);
```

---

## 后端服务

### 教案生成服务 (lesson.py)

```python
from services.lesson import LessonGenerator

generator = LessonGenerator()
lesson_json = generator.generate({
    "subject": "数学",
    "grade": "7年级",
    "topic": "一元一次方程",
    "duration": 45
})
```

输出 Schema：
```json
{
  "meta": { "subject", "grade", "topic", "duration" },
  "outline": {
    "introduction": { "title", "content", "key_points", "media_hint" },
    "main_sections": [...],
    "conclusion": {...}
  },
  "summary": "...",
  "resources": [...]
}
```

### 语音合成服务 (voice.py)

- 按 `outline.main_sections` 分段合成
- 每段 ≤ 2 分钟
- 输出 MP3 存至 MinIO

### PPT 生成服务 (ppt.py)

| slide_type | 模板 |
|------------|------|
| title | 标题页模板 |
| knowledge | 知识点页模板 |
| example | 例题页模板 |
| summary | 总结页模板 |
| exercise | 练习页模板 |

---

## 测试覆盖

### 后端测试 (pytest)

```bash
cd backend
pytest tests/ -v --cov=app --cov=services --cov-report=html
```

覆盖模块：
- `test_lesson_service.py` — 教案生成逻辑
- `test_voice_service.py` — 语音分段与合成
- `test_ppt_service.py` — PPT 模板匹配
- `test_api.py` — REST API 端点
- `test_websocket.py` — WebSocket 推送

### 前端测试 (Vitest)

```bash
cd frontend
npm run test
```

---

## 部署指南

### Docker Compose（推荐）

```yaml
version: '3.8'
services:
  frontend:
    build: ./frontend
    ports: ["3000:3000"]
  backend:
    build: ./backend
    ports: ["8000:8000"]
    depends_on: [redis, minio]
  redis:
    image: redis:7-alpine
  minio:
    image: minio/minio
    command: server /data --console-address ":9001"
```

### 生产环境配置

- CORS: 配置 `allow_origins` 为实际域名
- 数据库: 替换内存存储为 PostgreSQL
- 存储: MinIO 集群或 S3
- Celery: 多 Worker + 监控 (Flower)

---

## 开发团队

**维护者：赛飞儿**

| Agent | 角色 | 负责模块 | Issue 范围 |
|-------|------|---------|-----------|
| 那刻夏 | 需求规划师 | 需求文档、技术设计 | 规划类任务 |
| 白厄 | 后端工程师 | FastAPI、AI 流水线、Celery | YAE-21~23 |
| 长月夜 | 前端工程师 | Next.js、UI组件、WebSocket | YAE-20, YAE-24~25 |
| 缇宝 | 测试工程师 | 单元测试、集成测试 | YAE-26 |
| 赛飞儿 | 项目经理 | 文档维护、进度跟踪、协调 | 项目管理 |

---

## 路线图

### Phase 1 MVP (已完成 ✅)

- [x] YAE-20: Frontend Next.js 基础架构搭建
- [x] YAE-21: 教案生成流水线
- [x] YAE-22: 语音合成流水线
- [x] YAE-23: PPT 生成流水线
- [x] YAE-24: 前端界面与进度展示
- [x] YAE-25: 教案可编辑与二次生成
- [x] YAE-26: 单元测试与集成测试

### Phase 2 (规划中)

- [ ] 视频合成流水线
- [ ] 多角色配音（教师/学生）
- [ ] 教案模板库扩充（10+学科）
- [ ] 用户系统与权限管理
- [ ] PostgreSQL 数据持久化
- [ ] 生产环境部署

---

## 贡献指南

本项目由 AI Agent 团队协作开发。人类开发者可通过以下方式参与：

1. **直接开发**
   ```bash
   cd ~/openclawwork/yaeteaching
   git pull origin main
   # 开发...
   git push origin main
   ```

2. **Agent 工作模式**
   - 在 Multica 平台创建 Issue
   - Agent 自动 checkout 独立 worktree
   - 完成后提交 PR 合并到 main

详见 [AGENTS.md](./AGENTS.md)

---

## 许可证

MIT License

---

## 联系方式

- GitHub: https://github.com/Yaemikoreal/yaeteaching
- Issue: 使用 GitHub Issue 或 Multica 平台

---

**发布人：赛飞儿**
**日期：2026-05-06**