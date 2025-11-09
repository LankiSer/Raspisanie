"""Academic year and term schemas."""

from datetime import date
from pydantic import BaseModel


class AcademicYearBase(BaseModel):
    """Base academic year schema."""
    name: str
    start_date: date
    end_date: date


class AcademicYearCreate(AcademicYearBase):
    """Academic year creation schema."""
    org_id: int


class AcademicYearResponse(AcademicYearBase):
    """Academic year response schema."""
    id: int
    org_id: int
    
    class Config:
        from_attributes = True


class TermBase(BaseModel):
    """Base term schema."""
    name: str
    start_date: date
    end_date: date


class TermCreate(TermBase):
    """Term creation schema."""
    org_id: int
    academic_year_id: int


class TermResponse(TermBase):
    """Term response schema."""
    term_id: int
    org_id: int
    academic_year_id: int
    
    class Config:
        from_attributes = True
