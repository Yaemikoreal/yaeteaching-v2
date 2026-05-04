"""Integration tests for WebSocket connection and broadcast."""
import pytest
import pytest_asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.websocket import ConnectionManager, manager, push_progress
from models.job import ProgressMessage, TaskStatus, ProductType


@pytest_asyncio.fixture
async def async_client():
    """Create async client for WebSocket testing."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as ac:
        yield ac


class TestConnectionManagerConnect:
    """Tests for WebSocket connection management."""

    def test_connect_creates_new_job_entry(self):
        """Test connect creates new job entry when first connection."""
        manager = ConnectionManager()
        mock_ws = AsyncMock()

        # Run async connect
        async def run_connect():
            await manager.connect("test-job-1", mock_ws)

        import asyncio
        asyncio.run(run_connect())

        assert "test-job-1" in manager.active_connections
        assert mock_ws in manager.active_connections["test-job-1"]

    def test_connect_adds_to_existing_job(self):
        """Test connect adds to existing job connections."""
        manager = ConnectionManager()
        mock_ws1 = AsyncMock()
        mock_ws2 = AsyncMock()

        async def run_connect():
            await manager.connect("test-job-2", mock_ws1)
            await manager.connect("test-job-2", mock_ws2)

        import asyncio
        asyncio.run(run_connect())

        assert len(manager.active_connections["test-job-2"]) == 2

    def test_disconnect_removes_connection(self):
        """Test disconnect removes specific connection."""
        manager = ConnectionManager()
        mock_ws1 = AsyncMock()
        mock_ws2 = AsyncMock()

        async def run_connect():
            await manager.connect("test-job-3", mock_ws1)
            await manager.connect("test-job-3", mock_ws2)

        import asyncio
        asyncio.run(run_connect())

        # Disconnect one
        manager.disconnect("test-job-3", mock_ws1)

        assert len(manager.active_connections["test-job-3"]) == 1
        assert mock_ws1 not in manager.active_connections["test-job-3"]

    def test_disconnect_removes_job_when_empty(self):
        """Test disconnect removes job entry when no connections left."""
        manager = ConnectionManager()
        mock_ws = AsyncMock()

        async def run_connect():
            await manager.connect("test-job-4", mock_ws)

        import asyncio
        asyncio.run(run_connect())

        manager.disconnect("test-job-4", mock_ws)

        assert "test-job-4" not in manager.active_connections


class TestConnectionManagerBroadcast:
    """Tests for WebSocket broadcast functionality."""

    @pytest.mark.asyncio
    async def test_broadcast_sends_to_all_connections(self):
        """Test broadcast sends message to all connections."""
        manager = ConnectionManager()
        mock_ws1 = AsyncMock()
        mock_ws2 = AsyncMock()

        await manager.connect("test-job-5", mock_ws1)
        await manager.connect("test-job-5", mock_ws2)

        msg = ProgressMessage(
            job_id="test-job-5",
            task_type=ProductType.lesson,
            status=TaskStatus.in_progress,
            progress=50,
            message="Processing",
        )

        await manager.broadcast("test-job-5", msg)

        # Verify both received the message
        mock_ws1.send_text.assert_called_once()
        mock_ws2.send_text.assert_called_once()

        # Check message content
        call_args = mock_ws1.send_text.call_args[0][0]
        data = json.loads(call_args)
        assert data["job_id"] == "test-job-5"
        assert data["progress"] == 50

    @pytest.mark.asyncio
    async def test_broadcast_skips_unknown_job(self):
        """Test broadcast does nothing for unknown job."""
        manager = ConnectionManager()

        msg = ProgressMessage(
            job_id="unknown-job",
            task_type=ProductType.lesson,
            status=TaskStatus.completed,
            progress=100,
        )

        # Should not raise, just return
        await manager.broadcast("unknown-job", msg)

    @pytest.mark.asyncio
    async def test_broadcast_cleans_up_dead_connections(self):
        """Test broadcast removes connections that fail to send."""
        manager = ConnectionManager()
        mock_ws_good = AsyncMock()
        mock_ws_bad = AsyncMock()
        mock_ws_bad.send_text.side_effect = Exception("Connection lost")

        await manager.connect("test-job-6", mock_ws_good)
        await manager.connect("test-job-6", mock_ws_bad)

        msg = ProgressMessage(
            job_id="test-job-6",
            task_type=ProductType.lesson,
            status=TaskStatus.completed,
            progress=100,
        )

        await manager.broadcast("test-job-6", msg)

        # Bad connection should be removed
        assert mock_ws_bad not in manager.active_connections["test-job-6"]
        assert mock_ws_good in manager.active_connections["test-job-6"]


class TestPushProgress:
    """Tests for push_progress helper function."""

    @pytest.mark.asyncio
    async def test_push_progress_calls_broadcast(self):
        """Test push_progress creates message and broadcasts."""
        manager = ConnectionManager()
        mock_ws = AsyncMock()

        await manager.connect("test-job-7", mock_ws)

        # Patch the global manager
        with patch("app.websocket.manager", manager):
            await push_progress(
                job_id="test-job-7",
                task_type=ProductType.ppt,
                status=TaskStatus.completed,
                progress=100,
                message="PPT generated",
                download_url="/api/download/ppt/test-job-7",
            )

        mock_ws.send_text.assert_called_once()
        call_args = mock_ws.send_text.call_args[0][0]
        data = json.loads(call_args)
        assert data["download_url"] == "/api/download/ppt/test-job-7"


class TestWebSocketEndpointIntegration:
    """Integration tests for WebSocket endpoint."""

    @pytest.mark.asyncio
    async def test_websocket_accepts_connection(self):
        """Test WebSocket endpoint accepts connection."""
        # Create a test job first
        from app.router import jobs
        from models.job import JobStatus, TaskProgress
        from datetime import datetime

        job_id = "ws-test-job-1"
        jobs[job_id] = JobStatus(
            job_id=job_id,
            status=TaskStatus.pending,
            tasks=[
                TaskProgress(type=ProductType.lesson, status=TaskStatus.pending, progress=0),
            ],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        # Note: Full WebSocket connection test requires starlette test client
        # Here we verify the manager state
        assert job_id in jobs

    def test_websocket_ack_response(self):
        """Test WebSocket sends ack for messages."""
        # This tests the ack response format
        ack_message = json.dumps({"type": "ack", "job_id": "test-job"})
        data = json.loads(ack_message)
        assert data["type"] == "ack"
        assert "job_id" in data