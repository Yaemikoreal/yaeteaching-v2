"""Tests for authentication service and routes."""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from services.auth import auth_service, AuthService
from models.user import UserCreate, UserLogin, UserRole


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def fresh_auth_service():
    """Create fresh auth service for each test."""
    return AuthService()


class TestAuthService:
    """Test AuthService core functionality."""

    def test_hash_password(self, fresh_auth_service):
        """Test password hashing."""
        password = "testpassword123"
        hashed = fresh_auth_service.hash_password(password)
        assert hashed != password
        assert len(hashed) > 0

    def test_verify_password_correct(self, fresh_auth_service):
        """Test password verification with correct password."""
        password = "testpassword123"
        hashed = fresh_auth_service.hash_password(password)
        assert fresh_auth_service.verify_password(password, hashed)

    def test_verify_password_wrong(self, fresh_auth_service):
        """Test password verification with wrong password."""
        password = "testpassword123"
        hashed = fresh_auth_service.hash_password(password)
        assert not fresh_auth_service.verify_password("wrongpassword", hashed)

    def test_create_user(self, fresh_auth_service):
        """Test user creation."""
        user_create = UserCreate(
            email="test@example.com",
            password="testpassword123",
            name="Test User",
            role=UserRole.student
        )
        user = fresh_auth_service.create_user(user_create)
        assert user.email == user_create.email
        assert user.name == user_create.name
        assert user.role == UserRole.student
        assert user.hashed_password != user_create.password

    def test_create_user_duplicate_email(self, fresh_auth_service):
        """Test creating user with duplicate email fails."""
        user_create = UserCreate(
            email="test@example.com",
            password="testpassword123",
            name="Test User"
        )
        fresh_auth_service.create_user(user_create)
        with pytest.raises(ValueError, match="Email already registered"):
            fresh_auth_service.create_user(user_create)

    def test_authenticate_user_success(self, fresh_auth_service):
        """Test successful authentication."""
        user_create = UserCreate(
            email="test@example.com",
            password="testpassword123",
            name="Test User"
        )
        fresh_auth_service.create_user(user_create)

        user_login = UserLogin(email="test@example.com", password="testpassword123")
        user = fresh_auth_service.authenticate_user(user_login)
        assert user is not None
        assert user.email == "test@example.com"

    def test_authenticate_user_wrong_password(self, fresh_auth_service):
        """Test authentication with wrong password."""
        user_create = UserCreate(
            email="test@example.com",
            password="testpassword123",
            name="Test User"
        )
        fresh_auth_service.create_user(user_create)

        user_login = UserLogin(email="test@example.com", password="wrongpassword")
        user = fresh_auth_service.authenticate_user(user_login)
        assert user is None

    def test_authenticate_user_unknown_email(self, fresh_auth_service):
        """Test authentication with unknown email."""
        user_login = UserLogin(email="unknown@example.com", password="testpassword123")
        user = fresh_auth_service.authenticate_user(user_login)
        assert user is None

    def test_generate_access_token(self, fresh_auth_service):
        """Test access token generation."""
        user_create = UserCreate(
            email="test@example.com",
            password="testpassword123",
            name="Test User"
        )
        user = fresh_auth_service.create_user(user_create)
        token = fresh_auth_service.generate_access_token(user.id, user.role)
        assert token is not None
        assert len(token) > 0

    def test_verify_token_valid(self, fresh_auth_service):
        """Test token verification with valid token."""
        user_create = UserCreate(
            email="test@example.com",
            password="testpassword123",
            name="Test User"
        )
        user = fresh_auth_service.create_user(user_create)
        token = fresh_auth_service.generate_access_token(user.id, user.role)

        payload = fresh_auth_service.verify_token(token)
        assert payload is not None
        assert payload["sub"] == user.id
        assert payload["role"] == user.role
        assert payload["type"] == "access"

    def test_verify_token_invalid(self, fresh_auth_service):
        """Test token verification with invalid token."""
        payload = fresh_auth_service.verify_token("invalid-token")
        assert payload is None


class TestAuthRoutes:
    """Test authentication API routes."""

    def test_register_success(self, client):
        """Test successful user registration."""
        response = client.post(
            "/api/auth/register",
            json={
                "email": "test@example.com",
                "password": "testpassword123",
                "name": "Test User"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    def test_register_duplicate_email(self, client):
        """Test registration with duplicate email."""
        # First registration
        client.post(
            "/api/auth/register",
            json={
                "email": "duplicate@example.com",
                "password": "testpassword123",
                "name": "First User"
            }
        )
        # Second registration with same email
        response = client.post(
            "/api/auth/register",
            json={
                "email": "duplicate@example.com",
                "password": "testpassword123",
                "name": "Second User"
            }
        )
        assert response.status_code == 400

    def test_register_invalid_email(self, client):
        """Test registration with invalid email format."""
        response = client.post(
            "/api/auth/register",
            json={
                "email": "invalid-email",
                "password": "testpassword123",
                "name": "Test User"
            }
        )
        assert response.status_code == 422

    def test_register_short_password(self, client):
        """Test registration with short password."""
        response = client.post(
            "/api/auth/register",
            json={
                "email": "test@example.com",
                "password": "short",
                "name": "Test User"
            }
        )
        assert response.status_code == 422

    def test_login_success(self, client):
        """Test successful login."""
        # Register first
        client.post(
            "/api/auth/register",
            json={
                "email": "login@example.com",
                "password": "testpassword123",
                "name": "Login User"
            }
        )
        # Login
        response = client.post(
            "/api/auth/login",
            json={
                "email": "login@example.com",
                "password": "testpassword123"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data

    def test_login_wrong_password(self, client):
        """Test login with wrong password."""
        # Register first
        client.post(
            "/api/auth/register",
            json={
                "email": "wrongpass@example.com",
                "password": "testpassword123",
                "name": "Wrong Pass User"
            }
        )
        # Login with wrong password
        response = client.post(
            "/api/auth/login",
            json={
                "email": "wrongpass@example.com",
                "password": "wrongpassword"
            }
        )
        assert response.status_code == 401

    def test_login_unknown_email(self, client):
        """Test login with unknown email."""
        response = client.post(
            "/api/auth/login",
            json={
                "email": "unknown@example.com",
                "password": "testpassword123"
            }
        )
        assert response.status_code == 401

    def test_get_me_authenticated(self, client):
        """Test getting current user info when authenticated."""
        # Register and get token
        register_response = client.post(
            "/api/auth/register",
            json={
                "email": "me@example.com",
                "password": "testpassword123",
                "name": "Me User"
            }
        )
        token = register_response.json()["access_token"]

        # Get current user
        response = client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "me@example.com"
        assert data["name"] == "Me User"

    def test_get_me_unauthenticated(self, client):
        """Test getting current user info without authentication."""
        response = client.get("/api/auth/me")
        assert response.status_code == 401

    def test_logout(self, client):
        """Test logout."""
        # Register and get token
        register_response = client.post(
            "/api/auth/register",
            json={
                "email": "logout@example.com",
                "password": "testpassword123",
                "name": "Logout User"
            }
        )
        token = register_response.json()["access_token"]

        response = client.post(
            "/api/auth/logout",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200