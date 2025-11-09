"""Scheduling router for lesson management."""

from datetime import date
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.database import get_db
from ..core.auth import get_current_active_user, require_role
from ..repositories.lesson import LessonRepository
from ..models.user import User, UserRole
from ..schemas.scheduling import (
    LessonInstanceCreate, LessonInstanceUpdate, LessonInstanceResponse,
    LessonConflictResponse
)

router = APIRouter()


@router.get("/day", response_model=List[LessonInstanceResponse])
async def get_lessons_by_day(
    date: date,
    group_id: Optional[int] = None,
    teacher_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get lessons for a specific day."""
    lesson_repo = LessonRepository(db)
    lessons = await lesson_repo.get_by_day(
        org_id=current_user.org_id,
        date=date,
        group_id=group_id,
        teacher_id=teacher_id
    )
    return lessons


@router.get("/term", response_model=List[LessonInstanceResponse])
async def get_lessons_by_term(
    term_id: int,
    start_date: date,
    end_date: date,
    group_id: Optional[int] = None,
    teacher_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get lessons for a date range."""
    lesson_repo = LessonRepository(db)
    lessons = await lesson_repo.get_by_date_range(
        org_id=current_user.org_id,
        start_date=start_date,
        end_date=end_date,
        group_id=group_id,
        teacher_id=teacher_id
    )
    return lessons


@router.post("/", response_model=LessonInstanceResponse)
async def create_lesson(
    lesson: LessonInstanceCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.METHODIST]))
):
    """Create a new lesson."""
    # Check for conflicts
    lesson_repo = LessonRepository(db)
    conflicts = await lesson_repo.check_conflicts(
        org_id=current_user.org_id,
        date=lesson.date,
        slot_id=lesson.slot_id,
        enrollment_id=lesson.enrollment_id,
        room_id=lesson.room_id
    )
    
    if conflicts:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"conflicts": conflicts}
        )
    
    # Create lesson
    lesson_data = lesson.dict()
    lesson_data["created_by"] = current_user.user_id
    
    try:
        new_lesson = await lesson_repo.create(lesson_data)
        return await lesson_repo.get_by_id(new_lesson.lesson_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create lesson"
        )


@router.patch("/{lesson_id}", response_model=LessonInstanceResponse)
async def update_lesson(
    lesson_id: int,
    lesson_update: LessonInstanceUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.METHODIST]))
):
    """Update a lesson with optimistic locking."""
    lesson_repo = LessonRepository(db)
    
    # Get existing lesson
    existing_lesson = await lesson_repo.get_by_id(lesson_id)
    if not existing_lesson:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lesson not found"
        )
    
    # Check version for optimistic locking
    if existing_lesson.version != lesson_update.version:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Lesson has been modified by another user"
        )
    
    # Check for conflicts if position is changing
    if (lesson_update.date or lesson_update.slot_id or lesson_update.room_id):
        new_date = lesson_update.date or existing_lesson.date
        new_slot_id = lesson_update.slot_id or existing_lesson.slot_id
        new_room_id = lesson_update.room_id or existing_lesson.room_id
        
        conflicts = await lesson_repo.check_conflicts(
            org_id=current_user.org_id,
            date=new_date,
            slot_id=new_slot_id,
            enrollment_id=existing_lesson.enrollment_id,
            room_id=new_room_id,
            exclude_lesson_id=lesson_id
        )
        
        if conflicts:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={"conflicts": conflicts}
            )
    
    # Update lesson
    update_data = lesson_update.dict(exclude_unset=True, exclude={"version"})
    update_data["updated_by"] = current_user.user_id
    update_data["version"] = existing_lesson.version + 1
    
    try:
        updated_lesson = await lesson_repo.update(existing_lesson, update_data)
        return await lesson_repo.get_by_id(updated_lesson.lesson_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update lesson"
        )


@router.delete("/{lesson_id}")
async def delete_lesson(
    lesson_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.METHODIST]))
):
    """Delete a lesson."""
    lesson_repo = LessonRepository(db)
    
    success = await lesson_repo.delete(lesson_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lesson not found"
        )
    
    return {"message": "Lesson deleted successfully"}


@router.post("/check-conflicts", response_model=LessonConflictResponse)
async def check_lesson_conflicts(
    lesson: LessonInstanceCreate,
    lesson_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Check for scheduling conflicts."""
    lesson_repo = LessonRepository(db)
    
    conflicts = await lesson_repo.check_conflicts(
        org_id=current_user.org_id,
        date=lesson.date,
        slot_id=lesson.slot_id,
        enrollment_id=lesson.enrollment_id,
        room_id=lesson.room_id,
        exclude_lesson_id=lesson_id
    )
    
    return LessonConflictResponse(
        conflicts=conflicts,
        can_proceed=len(conflicts) == 0
    )
