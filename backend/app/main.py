"""FastAPI application entry point."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config.settings import settings
from app.router import api_router
from app.websocket import websocket_router


# API tags for documentation
tags_metadata = [
    {
        "name": "generation",
        "description": "教案生成相关接口。创建任务、查询状态、下载产物。",
    },
    {
        "name": "health",
        "description": "服务健康检查。",
    },
]


app = FastAPI(
    title=settings.app_name,
    description="""
## YaeTeaching API

一句话生成教案、语音、PPT、视频的教学内容生成平台。

### 功能特性

- **教案生成**: 通过 LLM 自动生成结构化教案 JSON
- **语音合成**: 使用 edge-tts/ChatTTS 生成教学语音
- **PPT生成**: 基于 python-pptx 自动生成课件
- **实时进度**: WebSocket 推送任务处理进度

### 使用流程

1. POST `/api/generate` 创建生成任务
2. WS `/ws/job/{id}` 订阅进度更新
3. GET `/api/job/{id}/status` 查询任务状态
4. GET `/api/download/{type}/{id}` 下载产物

### 技术栈

- Python 3.11+ / FastAPI
- Celery + Redis 异步任务队列
- DeepSeek / OpenAI LLM API
- edge-tts / ChatTTS 语音合成
- python-pptx PPT生成
""",
    version="1.0.0",
    openapi_tags=tags_metadata,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(api_router, prefix="/api", tags=["generation"])
app.include_router(websocket_router, prefix="/ws")


@app.get("/health", tags=["health"])
async def health_check():
    """健康检查端点。

    Returns:
        服务状态信息
    """
    return {
        "status": "ok",
        "service": settings.app_name,
        "version": "1.0.0"
    }