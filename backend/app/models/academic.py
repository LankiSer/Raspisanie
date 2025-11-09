"""Academic year and term models."""

from datetime import date
from sqlalchemy import Column, Integer, String, Date, ForeignKey
from sqlalchemy.orm import relationship
from ..core.database import Base


class AcademicYear(Base):
    """Academic year model."""
    
    __tablename__ = "academic_years"
    
    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.org_id"), nullable=False, index=True)
    name = Column(String(100), nullable=False)  # e.g., "2024-2025"
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    
    # Relationships
    organization = relationship("Organization", back_populates="academic_years")
    terms = relationship("Term", back_populates="academic_year", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<AcademicYear(id={self.id}, name='{self.name}')>"


class Term(Base):
    """Term/semester model."""
    
    __tablename__ = "terms"
    
    term_id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.org_id"), nullable=False, index=True)
    academic_year_id = Column(Integer, ForeignKey("academic_years.id"), nullable=False, index=True)
    name = Column(String(100), nullable=False)  # e.g., "Fall 2024", "Spring 2024"
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    
    # Relationships
    organization = relationship("Organization", back_populates="terms")
    academic_year = relationship("AcademicYear", back_populates="terms")
    lesson_instances = relationship("LessonInstance", back_populates="term", cascade="all, delete-orphan")
    generation_jobs = relationship("GenerationJob", back_populates="term", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Term(id={self.term_id}, name='{self.name}')>"
