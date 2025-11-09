"""Reports router."""

from fastapi import APIRouter, Depends
from ..core.auth import get_current_active_user

router = APIRouter()

@router.get("/workload/teacher")
async def get_teacher_workload(current_user = Depends(get_current_active_user)):
    return {"message": "Teacher workload report - TODO"}

@router.get("/workload/group")
async def get_group_workload(current_user = Depends(get_current_active_user)):
    return {"message": "Group workload report - TODO"}

@router.get("/conflicts")
async def get_conflicts(current_user = Depends(get_current_active_user)):
    return {"message": "Conflicts report - TODO"}
