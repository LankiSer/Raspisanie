"""Educational entities schemas."""

from typing import Optional
from pydantic import BaseModel, EmailStr
# from ..models.educational import HoursUnit  # No longer needed


# Group schemas
class GroupBase(BaseModel):
    """Base group schema."""
    name: str
    size: int = 25
    year_level: Optional[int] = None
    generation_type: int = 2  # 2, 3, or 5 lessons per block
    is_active: bool = True


class GroupCreate(GroupBase):
    """Group creation schema."""
    org_id: int


class GroupUpdate(BaseModel):
    """Group update schema."""
    name: Optional[str] = None
    size: Optional[int] = None
    year_level: Optional[int] = None
    generation_type: Optional[int] = None
    is_active: Optional[bool] = None


class GroupResponse(GroupBase):
    """Group response schema."""
    group_id: int
    org_id: int
    
    class Config:
        from_attributes = True


# Teacher schemas
class TeacherBase(BaseModel):
    """Base teacher schema."""
    first_name: str
    last_name: str
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    is_active: bool = True


class TeacherCreate(TeacherBase):
    """Teacher creation schema."""
    org_id: int


class TeacherUpdate(BaseModel):
    """Teacher update schema."""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    is_active: Optional[bool] = None


class TeacherResponse(TeacherBase):
    """Teacher response schema."""
    teacher_id: int
    org_id: int
    
    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"
    
    class Config:
        from_attributes = True


# Course schemas
class CourseBase(BaseModel):
    """Base course schema."""
    name: str
    type: Optional[str] = None
    is_active: bool = True


class CourseCreate(CourseBase):
    """Course creation schema."""
    org_id: int


class CourseUpdate(BaseModel):
    """Course update schema."""
    name: Optional[str] = None
    type: Optional[str] = None
    is_active: Optional[bool] = None


class CourseResponse(CourseBase):
    """Course response schema."""
    course_id: int
    org_id: int
    
    class Config:
        from_attributes = True


# Course assignment schemas
class CourseAssignmentCreate(BaseModel):
    """Course assignment creation schema."""
    org_id: int
    course_id: int
    teacher_id: int


class CourseAssignmentResponse(BaseModel):
    """Course assignment response schema."""
    assignment_id: int
    org_id: int
    course_id: int
    teacher_id: int
    course: Optional[CourseResponse] = None
    teacher: Optional[TeacherResponse] = None
    
    class Config:
        from_attributes = True


# Enrollment schemas
class EnrollmentBase(BaseModel):
    """Base enrollment schema."""
    planned_hours: int
    unit: str = "per_week"


class EnrollmentCreate(EnrollmentBase):
    """Enrollment creation schema."""
    org_id: int
    assignment_id: int
    group_id: int


class EnrollmentCreateFromFrontend(BaseModel):
    """Enrollment creation schema from frontend."""
    group_id: int
    course_id: int
    teacher_id: int
    planned_hours_per_semester: int


class EnrollmentUpdate(BaseModel):
    """Enrollment update schema."""
    planned_hours: Optional[int] = None
    unit: Optional[str] = None


class EnrollmentResponse(EnrollmentBase):
    """Enrollment response schema."""
    enrollment_id: int
    org_id: int
    assignment_id: int
    group_id: int
    assignment: Optional[CourseAssignmentResponse] = None
    group: Optional[GroupResponse] = None
    
    class Config:
        from_attributes = True
