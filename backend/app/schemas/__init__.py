"""Pydantic schemas for request/response DTOs."""

from .auth import LoginRequest, LoginResponse, RegisterRequest, UserInfo
from .organization import OrganizationCreate, OrganizationResponse
from .user import UserCreate, UserUpdate, UserResponse, UserRole
from .academic import AcademicYearCreate, AcademicYearResponse, TermCreate, TermResponse  
from .educational import (
    GroupCreate, GroupUpdate, GroupResponse,
    TeacherCreate, TeacherUpdate, TeacherResponse,
    CourseCreate, CourseUpdate, CourseResponse,
    CourseAssignmentCreate, CourseAssignmentResponse,
    EnrollmentCreate, EnrollmentUpdate, EnrollmentResponse
)
from .facilities import (
    RoomCreate, RoomUpdate, RoomResponse,
    TimeSlotCreate, TimeSlotUpdate, TimeSlotResponse,
    TeacherAvailabilityCreate, TeacherAvailabilityUpdate, TeacherAvailabilityResponse,
    HolidayCreate, HolidayResponse
)
from .scheduling import (
    LessonInstanceCreate, LessonInstanceUpdate, LessonInstanceResponse,
    LessonStatus, GenerationJobCreate, GenerationJobResponse,
    GenerationScope, GenerationStatus, LessonConflictResponse
)
from .generation import GenerationRuleSet, GenerationPreviewRequest, GenerationRunRequest

__all__ = [
    # Auth
    "LoginRequest", "LoginResponse", "RegisterRequest", "UserInfo",
    # Organization
    "OrganizationCreate", "OrganizationResponse",
    # User
    "UserCreate", "UserUpdate", "UserResponse", "UserRole",
    # Academic
    "AcademicYearCreate", "AcademicYearResponse", "TermCreate", "TermResponse",
    # Educational
    "GroupCreate", "GroupUpdate", "GroupResponse",
    "TeacherCreate", "TeacherUpdate", "TeacherResponse",
    "CourseCreate", "CourseUpdate", "CourseResponse",
    "CourseAssignmentCreate", "CourseAssignmentResponse",
    "EnrollmentCreate", "EnrollmentUpdate", "EnrollmentResponse",
    # Facilities
    "RoomCreate", "RoomUpdate", "RoomResponse",
    "TimeSlotCreate", "TimeSlotUpdate", "TimeSlotResponse",
    "TeacherAvailabilityCreate", "TeacherAvailabilityUpdate", "TeacherAvailabilityResponse",
    "HolidayCreate", "HolidayResponse",
    # Scheduling
    "LessonInstanceCreate", "LessonInstanceUpdate", "LessonInstanceResponse",
    "LessonStatus", "GenerationJobCreate", "GenerationJobResponse",
    "GenerationScope", "GenerationStatus", "LessonConflictResponse",
    # Generation
    "GenerationRuleSet", "GenerationPreviewRequest", "GenerationRunRequest"
]
