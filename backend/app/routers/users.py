"""Users router."""

from fastapi import APIRouter, Depends
from ..core.auth import get_current_active_user

router = APIRouter()

@router.get("/")
async def get_users(current_user = Depends(get_current_active_user)):
    return {"message": "Users endpoint - TODO"}
