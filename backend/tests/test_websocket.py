"""Tests for WebSocket handler."""
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from app.websocket import ConnectionManager, manager
from models.job import ProgressMessage, TaskStatus, ProductType


@pytest.fixture
def mock_websocket():
    """Mock WebSocket connection."""
    ws = MagicMock()
    ws.accept = AsyncMock()
    ws.send_text = AsyncMock()
    return ws


def test_connection_manager_init():
    """Test ConnectionManager initializes correctly."""
    manager = ConnectionManager()
    assert manager.active_connections == {}


@pytest.mark.asyncio
async def test_connection_manager_connect(mock_websocket):
    """Test WebSocket connection is accepted and registered."""
    manager = ConnectionManager()
    await manager.connect("test-job-id", mock_websocket)

    mock_websocket.accept.assert_called_once()
    assert "test-job-id" in manager.active_connections
    assert mock_websocket in manager.active_connections["test-job-id"]


@pytest.mark.asyncio
async def test_connection_manager_disconnect(mock_websocket):
    """Test WebSocket connection is removed."""
    manager = ConnectionManager()
    manager.active_connections["test-job-id"] = [mock_websocket]

    manager.disconnect("test-job-id", mock_websocket)

    assert "test-job-id" not in manager.active_connections


@pytest.mark.asyncio
async def test_connection_manager_disconnect_last(mock_websocket):
    """Test removing last connection removes job entry."""
    manager = ConnectionManager()
    manager.active_connections["test-job-id"] = [mock_websocket]

    manager.disconnect("test-job-id", mock_websocket)

    # Should remove empty job entry
    assert "test-job-id" not in manager.active_connections


@pytest.mark.asyncio
async def test_connection_manager_multiple_connections(mock_websocket):
    """Test managing multiple connections for same job."""
    manager = ConnectionManager()
    ws2 = MagicMock()
    ws2.accept = AsyncMock()
    ws2.send_text = AsyncMock()

    await manager.connect("test-job-id", mock_websocket)
    await manager.connect("test-job-id", ws2)

    assert len(manager.active_connections["test-job-id"]) == 2


@pytest.mark.asyncio
async def test_connection_manager_broadcast(mock_websocket):
    """Test broadcasting message to connections."""
    manager = ConnectionManager()
    await manager.connect("test-job-id", mock_websocket)

    message = ProgressMessage(
        job_id="test-job-id",
        task_type=ProductType.lesson,
        status=TaskStatus.in_progress,
        progress=50,
        message="正在生成教案",
    )

    await manager.broadcast("test-job-id", message)

    mock_websocket.send_text.assert_called_once()


@pytest.mark.asyncio
async def test_connection_manager_broadcast_no_connections():
    """Test broadcasting when no connections exist."""
    manager = ConnectionManager()
    message = ProgressMessage(
        job_id="no-connections",
        task_type=ProductType.lesson,
        status=TaskStatus.completed,
        progress=100,
    )

    # Should not raise error
    await manager.broadcast("no-connections", message)


@pytest.mark.asyncio
async def test_connection_manager_broadcast_dead_connection():
    """Test cleaning up dead connections during broadcast."""
    manager = ConnectionManager()
    mock_ws = MagicMock()
    mock_ws.accept = AsyncMock()
    mock_ws.send_text = AsyncMock(side_effect=Exception("Connection dead"))

    await manager.connect("test-job-id", mock_ws)

    message = ProgressMessage(
        job_id="test-job-id",
        task_type=ProductType.lesson,
        status=TaskStatus.completed,
        progress=100,
    )

    await manager.broadcast("test-job-id", message)

    # Dead connection should be removed
    assert "test-job-id" not in manager.active_connections


@pytest.mark.asyncio
async def test_push_progress():
    """Test push_progress function."""
    from app.websocket import push_progress

    # Create a fresh manager for testing
    test_manager = ConnectionManager()
    mock_ws = MagicMock()
    mock_ws.accept = AsyncMock()
    mock_ws.send_text = AsyncMock()
    await test_manager.connect("test-job-id", mock_ws)

    with patch("app.websocket.manager", test_manager):
        await push_progress(
            job_id="test-job-id",
            task_type=ProductType.lesson,
            status=TaskStatus.completed,
            progress=100,
            message="教案生成完成",
            download_url="/api/download/lesson/test-job-id",
        )

        mock_ws.send_text.assert_called_once()