"""Organization repository."""

from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from .base import BaseRepository
from ..models.organization import Organization


class OrganizationRepository(BaseRepository[Organization]):
    """Organization repository."""
    
    def __init__(self, db: AsyncSession):
        super().__init__(db, Organization)
    
    async def get_by_id(self, org_id: int) -> Optional[Organization]:
        """Get organization by ID."""
        result = await self.db.execute(
            select(Organization).where(Organization.org_id == org_id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_name(self, name: str) -> Optional[Organization]:
        """Get organization by name."""
        result = await self.db.execute(
            select(Organization).where(Organization.name == name)
        )
        return result.scalar_one_or_none()
