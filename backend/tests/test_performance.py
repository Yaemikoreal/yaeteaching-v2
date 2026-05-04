"""Performance tests for the application."""
import pytest
import time
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from app.main import app
from services.lesson import LessonGenerator
from services.voice import VoiceGenerator
from services.ppt import PPTGenerator


client = TestClient(app)


class TestAPIPerformance:
    """Performance tests for API endpoints."""

    def test_health_check_response_time(self):
        """Test health endpoint responds quickly."""
        start = time.time()
        response = client.get("/health")
        elapsed = time.time() - start

        assert response.status_code == 200
        assert elapsed < 0.1  # Should respond in under 100ms

    def test_generate_endpoint_response_time(self):
        """Test generate endpoint responds quickly."""
        start = time.time()
        response = client.post(
            "/api/generate",
            json={
                "subject": "数学",
                "grade": "7年级",
                "duration": 45,
                "topic": "一元一次方程",
            },
        )
        elapsed = time.time() - start

        assert response.status_code == 200
        assert elapsed < 0.5  # Should respond in under 500ms (job creation is fast)

    def test_job_status_response_time(self):
        """Test job status endpoint responds quickly."""
        # Create a job first
        create_response = client.post(
            "/api/generate",
            json={"subject": "数学", "grade": "7年级", "duration": 45, "topic": "test"},
        )
        job_id = create_response.json()["job_id"]

        start = time.time()
        response = client.get(f"/api/job/{job_id}/status")
        elapsed = time.time() - start

        assert response.status_code == 200
        assert elapsed < 0.1


class TestGeneratorPerformance:
    """Performance tests for generator services."""

    def test_lesson_generator_template_performance(self):
        """Test template generation is fast."""
        generator = LessonGenerator()
        generator.deepseek_key = ""
        generator.openai_key = ""

        start = time.time()
        for i in range(10):
            generator.generate({
                "subject": "数学",
                "grade": "7年级",
                "topic": f"测试{i}",
                "duration": 45,
            })
        elapsed = time.time() - start

        # Template generation should be very fast
        assert elapsed < 1.0  # 10 generations in under 1 second

    def test_voice_generator_performance(self):
        """Test voice generator placeholder is fast."""
        generator = VoiceGenerator()

        lesson = {
            "meta": {"subject": "数学"},
            "outline": {
                "introduction": {"title": "导入", "content": "内容"},
                "main_sections": [
                    {"title": "知识点1", "content": "内容1"},
                    {"title": "知识点2", "content": "内容2"},
                    {"title": "知识点3", "content": "内容3"},
                ],
                "conclusion": {"title": "总结", "content": "内容"},
            },
        }

        start = time.time()
        for i in range(10):
            generator.generate(lesson)
        elapsed = time.time() - start

        # Placeholder should be very fast
        assert elapsed < 0.5

    def test_ppt_generator_slide_creation_performance(self):
        """Test PPT slide creation is reasonably fast."""
        generator = PPTGenerator()

        from pptx import Presentation
        from models.lesson import SlideType

        lesson = {
            "meta": {"subject": "数学", "topic": "测试"},
            "outline": {
                "introduction": {"title": "导入", "content": "内容"},
                "main_sections": [
                    {"title": f"知识点{i}", "content": f"内容{i}", "key_points": ["要点"]}
                    for i in range(5)
                ],
                "conclusion": {"title": "总结", "content": "内容"},
            },
        }

        start = time.time()
        for i in range(5):
            prs = Presentation()
            generator._add_title_slide(prs, lesson["meta"])
            for section in lesson["outline"]["main_sections"]:
                generator._add_content_slide(prs, section, SlideType.knowledge)
        elapsed = time.time() - start

        # Slide creation should be reasonably fast
        assert elapsed < 2.0


class TestWebSocketPerformance:
    """Performance tests for WebSocket handling."""

    def test_manager_connect_performance(self):
        """Test WebSocket connection management is fast."""
        from app.websocket import ConnectionManager

        manager = ConnectionManager()

        async def connect_many():
            mock_ws = AsyncMock()
            for i in range(100):
                await manager.connect(f"job-{i}", mock_ws)

        start = time.time()
        asyncio.run(connect_many())
        elapsed = time.time() - start

        assert elapsed < 1.0

    def test_manager_broadcast_performance(self):
        """Test broadcast to many connections is fast."""
        from app.websocket import ConnectionManager
        from models.job import ProgressMessage, TaskStatus, ProductType

        manager = ConnectionManager()

        async def setup_and_broadcast():
            # Setup many connections
            for i in range(50):
                mock_ws = AsyncMock()
                await manager.connect("test-job", mock_ws)

            # Broadcast
            msg = ProgressMessage(
                job_id="test-job",
                task_type=ProductType.lesson,
                status=TaskStatus.in_progress,
                progress=50,
            )
            await manager.broadcast("test-job", msg)

        start = time.time()
        asyncio.run(setup_and_broadcast())
        elapsed = time.time() - start

        # Broadcast should be reasonably fast
        assert elapsed < 1.0


class TestConcurrentJobCreation:
    """Performance tests for concurrent job creation."""

    def test_multiple_jobs_created_quickly(self):
        """Test multiple jobs can be created quickly."""
        start = time.time()

        job_ids = []
        for i in range(10):
            response = client.post(
                "/api/generate",
                json={
                    "subject": "数学",
                    "grade": "7年级",
                    "duration": 45,
                    "topic": f"测试{i}",
                },
            )
            assert response.status_code == 200
            job_ids.append(response.json()["job_id"])

        elapsed = time.time() - start

        # 10 job creations should be fast
        assert elapsed < 5.0

        # All job IDs should be unique
        assert len(set(job_ids)) == 10

    def test_job_status_queries_quickly(self):
        """Test multiple status queries are fast."""
        # Create jobs first
        job_ids = []
        for i in range(10):
            response = client.post(
                "/api/generate",
                json={"subject": "数学", "grade": "7年级", "duration": 45, "topic": f"test{i}"},
            )
            job_ids.append(response.json()["job_id"])

        start = time.time()

        for job_id in job_ids:
            response = client.get(f"/api/job/{job_id}/status")
            assert response.status_code == 200

        elapsed = time.time() - start

        # 10 status queries should be fast
        assert elapsed < 2.0


class TestMemoryUsage:
    """Basic memory usage tests."""

    def test_job_storage_memory_efficient(self):
        """Test job storage doesn't grow excessively."""
        from app.router import jobs
        from models.job import JobStatus, TaskProgress, TaskStatus, ProductType
        from datetime import datetime

        initial_count = len(jobs)

        # Create many jobs
        for i in range(50):
            job_id = f"memory-test-{i}"
            jobs[job_id] = JobStatus(
                job_id=job_id,
                status=TaskStatus.pending,
                tasks=[
                    TaskProgress(type=t, status=TaskStatus.pending, progress=0)
                    for t in ProductType
                ],
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )

        # Should have added exactly 50
        assert len(jobs) == initial_count + 50

        # Clean up
        for i in range(50):
            del jobs[f"memory-test-{i}"]

        assert len(jobs) == initial_count

    def test_websocket_manager_memory_cleanup(self):
        """Test WebSocket manager cleans up properly."""
        from app.websocket import ConnectionManager

        manager = ConnectionManager()

        async def test_cleanup():
            mock_ws = AsyncMock()
            await manager.connect("cleanup-test", mock_ws)

            assert "cleanup-test" in manager.active_connections

            manager.disconnect("cleanup-test", mock_ws)

            assert "cleanup-test" not in manager.active_connections

        asyncio.run(test_cleanup())


class TestModelSerializationPerformance:
    """Performance tests for model serialization."""

    def test_progress_message_serialization_fast(self):
        """Test ProgressMessage serialization is fast."""
        from models.job import ProgressMessage, TaskStatus, ProductType

        msg = ProgressMessage(
            job_id="test",
            task_type=ProductType.lesson,
            status=TaskStatus.in_progress,
            progress=50,
            message="Processing...",
        )

        start = time.time()
        for i in range(1000):
            msg.model_dump_json()
        elapsed = time.time() - start

        # Serialization should be fast
        assert elapsed < 1.0

    def test_job_status_serialization_fast(self):
        """Test JobStatus serialization is fast."""
        from models.job import JobStatus, TaskProgress, TaskStatus, ProductType
        from datetime import datetime

        job = JobStatus(
            job_id="test",
            status=TaskStatus.in_progress,
            tasks=[
                TaskProgress(type=t, status=TaskStatus.in_progress, progress=50)
                for t in ProductType
            ],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        start = time.time()
        for i in range(100):
            job.model_dump()
        elapsed = time.time() - start

        assert elapsed < 0.5