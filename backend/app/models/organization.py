"""Organization model."""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, func
from sqlalchemy.orm import relationship
from ..core.database import Base


class Organization(Base):
    """Organization model."""
    
    __tablename__ = "organizations"
    
    org_id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    locale = Column(String(10), nullable=False, default="ru")
    tz = Column(String(50), nullable=False, default="Europe/Moscow")
    created_at = Column(
        DateTime(timezone=True), 
        server_default=func.now(),
        nullable=False
    )
    
    # Relationships
    users = relationship("User", back_populates="organization", cascade="all, delete-orphan")
    academic_years = relationship("AcademicYear", back_populates="organization", cascade="all, delete-orphan")
    terms = relationship("Term", back_populates="organization", cascade="all, delete-orphan")
    groups = relationship("Group", back_populates="organization", cascade="all, delete-orphan")
    teachers = relationship("Teacher", back_populates="organization", cascade="all, delete-orphan")
    courses = relationship("Course", back_populates="organization", cascade="all, delete-orphan")
    course_assignments = relationship("CourseAssignment", back_populates="organization", cascade="all, delete-orphan")
    enrollments = relationship("Enrollment", back_populates="organization", cascade="all, delete-orphan")
    rooms = relationship("Room", back_populates="organization", cascade="all, delete-orphan")
    time_slots = relationship("TimeTableSlot", back_populates="organization", cascade="all, delete-orphan")
    teacher_availabilities = relationship("TeacherAvailability", back_populates="organization", cascade="all, delete-orphan")
    holidays = relationship("Holiday", back_populates="organization", cascade="all, delete-orphan")
    lesson_instances = relationship("LessonInstance", back_populates="organization", cascade="all, delete-orphan")
    change_logs = relationship("ChangeLog", back_populates="organization", cascade="all, delete-orphan")
    generation_jobs = relationship("GenerationJob", back_populates="organization", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Organization(id={self.org_id}, name='{self.name}')>"
