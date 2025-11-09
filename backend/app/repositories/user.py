"""User repository."""

from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from .base import BaseRepository
from ..models.user import User


class UserRepository(BaseRepository[User]):
    """User repository."""
    
    def __init__(self, db: AsyncSession):
        super().__init__(db, User)
    
    async def get_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID."""
        result = await self.db.execute(
            select(User).where(User.user_id == user_id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        result = await self.db.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()
    
    async def get_by_org(self, org_id: int, skip: int = 0, limit: int = 100) -> list[User]:
        """Get users by organization."""
        result = await self.db.execute(
            select(User)
            .where(User.org_id == org_id)
            .offset(skip)
            .limit(limit)
            .order_by(User.created_at.desc())
        )
        return result.scalars().all()
