"""Authentication service: password hashing and JWT token generation."""
import bcrypt
import jwt
from datetime import datetime, timedelta
from typing import Optional
from uuid import uuid4

from models.user import (
    User, UserCreate, UserLogin, UserResponse,
    TokenResponse, UserRole, AuthConfig
)
from config.settings import settings


class AuthService:
    """Authentication and user management service."""

    # In-memory user storage (replace with PostgreSQL in production)
    users: dict[str, User] = {}

    def __init__(self):
        self.config = AuthConfig(
            jwt_secret=settings.debug and "dev-secret-key" or self._get_jwt_secret()
        )

    def _get_jwt_secret(self) -> str:
        """Get JWT secret from environment."""
        # In production, this should come from settings/env
        return settings.debug and "dev-secret-key" or "CHANGE-ME-IN-PRODUCTION"

    def hash_password(self, password: str) -> str:
        """Hash password using bcrypt."""
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
        return hashed.decode("utf-8")

    def verify_password(self, password: str, hashed_password: str) -> bool:
        """Verify password against hashed password."""
        return bcrypt.checkpw(
            password.encode("utf-8"),
            hashed_password.encode("utf-8")
        )

    def generate_access_token(self, user_id: str, role: UserRole) -> str:
        """Generate JWT access token."""
        expire = datetime.utcnow() + timedelta(
            minutes=self.config.access_token_expire_minutes
        )
        payload = {
            "sub": user_id,
            "role": role,
            "type": "access",
            "exp": expire,
            "iat": datetime.utcnow()
        }
        return jwt.encode(payload, self.config.jwt_secret, algorithm=self.config.jwt_algorithm)

    def generate_refresh_token(self, user_id: str) -> str:
        """Generate JWT refresh token."""
        expire = datetime.utcnow() + timedelta(
            days=self.config.refresh_token_expire_days
        )
        payload = {
            "sub": user_id,
            "type": "refresh",
            "exp": expire,
            "iat": datetime.utcnow()
        }
        return jwt.encode(payload, self.config.jwt_secret, algorithm=self.config.jwt_algorithm)

    def verify_token(self, token: str) -> Optional[dict]:
        """Verify and decode JWT token."""
        try:
            payload = jwt.decode(
                token,
                self.config.jwt_secret,
                algorithms=[self.config.jwt_algorithm]
            )
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None

    def create_user(self, user_create: UserCreate) -> User:
        """Create a new user."""
        # Check if email already exists
        for user in self.users.values():
            if user.email == user_create.email:
                raise ValueError("Email already registered")

        user_id = str(uuid4())
        hashed_password = self.hash_password(user_create.password)

        user = User(
            id=user_id,
            email=user_create.email,
            name=user_create.name,
            role=user_create.role or UserRole.student,
            hashed_password=hashed_password
        )
        self.users[user_id] = user
        return user

    def authenticate_user(self, user_login: UserLogin) -> Optional[User]:
        """Authenticate user with email and password."""
        for user in self.users.values():
            if user.email == user_login.email:
                if self.verify_password(user_login.password, user.hashed_password):
                    if user.is_active:
                        return user
        return None

    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID."""
        return self.users.get(user_id)

    def get_user_response(self, user: User) -> UserResponse:
        """Convert User to UserResponse (no sensitive data)."""
        return UserResponse(
            id=user.id,
            email=user.email,
            name=user.name,
            role=user.role,
            created_at=user.created_at,
            is_active=user.is_active
        )

    def generate_token_response(self, user: User) -> TokenResponse:
        """Generate token response for authenticated user."""
        access_token = self.generate_access_token(user.id, user.role)
        refresh_token = self.generate_refresh_token(user.id)
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=self.config.access_token_expire_minutes * 60
        )


# Global auth service instance
auth_service = AuthService()