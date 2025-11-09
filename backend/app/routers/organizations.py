"""Organizations router."""

from fastapi import APIRouter, Depends
from ..core.auth import require_role
from ..models.user import UserRole

router = APIRouter()

@router.get("/")
async def get_organizations(
    current_user = Depends(require_role([UserRole.SUPERADMIN]))
):
    """Get all organizations (superadmin only)."""
    return {"message": "Organizations endpoint - TODO"}
