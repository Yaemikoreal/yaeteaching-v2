"""API routes for generation endpoints."""
from fastapi import APIRouter, HTTPException, Depends
from uuid import uuid4
from models.request import GenerateRequest, GenerateResponse
from models.job import JobStatus, TaskProgress, TaskStatus, ProductType
from models.user import UserResponse
from datetime import datetime
from app.auth import get_current_user, require_role

api_router = APIRouter()

# In-memory job storage (replace with Redis/Postgres later)
jobs: dict[str, JobStatus] = {}


def create_initial_tasks() -> list[TaskProgress]:
    """Create initial task progress list."""
    return [
        TaskProgress(type=ProductType.lesson, status=TaskStatus.pending, progress=0),
        TaskProgress(type=ProductType.tts, status=TaskStatus.pending, progress=0),
        TaskProgress(type=ProductType.ppt, status=TaskStatus.pending, progress=0),
        TaskProgress(type=ProductType.video, status=TaskStatus.pending, progress=0),
    ]


@api_router.post("/generate", response_model=GenerateResponse)
async def generate_lesson_plan(
    request: GenerateRequest,
    user: UserResponse = Depends(get_current_user)
):
    """Create a new lesson generation job (requires authentication)."""
    job_id = str(uuid4())

    job = JobStatus(
        job_id=job_id,
        user_id=user.id,  # 白厄: associate job with user
        status=TaskStatus.pending,
        tasks=create_initial_tasks(),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    jobs[job_id] = job

    # Trigger Celery task for async processing
    try:
        from celery.tasks import start_generation_pipeline
        start_generation_pipeline.delay(job_id, request.model_dump())
    except Exception as e:
        # If Celery is not available, log the error but don't fail the request
        # The job will be created but won't be processed automatically
        print(f"Warning: Could not trigger Celery task: {e}")

    return GenerateResponse(job_id=job_id, message="任务已创建，正在处理")


@api_router.get("/job/{job_id}/status", response_model=JobStatus)
async def get_job_status(
    job_id: str,
    user: UserResponse = Depends(get_current_user)
):
    """Get current status of a generation job (requires authentication)."""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    job = jobs[job_id]

    # 白厄: 用户只能查看自己的任务（管理员可以查看所有任务）
    if job.user_id != user.id and user.role != "admin":
        raise HTTPException(status_code=403, detail="Access denied")

    return job


@api_router.get("/download/{product_type}/{job_id}")
async def get_download_url(
    product_type: str,
    job_id: str,
    user: UserResponse = Depends(get_current_user)
):
    """Get download URL for a generated product (requires authentication)."""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    job = jobs[job_id]

    # 白厄: 用户只能下载自己的产物（管理员可以下载所有产物）
    if job.user_id != user.id and user.role != "admin":
        raise HTTPException(status_code=403, detail="Access denied")

    task = next((t for t in job.tasks if t.type == product_type), None)

    if not task or task.status != TaskStatus.completed:
        raise HTTPException(
            status_code=400, detail="Product not ready for download"
        )

    return {"download_url": task.download_url}