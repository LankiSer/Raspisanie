from pydantic import BaseModel, Field, field_validator
from typing import Optional, Union
from datetime import date, time
from ..models.scheduling import LessonStatus

class LessonBase(BaseModel):
    org_id: int
    date: date
    slot_id: int
    room_id: Optional[int] = None
    enrollment_id: int
    status: str = "PLANNED"
    
    @field_validator('status', mode='before')
    @classmethod
    def validate_status(cls, v):
        if v is None:
            return "PLANNED"
        if isinstance(v, str):
            # Convert lowercase to uppercase
            v = v.upper()
            # Validate against enum values
            valid_statuses = [e.value for e in LessonStatus]
            if v not in valid_statuses:
                raise ValueError(f"Invalid status. Must be one of: {valid_statuses}")
            return v
        return v

class LessonCreate(LessonBase):
    pass

class LessonUpdate(BaseModel):
    date: Optional[date] = Field(None, description="Lesson date")
    slot_id: Optional[int] = Field(None, description="Time slot ID")
    room_id: Optional[int] = Field(None, description="Room ID")
    enrollment_id: Optional[int] = Field(None, description="Enrollment ID")
    status: Optional[str] = Field(None, description="Lesson status")
    reason: Optional[str] = Field(None, description="Reason for status change")
    version: Optional[int] = Field(None, description="Version for optimistic locking")
    
    @field_validator('status', mode='before')
    @classmethod
    def validate_status(cls, v):
        if v is None:
            return None
        if isinstance(v, str):
            # Convert lowercase to uppercase
            v = v.upper()
            # Validate against enum values
            valid_statuses = [e.value for e in LessonStatus]
            if v not in valid_statuses:
                raise ValueError(f"Invalid status. Must be one of: {valid_statuses}")
            return v
        return v
    
    model_config = {"from_attributes": True, "arbitrary_types_allowed": True}

class LessonResponse(BaseModel):
    lesson_id: int
    org_id: int
    date: str
    slot_id: int
    room_id: Optional[int]
    enrollment_id: int
    status: str
    group_name: str
    teacher_name: str
    course_name: str
    room_number: str
    start_time: str
    end_time: str
    
    @field_validator('status', mode='after')
    @classmethod
    def convert_status_to_lowercase(cls, v):
        """Convert status to lowercase for frontend compatibility"""
        if isinstance(v, str):
            return v.lower()
        return v

    class Config:
        from_attributes = True
