"""Scheduling schemas."""

from datetime import datetime, date
from typing import Optional, List
from pydantic import BaseModel
from ..models.scheduling import LessonStatus, GenerationStatus, GenerationScope


# Lesson instance schemas
class LessonInstanceBase(BaseModel):
    """Base lesson instance schema."""
    date: date
    slot_id: int
    room_id: Optional[int] = None
    status: LessonStatus = LessonStatus.PLANNED
    reason: Optional[str] = None


class LessonInstanceCreate(LessonInstanceBase):
    """Lesson instance creation schema."""
    org_id: int
    term_id: int
    enrollment_id: int


class LessonInstanceUpdate(BaseModel):
    """Lesson instance update schema."""
    date: Optional[date] = None
    slot_id: Optional[int] = None
    room_id: Optional[int] = None
    status: Optional[LessonStatus] = None
    reason: Optional[str] = None
    version: int  # for optimistic locking


class LessonInstanceResponse(LessonInstanceBase):
    """Lesson instance response schema."""
    lesson_id: int
    org_id: int
    term_id: int
    enrollment_id: int
    created_by: int
    created_at: datetime
    updated_by: Optional[int] = None
    updated_at: Optional[datetime] = None
    version: int
    
    # Related data (optional, loaded based on context)
    enrollment: Optional["EnrollmentResponse"] = None
    room: Optional["RoomResponse"] = None
    time_slot: Optional["TimeSlotResponse"] = None
    
    class Config:
        from_attributes = True


# Generation job schemas
class GenerationJobCreate(BaseModel):
    """Generation job creation schema."""
    org_id: int
    term_id: int
    scope: GenerationScope
    from_date: date
    to_date: date
    ruleset_json: dict


class GenerationJobResponse(BaseModel):
    """Generation job response schema."""
    job_id: int
    org_id: int
    term_id: int
    scope: GenerationScope
    from_date: date
    to_date: date
    ruleset_json: dict
    status: GenerationStatus
    progress: float
    created_by: int
    created_at: datetime
    finished_at: Optional[datetime] = None
    error: Optional[str] = None
    result_json: Optional[dict] = None
    
    class Config:
        from_attributes = True


# Conflict response
class LessonConflictResponse(BaseModel):
    """Lesson conflict response schema."""
    conflicts: List[str]
    can_proceed: bool
