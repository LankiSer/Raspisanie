"""Scheduling and lesson management models."""

import enum
from datetime import datetime, date
from sqlalchemy import Column, Integer, String, DateTime, Date, ForeignKey, Enum, Text, Float, JSON, func, UniqueConstraint
from sqlalchemy.orm import relationship
from ..core.database import Base


class LessonStatus(enum.Enum):
    """Lesson status enumeration."""
    PLANNED = "PLANNED"
    CONFIRMED = "CONFIRMED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    SKIPPED = "SKIPPED"
    MOVED = "MOVED"


class GenerationStatus(enum.Enum):
    """Generation job status enumeration."""
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class GenerationScope(enum.Enum):
    """Generation scope enumeration."""
    FULL = "FULL"
    PARTIAL = "PARTIAL"


class LessonInstance(Base):
    """Lesson instance model - represents a specific lesson occurrence."""
    
    __tablename__ = "lesson_instances"
    
    lesson_id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.org_id"), nullable=False, index=True)
    term_id = Column(Integer, ForeignKey("terms.term_id"), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    slot_id = Column(Integer, ForeignKey("time_slots.slot_id"), nullable=False, index=True)
    room_id = Column(Integer, ForeignKey("rooms.room_id"), nullable=True, index=True)  # can be null initially
    enrollment_id = Column(Integer, ForeignKey("enrollments.enrollment_id"), nullable=False, index=True)
    status = Column(Enum(LessonStatus, values_callable=lambda obj: [e.value for e in obj]), nullable=False, default=LessonStatus.PLANNED, index=True)
    reason = Column(Text, nullable=True)  # reason for cancellation, move, etc.
    created_by = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_by = Column(Integer, ForeignKey("users.user_id"), nullable=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    version = Column(Integer, nullable=False, default=1)  # for optimistic locking
    
    # Unique constraints to prevent conflicts
    __table_args__ = (
        # Room can only have one lesson per date/slot
        UniqueConstraint('org_id', 'date', 'slot_id', 'room_id', name='uq_org_date_slot_room'),
        # Index for common queries
    )
    
    # Relationships
    organization = relationship("Organization", back_populates="lesson_instances")
    term = relationship("Term", back_populates="lesson_instances")
    time_slot = relationship("TimeTableSlot", back_populates="lesson_instances")
    room = relationship("Room", back_populates="lesson_instances")
    enrollment = relationship("Enrollment", back_populates="lesson_instances")
    creator = relationship("User", foreign_keys=[created_by], back_populates="created_lessons")
    updater = relationship("User", foreign_keys=[updated_by], back_populates="updated_lessons")
    change_logs = relationship("ChangeLog", back_populates="lesson", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<LessonInstance(id={self.lesson_id}, date={self.date}, status='{self.status}')>"


class ChangeLog(Base):
    """Change log model for audit trail."""
    
    __tablename__ = "change_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.org_id"), nullable=False, index=True)
    lesson_id = Column(Integer, ForeignKey("lesson_instances.lesson_id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False, index=True)
    action = Column(Text, nullable=False)  # description of what changed
    payload_json = Column(JSON, nullable=True)  # before/after data
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    
    # Relationships
    organization = relationship("Organization", back_populates="change_logs")
    lesson = relationship("LessonInstance", back_populates="change_logs")
    user = relationship("User", back_populates="change_logs")
    
    def __repr__(self):
        return f"<ChangeLog(id={self.id}, lesson_id={self.lesson_id}, action='{self.action}')>"


class GenerationJob(Base):
    """Generation job model for schedule generation tasks."""
    
    __tablename__ = "generation_jobs"
    
    job_id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.org_id"), nullable=False, index=True)
    term_id = Column(Integer, ForeignKey("terms.term_id"), nullable=False, index=True)
    scope = Column(Enum(GenerationScope, values_callable=lambda obj: [e.value for e in obj]), nullable=False, index=True)
    from_date = Column(Date, nullable=False)
    to_date = Column(Date, nullable=False)
    ruleset_json = Column(JSON, nullable=False)  # generation parameters
    status = Column(Enum(GenerationStatus, values_callable=lambda obj: [e.value for e in obj]), nullable=False, default=GenerationStatus.PENDING, index=True)
    progress = Column(Float, nullable=False, default=0.0)  # 0.0 to 1.0
    created_by = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    finished_at = Column(DateTime(timezone=True), nullable=True)
    error = Column(Text, nullable=True)
    result_json = Column(JSON, nullable=True)  # generated lessons data (for preview)
    
    # Relationships
    organization = relationship("Organization", back_populates="generation_jobs")
    term = relationship("Term", back_populates="generation_jobs")
    created_by_user = relationship("User", foreign_keys=[created_by], back_populates="generation_jobs")
    
    def __repr__(self):
        return f"<GenerationJob(id={self.job_id}, status='{self.status}', progress={self.progress})>"
