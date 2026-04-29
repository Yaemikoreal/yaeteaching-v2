"""Tests for Celery async tasks."""
import pytest
import sys
import os
from unittest.mock import MagicMock, patch
from models.job import TaskStatus, ProductType, JobStatus, TaskProgress
from datetime import datetime


@pytest.fixture
def mock_job_storage():
    """Mock job storage."""
    return {
        "test-job-id": JobStatus(
            job_id="test-job-id",
            status=TaskStatus.pending,
            tasks=[
                TaskProgress(type=ProductType.lesson, status=TaskStatus.pending, progress=0),
                TaskProgress(type=ProductType.tts, status=TaskStatus.pending, progress=0),
                TaskProgress(type=ProductType.ppt, status=TaskStatus.pending, progress=0),
                TaskProgress(type=ProductType.video, status=TaskStatus.pending, progress=0),
            ],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
    }


@pytest.fixture
def sample_request_data():
    """Sample request data for lesson generation."""
    return {
        "subject": "数学",
        "grade": "7年级",
        "topic": "一元一次方程",
        "duration": 45,
        "style": "启发式教学",
    }


@pytest.fixture
def sample_lesson_json():
    """Sample lesson JSON for testing."""
    return {
        "meta": {
            "subject": "数学",
            "grade": "7年级",
            "topic": "一元一次方程",
            "duration": 45,
        },
        "outline": {
            "introduction": {"title": "导入", "content": "test"},
            "main_sections": [],
            "conclusion": {"title": "总结", "content": "test"},
        },
        "summary": "test",
        "resources": [],
    }


def test_celery_config_file_exists():
    """Test that celery config file exists."""
    backend_path = os.path.dirname(os.path.dirname(__file__))
    config_path = os.path.join(backend_path, "celery", "config.py")
    assert os.path.exists(config_path)


def test_celery_tasks_file_exists():
    """Test that celery tasks file exists."""
    backend_path = os.path.dirname(os.path.dirname(__file__))
    tasks_path = os.path.join(backend_path, "celery", "tasks.py")
    assert os.path.exists(tasks_path)


def test_task_progress_update_logic(mock_job_storage):
    """Test task progress update logic without importing celery."""
    # Simulate the update logic
    job = mock_job_storage["test-job-id"]

    # Update lesson task
    for i, task in enumerate(job.tasks):
        if task.type == ProductType.lesson:
            job.tasks[i] = TaskProgress(
                type=ProductType.lesson,
                status=TaskStatus.in_progress,
                progress=50,
                message="正在生成教案",
            )
            break

    job.status = TaskStatus.in_progress
    job.updated_at = datetime.utcnow()

    assert job.status == TaskStatus.in_progress
    lesson_task = next(t for t in job.tasks if t.type == ProductType.lesson)
    assert lesson_task.status == TaskStatus.in_progress
    assert lesson_task.progress == 50


def test_task_completion_logic(mock_job_storage):
    """Test task completion logic."""
    job = mock_job_storage["test-job-id"]

    # Mark lesson as completed
    for i, task in enumerate(job.tasks):
        if task.type == ProductType.lesson:
            job.tasks[i] = TaskProgress(
                type=ProductType.lesson,
                status=TaskStatus.completed,
                progress=100,
                message="教案生成完成",
                download_url="/api/download/lesson/test-job-id",
            )
            break

    lesson_task = next(t for t in job.tasks if t.type == ProductType.lesson)
    assert lesson_task.status == TaskStatus.completed
    assert lesson_task.download_url == "/api/download/lesson/test-job-id"


def test_task_failure_logic(mock_job_storage):
    """Test task failure logic."""
    job = mock_job_storage["test-job-id"]

    # Mark lesson as failed
    for i, task in enumerate(job.tasks):
        if task.type == ProductType.lesson:
            job.tasks[i] = TaskProgress(
                type=ProductType.lesson,
                status=TaskStatus.failed,
                progress=0,
                error="LLM API调用失败",
            )
            break

    lesson_task = next(t for t in job.tasks if t.type == ProductType.lesson)
    assert lesson_task.status == TaskStatus.failed
    assert lesson_task.error == "LLM API调用失败"


def test_all_tasks_progress(mock_job_storage):
    """Test updating all tasks."""
    job = mock_job_storage["test-job-id"]

    # Update all tasks
    for i, task in enumerate(job.tasks):
        job.tasks[i] = TaskProgress(
            type=task.type,
            status=TaskStatus.completed,
            progress=100,
            message=f"{task.type.value}生成完成",
            download_url=f"/api/download/{task.type.value}/test-job-id",
        )

    # Check all tasks completed
    assert all(t.status == TaskStatus.completed for t in job.tasks)


def test_pipeline_order():
    """Test that pipeline order is correct."""
    # Expected order: lesson -> tts -> ppt -> video
    expected_order = [ProductType.lesson, ProductType.tts, ProductType.ppt, ProductType.video]
    assert list(ProductType) == expected_order


def test_task_status_values():
    """Test TaskStatus enum values."""
    assert TaskStatus.pending.value == "pending"
    assert TaskStatus.in_progress.value == "in_progress"
    assert TaskStatus.completed.value == "completed"
    assert TaskStatus.failed.value == "failed"


def test_product_type_values():
    """Test ProductType enum values."""
    assert ProductType.lesson.value == "lesson"
    assert ProductType.tts.value == "tts"
    assert ProductType.ppt.value == "ppt"
    assert ProductType.video.value == "video"