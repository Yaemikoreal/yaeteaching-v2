"""User model and authentication schemas."""
from pydantic import BaseModel, Field, EmailStr
from typing import Optional
from datetime import datetime
from enum import Enum


class UserRole(str, Enum):
    """User roles for permission control."""

    student = "student"
    teacher = "teacher"
    admin = "admin"


class User(BaseModel):
    """User data model."""

    id: str = Field(..., description="User unique ID")
    email: EmailStr = Field(..., description="User email")
    name: str = Field(..., description="User display name")
    role: UserRole = Field(default=UserRole.student, description="User role")
    hashed_password: str = Field(..., description="Hashed password (bcrypt)")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = Field(default=True, description="User active status")


class UserCreate(BaseModel):
    """Request model for user registration."""

    email: EmailStr = Field(..., description="Email address")
    password: str = Field(..., min_length=8, max_length=128, description="Password (8-128 chars)")
    name: str = Field(..., min_length=2, max_length=50, description="Display name")
    role: Optional[UserRole] = Field(default=UserRole.student, description="User role")


class UserLogin(BaseModel):
    """Request model for user login."""

    email: EmailStr = Field(..., description="Email address")
    password: str = Field(..., description="Password")


class UserResponse(BaseModel):
    """Response model for user info (no sensitive data)."""

    id: str
    email: EmailStr
    name: str
    role: UserRole
    created_at: datetime
    is_active: bool


class TokenResponse(BaseModel):
    """Response model for JWT token."""

    access_token: str = Field(..., description="JWT access token")
    refresh_token: Optional[str] = Field(None, description="JWT refresh token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(default=3600, description="Token expiry in seconds")


class AuthConfig(BaseModel):
    """Authentication configuration."""

    jwt_secret: str = Field(default="change-me-in-production", description="JWT secret key")
    jwt_algorithm: str = Field(default="HS256", description="JWT algorithm")
    access_token_expire_minutes: int = Field(default=60, description="Access token expiry")
    refresh_token_expire_days: int = Field(default=7, description="Refresh token expiry")