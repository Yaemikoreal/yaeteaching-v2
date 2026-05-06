"""Celery async tasks for content generation with DAG architecture."""
import structlog
from datetime import datetime
from typing import Dict, Any, Optional, List

from celery import shared_task, chain, group, chord, signature
from celery.exceptions import Reject, Retry

from models.job import TaskStatus, ProductType
from config.settings import settings

# Configure structured logging
logger = structlog.get_logger()


def _run_async(coro):
    """Run async coroutine in Celery worker context."""
    import asyncio
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import nest_asyncio
            nest_asyncio.apply()
            return loop.run_until_complete(coro)
        return loop.run_until_complete(coro)
    except RuntimeError:
        return asyncio.run(coro)


def _update_progress_sync(job_id: str, task_type: ProductType, status: TaskStatus,
                          progress: int, message: str = None, error: str = None,
                          download_url: str = None):
    """Update progress synchronously by storing in job state."""
    from app.router import jobs
    if job_id in jobs:
        job = jobs[job_id]
        for i, task in enumerate(job.tasks):
            if task.type == task_type:
                job.tasks[i] = task.__class__(
                    type=task_type,
                    status=status,
                    progress=progress,
                    message=message,
                    error=error,
                    download_url=download_url,
                )
                break
        job.status = status
        job.updated_at = datetime.utcnow()


# ============================================================================
# Pipeline Entry Points
# ============================================================================

def build_pipeline_dag(job_id: str, request_data: dict):
    """Build the complete pipeline DAG using Celery Canvas.

    DAG Structure:
        start_pipeline → generate_lesson → [generate_tts + generate_ppt] → generate_video → final_package

    Returns:
        Celery chain object ready for apply_async
    """
    # Step 1: Initialize pipeline
    init_sig = initialize_pipeline_task.s(job_id, request_data)

    # Step 2: Generate lesson (LLM call)
    lesson_sig = generate_lesson_task.s(job_id, request_data)

    # Step 3: Parallel TTS + PPT generation
    # Note: TTS and PPT both need lesson_json, passed from generate_lesson_task result
    parallel_group = group(
        generate_tts_task.s(job_id),
        generate_ppt_task.s(job_id),
    )

    # Step 4: Video synthesis (requires TTS + PPT complete)
    video_sig = generate_video_task.s(job_id)

    # Step 5: Package all products
    package_sig = final_package_task.s(job_id)

    # Build the DAG: init → lesson → [tts, ppt parallel] → video → package
    # Using chord for parallel execution with callback
    pipeline = chain(
        init_sig,
        lesson_sig,
        chord(header=parallel_group, body=video_sig),
        package_sig,
    )

    return pipeline


def start_generation_pipeline(job_id: str, request_data: dict):
    """Start the complete generation pipeline.

    Usage:
        pipeline = build_pipeline_dag(job_id, request_data)
        result = pipeline.apply_async(link_error=error_handler.s(job_id))
    """
    pipeline = build_pipeline_dag(job_id, request_data)
    return pipeline.apply_async(
        link_error=error_handler.s(job_id),
        task_id=f"pipeline-{job_id}",
    )


# ============================================================================
# Pipeline Tasks
# ============================================================================

@shared_task(bind=True)
def initialize_pipeline_task(self, job_id: str, request_data: dict):
    """Initialize pipeline state and validate input."""
    logger.info("pipeline_init", job_id=job_id, task_id=self.request.id)

    _update_progress_sync(
        job_id, ProductType.lesson, TaskStatus.pending, 0,
        message="流水线初始化中..."
    )

    # Validate request data
    required_fields = ["subject", "grade", "topic"]
    for field in required_fields:
        if field not in request_data:
            raise ValueError(f"Missing required field: {field}")

    # Store request data for later tasks
    from app.router import jobs
    if job_id in jobs:
        jobs[job_id].request_data = request_data

    logger.info("pipeline_initialized", job_id=job_id)
    return {"status": "initialized", "job_id": job_id}


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    max_retries=3,
    retry_backoff=True,
    retry_backoff_max=60,
    retry_jitter=True,
    rate_limit='10/m',
    time_limit=300,
    soft_time_limit=240,
    acks_late=True,
    reject_on_worker_lost=True,
)
def generate_lesson_task(self, job_id: str, request_data: dict) -> Dict[str, Any]:
    """Generate lesson plan JSON via LLM with retry and fallback.

    Retry Policy:
        - 3 retries with exponential backoff (2^n seconds)
        - Fallback: DeepSeek → OpenAI → Template

    Args:
        job_id: Job identifier
        request_data: GenerateRequest dict

    Returns:
        Lesson JSON dict with meta, outline, summary
    """
    logger.info(
        "task_started",
        task_id=self.request.id,
        job_id=job_id,
        task_name="generate_lesson",
        retry_count=self.request.retries,
    )

    _update_progress_sync(
        job_id, ProductType.lesson, TaskStatus.in_progress, 10,
        message="正在调用 LLM 生成教案..."
    )

    try:
        from services.lesson import LessonGenerator
        generator = LessonGenerator()
        lesson_json = generator.generate(request_data)

        # Store lesson_json for downstream tasks
        from app.router import jobs
        if job_id in jobs:
            jobs[job_id].lesson_json = lesson_json

        _update_progress_sync(
            job_id, ProductType.lesson, TaskStatus.completed, 100,
            message="教案生成完成",
            download_url=f"/api/download/lesson/{job_id}"
        )

        logger.info(
            "task_completed",
            task_id=self.request.id,
            job_id=job_id,
        )

        # Return lesson_json for downstream tasks (chord header needs this)
        return lesson_json

    except Exception as e:
        logger.error(
            "task_failed",
            task_id=self.request.id,
            job_id=job_id,
            error=str(e),
            retry_count=self.request.retries,
            exc_info=True,
        )

        # Update progress with retry info
        _update_progress_sync(
            job_id, ProductType.lesson, TaskStatus.in_progress, 10,
            message=f"生成失败，正在重试 ({self.request.retries + 1}/3)...",
            error=str(e)
        )

        # If max retries reached, mark as failed
        if self.request.retries >= self.max_retries - 1:
            _update_progress_sync(
                job_id, ProductType.lesson, TaskStatus.failed, 0,
                error=f"教案生成失败: {str(e)}"
            )

        raise


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    max_retries=3,
    retry_backoff=True,
    retry_backoff_max=60,
    retry_jitter=True,
    rate_limit='5/m',
    time_limit=600,
    soft_time_limit=500,
    acks_late=True,
)
def generate_tts_task(self, job_id: str, lesson_json: Optional[Dict] = None) -> Dict[str, Any]:
    """Generate TTS audio from lesson content with retry.

    Args:
        job_id: Job identifier
        lesson_json: Lesson JSON dict (passed from generate_lesson_task)

    Returns:
        Dict with audio file paths list
    """
    logger.info(
        "task_started",
        task_id=self.request.id,
        job_id=job_id,
        task_name="generate_tts",
    )

    _update_progress_sync(
        job_id, ProductType.tts, TaskStatus.in_progress, 10,
        message="正在合成语音..."
    )

    try:
        # Get lesson_json from job state if not passed
        if lesson_json is None:
            from app.router import jobs
            if job_id in jobs:
                lesson_json = jobs[job_id].lesson_json

        if lesson_json is None:
            raise ValueError("Lesson JSON not found for TTS generation")

        from services.voice import VoiceGenerator
        generator = VoiceGenerator()
        audio_files = generator.generate(lesson_json)

        # Store audio files for video task
        from app.router import jobs
        if job_id in jobs:
            jobs[job_id].audio_files = audio_files

        _update_progress_sync(
            job_id, ProductType.tts, TaskStatus.completed, 100,
            message="语音合成完成",
            download_url=f"/api/download/tts/{job_id}"
        )

        logger.info("task_completed", task_id=self.request.id, job_id=job_id)

        return {"audio_files": audio_files}

    except Exception as e:
        logger.error(
            "task_failed",
            task_id=self.request.id,
            job_id=job_id,
            error=str(e),
            exc_info=True,
        )

        if self.request.retries >= self.max_retries - 1:
            _update_progress_sync(
                job_id, ProductType.tts, TaskStatus.failed, 0,
                error=f"语音合成失败: {str(e)}"
            )

        raise


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    max_retries=2,
    retry_backoff=True,
    retry_backoff_max=30,
    time_limit=120,
    soft_time_limit=100,
    acks_late=True,
)
def generate_ppt_task(self, job_id: str, lesson_json: Optional[Dict] = None) -> Dict[str, Any]:
    """Generate PPT from lesson content.

    Args:
        job_id: Job identifier
        lesson_json: Lesson JSON dict

    Returns:
        Dict with PPT file path
    """
    logger.info(
        "task_started",
        task_id=self.request.id,
        job_id=job_id,
        task_name="generate_ppt",
    )

    _update_progress_sync(
        job_id, ProductType.ppt, TaskStatus.in_progress, 10,
        message="正在生成 PPT..."
    )

    try:
        if lesson_json is None:
            from app.router import jobs
            if job_id in jobs:
                lesson_json = jobs[job_id].lesson_json

        if lesson_json is None:
            raise ValueError("Lesson JSON not found for PPT generation")

        from services.ppt import PPTGenerator
        generator = PPTGenerator()
        ppt_path = generator.generate(lesson_json)

        # Store PPT path for video task
        from app.router import jobs
        if job_id in jobs:
            jobs[job_id].ppt_path = ppt_path

        _update_progress_sync(
            job_id, ProductType.ppt, TaskStatus.completed, 100,
            message="PPT生成完成",
            download_url=f"/api/download/ppt/{job_id}"
        )

        logger.info("task_completed", task_id=self.request.id, job_id=job_id)

        return {"ppt_path": ppt_path}

    except Exception as e:
        logger.error(
            "task_failed",
            task_id=self.request.id,
            job_id=job_id,
            error=str(e),
            exc_info=True,
        )

        if self.request.retries >= self.max_retries - 1:
            _update_progress_sync(
                job_id, ProductType.ppt, TaskStatus.failed, 0,
                error=f"PPT生成失败: {str(e)}"
            )

        raise


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    max_retries=3,
    retry_backoff=True,
    retry_backoff_max=120,
    retry_jitter=True,
    rate_limit='2/m',
    time_limit=1800,
    soft_time_limit=1500,
    acks_late=True,
    reject_on_worker_lost=True,
)
def generate_video_task(self, job_id: str, results: Optional[List] = None) -> Dict[str, Any]:
    """Generate video by combining TTS audio + PPT slides.

    This is the most resource-intensive task, requires TTS + PPT complete.

    Args:
        job_id: Job identifier
        results: Results from parallel tasks (from chord header)

    Returns:
        Dict with video file path
    """
    logger.info(
        "task_started",
        task_id=self.request.id,
        job_id=job_id,
        task_name="generate_video",
    )

    _update_progress_sync(
        job_id, ProductType.video, TaskStatus.in_progress, 10,
        message="正在合成视频..."
    )

    try:
        # Get audio files and PPT path from job state
        from app.router import jobs
        if job_id not in jobs:
            raise ValueError(f"Job {job_id} not found")

        job = jobs[job_id]
        audio_files = job.audio_files
        ppt_path = job.ppt_path

        if not audio_files or not ppt_path:
            raise ValueError("Missing audio files or PPT for video synthesis")

        # Video synthesis implementation (placeholder)
        # TODO: Implement ffmpeg-based video synthesis
        video_path = _synthesize_video(job_id, audio_files, ppt_path, job.lesson_json)

        job.video_path = video_path

        _update_progress_sync(
            job_id, ProductType.video, TaskStatus.completed, 100,
            message="视频合成完成",
            download_url=f"/api/download/video/{job_id}"
        )

        logger.info("task_completed", task_id=self.request.id, job_id=job_id)

        return {"video_path": video_path}

    except Exception as e:
        logger.error(
            "task_failed",
            task_id=self.request.id,
            job_id=job_id,
            error=str(e),
            exc_info=True,
        )

        if self.request.retries >= self.max_retries - 1:
            _update_progress_sync(
                job_id, ProductType.video, TaskStatus.failed, 0,
                error=f"视频合成失败: {str(e)}"
            )

        raise


def _synthesize_video(job_id: str, audio_files: List[str], ppt_path: str, lesson_json: dict) -> str:
    """Synthesize video from audio and PPT.

    TODO: Implement actual ffmpeg-based synthesis.
    """
    # Placeholder implementation
    # Real implementation would:
    # 1. Convert PPT slides to images (python-pptx + PIL)
    # 2. Match audio segments to slides based on lesson outline
    # 3. Use ffmpeg to combine images + audio into video

    output_path = f"/storage/video/{job_id}.mp4"
    logger.info("video_synthesis_placeholder", job_id=job_id, output_path=output_path)

    return output_path


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    max_retries=2,
    time_limit=60,
    soft_time_limit=50,
)
def final_package_task(self, job_id: str) -> Dict[str, Any]:
    """Package all generated products for download.

    Args:
        job_id: Job identifier

    Returns:
        Dict with package download URL
    """
    logger.info(
        "task_started",
        task_id=self.request.id,
        job_id=job_id,
        task_name="final_package",
    )

    try:
        from app.router import jobs
        if job_id not in jobs:
            raise ValueError(f"Job {job_id} not found")

        job = jobs[job_id]

        # Package all products into zip
        package_url = _create_package(job_id, job)

        logger.info("task_completed", task_id=self.request.id, job_id=job_id)

        return {"package_url": package_url}

    except Exception as e:
        logger.error(
            "task_failed",
            task_id=self.request.id,
            job_id=job_id,
            error=str(e),
            exc_info=True,
        )
        raise


def _create_package(job_id: str, job) -> str:
    """Create zip package of all products."""
    import zipfile
    import os

    package_path = f"/storage/packages/{job_id}.zip"

    # TODO: Implement actual packaging
    # Would include: lesson.json, audio files, ppt, video

    logger.info("package_created", job_id=job_id, package_path=package_path)

    return f"/api/download/package/{job_id}"


# ============================================================================
# Error Handling
# ============================================================================

@shared_task(bind=True)
def error_handler(self, job_id: str, request, exc, traceback):
    """Global error handler for pipeline tasks.

    Args:
        job_id: Job identifier
        request: Original task request
        exc: Exception that caused failure
        traceback: Exception traceback
    """
    error_info = {
        'task_name': request.name,
        'task_id': request.id,
        'exception': str(exc),
        'exception_type': exc.__class__.__name__,
        'traceback': str(traceback),
        'timestamp': datetime.utcnow().isoformat(),
    }

    logger.error(
        "pipeline_error",
        job_id=job_id,
        error_info=error_info,
    )

    # Determine which task type failed
    task_type_map = {
        'generate_lesson_task': ProductType.lesson,
        'generate_tts_task': ProductType.tts,
        'generate_ppt_task': ProductType.ppt,
        'generate_video_task': ProductType.video,
        'final_package_task': ProductType.lesson,  # fallback
    }

    task_type = task_type_map.get(request.name, ProductType.lesson)

    _update_progress_sync(
        job_id, task_type, TaskStatus.failed, 0,
        error=f"{exc.__class__.__name__}: {str(exc)}"
    )

    # Store error for later retrieval
    from app.router import jobs
    if job_id in jobs:
        jobs[job_id].error_info = error_info

    return error_info


# ============================================================================
# Legacy Compatibility (保持旧 API 兼容)
# ============================================================================

@shared_task(bind=True)
def start_generation_pipeline_legacy(self, job_id: str, request_data: dict):
    """Legacy pipeline entry point (sequential, no parallel).

    Deprecated: Use build_pipeline_dag() for new implementations.
    """
    # Step 1: Generate lesson plan
    lesson_json = generate_lesson_task(job_id, request_data)

    # Step 2: Generate TTS audio
    if lesson_json:
        generate_tts_task(job_id, lesson_json)

    # Step 3: Generate PPT
    if lesson_json:
        generate_ppt_task(job_id, lesson_json)

    # Step 4: Generate video (future)
    # generate_video_task(job_id, lesson_json)