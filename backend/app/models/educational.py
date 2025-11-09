"""Educational entities models (Group, Teacher, Course, etc.)."""

from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from ..core.database import Base


class Group(Base):
    """Student group model."""
    
    __tablename__ = "groups"
    
    group_id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.org_id"), nullable=False, index=True)
    name = Column(String(100), nullable=False, index=True)
    size = Column(Integer, nullable=False, default=25)
    year_level = Column(Integer, nullable=True)  # 1, 2, 3, 4 for university, etc.
    generation_type = Column(Integer, nullable=False, default=2)  # 2, 3, or 5 lessons per block
    is_active = Column(Boolean, nullable=False, default=True)
    
    # Unique constraint: name unique within organization
    __table_args__ = (UniqueConstraint('org_id', 'name', name='uq_org_group_name'),)
    
    # Relationships
    organization = relationship("Organization", back_populates="groups")
    enrollments = relationship("Enrollment", back_populates="group", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Group(id={self.group_id}, name='{self.name}', size={self.size})>"


class Teacher(Base):
    """Teacher model."""
    
    __tablename__ = "teachers"
    
    teacher_id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.org_id"), nullable=False, index=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(255), nullable=True, index=True)
    phone = Column(String(50), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    
    # Unique constraint: email unique within organization (if provided)
    __table_args__ = (UniqueConstraint('org_id', 'email', name='uq_org_teacher_email'),)
    
    # Relationships
    organization = relationship("Organization", back_populates="teachers")
    course_assignments = relationship("CourseAssignment", back_populates="teacher", cascade="all, delete-orphan")
    availabilities = relationship("TeacherAvailability", back_populates="teacher", cascade="all, delete-orphan")
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    def __repr__(self):
        return f"<Teacher(id={self.teacher_id}, name='{self.full_name}')>"


class Course(Base):
    """Course/subject model."""
    
    __tablename__ = "courses"
    
    course_id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.org_id"), nullable=False, index=True)
    name = Column(String(200), nullable=False)
    type = Column(String(50), nullable=True)  # lecture, seminar, lab, etc.
    is_active = Column(Boolean, nullable=False, default=True)
    
    # Relationships
    organization = relationship("Organization", back_populates="courses")
    course_assignments = relationship("CourseAssignment", back_populates="course", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Course(id={self.course_id}, name='{self.name}')>"


class CourseAssignment(Base):
    """Course assignment - who teaches what course."""
    
    __tablename__ = "course_assignments"
    
    assignment_id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.org_id"), nullable=False, index=True)
    course_id = Column(Integer, ForeignKey("courses.course_id"), nullable=False, index=True)
    teacher_id = Column(Integer, ForeignKey("teachers.teacher_id"), nullable=False, index=True)
    
    # Relationships
    organization = relationship("Organization", back_populates="course_assignments")
    course = relationship("Course", back_populates="course_assignments")
    teacher = relationship("Teacher", back_populates="course_assignments")
    enrollments = relationship("Enrollment", back_populates="assignment", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<CourseAssignment(id={self.assignment_id}, course_id={self.course_id}, teacher_id={self.teacher_id})>"


class Enrollment(Base):
    """Enrollment - which group takes which course assignment with planned hours."""
    
    __tablename__ = "enrollments"
    
    enrollment_id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.org_id"), nullable=False, index=True)
    assignment_id = Column(Integer, ForeignKey("course_assignments.assignment_id"), nullable=False, index=True)
    group_id = Column(Integer, ForeignKey("groups.group_id"), nullable=False, index=True)
    planned_hours = Column(Integer, nullable=False)
    unit = Column(String(20), nullable=False, default="per_week")
    
    # Relationships
    organization = relationship("Organization", back_populates="enrollments")
    assignment = relationship("CourseAssignment", back_populates="enrollments")
    group = relationship("Group", back_populates="enrollments")
    lesson_instances = relationship("LessonInstance", back_populates="enrollment", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Enrollment(id={self.enrollment_id}, assignment_id={self.assignment_id}, group_id={self.group_id}, hours={self.planned_hours})>"
