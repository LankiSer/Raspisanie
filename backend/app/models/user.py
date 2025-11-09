"""User model and enums."""

import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Enum, func
from sqlalchemy.orm import relationship
from ..core.database import Base


class UserRole(enum.Enum):
    """User role enumeration."""
    SUPERADMIN = "SUPERADMIN"
    ADMIN = "ADMIN" 
    METHODIST = "METHODIST"
    TEACHER = "TEACHER"
    STUDENT = "STUDENT"


class User(Base):
    """User model."""
    
    __tablename__ = "users"
    
    user_id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.org_id"), nullable=False, index=True)
    email = Column(String(255), nullable=False, unique=True, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(Enum(UserRole, values_callable=lambda obj: [e.value for e in obj]), nullable=False, default=UserRole.STUDENT, index=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(
        DateTime(timezone=True), 
        server_default=func.now(),
        nullable=False
    )
    
    # Relationships
    organization = relationship("Organization", back_populates="users")
    change_logs = relationship("ChangeLog", back_populates="user")
    generation_jobs = relationship("GenerationJob", back_populates="created_by_user", 
                                    foreign_keys="GenerationJob.created_by")
    created_lessons = relationship("LessonInstance", back_populates="creator",
                                   foreign_keys="LessonInstance.created_by")
    updated_lessons = relationship("LessonInstance", back_populates="updater", 
                                   foreign_keys="LessonInstance.updated_by")
    
    def __repr__(self):
        return f"<User(id={self.user_id}, email='{self.email}', role='{self.role}')>"
