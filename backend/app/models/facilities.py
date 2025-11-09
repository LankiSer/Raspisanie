"""Facilities and scheduling infrastructure models."""

from datetime import time, date
from sqlalchemy import Column, Integer, String, Boolean, Time, Date, ForeignKey, SmallInteger, UniqueConstraint
from sqlalchemy.orm import relationship
from ..core.database import Base


class Room(Base):
    """Room/classroom model."""
    
    __tablename__ = "rooms"
    
    room_id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.org_id"), nullable=False, index=True)
    number = Column(String(50), nullable=False)  # room number/identifier
    capacity = Column(Integer, nullable=False, default=30)
    kind = Column(String(50), nullable=True)  # lecture hall, computer lab, etc.
    building = Column(String(100), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    
    # Relationships
    organization = relationship("Organization", back_populates="rooms")
    lesson_instances = relationship("LessonInstance", back_populates="room")
    
    def __repr__(self):
        return f"<Room(id={self.room_id}, number='{self.number}', capacity={self.capacity})>"


class TimeTableSlot(Base):
    """Time slot configuration model."""
    
    __tablename__ = "time_slots"
    
    slot_id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.org_id"), nullable=False, index=True)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    break_minutes = Column(Integer, nullable=False, default=10)  # break after this slot
    label = Column(String(50), nullable=True)  # "1st period", "Morning", etc.
    weekday_mask = Column(SmallInteger, nullable=False, default=31)  # bitmask for Mon-Fri (1-5), 31 = 11111
    
    # Relationships
    organization = relationship("Organization", back_populates="time_slots")
    lesson_instances = relationship("LessonInstance", back_populates="time_slot")
    
    def is_available_on_weekday(self, weekday: int) -> bool:
        """Check if slot is available on given weekday (1=Monday, 7=Sunday)."""
        if weekday < 1 or weekday > 7:
            return False
        # Convert to 0-based and check bit
        bit_position = weekday - 1
        return bool(self.weekday_mask & (1 << bit_position))
    
    def __repr__(self):
        return f"<TimeTableSlot(id={self.slot_id}, time={self.start_time}-{self.end_time})>"


class TeacherAvailability(Base):
    """Teacher availability model."""
    
    __tablename__ = "teacher_availabilities"
    
    availability_id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.org_id"), nullable=False, index=True)
    teacher_id = Column(Integer, ForeignKey("teachers.teacher_id"), nullable=False, index=True)
    weekday = Column(Integer, nullable=False)  # 1=Monday, 7=Sunday
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    is_available = Column(Boolean, nullable=False, default=True)  # True=available, False=unavailable
    
    # Relationships
    organization = relationship("Organization", back_populates="teacher_availabilities")
    teacher = relationship("Teacher", back_populates="availabilities")
    
    def __repr__(self):
        return f"<TeacherAvailability(teacher_id={self.teacher_id}, weekday={self.weekday}, {self.start_time}-{self.end_time}, available={self.is_available})>"


class Holiday(Base):
    """Holiday model."""
    
    __tablename__ = "holidays"
    
    holiday_id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.org_id"), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    
    # Unique constraint: one holiday per date per organization
    __table_args__ = (UniqueConstraint('org_id', 'date', name='uq_org_holiday_date'),)
    
    # Relationships
    organization = relationship("Organization", back_populates="holidays")
    
    def __repr__(self):
        return f"<Holiday(id={self.holiday_id}, date={self.date}, name='{self.name}')>"
