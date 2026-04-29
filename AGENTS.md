# YaeTeaching Agent 工作指南

## 📁 统一工作目录

**所有 Agent 必须在以下目录工作：**
```
~/openclawwork/yaeteaching/
```

**禁止**在 Multica 临时工作目录 (`~/multica_workspaces/...`) 直接修改代码。

---

## 🏗️ 项目结构

```
yaeteaching/
├── frontend/          # Next.js 前端 (长月夜)
│   ├── src/
│   │   ├── app/      # Next.js App Router
│   │   ├── components/  # React 组件
│   │   ├── hooks/    # 自定义 Hooks
│   │   ├── lib/      # 工具函数/API
│   │   └── types/    # TypeScript 类型
│   ├── public/       # 静态资源
│   └── package.json
├── backend/          # Python/FastAPI 后端 (白厄)
│   ├── app/          # FastAPI 应用
│   ├── celery/       # Celery 任务
│   ├── models/       # 数据模型
│   ├── services/     # 业务逻辑
│   └── tests/        # 测试文件
├── docs/             # 项目文档
└── README.md
```

---

## 👥 Agent 职责与目录

| Agent | 角色 | 工作目录 | 负责模块 |
|-------|------|---------|---------|
| **长月夜** | 前端工程师 | `frontend/` | Next.js 前端、UI 组件、WebSocket |
| **白厄** | 后端工程师 | `backend/` | FastAPI、AI 流水线、Celery 任务 |
| **缇宝** | 测试工程师 | `frontend/tests/`, `backend/tests/` | 单元测试、集成测试 |
| **赛飞儿** | 项目经理 | 根目录 | 文档、进度跟踪 |
| **那刻夏** | 需求规划师 | `docs/` | 需求文档、技术设计 |

---

## 🔄 工作流程

### 1. 开始任务前
```bash
cd ~/openclawwork/yaeteaching
git pull origin main
```

### 2. 开发时
- 在对应目录修改代码
- 遵循各模块的代码规范
- 及时提交到本地分支

### 3. 完成任务后
```bash
git add .
git commit -m "[YAE-XX] 任务描述"
git push origin main
```

---

## 📋 当前任务对应目录

| Issue | 标题 | Agent | 工作目录 |
|-------|------|-------|---------|
| YAE-20 | Frontend Next.js基础架构 | 长月夜 | ✅ 已完成，代码在 `frontend/` |
| YAE-21 | 教案生成流水线 | 白厄 | `backend/app/services/lesson.py` |
| YAE-22 | 语音合成流水线 | 白厄 | `backend/app/services/voice.py` |
| YAE-23 | PPT生成流水线 | 白厄 | `backend/app/services/ppt.py` |
| YAE-24 | 前端界面与进度展示 | 长月夜 | `frontend/src/components/`, `frontend/src/app/` |
| YAE-25 | 教案可编辑与二次生成 | 长月夜 | `frontend/src/components/LessonEditor.tsx` |
| YAE-26 | 单元测试与集成测试 | 缇宝 | `frontend/tests/`, `backend/tests/` |

---

## 🔗 代码仓库

- **GitHub**: https://github.com/Yaemikoreal/yaeteaching-v2
- **本地路径**: `~/openclawwork/yaeteaching/`

---

## ⚠️ 重要提醒

1. **所有代码修改必须在 `~/openclawwork/yaeteaching/` 进行**
2. **Multica 工作目录 (`~/multica_workspaces/...`) 仅用于读取上下文**
3. **完成后及时 push 到 GitHub**
4. **保持 README 和 AGENTS.md 更新**
