"""Authentication schemas."""

from pydantic import BaseModel, EmailStr
from .user import UserRole


class LoginRequest(BaseModel):
    """Login request schema."""
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    """Login response schema."""
    access_token: str
    token_type: str = "bearer"
    user: "UserInfo"


class RegisterRequest(BaseModel):
    """Registration request schema."""
    email: EmailStr
    password: str
    organization_name: str
    locale: str = "ru"
    tz: str = "Europe/Moscow"


class UserInfo(BaseModel):
    """User info schema."""
    user_id: int
    email: str
    role: UserRole
    org_id: int
    is_active: bool
    
    class Config:
        from_attributes = True


# Avoid circular import
LoginResponse.model_rebuild()
