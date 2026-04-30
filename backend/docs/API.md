# YaeTeaching Backend API 文档

## 概述

YaeTeaching API 提供一键生成教案、语音、PPT、视频的教学内容生成服务。

- **版本**: 1.0.0
- **基础URL**: `http://localhost:8000`
- **认证**: 无（Phase 1 MVP）

---

## API 端点

### 1. 健康检查

**GET** `/health`

检查服务状态。

#### 响应示例

```json
{
  "status": "ok",
  "service": "YaeTeaching API"
}
```

---

### 2. 创建生成任务

**POST** `/api/generate`

创建教案生成任务，触发异步处理流水线。

#### 请求体

```json
{
  "subject": "数学",
  "grade": "7年级",
  "duration": 45,
  "topic": "一元一次方程",
  "style": "启发式教学"
}
```

| 字段 | 类型 | 必填 | 描述 |
|------|------|------|------|
| subject | string | ✓ | 学科：数学、物理、语文等 |
| grade | string | ✓ | 年级：如 7年级、高一 |
| duration | integer | ✓ | 课程时长（分钟），范围 15-120 |
| topic | string | ✓ | 教学主题/知识点 |
| style | string | ✗ | 教学风格（可选） |

#### 响应

```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "任务已创建，正在处理"
}
```

---

### 3. 查询任务状态

**GET** `/api/job/{job_id}/status`

查询生成任务的当前状态和进度。

#### 路径参数

- `job_id`: 任务ID（UUID格式）

#### 响应

```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "in_progress",
  "tasks": [
    {
      "type": "lesson",
      "status": "completed",
      "progress": 100,
      "message": "教案生成完成",
      "download_url": "/api/download/lesson/550e8400..."
    },
    {
      "type": "tts",
      "status": "in_progress",
      "progress": 50,
      "message": "正在合成语音..."
    },
    {
      "type": "ppt",
      "status": "pending",
      "progress": 0
    },
    {
      "type": "video",
      "status": "pending",
      "progress": 0
    }
  ],
  "created_at": "2026-04-30T10:00:00Z",
  "updated_at": "2026-04-30T10:05:00Z"
}
```

#### 任务状态说明

| 状态 | 描述 |
|------|------|
| pending | 等待处理 |
| in_progress | 正在处理 |
| completed | 完成 |
| failed | 失败 |

#### 产品类型说明

| 类型 | 描述 |
|------|------|
| lesson | 教案 JSON |
| tts | 语音 MP3 |
| ppt | PPT 文件 |
| video | 视频（Phase 2） |

---

### 4. 下载产物

**GET** `/api/download/{product_type}/{job_id}`

获取生成产物的下载链接。

#### 路径参数

- `product_type`: 产物类型（lesson, tts, ppt, video）
- `job_id`: 任务ID

#### 响应

```json
{
  "download_url": "/storage/ppt/一元一次方程_abc123.pptx"
}
```

#### 错误响应

| 状态码 | 描述 |
|--------|------|
| 404 | 任务不存在 |
| 400 | 产物未准备好 |

---

## WebSocket 接口

### 进度推送

**WS** `/ws/job/{job_id}`

实时接收任务进度更新。

#### 连接示例

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/job/{job_id}');
ws.onmessage = (event) => {
  const progress = JSON.parse(event.data);
  console.log(progress);
};
```

#### 推送消息格式

```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "task_type": "tts",
  "status": "in_progress",
  "progress": 75,
  "message": "正在合成第3段语音..."
}
```

---

## 教案 JSON Schema

生成的教案 JSON 结构：

```json
{
  "meta": {
    "subject": "数学",
    "grade": "7年级",
    "topic": "一元一次方程",
    "duration": 45,
    "style": "启发式教学"
  },
  "outline": {
    "introduction": {
      "title": "课程导入",
      "content": "导入内容...",
      "key_points": ["要点1"],
      "media_hint": {
        "slide_type": "title",
        "voice_style": "teacher"
      }
    },
    "main_sections": [
      {
        "title": "核心概念",
        "content": "内容...",
        "key_points": ["要点1", "要点2"],
        "media_hint": {
          "slide_type": "knowledge"
        }
      }
    ],
    "conclusion": {
      "title": "课堂总结",
      "content": "总结内容...",
      "media_hint": {
        "slide_type": "summary"
      }
    }
  },
  "summary": "课程总结...",
  "resources": []
}
```

### Slide Type 类型

| 值 | 描述 |
|----|------|
| title | 标题页 |
| knowledge | 知识点页 |
| example | 例题页 |
| summary | 总结页 |
| exercise | 练习页 |

### Voice Style 类型

| 值 | 描述 |
|----|------|
| teacher | 教师音（女声） |
| teacher_male | 教师音（男声） |
| student | 学生音 |
| narrator | 旁白音 |

---

## 错误处理

### 常见错误

| 状态码 | 描述 | 处理建议 |
|--------|------|----------|
| 404 | 任务不存在 | 检查 job_id 是否正确 |
| 400 | 参数校验失败 | 检查请求参数格式 |
| 500 | 服务内部错误 | 重试或联系管理员 |

### 错误响应格式

```json
{
  "detail": "Job not found"
}
```

---

## 环境配置

### 必需环境变量

| 变量 | 描述 | 默认值 |
|------|------|--------|
| DEEPSEEK_API_KEY | DeepSeek API 密钥 | "" |
| OPENAI_API_KEY | OpenAI API 密钥 | "" |
| REDIS_URL | Redis 连接URL | redis://localhost:6379/0 |
| MINIO_ENDPOINT | MinIO 存储端点 | localhost:9000 |
| STORAGE_DIR | 本地存储目录 | /tmp/yaeteaching/storage |

---

## 使用示例

### Python 客户端

```python
import httpx

# 创建任务
response = httpx.post(
    "http://localhost:8000/api/generate",
    json={
        "subject": "数学",
        "grade": "7年级",
        "duration": 45,
        "topic": "一元一次方程"
    }
)
job_id = response.json()["job_id"]

# 查询状态
status = httpx.get(f"http://localhost:8000/api/job/{job_id}/status")
print(status.json())
```

### JavaScript 前端

```javascript
// 创建任务并订阅进度
const response = await fetch('/api/generate', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    subject: '数学',
    grade: '7年级',
    duration: 45,
    topic: '一元一次方程'
  })
});
const { job_id } = await response.json();

// WebSocket 进度订阅
const ws = new WebSocket(`ws://localhost:8000/ws/job/${job_id}`);
ws.onmessage = (e) => updateProgress(JSON.parse(e.data));
```

---

## 版本历史

| 版本 | 日期 | 更新内容 |
|------|------|----------|
| 1.0.0 | 2026-04-30 | Phase 1 MVP 发布 |