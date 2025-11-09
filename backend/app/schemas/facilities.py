"""Facilities and infrastructure schemas."""

from datetime import time, date
from typing import Optional
from pydantic import BaseModel


# Room schemas
class RoomBase(BaseModel):
    """Base room schema."""
    number: str
    capacity: int = 30
    kind: Optional[str] = None
    building: Optional[str] = None
    is_active: bool = True


class RoomCreate(RoomBase):
    """Room creation schema."""
    org_id: int


class RoomUpdate(BaseModel):
    """Room update schema."""
    number: Optional[str] = None
    capacity: Optional[int] = None
    kind: Optional[str] = None
    building: Optional[str] = None
    is_active: Optional[bool] = None


class RoomResponse(RoomBase):
    """Room response schema."""
    room_id: int
    org_id: int
    
    class Config:
        from_attributes = True


# Time slot schemas
class TimeSlotBase(BaseModel):
    """Base time slot schema."""
    start_time: time
    end_time: time
    break_minutes: int = 10
    label: Optional[str] = None
    weekday_mask: int = 31  # Monday-Friday


class TimeSlotCreate(TimeSlotBase):
    """Time slot creation schema."""
    org_id: int


class TimeSlotUpdate(BaseModel):
    """Time slot update schema."""
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    break_minutes: Optional[int] = None
    label: Optional[str] = None
    weekday_mask: Optional[int] = None


class TimeSlotResponse(TimeSlotBase):
    """Time slot response schema."""
    slot_id: int
    org_id: int
    
    class Config:
        from_attributes = True


# Teacher availability schemas
class TeacherAvailabilityBase(BaseModel):
    """Base teacher availability schema."""
    weekday: int  # 1=Monday, 7=Sunday
    start_time: time
    end_time: time
    is_available: bool = True


class TeacherAvailabilityCreate(TeacherAvailabilityBase):
    """Teacher availability creation schema."""
    org_id: int
    teacher_id: int


class TeacherAvailabilityUpdate(BaseModel):
    """Teacher availability update schema."""
    weekday: Optional[int] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    is_available: Optional[bool] = None


class TeacherAvailabilityResponse(TeacherAvailabilityBase):
    """Teacher availability response schema."""
    availability_id: int
    org_id: int
    teacher_id: int
    
    class Config:
        from_attributes = True


# Holiday schemas
class HolidayCreate(BaseModel):
    """Holiday creation schema."""
    org_id: int
    date: date
    name: str


class HolidayResponse(BaseModel):
    """Holiday response schema."""
    holiday_id: int
    org_id: int
    date: date
    name: str
    
    class Config:
        from_attributes = True
