"""User schemas."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr
from ..models.user import UserRole


class UserBase(BaseModel):
    """Base user schema."""
    email: EmailStr
    role: UserRole = UserRole.STUDENT
    is_active: bool = True


class UserCreate(UserBase):
    """User creation schema."""
    password: str
    org_id: int


class UserUpdate(BaseModel):
    """User update schema."""
    email: Optional[EmailStr] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None


class UserResponse(UserBase):
    """User response schema."""
    user_id: int
    org_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True
