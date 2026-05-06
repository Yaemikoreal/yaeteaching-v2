# YaeTeaching

一句话生成教案、视频、语音、PPT 的教学平台。

## 项目状态

**Phase 1 MVP 已完成** (2026-05-06)

## 项目结构

```
yaeteaching/
├── frontend/          # Next.js 前端应用
│   ├── src/          # 源代码
│   │   ├── app/      # Next.js App Router
│   │   ├── components/  # React 组件
│   │   ├── hooks/    # 自定义 Hooks
│   │   ├── lib/      # 工具函数/API
│   │   └── types/    # TypeScript 类型
│   ├── public/       # 静态资源
│   └── tests/        # 前端测试
├── backend/          # Python/FastAPI 后端服务
│   ├── app/          # FastAPI 应用
│   ├── celery/       # Celery 任务
│   ├── models/       # 数据模型
│   ├── services/     # 业务逻辑
│   ├── config/       # 配置文件
│   └── tests/        # 后端测试
├── docs/             # 项目文档
└── AGENTS.md         # Agent 工作指南
```

## 技术栈

### 前端
- Next.js 14+ (App Router)
- React 18 + TypeScript
- Tailwind CSS
- WebSocket 实时通信

### 后端
- Python 3.11+
- FastAPI
- Celery + Redis
- PostgreSQL / MinIO

## 开发团队

维护者：赛飞儿

| Agent | 角色 | 负责模块 |
|-------|------|---------|
| 那刻夏 | 需求规划师 | 需求分析、任务拆解 |
| 白厄 | 后端工程师 | API 服务、AI 流水线 |
| 长月夜 | 前端工程师 | Next.js 前端、UI 实现 |
| 缇宝 | 测试工程师 | 测试覆盖、质量门禁 |
| 赛飞儿 | 项目经理 | 进度跟踪、协调沟通 |

## 工作目录

所有 Agent 开发工作统一在以下目录进行：
```
~/openclawwork/yaeteaching/
```

## Phase 1 MVP 任务完成情况

- [x] YAE-20: Frontend Next.js 基础架构搭建
- [x] YAE-21: 教案生成流水线
- [x] YAE-22: 语音合成流水线
- [x] YAE-23: PPT 生成流水线
- [x] YAE-24: 前端界面与进度展示
- [x] YAE-25: 教案可编辑与二次生成
- [x] YAE-26: 单元测试与集成测试
