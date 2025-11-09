"""Organization schemas."""

from datetime import datetime
from pydantic import BaseModel


class OrganizationBase(BaseModel):
    """Base organization schema."""
    name: str
    locale: str = "ru"
    tz: str = "Europe/Moscow"


class OrganizationCreate(OrganizationBase):
    """Organization creation schema."""
    pass


class OrganizationResponse(OrganizationBase):
    """Organization response schema."""
    org_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True
