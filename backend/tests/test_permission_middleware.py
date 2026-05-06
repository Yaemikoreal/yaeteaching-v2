"""Tests for permission middleware and authenticated API access."""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from services.auth import auth_service, AuthService
from models.user import UserCreate, UserRole


@pytest.fixture(autouse=True)
def reset_auth_service():
    """Reset auth service before each test to avoid duplicate users."""
    auth_service.users.clear()


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def test_user():
    """Create a test user."""
    user_create = UserCreate(
        email="testuser@example.com",
        password="testpassword123",
        name="Test User",
        role=UserRole.student
    )
    return auth_service.create_user(user_create)


@pytest.fixture
def admin_user():
    """Create an admin test user."""
    user_create = UserCreate(
        email="admin@example.com",
        password="adminpassword123",
        name="Admin User",
        role=UserRole.admin
    )
    return auth_service.create_user(user_create)


@pytest.fixture
def test_user_token(test_user):
    """Generate token for test user."""
    return auth_service.generate_token_response(test_user).access_token


@pytest.fixture
def admin_token(admin_user):
    """Generate token for admin user."""
    return auth_service.generate_token_response(admin_user).access_token


class TestPermissionMiddleware:
    """Test permission middleware on API routes."""

    def test_generate_requires_authentication(self, client):
        """Test that /api/generate returns 401 without authentication."""
        response = client.post(
            "/api/generate",
            json={
                "subject": "数学",
                "grade": "7年级",
                "duration": 45,
                "topic": "一元一次方程",
            },
        )
        assert response.status_code == 401
        assert response.json()["detail"] == "Not authenticated"

    def test_generate_with_authentication(self, client, test_user_token):
        """Test that /api/generate works with authentication."""
        response = client.post(
            "/api/generate",
            headers={"Authorization": f"Bearer {test_user_token}"},
            json={
                "subject": "数学",
                "grade": "7年级",
                "duration": 45,
                "topic": "一元一次方程",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "job_id" in data
        assert data["message"] == "任务已创建，正在处理"

    def test_job_status_requires_authentication(self, client, test_user_token):
        """Test that /api/job/{job_id}/status requires authentication."""
        # First create a job
        create_response = client.post(
            "/api/generate",
            headers={"Authorization": f"Bearer {test_user_token}"},
            json={
                "subject": "物理",
                "grade": "高一",
                "duration": 30,
                "topic": "牛顿第一定律",
            },
        )
        job_id = create_response.json()["job_id"]

        # Then try to get status without authentication
        response = client.get(f"/api/job/{job_id}/status")
        assert response.status_code == 401

    def test_user_can_access_own_jobs(self, client, test_user_token):
        """Test that user can access their own jobs."""
        # Create a job as test user
        create_response = client.post(
            "/api/generate",
            headers={"Authorization": f"Bearer {test_user_token}"},
            json={
                "subject": "化学",
                "grade": "高二",
                "duration": 40,
                "topic": "化学平衡",
            },
        )
        job_id = create_response.json()["job_id"]

        # Get job status as test user
        response = client.get(
            f"/api/job/{job_id}/status",
            headers={"Authorization": f"Bearer {test_user_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["job_id"] == job_id

    def test_user_cannot_access_others_jobs(self, client):
        """Test that user cannot access jobs created by other users."""
        # Create test user 1
        user1_create = UserCreate(
            email="user1@example.com",
            password="password123",
            name="User 1",
            role=UserRole.student
        )
        user1 = auth_service.create_user(user1_create)
        token1 = auth_service.generate_token_response(user1).access_token

        # Create test user 2
        user2_create = UserCreate(
            email="user2@example.com",
            password="password123",
            name="User 2",
            role=UserRole.student
        )
        user2 = auth_service.create_user(user2_create)
        token2 = auth_service.generate_token_response(user2).access_token

        # Create job as user1
        create_response = client.post(
            "/api/generate",
            headers={"Authorization": f"Bearer {token1}"},
            json={
                "subject": "语文",
                "grade": "初三",
                "duration": 50,
                "topic": "古诗文鉴赏",
            },
        )
        job_id = create_response.json()["job_id"]

        # Try to access user1's job as user2
        response = client.get(
            f"/api/job/{job_id}/status",
            headers={"Authorization": f"Bearer {token2}"}
        )
        assert response.status_code == 403
        assert response.json()["detail"] == "Access denied"

    def test_admin_can_access_all_jobs(self, client, test_user_token, admin_token):
        """Test that admin can access jobs created by other users."""
        # Create job as test user
        create_response = client.post(
            "/api/generate",
            headers={"Authorization": f"Bearer {test_user_token}"},
            json={
                "subject": "历史",
                "grade": "初二",
                "duration": 45,
                "topic": "近代史",
            },
        )
        job_id = create_response.json()["job_id"]

        # Access test user's job as admin
        response = client.get(
            f"/api/job/{job_id}/status",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["job_id"] == job_id

    def test_download_requires_authentication(self, client, test_user_token):
        """Test that download endpoint requires authentication."""
        # Create a job
        create_response = client.post(
            "/api/generate",
            headers={"Authorization": f"Bearer {test_user_token}"},
            json={
                "subject": "地理",
                "grade": "初一",
                "duration": 35,
                "topic": "地球运动",
            },
        )
        job_id = create_response.json()["job_id"]

        # Try to download without authentication
        response = client.get(f"/api/download/lesson/{job_id}")
        assert response.status_code == 401

    def test_invalid_token_returns_401(self, client):
        """Test that invalid JWT token returns 401."""
        response = client.post(
            "/api/generate",
            headers={"Authorization": "Bearer invalid_token_here"},
            json={
                "subject": "数学",
                "grade": "7年级",
                "duration": 45,
                "topic": "一元一次方程",
            },
        )
        assert response.status_code == 401
        assert response.json()["detail"] == "Invalid or expired token"

    def test_expired_token_returns_401(self, client):
        """Test that expired JWT token returns 401."""
        # Create a user and generate a token with very short expiry
        user_create = UserCreate(
            email="expired@example.com",
            password="password123",
            name="Expired User",
            role=UserRole.student
        )
        user = auth_service.create_user(user_create)

        # Generate token with 1 second expiry (manually create for testing)
        import jwt
        from datetime import datetime, timedelta
        expired_payload = {
            "sub": user.id,
            "role": user.role,
            "type": "access",
            "exp": datetime.utcnow() - timedelta(seconds=1),  # Already expired
            "iat": datetime.utcnow() - timedelta(seconds=10)
        }
        expired_token = jwt.encode(expired_payload, "dev-secret-key", algorithm="HS256")

        response = client.post(
            "/api/generate",
            headers={"Authorization": f"Bearer {expired_token}"},
            json={
                "subject": "数学",
                "grade": "7年级",
                "duration": 45,
                "topic": "一元一次方程",
            },
        )
        assert response.status_code == 401
        assert response.json()["detail"] == "Invalid or expired token"


class TestRoleBasedAccess:
    """Test role-based access control."""

    def test_student_role(self, client):
        """Test student role can create and view own jobs."""
        user_create = UserCreate(
            email="student@example.com",
            password="password123",
            name="Student User",
            role=UserRole.student
        )
        user = auth_service.create_user(user_create)
        token = auth_service.generate_token_response(user).access_token

        # Student can create jobs
        response = client.post(
            "/api/generate",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "subject": "英语",
                "grade": "高一",
                "duration": 40,
                "topic": "阅读理解",
            },
        )
        assert response.status_code == 200

    def test_teacher_role(self, client):
        """Test teacher role has same permissions as student."""
        user_create = UserCreate(
            email="teacher@example.com",
            password="password123",
            name="Teacher User",
            role=UserRole.teacher
        )
        user = auth_service.create_user(user_create)
        token = auth_service.generate_token_response(user).access_token

        # Teacher can create jobs
        response = client.post(
            "/api/generate",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "subject": "政治",
                "grade": "初三",
                "duration": 45,
                "topic": "经济全球化",
            },
        )
        assert response.status_code == 200

    def test_admin_role_can_access_all(self, client, test_user_token, admin_token):
        """Test admin role can access all users' resources."""
        # Create job as regular user
        create_response = client.post(
            "/api/generate",
            headers={"Authorization": f"Bearer {test_user_token}"},
            json={
                "subject": "音乐",
                "grade": "初一",
                "duration": 30,
                "topic": "民歌鉴赏",
            },
        )
        job_id = create_response.json()["job_id"]

        # Admin can access it
        response = client.get(
            f"/api/job/{job_id}/status",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200