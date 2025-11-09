from pydantic import BaseModel, Field
from typing import Optional, Union
from datetime import date, time

class LessonBase(BaseModel):
    org_id: int
    date: date
    slot_id: int
    room_id: int
    enrollment_id: int
    status: str = "scheduled"

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
    
    model_config = {"from_attributes": True, "arbitrary_types_allowed": True}

class LessonResponse(LessonBase):
    lesson_id: int
    group_name: str
    teacher_name: str
    course_name: str
    room_number: str
    start_time: str
    end_time: str

    class Config:
        from_attributes = True
