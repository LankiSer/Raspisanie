"""Facilities router with real database operations."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert, update, delete
from pydantic import BaseModel
from datetime import date, time

from app.core.database import get_db
from app.core.auth import get_current_active_user_or_demo
from app.models.facilities import Room, TimeTableSlot, TeacherAvailability, Holiday
from app.models.user import User

router = APIRouter()

# Room response models
class RoomResponse(BaseModel):
    room_id: int
    org_id: int
    number: str
    capacity: int
    kind: str
    building: Optional[str] = None
    is_active: bool = True

class RoomCreate(BaseModel):
    number: str
    capacity: int
    kind: str
    building: Optional[str] = None
    is_active: bool = True

class RoomUpdate(BaseModel):
    number: Optional[str] = None
    capacity: Optional[int] = None
    kind: Optional[str] = None
    building: Optional[str] = None
    is_active: Optional[bool] = None

# Rooms endpoints
@router.get("/rooms", response_model=List[RoomResponse])
async def get_rooms(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user_or_demo)
):
    """Get rooms with pagination and search."""
    query = select(Room).where(Room.org_id == current_user.org_id)
    
    if search:
        query = query.where(Room.number.ilike(f"%{search}%"))
    
    query = query.offset(skip).limit(limit)
    
    result = await db.execute(query)
    rooms = result.scalars().all()
    
    return [
        RoomResponse(
            room_id=room.room_id,
            org_id=room.org_id,
            number=room.number,
            capacity=room.capacity,
            kind=room.kind,
            building=room.building,
            is_active=room.is_active
        )
        for room in rooms
    ]

@router.post("/rooms", response_model=RoomResponse)
async def create_room(
    room: RoomCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user_or_demo)
):
    """Create a new room."""
    # Check if room with same number already exists
    existing_room = await db.execute(
        select(Room).where(
            Room.org_id == current_user.org_id,
            Room.number == room.number
        )
    )
    if existing_room.scalar_one_or_none():
        raise HTTPException(
            status_code=400, 
            detail=f"Room with number '{room.number}' already exists in this organization"
        )
    
    new_room = Room(
        org_id=current_user.org_id,
        number=room.number,
        capacity=room.capacity,
        kind=room.kind,
        building=room.building,
        is_active=room.is_active
    )
    
    db.add(new_room)
    await db.commit()
    await db.refresh(new_room)
    
    return RoomResponse(
        room_id=new_room.room_id,
        org_id=new_room.org_id,
        number=new_room.number,
        capacity=new_room.capacity,
        kind=new_room.kind,
        building=new_room.building,
        is_active=new_room.is_active
    )

@router.patch("/rooms/{room_id}", response_model=RoomResponse)
async def update_room(
    room_id: int,
    room: RoomUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user_or_demo)
):
    """Update a room."""
    result = await db.execute(
        select(Room).where(
            Room.room_id == room_id,
            Room.org_id == current_user.org_id
        )
    )
    existing_room = result.scalar_one_or_none()
    
    if not existing_room:
        raise HTTPException(status_code=404, detail="Room not found")
    
    update_data = room.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(existing_room, field, value)
    
    await db.commit()
    await db.refresh(existing_room)
    
    return RoomResponse(
        room_id=existing_room.room_id,
        org_id=existing_room.org_id,
        number=existing_room.number,
        capacity=existing_room.capacity,
        kind=existing_room.kind,
        building=existing_room.building,
        is_active=existing_room.is_active
    )

@router.delete("/rooms/{room_id}")
async def delete_room(
    room_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user_or_demo)
):
    """Delete a room."""
    result = await db.execute(
        select(Room).where(
            Room.room_id == room_id,
            Room.org_id == current_user.org_id
        )
    )
    existing_room = result.scalar_one_or_none()
    
    if not existing_room:
        raise HTTPException(status_code=404, detail="Room not found")
    
    existing_room.is_active = False
    await db.commit()
    
    return {"message": "Room deleted successfully"}

# Time slot response models
class TimeSlotResponse(BaseModel):
    slot_id: int
    org_id: int
    start_time: time
    end_time: time
    break_minutes: int
    label: str
    weekday_mask: int

class TimeSlotCreate(BaseModel):
    start_time: time
    end_time: time
    break_minutes: int = 10
    label: str
    weekday_mask: int = 31

class TimeSlotUpdate(BaseModel):
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    break_minutes: Optional[int] = None
    label: Optional[str] = None
    weekday_mask: Optional[int] = None

# Time slots endpoints
@router.get("/slots", response_model=List[TimeSlotResponse])
async def get_time_slots(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user_or_demo)
):
    """Get time slots with pagination."""
    query = select(TimeTableSlot).where(TimeTableSlot.org_id == current_user.org_id)
    query = query.offset(skip).limit(limit)
    
    result = await db.execute(query)
    slots = result.scalars().all()
    
    return [
        TimeSlotResponse(
            slot_id=slot.slot_id,
            org_id=slot.org_id,
            start_time=slot.start_time,
            end_time=slot.end_time,
            break_minutes=slot.break_minutes,
            label=slot.label,
            weekday_mask=slot.weekday_mask
        )
        for slot in slots
    ]

@router.post("/slots", response_model=TimeSlotResponse)
async def create_time_slot(
    slot: TimeSlotCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user_or_demo)
):
    """Create a new time slot."""
    new_slot = TimeTableSlot(
        org_id=current_user.org_id,
        start_time=slot.start_time,
        end_time=slot.end_time,
        break_minutes=slot.break_minutes,
        label=slot.label,
        weekday_mask=slot.weekday_mask
    )
    
    db.add(new_slot)
    await db.commit()
    await db.refresh(new_slot)
    
    return TimeSlotResponse(
        slot_id=new_slot.slot_id,
        org_id=new_slot.org_id,
        start_time=new_slot.start_time,
        end_time=new_slot.end_time,
        break_minutes=new_slot.break_minutes,
        label=new_slot.label,
        weekday_mask=new_slot.weekday_mask
    )

@router.patch("/slots/{slot_id}", response_model=TimeSlotResponse)
async def update_time_slot(
    slot_id: int,
    slot: TimeSlotUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user_or_demo)
):
    """Update a time slot."""
    result = await db.execute(
        select(TimeTableSlot).where(
            TimeTableSlot.slot_id == slot_id,
            TimeTableSlot.org_id == current_user.org_id
        )
    )
    existing_slot = result.scalar_one_or_none()
    
    if not existing_slot:
        raise HTTPException(status_code=404, detail="Time slot not found")
    
    update_data = slot.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(existing_slot, field, value)
    
    await db.commit()
    await db.refresh(existing_slot)
    
    return TimeSlotResponse(
        slot_id=existing_slot.slot_id,
        org_id=existing_slot.org_id,
        start_time=existing_slot.start_time,
        end_time=existing_slot.end_time,
        break_minutes=existing_slot.break_minutes,
        label=existing_slot.label,
        weekday_mask=existing_slot.weekday_mask
    )

@router.delete("/slots/{slot_id}")
async def delete_time_slot(
    slot_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user_or_demo)
):
    """Delete a time slot."""
    result = await db.execute(
        select(TimeTableSlot).where(
            TimeTableSlot.slot_id == slot_id,
            TimeTableSlot.org_id == current_user.org_id
        )
    )
    existing_slot = result.scalar_one_or_none()
    
    if not existing_slot:
        raise HTTPException(status_code=404, detail="Time slot not found")
    
    await db.delete(existing_slot)
    await db.commit()
    
    return {"message": "Time slot deleted successfully"}

# Holiday response models
class HolidayResponse(BaseModel):
    holiday_id: int
    org_id: int
    date: date
    name: str

class HolidayCreate(BaseModel):
    org_id: int
    date: date
    name: str

# Holidays endpoints
@router.get("/holidays", response_model=List[HolidayResponse])
async def get_holidays(
    skip: int = 0,
    limit: int = 100,
    year: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user_or_demo)
):
    """Get holidays with pagination."""
    query = select(Holiday).where(Holiday.org_id == current_user.org_id)
    
    if year:
        query = query.where(Holiday.date >= date(year, 1, 1), Holiday.date <= date(year, 12, 31))
    
    query = query.offset(skip).limit(limit)
    
    result = await db.execute(query)
    holidays = result.scalars().all()
    
    return [
        HolidayResponse(
            holiday_id=holiday.holiday_id,
            org_id=holiday.org_id,
            date=holiday.date,
            name=holiday.name
        )
        for holiday in holidays
    ]

@router.post("/holidays", response_model=HolidayResponse)
async def create_holiday(
    holiday: HolidayCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user_or_demo)
):
    """Create a new holiday."""
    new_holiday = Holiday(
        org_id=holiday.org_id,
        date=holiday.date,
        name=holiday.name
    )
    
    db.add(new_holiday)
    await db.commit()
    await db.refresh(new_holiday)
    
    return HolidayResponse(
        holiday_id=new_holiday.holiday_id,
        org_id=new_holiday.org_id,
        date=new_holiday.date,
        name=new_holiday.name
    )

@router.delete("/holidays/{holiday_id}")
async def delete_holiday(
    holiday_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user_or_demo)
):
    """Delete a holiday."""
    result = await db.execute(
        select(Holiday).where(
            Holiday.holiday_id == holiday_id,
            Holiday.org_id == current_user.org_id
        )
    )
    existing_holiday = result.scalar_one_or_none()
    
    if not existing_holiday:
        raise HTTPException(status_code=404, detail="Holiday not found")
    
    await db.delete(existing_holiday)
    await db.commit()
    
    return {"message": "Holiday deleted successfully"}

# Teacher availability response models
class TeacherAvailabilityResponse(BaseModel):
    availability_id: int
    org_id: int
    teacher_id: int
    weekday: int
    start_time: time
    end_time: time
    is_available: bool = True

class TeacherAvailabilityCreate(BaseModel):
    org_id: int
    teacher_id: int
    weekday: int
    start_time: time
    end_time: time
    is_available: bool = True

class TeacherAvailabilityUpdate(BaseModel):
    weekday: Optional[int] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    is_available: Optional[bool] = None

# Teacher availability endpoints
@router.get("/teacher-availability", response_model=List[TeacherAvailabilityResponse])
async def get_teacher_availability(
    teacher_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user_or_demo)
):
    """Get teacher availability with pagination."""
    query = select(TeacherAvailability).where(TeacherAvailability.org_id == current_user.org_id)
    
    if teacher_id:
        query = query.where(TeacherAvailability.teacher_id == teacher_id)
    
    query = query.offset(skip).limit(limit)
    
    result = await db.execute(query)
    availabilities = result.scalars().all()
    
    return [
        TeacherAvailabilityResponse(
            availability_id=availability.availability_id,
            org_id=availability.org_id,
            teacher_id=availability.teacher_id,
            weekday=availability.weekday,
            start_time=availability.start_time,
            end_time=availability.end_time,
            is_available=availability.is_available
        )
        for availability in availabilities
    ]

@router.post("/teacher-availability", response_model=TeacherAvailabilityResponse)
async def create_teacher_availability(
    availability: TeacherAvailabilityCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user_or_demo)
):
    """Create a new teacher availability."""
    new_availability = TeacherAvailability(
        org_id=availability.org_id,
        teacher_id=availability.teacher_id,
        weekday=availability.weekday,
        start_time=availability.start_time,
        end_time=availability.end_time,
        is_available=availability.is_available
    )
    
    db.add(new_availability)
    await db.commit()
    await db.refresh(new_availability)
    
    return TeacherAvailabilityResponse(
        availability_id=new_availability.availability_id,
        org_id=new_availability.org_id,
        teacher_id=new_availability.teacher_id,
        weekday=new_availability.weekday,
        start_time=new_availability.start_time,
        end_time=new_availability.end_time,
        is_available=new_availability.is_available
    )

@router.patch("/teacher-availability/{availability_id}", response_model=TeacherAvailabilityResponse)
async def update_teacher_availability(
    availability_id: int,
    availability: TeacherAvailabilityUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user_or_demo)
):
    """Update teacher availability."""
    result = await db.execute(
        select(TeacherAvailability).where(
            TeacherAvailability.availability_id == availability_id,
            TeacherAvailability.org_id == current_user.org_id
        )
    )
    existing_availability = result.scalar_one_or_none()
    
    if not existing_availability:
        raise HTTPException(status_code=404, detail="Teacher availability not found")
    
    update_data = availability.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(existing_availability, field, value)
    
    await db.commit()
    await db.refresh(existing_availability)
    
    return TeacherAvailabilityResponse(
        availability_id=existing_availability.availability_id,
        org_id=existing_availability.org_id,
        teacher_id=existing_availability.teacher_id,
        weekday=existing_availability.weekday,
        start_time=existing_availability.start_time,
        end_time=existing_availability.end_time,
        is_available=existing_availability.is_available
    )

@router.delete("/teacher-availability/{availability_id}")
async def delete_teacher_availability(
    availability_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user_or_demo)
):
    """Delete teacher availability."""
    result = await db.execute(
        select(TeacherAvailability).where(
            TeacherAvailability.availability_id == availability_id,
            TeacherAvailability.org_id == current_user.org_id
        )
    )
    existing_availability = result.scalar_one_or_none()
    
    if not existing_availability:
        raise HTTPException(status_code=404, detail="Teacher availability not found")
    
    await db.delete(existing_availability)
    await db.commit()
    
    return {"message": "Teacher availability deleted successfully"}
