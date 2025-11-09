# Import all models to ensure they are registered with SQLAlchemy
from .organization import Organization
from .user import User, UserRole
from .academic import AcademicYear, Term
from .educational import Group, Teacher, Course, CourseAssignment, Enrollment
from .facilities import Room, TimeTableSlot, TeacherAvailability, Holiday
from .scheduling import LessonInstance, LessonStatus, ChangeLog, GenerationJob, GenerationStatus, GenerationScope

__all__ = [
    "Organization",
    "User", "UserRole",
    "AcademicYear", "Term",
    "Group", "Teacher", "Course", "CourseAssignment", "Enrollment",
    "Room", "TimeTableSlot", "TeacherAvailability", "Holiday", 
    "LessonInstance", "LessonStatus", "ChangeLog", "GenerationJob", "GenerationStatus", "GenerationScope"
]
