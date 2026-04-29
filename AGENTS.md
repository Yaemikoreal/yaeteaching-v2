# YaeTeaching Agent 工作指南

## 📁 工作目录说明

**Multica 自动管理工作目录：**
```
~/multica_workspaces/{workspace_id}/{task_id}/workdir/yaeteaching-v2/
```

每个任务会 checkout 一个独立的 git worktree，分支名为 `agent/agent/{task_id}`。

**无需手动指定工作目录** — Multica Daemon 会自动处理 repo checkout。

**本地开发参考目录**（仅供人类查看）：`~/openclawwork/yaeteaching/`

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

## 🔄 工作流程（Multica 自动化）

### 1. 任务分配
- Issue 分配给 Agent 后，Multica 自动 checkout repo 到任务工作目录

### 2. Agent 执行
- 在独立的 worktree 分支工作：`agent/agent/{task_id}`
- 修改代码、测试、提交

### 3. 完成后
- 代码提交到任务分支
- 创建 PR 合并到 main
- Issue 状态自动变为 done

### 4. 人类开发（可选）
```bash
cd ~/openclawwork/yaeteaching
git pull origin main
# 开发...
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

1. **Multica 自动 checkout repo 到任务目录**，无需手动操作
2. **每个任务在独立 worktree 分支工作**，避免冲突
3. **完成后代码提交到任务分支**，通过 PR 合并
4. **人类可直接在 `~/openclawwork/yaeteaching/` 开发**，push 到 main
5. **保持 README 和 AGENTS.md 更新**
