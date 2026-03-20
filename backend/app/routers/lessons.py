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
from app.models.academic import Term
from app.schemas.lessons import LessonCreate, LessonUpdate, LessonResponse
from pydantic import ValidationError
from app.models.user import User
from app.repositories.lesson import LessonRepository

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
    # Use mappings() to get dicts instead of Row objects to avoid any lazy loading
    lessons = result.mappings().all()
    
    return [
        {
            "lesson_id": int(lesson.get('lesson_id', 0)),
            "org_id": int(lesson.get('org_id', 0)),
            "date": str(lesson.get('date', '')),
            "slot_id": int(lesson.get('slot_id', 0)),
            "room_id": int(lesson.get('room_id')) if lesson.get('room_id') else None,
            "enrollment_id": int(lesson.get('enrollment_id', 0)),
            "group_name": str(lesson.get('group_name', '')),
            "teacher_name": str(lesson.get('teacher_name', '')),
            "course_name": str(lesson.get('course_name', '')),
            "room_number": str(lesson.get('room_number', '')),
            "start_time": str(lesson.get('start_time', '')),
            "end_time": str(lesson.get('end_time', '')),
            "status": str(lesson.get('status', '')).lower() if isinstance(lesson.get('status'), str) else (lesson.get('status').value.lower() if hasattr(lesson.get('status'), 'value') else str(lesson.get('status', 'planned')).lower())
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
    # Use mappings() to get dicts instead of Row objects to avoid any lazy loading
    lessons = result.mappings().all()
    
    return [
        {
            "lesson_id": int(lesson.get('lesson_id', 0)),
            "org_id": int(lesson.get('org_id', 0)),
            "date": str(lesson.get('date', '')),
            "slot_id": int(lesson.get('slot_id', 0)),
            "room_id": int(lesson.get('room_id')) if lesson.get('room_id') else None,
            "enrollment_id": int(lesson.get('enrollment_id', 0)),
            "group_name": str(lesson.get('group_name', '')),
            "teacher_name": str(lesson.get('teacher_name', '')),
            "course_name": str(lesson.get('course_name', '')),
            "room_number": str(lesson.get('room_number', '')),
            "start_time": str(lesson.get('start_time', '')),
            "end_time": str(lesson.get('end_time', '')),
            "status": str(lesson.get('status', '')).lower() if isinstance(lesson.get('status'), str) else (lesson.get('status').value.lower() if hasattr(lesson.get('status'), 'value') else str(lesson.get('status', 'planned')).lower())
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
    # Use mappings() to get dicts instead of Row objects to avoid any lazy loading
    lessons = result.mappings().all()
    
    return [
        {
            "lesson_id": int(lesson.get('lesson_id', 0)),
            "org_id": int(lesson.get('org_id', 0)),
            "date": str(lesson.get('date', '')),
            "slot_id": int(lesson.get('slot_id', 0)),
            "room_id": int(lesson.get('room_id')) if lesson.get('room_id') else None,
            "enrollment_id": int(lesson.get('enrollment_id', 0)),
            "group_name": str(lesson.get('group_name', '')),
            "teacher_name": str(lesson.get('teacher_name', '')),
            "course_name": str(lesson.get('course_name', '')),
            "room_number": str(lesson.get('room_number', '')),
            "start_time": str(lesson.get('start_time', '')),
            "end_time": str(lesson.get('end_time', '')),
            "status": str(lesson.get('status', '')).lower() if isinstance(lesson.get('status'), str) else (lesson.get('status').value.lower() if hasattr(lesson.get('status'), 'value') else str(lesson.get('status', 'planned')).lower())
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
    # Check for conflicts before creating (unless ignore_conflicts is True)
    ignore_conflicts = getattr(lesson, 'ignore_conflicts', False) if hasattr(lesson, 'ignore_conflicts') else False
    if not ignore_conflicts:
        lesson_repo = LessonRepository(db)
        conflicts = await lesson_repo.check_conflicts(
            org_id=lesson.org_id,
            date=lesson.date,
            slot_id=lesson.slot_id,
            enrollment_id=lesson.enrollment_id,
            room_id=lesson.room_id,
            exclude_lesson_id=None
        )
        
        if conflicts:
            raise HTTPException(
                status_code=409,
                detail={
                    "message": "Conflicts detected",
                    "conflicts": conflicts
                }
            )
    
    # Create new lesson
    # Convert status string to LessonStatus enum
    status_value = lesson.status.upper() if lesson.status else "PLANNED"
    try:
        lesson_status = LessonStatus(status_value)
    except ValueError:
        lesson_status = LessonStatus.PLANNED
    
    # Get term for the lesson date
    term_result = await db.execute(
        select(Term.term_id).where(
            Term.org_id == current_user.org_id,
            Term.start_date <= lesson.date,
            Term.end_date >= lesson.date
        ).order_by(Term.start_date.desc())
    )
    term_id = term_result.scalar_one_or_none()
    
    if not term_id:
        raise HTTPException(
            status_code=400,
            detail=f"No term found for date {lesson.date}. Please create a term that covers this date."
        )
    
    new_lesson = LessonInstance(
        org_id=lesson.org_id,
        term_id=term_id,
        date=lesson.date,
        slot_id=lesson.slot_id,
        room_id=lesson.room_id,
        enrollment_id=lesson.enrollment_id,
        status=lesson_status,
        created_by=current_user.user_id
    )
    
    db.add(new_lesson)
    await db.flush()  # Flush to get lesson_id without committing
    
    # Save ALL values before commit to avoid lazy loading issues
    status_value = new_lesson.status.value.lower() if hasattr(new_lesson.status, 'value') else str(new_lesson.status).lower()
    lesson_id = new_lesson.lesson_id
    org_id_saved = new_lesson.org_id
    date_saved = str(new_lesson.date)
    slot_id_saved = new_lesson.slot_id
    room_id_saved = new_lesson.room_id
    enrollment_id_saved = new_lesson.enrollment_id
    
    await db.commit()
    
    # Expunge all objects from session to prevent any lazy loading
    # This ensures no objects remain in session that could trigger lazy loading
    db.expunge_all()
    
    # Get related data for response (don't use refresh to avoid lazy loading issues)
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
    ).where(LessonInstance.lesson_id == lesson_id)
    
    result = await db.execute(query)
    # Use mappings() to get dict instead of Row object to avoid any lazy loading
    lesson_data = result.mappings().first()
    
    if not lesson_data:
        raise HTTPException(status_code=500, detail="Failed to retrieve lesson data after creation")
    
    # Convert all data to simple types immediately from dict
    group_name_val = str(lesson_data.get('group_name', ''))
    teacher_name_val = str(lesson_data.get('teacher_name', ''))
    course_name_val = str(lesson_data.get('course_name', ''))
    room_number_val = str(lesson_data.get('room_number', ''))
    start_time_val = str(lesson_data.get('start_time', ''))
    end_time_val = str(lesson_data.get('end_time', ''))
    
    # Create response dict and validate with Pydantic to ensure proper serialization
    response_dict = {
        "lesson_id": lesson_id,
        "org_id": org_id_saved,
        "date": date_saved,
        "slot_id": slot_id_saved,
        "room_id": room_id_saved,
        "enrollment_id": enrollment_id_saved,
        "group_name": group_name_val,
        "teacher_name": teacher_name_val,
        "course_name": course_name_val,
        "room_number": room_number_val,
        "start_time": start_time_val,
        "end_time": end_time_val,
        "status": status_value
    }
    
    # Validate with Pydantic to ensure proper serialization (this prevents any lazy loading)
    try:
        return LessonResponse.model_validate(response_dict).model_dump()
    except ValidationError as e:
        # If validation fails, return dict directly (shouldn't happen, but just in case)
        return response_dict

@router.post("/bulk", response_model=dict)
async def create_lessons_bulk(
    lessons: List[LessonCreate],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user_or_demo)
):
    """Create multiple lessons at once."""
    created_lessons = []
    
    for lesson_data in lessons:
        # Convert status string to LessonStatus enum
        status_value = lesson_data.status.upper() if lesson_data.status else "PLANNED"
        try:
            lesson_status = LessonStatus(status_value)
        except ValueError:
            lesson_status = LessonStatus.PLANNED
        
        # Get term for the lesson date
        term_result = await db.execute(
            select(Term).where(
                Term.org_id == current_user.org_id,
                Term.start_date <= lesson_data.date,
                Term.end_date >= lesson_data.date
            ).order_by(Term.start_date.desc())
        )
        term = term_result.scalar_one_or_none()
        
        if not term:
            raise HTTPException(
                status_code=400,
                detail=f"No term found for date {lesson_data.date}. Please create a term that covers this date."
            )
        
        new_lesson = LessonInstance(
            org_id=lesson_data.org_id,
            term_id=term.term_id,
            date=lesson_data.date,
            slot_id=lesson_data.slot_id,
            room_id=lesson_data.room_id,
            enrollment_id=lesson_data.enrollment_id,
            status=lesson_status,
            created_by=current_user.user_id
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
    # Use mappings() to get dict instead of Row object to avoid any lazy loading
    lesson = result.mappings().first()
    
    if not lesson:
        raise HTTPException(status_code=404, detail="LessonInstance not found")
    
    # Convert all data to simple types immediately from dict to avoid any lazy loading
    lesson_id_val = int(lesson.get('lesson_id', 0))
    org_id_val = int(lesson.get('org_id', 0))
    date_val = str(lesson.get('date', ''))
    slot_id_val = int(lesson.get('slot_id', 0))
    room_id_val = int(lesson.get('room_id')) if lesson.get('room_id') else None
    enrollment_id_val = int(lesson.get('enrollment_id', 0))
    group_name_val = str(lesson.get('group_name', ''))
    teacher_name_val = str(lesson.get('teacher_name', ''))
    course_name_val = str(lesson.get('course_name', ''))
    room_number_val = str(lesson.get('room_number', ''))
    start_time_val = str(lesson.get('start_time', ''))
    end_time_val = str(lesson.get('end_time', ''))
    
    # Convert status safely from dict
    status_obj = lesson.get('status')
    try:
        if hasattr(status_obj, 'value'):
            status_val = status_obj.value.lower()
        else:
            status_val = str(status_obj).lower() if status_obj else "planned"
    except Exception:
        status_val = "planned"  # Fallback
    
    # Create response dict and validate with Pydantic to ensure proper serialization
    response_dict = {
        "lesson_id": lesson_id_val,
        "org_id": org_id_val,
        "date": date_val,
        "slot_id": slot_id_val,
        "room_id": room_id_val,
        "enrollment_id": enrollment_id_val,
        "group_name": group_name_val,
        "teacher_name": teacher_name_val,
        "course_name": course_name_val,
        "room_number": room_number_val,
        "start_time": start_time_val,
        "end_time": end_time_val,
        "status": status_val
    }
    
    # Validate with Pydantic to ensure proper serialization (this prevents any lazy loading)
    try:
        return LessonResponse.model_validate(response_dict).model_dump()
    except ValidationError as e:
        # If validation fails, return dict directly (shouldn't happen, but just in case)
        return response_dict

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

    if lesson.version is not None and lesson.version != existing_lesson.version:
        raise HTTPException(
            status_code=409,
            detail="Занятие изменено другим пользователем. Обновите страницу.",
        )
    
    # Update fields — только явно переданные непустые значения
    update_data = lesson.model_dump(exclude_unset=True, exclude_none=True)
    # version не пишем через setattr из тела запроса
    update_data.pop("version", None)
    # Нельзя обнулять обязательные поля PATCH-ом
    for key in ("slot_id", "enrollment_id", "term_id"):
        if key in update_data and update_data[key] is None:
            del update_data[key]
    if "slot_id" in update_data:
        sid = update_data["slot_id"]
        if not isinstance(sid, int) or sid < 1:
            raise HTTPException(status_code=400, detail="Некорректный slot_id")
    
    for field, value in update_data.items():
        if hasattr(existing_lesson, field):
            # Convert string dates to date objects
            if field == 'date' and isinstance(value, str):
                from datetime import datetime
                value = datetime.strptime(value, '%Y-%m-%d').date()
            # Convert status string to LessonStatus enum
            elif field == 'status' and isinstance(value, str):
                status_value = value.upper()
                try:
                    value = LessonStatus(status_value)
                except ValueError:
                    raise HTTPException(status_code=400, detail=f"Invalid status: {value}")
            setattr(existing_lesson, field, value)

    existing_lesson.version = (existing_lesson.version or 1) + 1
    
    # Update updated_by and updated_at
    existing_lesson.updated_by = current_user.user_id
    
    # Save status value before commit to avoid lazy loading issues
    status_value = existing_lesson.status.value.lower() if hasattr(existing_lesson.status, 'value') else str(existing_lesson.status).lower()
    
    await db.flush()  # Flush to ensure changes are in session
    await db.commit()
    
    # Expunge all objects from session to prevent any lazy loading
    # This ensures no objects remain in session that could trigger lazy loading
    db.expunge_all()
    
    # Get updated lesson with related data (don't use refresh to avoid lazy loading issues)
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
    # Use mappings() to get dict instead of Row object to avoid any lazy loading
    lesson_data = result.mappings().first()
    
    if not lesson_data:
        raise HTTPException(status_code=500, detail="Failed to retrieve lesson data after update")
    
    # Convert all data to simple types immediately from dict to avoid any lazy loading
    # Use saved status_value (it was saved before commit, so it's safe)
    lesson_id_val = int(lesson_data.get('lesson_id', 0))
    org_id_val = int(lesson_data.get('org_id', 0))
    date_val = str(lesson_data.get('date', ''))
    slot_id_val = int(lesson_data.get('slot_id', 0))
    room_id_val = int(lesson_data.get('room_id')) if lesson_data.get('room_id') else None
    enrollment_id_val = int(lesson_data.get('enrollment_id', 0))
    group_name_val = str(lesson_data.get('group_name', ''))
    teacher_name_val = str(lesson_data.get('teacher_name', ''))
    course_name_val = str(lesson_data.get('course_name', ''))
    room_number_val = str(lesson_data.get('room_number', ''))
    start_time_val = str(lesson_data.get('start_time', ''))
    end_time_val = str(lesson_data.get('end_time', ''))
    
    # Use saved status_value - it's the most recent value before commit
    query_status = status_value
    
    # Create response dict and validate with Pydantic to ensure proper serialization
    response_dict = {
        "lesson_id": lesson_id_val,
        "org_id": org_id_val,
        "date": date_val,
        "slot_id": slot_id_val,
        "room_id": room_id_val,
        "enrollment_id": enrollment_id_val,
        "group_name": group_name_val,
        "teacher_name": teacher_name_val,
        "course_name": course_name_val,
        "room_number": room_number_val,
        "start_time": start_time_val,
        "end_time": end_time_val,
        "status": query_status
    }
    
    # Validate with Pydantic to ensure proper serialization (this prevents any lazy loading)
    try:
        return LessonResponse.model_validate(response_dict).model_dump()
    except ValidationError as e:
        # If validation fails, return dict directly (shouldn't happen, but just in case)
        return response_dict

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
    
    # Soft delete - set status to CANCELLED
    existing_lesson.status = LessonStatus.CANCELLED
    existing_lesson.updated_by = current_user.user_id
    await db.commit()
    
    return {"message": "LessonInstance deleted successfully"}
