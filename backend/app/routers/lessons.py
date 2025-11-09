from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional
from datetime import date, time

from app.core.database import get_db
from app.core.auth import get_current_active_user_or_demo
from app.models.scheduling import LessonInstance, LessonStatus
from app.models.facilities import TimeTableSlot, Room
from app.models.educational import Enrollment, Group, Teacher, Course, CourseAssignment
from app.schemas.lessons import LessonCreate, LessonUpdate, LessonResponse
from app.models.user import User

router = APIRouter()

@router.get("/term", response_model=List[LessonResponse])
async def get_lessons_by_term(
    start_date: date = Query(...),
    end_date: date = Query(...),
    group_id: Optional[int] = Query(None),
    teacher_id: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user_or_demo)
):
    """Get lessons for a specific term/date range."""
    # Query lessons with joins to get related data
    query = select(
        LessonInstance.lesson_id,
        LessonInstance.org_id,
        LessonInstance.date,
        LessonInstance.slot_id,
        LessonInstance.room_id,
        LessonInstance.enrollment_id,
        LessonInstance.status,
        Group.name.label('group_name'),
        func.concat(Teacher.first_name, ' ', Teacher.last_name).label('teacher_name'),
        Course.name.label('course_name'),
        Room.number.label('room_number'),
        TimeTableSlot.start_time,
        TimeTableSlot.end_time
    ).select_from(
        LessonInstance
    ).join(Enrollment, LessonInstance.enrollment_id == Enrollment.enrollment_id
    ).join(CourseAssignment, Enrollment.assignment_id == CourseAssignment.assignment_id
    ).join(Group, Enrollment.group_id == Group.group_id
    ).join(Teacher, CourseAssignment.teacher_id == Teacher.teacher_id
    ).join(Course, CourseAssignment.course_id == Course.course_id
    ).join(Room, LessonInstance.room_id == Room.room_id
    ).join(TimeTableSlot, LessonInstance.slot_id == TimeTableSlot.slot_id
    ).where(
        LessonInstance.org_id == current_user.org_id,
        LessonInstance.date >= start_date,
        LessonInstance.date <= end_date,
        LessonInstance.status != LessonStatus.CANCELLED
    )
    
    # Apply filters
    if group_id:
        query = query.where(Enrollment.group_id == group_id)
    if teacher_id:
        query = query.where(CourseAssignment.teacher_id == teacher_id)
    
    query = query.order_by(LessonInstance.date, TimeTableSlot.start_time)
    
    result = await db.execute(query)
    lessons = result.all()
    
    return [
        {
            "lesson_id": lesson.lesson_id,
            "org_id": lesson.org_id,
            "date": str(lesson.date),
            "slot_id": lesson.slot_id,
            "room_id": lesson.room_id,
            "enrollment_id": lesson.enrollment_id,
            "group_name": lesson.group_name,
            "teacher_name": lesson.teacher_name,
            "course_name": lesson.course_name,
            "room_number": lesson.room_number,
            "start_time": str(lesson.start_time),
            "end_time": str(lesson.end_time),
            "status": lesson.status
        }
        for lesson in lessons
    ]

@router.get("/by-date/{lesson_date}", response_model=List[LessonResponse])
async def get_lessons_by_day(
    lesson_date: date,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user_or_demo)
):
    """Get lessons for a specific day."""
    # Query lessons with joins to get related data
    query = select(
        LessonInstance.lesson_id,
        LessonInstance.org_id,
        LessonInstance.date,
        LessonInstance.slot_id,
        LessonInstance.room_id,
        LessonInstance.enrollment_id,
        LessonInstance.status,
        Group.name.label('group_name'),
        func.concat(Teacher.first_name, ' ', Teacher.last_name).label('teacher_name'),
        Course.name.label('course_name'),
        Room.number.label('room_number'),
        TimeTableSlot.start_time,
        TimeTableSlot.end_time
    ).select_from(
        LessonInstance
    ).join(Enrollment, LessonInstance.enrollment_id == Enrollment.enrollment_id
    ).join(CourseAssignment, Enrollment.assignment_id == CourseAssignment.assignment_id
    ).join(Group, Enrollment.group_id == Group.group_id
    ).join(Teacher, CourseAssignment.teacher_id == Teacher.teacher_id
    ).join(Course, CourseAssignment.course_id == Course.course_id
    ).join(Room, LessonInstance.room_id == Room.room_id
    ).join(TimeTableSlot, LessonInstance.slot_id == TimeTableSlot.slot_id
    ).where(
        LessonInstance.org_id == current_user.org_id,
        LessonInstance.date == lesson_date,
        LessonInstance.status != LessonStatus.CANCELLED
    ).order_by(TimeTableSlot.start_time)
    
    result = await db.execute(query)
    lessons = result.all()
    
    return [
        {
            "lesson_id": lesson.lesson_id,
            "org_id": lesson.org_id,
            "date": str(lesson.date),
            "slot_id": lesson.slot_id,
            "room_id": lesson.room_id,
            "enrollment_id": lesson.enrollment_id,
            "group_name": lesson.group_name,
            "teacher_name": lesson.teacher_name,
            "course_name": lesson.course_name,
            "room_number": lesson.room_number,
            "start_time": str(lesson.start_time),
            "end_time": str(lesson.end_time),
            "status": lesson.status
        }
        for lesson in lessons
    ]

@router.get("/", response_model=List[LessonResponse])
async def get_lessons(
    date: Optional[date] = None,
    group_id: Optional[int] = None,
    teacher_id: Optional[int] = None,
    room_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user_or_demo)
):
    """Get lessons with optional filters."""
    # Query lessons with joins to get related data
    query = select(
        LessonInstance.lesson_id,
        LessonInstance.org_id,
        LessonInstance.date,
        LessonInstance.slot_id,
        LessonInstance.room_id,
        LessonInstance.enrollment_id,
        LessonInstance.status,
        Group.name.label('group_name'),
        func.concat(Teacher.first_name, ' ', Teacher.last_name).label('teacher_name'),
        Course.name.label('course_name'),
        Room.number.label('room_number'),
        TimeTableSlot.start_time,
        TimeTableSlot.end_time
    ).select_from(
        LessonInstance
    ).join(Enrollment, LessonInstance.enrollment_id == Enrollment.enrollment_id
    ).join(CourseAssignment, Enrollment.assignment_id == CourseAssignment.assignment_id
    ).join(Group, Enrollment.group_id == Group.group_id
    ).join(Teacher, CourseAssignment.teacher_id == Teacher.teacher_id
    ).join(Course, CourseAssignment.course_id == Course.course_id
    ).join(Room, LessonInstance.room_id == Room.room_id
    ).join(TimeTableSlot, LessonInstance.slot_id == TimeTableSlot.slot_id
    ).where(
        LessonInstance.org_id == current_user.org_id,
        LessonInstance.status != LessonStatus.CANCELLED
    )
    
    # Apply filters
    if date:
        query = query.where(LessonInstance.date == date)
    if group_id:
        query = query.where(Enrollment.group_id == group_id)
    if teacher_id:
        query = query.where(CourseAssignment.teacher_id == teacher_id)
    if room_id:
        query = query.where(LessonInstance.room_id == room_id)
    
    query = query.order_by(LessonInstance.date, TimeTableSlot.start_time)
    
    result = await db.execute(query)
    lessons = result.all()
    
    return [
        {
            "lesson_id": lesson.lesson_id,
            "org_id": lesson.org_id,
            "date": str(lesson.date),
            "slot_id": lesson.slot_id,
            "room_id": lesson.room_id,
            "enrollment_id": lesson.enrollment_id,
            "group_name": lesson.group_name,
            "teacher_name": lesson.teacher_name,
            "course_name": lesson.course_name,
            "room_number": lesson.room_number,
            "start_time": str(lesson.start_time),
            "end_time": str(lesson.end_time),
            "status": lesson.status
        }
        for lesson in lessons
    ]

@router.post("/", response_model=LessonResponse)
async def create_lesson(
    lesson: LessonCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user_or_demo)
):
    """Create a new lesson."""
    # Create new lesson
    new_lesson = LessonInstance(
        org_id=lesson.org_id,
        date=lesson.date,
        slot_id=lesson.slot_id,
        room_id=lesson.room_id,
        enrollment_id=lesson.enrollment_id,
        status=lesson.status or "scheduled"
    )
    
    db.add(new_lesson)
    await db.commit()
    await db.refresh(new_lesson)
    
    # Get related data for response
    query = select(
        Group.name.label('group_name'),
        func.concat(Teacher.first_name, ' ', Teacher.last_name).label('teacher_name'),
        Course.name.label('course_name'),
        Room.number.label('room_number'),
        TimeTableSlot.start_time,
        TimeTableSlot.end_time
    ).select_from(
        LessonInstance
    ).join(Enrollment, LessonInstance.enrollment_id == Enrollment.enrollment_id
    ).join(CourseAssignment, Enrollment.assignment_id == CourseAssignment.assignment_id
    ).join(Group, Enrollment.group_id == Group.group_id
    ).join(Teacher, CourseAssignment.teacher_id == Teacher.teacher_id
    ).join(Course, CourseAssignment.course_id == Course.course_id
    ).join(Room, LessonInstance.room_id == Room.room_id
    ).join(TimeTableSlot, LessonInstance.slot_id == TimeTableSlot.slot_id
    ).where(LessonInstance.lesson_id == new_lesson.lesson_id)
    
    result = await db.execute(query)
    lesson_data = result.first()
    
    return {
        "lesson_id": new_lesson.lesson_id,
        "org_id": new_lesson.org_id,
        "date": str(new_lesson.date),
        "slot_id": new_lesson.slot_id,
        "room_id": new_lesson.room_id,
        "enrollment_id": new_lesson.enrollment_id,
        "group_name": lesson_data.group_name,
        "teacher_name": lesson_data.teacher_name,
        "course_name": lesson_data.course_name,
        "room_number": lesson_data.room_number,
        "start_time": str(lesson_data.start_time),
        "end_time": str(lesson_data.end_time),
        "status": new_lesson.status
    }

@router.post("/bulk", response_model=dict)
async def create_lessons_bulk(
    lessons: List[LessonCreate],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user_or_demo)
):
    """Create multiple lessons at once."""
    created_lessons = []
    
    for lesson_data in lessons:
        new_lesson = LessonInstance(
            org_id=lesson_data.org_id,
            date=lesson_data.date,
            slot_id=lesson_data.slot_id,
            room_id=lesson_data.room_id,
            enrollment_id=lesson_data.enrollment_id,
            status=lesson_data.status or "scheduled"
        )
        db.add(new_lesson)
        created_lessons.append(new_lesson)
    
    await db.commit()
    
    return {
        "message": f"Created {len(lessons)} lessons",
        "created_count": len(lessons)
    }

@router.get("/{lesson_id}", response_model=LessonResponse)
async def get_lesson(
    lesson_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user_or_demo)
):
    """Get a specific lesson."""
    query = select(
        LessonInstance.lesson_id,
        LessonInstance.org_id,
        LessonInstance.date,
        LessonInstance.slot_id,
        LessonInstance.room_id,
        LessonInstance.enrollment_id,
        LessonInstance.status,
        Group.name.label('group_name'),
        func.concat(Teacher.first_name, ' ', Teacher.last_name).label('teacher_name'),
        Course.name.label('course_name'),
        Room.number.label('room_number'),
        TimeTableSlot.start_time,
        TimeTableSlot.end_time
    ).select_from(
        LessonInstance
    ).join(Enrollment, LessonInstance.enrollment_id == Enrollment.enrollment_id
    ).join(CourseAssignment, Enrollment.assignment_id == CourseAssignment.assignment_id
    ).join(Group, Enrollment.group_id == Group.group_id
    ).join(Teacher, CourseAssignment.teacher_id == Teacher.teacher_id
    ).join(Course, CourseAssignment.course_id == Course.course_id
    ).join(Room, LessonInstance.room_id == Room.room_id
    ).join(TimeTableSlot, LessonInstance.slot_id == TimeTableSlot.slot_id
    ).where(
        LessonInstance.lesson_id == lesson_id,
        LessonInstance.org_id == current_user.org_id
    )
    
    result = await db.execute(query)
    lesson = result.first()
    
    if not lesson:
        raise HTTPException(status_code=404, detail="LessonInstance not found")
    
    return {
        "lesson_id": lesson.lesson_id,
        "org_id": lesson.org_id,
        "date": str(lesson.date),
        "slot_id": lesson.slot_id,
        "room_id": lesson.room_id,
        "enrollment_id": lesson.enrollment_id,
        "group_name": lesson.group_name,
        "teacher_name": lesson.teacher_name,
        "course_name": lesson.course_name,
        "room_number": lesson.room_number,
        "start_time": str(lesson.start_time),
        "end_time": str(lesson.end_time),
        "status": lesson.status
    }

@router.patch("/{lesson_id}", response_model=LessonResponse)
async def update_lesson(
    lesson_id: int,
    lesson: LessonUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user_or_demo)
):
    """Update a lesson."""
    # Get existing lesson
    query = select(LessonInstance).where(
        LessonInstance.lesson_id == lesson_id,
        LessonInstance.org_id == current_user.org_id
    )
    result = await db.execute(query)
    existing_lesson = result.scalar_one_or_none()
    
    if not existing_lesson:
        raise HTTPException(status_code=404, detail="LessonInstance not found")
    
    # Update fields - only update non-None values
    update_data = lesson.model_dump(exclude_unset=True, exclude_none=True)
    
    # Debug logging
    print(f"Update data: {update_data}")
    
    for field, value in update_data.items():
        if hasattr(existing_lesson, field):
            # Convert string dates to date objects
            if field == 'date' and isinstance(value, str):
                from datetime import datetime
                value = datetime.strptime(value, '%Y-%m-%d').date()
            setattr(existing_lesson, field, value)
    
    await db.commit()
    await db.refresh(existing_lesson)
    
    # Get updated lesson with related data
    query = select(
        LessonInstance.lesson_id,
        LessonInstance.org_id,
        LessonInstance.date,
        LessonInstance.slot_id,
        LessonInstance.room_id,
        LessonInstance.enrollment_id,
        LessonInstance.status,
        Group.name.label('group_name'),
        func.concat(Teacher.first_name, ' ', Teacher.last_name).label('teacher_name'),
        Course.name.label('course_name'),
        Room.number.label('room_number'),
        TimeTableSlot.start_time,
        TimeTableSlot.end_time
    ).select_from(
        LessonInstance
    ).join(Enrollment, LessonInstance.enrollment_id == Enrollment.enrollment_id
    ).join(CourseAssignment, Enrollment.assignment_id == CourseAssignment.assignment_id
    ).join(Group, Enrollment.group_id == Group.group_id
    ).join(Teacher, CourseAssignment.teacher_id == Teacher.teacher_id
    ).join(Course, CourseAssignment.course_id == Course.course_id
    ).join(Room, LessonInstance.room_id == Room.room_id
    ).join(TimeTableSlot, LessonInstance.slot_id == TimeTableSlot.slot_id
    ).where(LessonInstance.lesson_id == lesson_id)
    
    result = await db.execute(query)
    lesson_data = result.first()
    
    return {
        "lesson_id": lesson_data.lesson_id,
        "org_id": lesson_data.org_id,
        "date": str(lesson_data.date),
        "slot_id": lesson_data.slot_id,
        "room_id": lesson_data.room_id,
        "enrollment_id": lesson_data.enrollment_id,
        "group_name": lesson_data.group_name,
        "teacher_name": lesson_data.teacher_name,
        "course_name": lesson_data.course_name,
        "room_number": lesson_data.room_number,
        "start_time": str(lesson_data.start_time),
        "end_time": str(lesson_data.end_time),
        "status": lesson_data.status
    }

@router.delete("/{lesson_id}")
async def delete_lesson(
    lesson_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user_or_demo)
):
    """Delete a lesson."""
    # Get existing lesson
    query = select(LessonInstance).where(
        LessonInstance.lesson_id == lesson_id,
        LessonInstance.org_id == current_user.org_id
    )
    result = await db.execute(query)
    existing_lesson = result.scalar_one_or_none()
    
    if not existing_lesson:
        raise HTTPException(status_code=404, detail="LessonInstance not found")
    
    # Soft delete - set is_active to False
    existing_lesson.is_active = False
    await db.commit()
    
    return {"message": "LessonInstance deleted successfully"}
