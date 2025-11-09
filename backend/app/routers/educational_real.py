"""Educational router with real database operations."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert, update, delete
from pydantic import BaseModel

from app.core.database import get_db
from app.core.auth import get_current_active_user_or_demo
from app.models.educational import Group, Teacher, Course, CourseAssignment, Enrollment
from app.models.user import User

router = APIRouter()

# Response models
class GroupResponse(BaseModel):
    group_id: int
    org_id: int
    name: str
    size: int
    year_level: Optional[int] = None
    generation_type: int
    is_active: bool = True

class GroupCreate(BaseModel):
    name: str
    size: int = 25
    year_level: Optional[int] = None
    generation_type: int = 2
    is_active: bool = True

class GroupUpdate(BaseModel):
    name: Optional[str] = None
    size: Optional[int] = None
    year_level: Optional[int] = None
    generation_type: Optional[int] = None
    is_active: Optional[bool] = None

# Groups endpoints
@router.get("/groups", response_model=List[GroupResponse])
async def get_groups(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user_or_demo)
):
    """Get groups with pagination and search."""
    query = select(Group).where(Group.org_id == current_user.org_id)
    
    if search:
        query = query.where(Group.name.ilike(f"%{search}%"))
    
    query = query.offset(skip).limit(limit)
    
    result = await db.execute(query)
    groups = result.scalars().all()
    
    return [
        GroupResponse(
            group_id=group.group_id,
            org_id=group.org_id,
            name=group.name,
            size=group.size,
            year_level=group.year_level,
            generation_type=group.generation_type,
            is_active=group.is_active
        )
        for group in groups
    ]

@router.post("/groups", response_model=GroupResponse)
async def create_group(
    group: GroupCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user_or_demo)
):
    """Create a new group."""
    # Check if group with same name already exists
    existing_group = await db.execute(
        select(Group).where(
            Group.org_id == current_user.org_id,
            Group.name == group.name
        )
    )
    if existing_group.scalar_one_or_none():
        raise HTTPException(
            status_code=400, 
            detail=f"Group with name '{group.name}' already exists in this organization"
        )
    
    # Create new group
    new_group = Group(
        org_id=current_user.org_id,
        name=group.name,
        size=group.size,
        year_level=group.year_level,
        generation_type=group.generation_type,
        is_active=group.is_active
    )
    
    db.add(new_group)
    await db.commit()
    await db.refresh(new_group)
    
    return GroupResponse(
        group_id=new_group.group_id,
        org_id=new_group.org_id,
        name=new_group.name,
        size=new_group.size,
        year_level=new_group.year_level,
        generation_type=new_group.generation_type,
        is_active=new_group.is_active
    )

@router.patch("/groups/{group_id}", response_model=GroupResponse)
async def update_group(
    group_id: int,
    group: GroupUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user_or_demo)
):
    """Update a group."""
    # Get existing group
    result = await db.execute(
        select(Group).where(
            Group.group_id == group_id,
            Group.org_id == current_user.org_id
        )
    )
    existing_group = result.scalar_one_or_none()
    
    if not existing_group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    # Update fields
    update_data = group.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(existing_group, field, value)
    
    await db.commit()
    await db.refresh(existing_group)
    
    return GroupResponse(
        group_id=existing_group.group_id,
        org_id=existing_group.org_id,
        name=existing_group.name,
        size=existing_group.size,
        year_level=existing_group.year_level,
        is_active=existing_group.is_active
    )

@router.delete("/groups/{group_id}")
async def delete_group(
    group_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user_or_demo)
):
    """Delete a group."""
    # Get existing group
    result = await db.execute(
        select(Group).where(
            Group.group_id == group_id,
            Group.org_id == current_user.org_id
        )
    )
    existing_group = result.scalar_one_or_none()
    
    if not existing_group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    # Soft delete - set is_active to False
    existing_group.is_active = False
    await db.commit()
    
    return {"message": "Group deleted successfully"}

# Teacher response models
class TeacherResponse(BaseModel):
    teacher_id: int
    org_id: int
    first_name: str
    last_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    is_active: bool = True

class TeacherCreate(BaseModel):
    first_name: str
    last_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    is_active: bool = True

class TeacherUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    is_active: Optional[bool] = None

# Teachers endpoints
@router.get("/teachers", response_model=List[TeacherResponse])
async def get_teachers(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user_or_demo)
):
    """Get teachers with pagination and search."""
    query = select(Teacher).where(Teacher.org_id == current_user.org_id)
    
    if search:
        query = query.where(
            Teacher.first_name.ilike(f"%{search}%") |
            Teacher.last_name.ilike(f"%{search}%")
        )
    
    query = query.offset(skip).limit(limit)
    
    result = await db.execute(query)
    teachers = result.scalars().all()
    
    return [
        TeacherResponse(
            teacher_id=teacher.teacher_id,
            org_id=teacher.org_id,
            first_name=teacher.first_name,
            last_name=teacher.last_name,
            email=teacher.email,
            phone=teacher.phone,
            is_active=teacher.is_active
        )
        for teacher in teachers
    ]

@router.post("/teachers", response_model=TeacherResponse)
async def create_teacher(
    teacher: TeacherCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user_or_demo)
):
    """Create a new teacher."""
    # Check if teacher with same email already exists (if email provided)
    if teacher.email:
        existing_teacher = await db.execute(
            select(Teacher).where(
                Teacher.org_id == current_user.org_id,
                Teacher.email == teacher.email
            )
        )
        if existing_teacher.scalar_one_or_none():
            raise HTTPException(
                status_code=400, 
                detail=f"Teacher with email '{teacher.email}' already exists in this organization"
            )
    
    new_teacher = Teacher(
        org_id=current_user.org_id,
        first_name=teacher.first_name,
        last_name=teacher.last_name,
        email=teacher.email,
        phone=teacher.phone,
        is_active=teacher.is_active
    )
    
    db.add(new_teacher)
    await db.commit()
    await db.refresh(new_teacher)
    
    return TeacherResponse(
        teacher_id=new_teacher.teacher_id,
        org_id=new_teacher.org_id,
        first_name=new_teacher.first_name,
        last_name=new_teacher.last_name,
        email=new_teacher.email,
        phone=new_teacher.phone,
        is_active=new_teacher.is_active
    )

@router.patch("/teachers/{teacher_id}", response_model=TeacherResponse)
async def update_teacher(
    teacher_id: int,
    teacher: TeacherUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user_or_demo)
):
    """Update a teacher."""
    result = await db.execute(
        select(Teacher).where(
            Teacher.teacher_id == teacher_id,
            Teacher.org_id == current_user.org_id
        )
    )
    existing_teacher = result.scalar_one_or_none()
    
    if not existing_teacher:
        raise HTTPException(status_code=404, detail="Teacher not found")
    
    update_data = teacher.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(existing_teacher, field, value)
    
    await db.commit()
    await db.refresh(existing_teacher)
    
    return TeacherResponse(
        teacher_id=existing_teacher.teacher_id,
        org_id=existing_teacher.org_id,
        first_name=existing_teacher.first_name,
        last_name=existing_teacher.last_name,
        email=existing_teacher.email,
        phone=existing_teacher.phone,
        is_active=existing_teacher.is_active
    )

@router.delete("/teachers/{teacher_id}")
async def delete_teacher(
    teacher_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user_or_demo)
):
    """Delete a teacher."""
    result = await db.execute(
        select(Teacher).where(
            Teacher.teacher_id == teacher_id,
            Teacher.org_id == current_user.org_id
        )
    )
    existing_teacher = result.scalar_one_or_none()
    
    if not existing_teacher:
        raise HTTPException(status_code=404, detail="Teacher not found")
    
    existing_teacher.is_active = False
    await db.commit()
    
    return {"message": "Teacher deleted successfully"}

# Course response models
class CourseResponse(BaseModel):
    course_id: int
    org_id: int
    name: str
    type: Optional[str] = None
    is_active: bool = True

class CourseCreate(BaseModel):
    name: str
    type: Optional[str] = None
    is_active: bool = True

class CourseUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = None
    is_active: Optional[bool] = None

# Courses endpoints
@router.get("/courses", response_model=List[CourseResponse])
async def get_courses(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user_or_demo)
):
    """Get courses with pagination and search."""
    query = select(Course).where(Course.org_id == current_user.org_id)
    
    if search:
        query = query.where(Course.name.ilike(f"%{search}%"))
    
    query = query.offset(skip).limit(limit)
    
    result = await db.execute(query)
    courses = result.scalars().all()
    
    return [
        CourseResponse(
            course_id=course.course_id,
            org_id=course.org_id,
            name=course.name,
            type=course.type,
            is_active=course.is_active
        )
        for course in courses
    ]

@router.post("/courses", response_model=CourseResponse)
async def create_course(
    course: CourseCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user_or_demo)
):
    """Create a new course."""
    # Check if course with same name already exists
    existing_course = await db.execute(
        select(Course).where(
            Course.org_id == current_user.org_id,
            Course.name == course.name
        )
    )
    if existing_course.scalar_one_or_none():
        raise HTTPException(
            status_code=400, 
            detail=f"Course with name '{course.name}' already exists in this organization"
        )
    
    new_course = Course(
        org_id=current_user.org_id,
        name=course.name,
        type=course.type,
        is_active=course.is_active
    )
    
    db.add(new_course)
    await db.commit()
    await db.refresh(new_course)
    
    return CourseResponse(
        course_id=new_course.course_id,
        org_id=new_course.org_id,
        name=new_course.name,
        type=new_course.type,
        is_active=new_course.is_active
    )

@router.patch("/courses/{course_id}", response_model=CourseResponse)
async def update_course(
    course_id: int,
    course: CourseUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user_or_demo)
):
    """Update a course."""
    result = await db.execute(
        select(Course).where(
            Course.course_id == course_id,
            Course.org_id == current_user.org_id
        )
    )
    existing_course = result.scalar_one_or_none()
    
    if not existing_course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    update_data = course.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(existing_course, field, value)
    
    await db.commit()
    await db.refresh(existing_course)
    
    return CourseResponse(
        course_id=existing_course.course_id,
        org_id=existing_course.org_id,
        name=existing_course.name,
        type=existing_course.type,
        is_active=existing_course.is_active
    )

@router.delete("/courses/{course_id}")
async def delete_course(
    course_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user_or_demo)
):
    """Delete a course."""
    result = await db.execute(
        select(Course).where(
            Course.course_id == course_id,
            Course.org_id == current_user.org_id
        )
    )
    existing_course = result.scalar_one_or_none()
    
    if not existing_course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    existing_course.is_active = False
    await db.commit()
    
    return {"message": "Course deleted successfully"}

# Course Assignment response models
class CourseAssignmentResponse(BaseModel):
    assignment_id: int
    org_id: int
    course_id: int
    teacher_id: int

class CourseAssignmentCreate(BaseModel):
    course_id: int
    teacher_id: int

# Course Assignments endpoints
@router.get("/course-assignments", response_model=List[CourseAssignmentResponse])
async def get_course_assignments(
    course_id: Optional[int] = None,
    teacher_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user_or_demo)
):
    """Get course assignments with pagination."""
    query = select(CourseAssignment).where(CourseAssignment.org_id == current_user.org_id)
    
    if course_id:
        query = query.where(CourseAssignment.course_id == course_id)
    if teacher_id:
        query = query.where(CourseAssignment.teacher_id == teacher_id)
    
    query = query.offset(skip).limit(limit)
    
    result = await db.execute(query)
    assignments = result.scalars().all()
    
    return [
        CourseAssignmentResponse(
            assignment_id=assignment.assignment_id,
            org_id=assignment.org_id,
            course_id=assignment.course_id,
            teacher_id=assignment.teacher_id
        )
        for assignment in assignments
    ]

@router.post("/course-assignments", response_model=CourseAssignmentResponse)
async def create_course_assignment(
    assignment: CourseAssignmentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user_or_demo)
):
    """Create a new course assignment."""
    new_assignment = CourseAssignment(
        org_id=current_user.org_id,
        course_id=assignment.course_id,
        teacher_id=assignment.teacher_id
    )
    
    db.add(new_assignment)
    await db.commit()
    await db.refresh(new_assignment)
    
    return CourseAssignmentResponse(
        assignment_id=new_assignment.assignment_id,
        org_id=new_assignment.org_id,
        course_id=new_assignment.course_id,
        teacher_id=new_assignment.teacher_id
    )

@router.delete("/course-assignments/{assignment_id}")
async def delete_course_assignment(
    assignment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user_or_demo)
):
    """Delete a course assignment."""
    result = await db.execute(
        select(CourseAssignment).where(
            CourseAssignment.assignment_id == assignment_id,
            CourseAssignment.org_id == current_user.org_id
        )
    )
    existing_assignment = result.scalar_one_or_none()
    
    if not existing_assignment:
        raise HTTPException(status_code=404, detail="Course assignment not found")
    
    await db.delete(existing_assignment)
    await db.commit()
    
    return {"message": "Course assignment deleted successfully"}

# Enrollment response models
class EnrollmentResponse(BaseModel):
    enrollment_id: int
    org_id: int
    assignment_id: int
    group_id: int
    planned_hours: int
    unit: str

class EnrollmentCreate(BaseModel):
    assignment_id: int
    group_id: int
    planned_hours: int
    unit: str = "per_term"


class EnrollmentCreateFromFrontend(BaseModel):
    """Enrollment creation schema from frontend."""
    group_id: int
    course_id: int
    teacher_id: int
    planned_hours_per_semester: int

class EnrollmentUpdateFromFrontend(BaseModel):
    """Enrollment update schema from frontend."""
    group_id: int
    course_id: int
    teacher_id: int
    planned_hours_per_semester: int

class EnrollmentUpdate(BaseModel):
    planned_hours: Optional[int] = None
    unit: Optional[str] = None

# Enrollments endpoints
@router.get("/enrollments", response_model=List[EnrollmentResponse])
async def get_enrollments(
    group_id: Optional[int] = None,
    assignment_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user_or_demo)
):
    """Get enrollments with pagination."""
    query = select(Enrollment).where(Enrollment.org_id == current_user.org_id)
    
    if group_id:
        query = query.where(Enrollment.group_id == group_id)
    if assignment_id:
        query = query.where(Enrollment.assignment_id == assignment_id)
    
    query = query.offset(skip).limit(limit)
    
    result = await db.execute(query)
    enrollments = result.scalars().all()
    
    return [
        EnrollmentResponse(
            enrollment_id=enrollment.enrollment_id,
            org_id=enrollment.org_id,
            assignment_id=enrollment.assignment_id,
            group_id=enrollment.group_id,
            planned_hours=enrollment.planned_hours,
            unit=enrollment.unit
        )
        for enrollment in enrollments
    ]

@router.post("/enrollments", response_model=EnrollmentResponse)
async def create_enrollment(
    enrollment: EnrollmentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user_or_demo)
):
    """Create a new enrollment."""
    new_enrollment = Enrollment(
        org_id=current_user.org_id,
        assignment_id=enrollment.assignment_id,
        group_id=enrollment.group_id,
        planned_hours=enrollment.planned_hours,
        unit=enrollment.unit
    )
    
    db.add(new_enrollment)
    await db.commit()
    await db.refresh(new_enrollment)
    
    return EnrollmentResponse(
        enrollment_id=new_enrollment.enrollment_id,
        org_id=new_enrollment.org_id,
        assignment_id=new_enrollment.assignment_id,
        group_id=new_enrollment.group_id,
        planned_hours=new_enrollment.planned_hours,
        unit=new_enrollment.unit
    )

@router.post("/enrollments/from-frontend", response_model=EnrollmentResponse)
async def create_enrollment_from_frontend(
    enrollment: EnrollmentCreateFromFrontend,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user_or_demo)
):
    """Create a new enrollment from frontend data."""
    # Find or create course assignment
    assignment_result = await db.execute(
        select(CourseAssignment).where(
            CourseAssignment.org_id == current_user.org_id,
            CourseAssignment.course_id == enrollment.course_id,
            CourseAssignment.teacher_id == enrollment.teacher_id
        )
    )
    assignment = assignment_result.scalar_one_or_none()
    
    if not assignment:
        # Create new assignment
        assignment = CourseAssignment(
            org_id=current_user.org_id,
            course_id=enrollment.course_id,
            teacher_id=enrollment.teacher_id
        )
        db.add(assignment)
        await db.flush()  # Get the assignment_id
    
    # Create enrollment
    new_enrollment = Enrollment(
        org_id=current_user.org_id,
        assignment_id=assignment.assignment_id,
        group_id=enrollment.group_id,
        planned_hours=enrollment.planned_hours_per_semester,
        unit="per_term"
    )
    
    db.add(new_enrollment)
    await db.commit()
    await db.refresh(new_enrollment)
    
    return EnrollmentResponse(
        enrollment_id=new_enrollment.enrollment_id,
        org_id=new_enrollment.org_id,
        assignment_id=new_enrollment.assignment_id,
        group_id=new_enrollment.group_id,
        planned_hours=new_enrollment.planned_hours,
        unit=new_enrollment.unit
    )

@router.patch("/enrollments/{enrollment_id}", response_model=EnrollmentResponse)
async def update_enrollment(
    enrollment_id: int,
    enrollment: EnrollmentUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user_or_demo)
):
    """Update an enrollment."""
    result = await db.execute(
        select(Enrollment).where(
            Enrollment.enrollment_id == enrollment_id,
            Enrollment.org_id == current_user.org_id
        )
    )
    existing_enrollment = result.scalar_one_or_none()
    
    if not existing_enrollment:
        raise HTTPException(status_code=404, detail="Enrollment not found")
    
    update_data = enrollment.model_dump(exclude_unset=True)
    
    # Unit is now a string, no conversion needed
    
    for field, value in update_data.items():
        setattr(existing_enrollment, field, value)
    
    await db.commit()
    await db.refresh(existing_enrollment)
    
    return EnrollmentResponse(
        enrollment_id=existing_enrollment.enrollment_id,
        org_id=existing_enrollment.org_id,
        assignment_id=existing_enrollment.assignment_id,
        group_id=existing_enrollment.group_id,
        planned_hours=existing_enrollment.planned_hours,
        unit=existing_enrollment.unit
    )

@router.patch("/enrollments/{enrollment_id}/from-frontend", response_model=EnrollmentResponse)
async def update_enrollment_from_frontend(
    enrollment_id: int,
    enrollment: EnrollmentUpdateFromFrontend,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user_or_demo)
):
    """Update an enrollment from frontend data."""
    # Find existing enrollment
    result = await db.execute(
        select(Enrollment).where(
            Enrollment.enrollment_id == enrollment_id,
            Enrollment.org_id == current_user.org_id
        )
    )
    existing_enrollment = result.scalar_one_or_none()
    
    if not existing_enrollment:
        raise HTTPException(status_code=404, detail="Enrollment not found")
    
    # Find or create course assignment
    assignment_result = await db.execute(
        select(CourseAssignment).where(
            CourseAssignment.org_id == current_user.org_id,
            CourseAssignment.course_id == enrollment.course_id,
            CourseAssignment.teacher_id == enrollment.teacher_id
        )
    )
    assignment = assignment_result.scalar_one_or_none()
    
    if not assignment:
        # Create new assignment
        assignment = CourseAssignment(
            org_id=current_user.org_id,
            course_id=enrollment.course_id,
            teacher_id=enrollment.teacher_id
        )
        db.add(assignment)
        await db.flush()  # Get the assignment_id
    
    # Update enrollment
    existing_enrollment.assignment_id = assignment.assignment_id
    existing_enrollment.group_id = enrollment.group_id
    existing_enrollment.planned_hours = enrollment.planned_hours_per_semester
    existing_enrollment.unit = "per_term"
    
    await db.commit()
    await db.refresh(existing_enrollment)
    
    return EnrollmentResponse(
        enrollment_id=existing_enrollment.enrollment_id,
        org_id=existing_enrollment.org_id,
        assignment_id=existing_enrollment.assignment_id,
        group_id=existing_enrollment.group_id,
        planned_hours=existing_enrollment.planned_hours,
        unit=existing_enrollment.unit
    )

@router.delete("/enrollments/{enrollment_id}")
async def delete_enrollment(
    enrollment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user_or_demo)
):
    """Delete an enrollment."""
    result = await db.execute(
        select(Enrollment).where(
            Enrollment.enrollment_id == enrollment_id,
            Enrollment.org_id == current_user.org_id
        )
    )
    existing_enrollment = result.scalar_one_or_none()
    
    if not existing_enrollment:
        raise HTTPException(status_code=404, detail="Enrollment not found")
    
    await db.delete(existing_enrollment)
    await db.commit()
    
    return {"message": "Enrollment deleted successfully"}
