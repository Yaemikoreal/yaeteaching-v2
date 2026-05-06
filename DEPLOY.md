# YaeTeaching 部署指南

本指南帮助你快速在本地或服务器部署 YaeTeaching 平台。

---

## 快速部署 (Docker Compose)

### 1. 环境要求

- Docker 20.10+
- Docker Compose 2.0+
- 8GB+ 内存
- DeepSeek API Key

### 2. 克隆仓库

```bash
git clone -b deploy-ready https://github.com/Yaemikoreal/yaeteaching.git
cd yaeteaching
```

### 3. 配置环境变量

```bash
cp .env.example .env
```

编辑 `.env` 文件，填写你的 DeepSeek API Key：

```
DEEPSEEK_API_KEY=your_actual_api_key
```

### 4. 启动服务

```bash
docker-compose up -d
```

等待所有服务启动完成（约 2-3 分钟）。

### 5. 访问应用

| 服务 | 地址 |
|------|------|
| **前端界面** | http://localhost:3000 |
| **后端 API** | http://localhost:8000 |
| **API 文档** | http://localhost:8000/docs |
| **MinIO 控制台** | http://localhost:9001 |

### 6. 停止服务

```bash
docker-compose down
```

---

## 服务说明

### 前端 (Next.js)

- 端口：3000
- 提供 Web 界面，用于生成教案、语音、PPT

### 后端 (FastAPI)

- 端口：8000
- REST API + WebSocket
- 处理生成请求

### Celery Worker

- 异步任务处理
- 教案生成、语音合成、PPT 生成

### Redis

- 端口：6379
- Celery 任务队列
- 状态缓存

### MinIO

- 端口：9000 (API) / 9001 (控制台)
- 对象存储
- 存放生成的 PPT、语音文件

---

## 常见问题

### Q: 启动后前端无法访问后端 API

检查 Docker 网络配置。确保 `NEXT_PUBLIC_API_URL` 设置为 `http://localhost:8000`（浏览器访问）而非 Docker 内部地址。

### Q: MinIO 控制台登录账号

- 用户名：minioadmin
- 密码：minioadmin

### Q: 如何查看日志

```bash
docker-compose logs -f backend
docker-compose logs -f celery-worker
```

---

## 发布人：赛飞儿