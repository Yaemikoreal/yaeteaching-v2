"""Authentication API routes."""
from fastapi import APIRouter, HTTPException, Depends, Header
from typing import Optional
from models.user import (
    UserCreate, UserLogin, UserResponse, TokenResponse, UserRole
)
from services.auth import auth_service

auth_router = APIRouter(prefix="/auth", tags=["authentication"])


def get_current_user(authorization: Optional[str] = Header(None)) -> UserResponse:
    """Dependency to get current authenticated user from JWT token."""
    if not authorization:
        raise HTTPException(status_code=401, detail="Not authenticated")

    # Extract token from "Bearer <token>" format
    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise HTTPException(status_code=401, detail="Invalid authentication scheme")
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid authorization header format")

    payload = auth_service.verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    user = auth_service.get_user_by_id(payload["sub"])
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    if not user.is_active:
        raise HTTPException(status_code=401, detail="User is inactive")

    return auth_service.get_user_response(user)


def require_role(required_role: UserRole):
    """Dependency factory to require specific role."""
    def role_checker(user: UserResponse = Depends(get_current_user)) -> UserResponse:
        if user.role != required_role and user.role != UserRole.admin:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return user
    return role_checker


@auth_router.post("/register", response_model=TokenResponse)
async def register(user_create: UserCreate):
    """Register a new user and return authentication tokens."""
    try:
        user = auth_service.create_user(user_create)
        return auth_service.generate_token_response(user)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@auth_router.post("/login", response_model=TokenResponse)
async def login(user_login: UserLogin):
    """Login with email and password, return authentication tokens."""
    user = auth_service.authenticate_user(user_login)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    return auth_service.generate_token_response(user)


@auth_router.post("/logout")
async def logout(user: UserResponse = Depends(get_current_user)):
    """Logout current user (token invalidation handled client-side for JWT)."""
    # JWT tokens cannot be invalidated server-side without additional storage
    # In production, use Redis to blacklist tokens or use shorter expiry
    return {"message": "Logged out successfully"}


@auth_router.get("/me", response_model=UserResponse)
async def get_me(user: UserResponse = Depends(get_current_user)):
    """Get current authenticated user info."""
    return user


@auth_router.post("/refresh", response_model=TokenResponse)
async def refresh_token(authorization: Optional[str] = Header(None)):
    """Refresh access token using refresh token."""
    if not authorization:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise HTTPException(status_code=401, detail="Invalid authentication scheme")
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid authorization header format")

    payload = auth_service.verify_token(token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    user = auth_service.get_user_by_id(payload["sub"])
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")

    return auth_service.generate_token_response(user)