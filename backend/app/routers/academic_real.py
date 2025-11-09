"""Academic router with real database operations."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert, update, delete
from pydantic import BaseModel
from datetime import date

from app.core.database import get_db
from app.core.auth import get_current_active_user_or_demo
from app.models.academic import AcademicYear, Term
from app.models.user import User

router = APIRouter()

# Academic Year response models
class AcademicYearResponse(BaseModel):
    id: int
    org_id: int
    name: str
    start_date: date
    end_date: date

class AcademicYearCreate(BaseModel):
    org_id: int
    name: str
    start_date: date
    end_date: date

class AcademicYearUpdate(BaseModel):
    name: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None

# Academic Years endpoints
@router.get("/years", response_model=List[AcademicYearResponse])
async def get_academic_years(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user_or_demo)
):
    """Get academic years with pagination."""
    query = select(AcademicYear).where(AcademicYear.org_id == current_user.org_id)
    query = query.offset(skip).limit(limit)
    
    result = await db.execute(query)
    years = result.scalars().all()
    
    return [
        AcademicYearResponse(
            id=year.id,
            org_id=year.org_id,
            name=year.name,
            start_date=year.start_date,
            end_date=year.end_date
        )
        for year in years
    ]

@router.post("/years", response_model=AcademicYearResponse)
async def create_academic_year(
    year: AcademicYearCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user_or_demo)
):
    """Create a new academic year."""
    # Check if academic year with same name already exists
    existing_year = await db.execute(
        select(AcademicYear).where(
            AcademicYear.org_id == year.org_id,
            AcademicYear.name == year.name
        )
    )
    if existing_year.scalar_one_or_none():
        raise HTTPException(
            status_code=400, 
            detail=f"Academic year with name '{year.name}' already exists in this organization"
        )
    
    new_year = AcademicYear(
        org_id=year.org_id,
        name=year.name,
        start_date=year.start_date,
        end_date=year.end_date
    )
    
    db.add(new_year)
    await db.commit()
    await db.refresh(new_year)
    
    return AcademicYearResponse(
        id=new_year.id,
        org_id=new_year.org_id,
        name=new_year.name,
        start_date=new_year.start_date,
        end_date=new_year.end_date
    )

@router.patch("/years/{year_id}", response_model=AcademicYearResponse)
async def update_academic_year(
    year_id: int,
    year: AcademicYearUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user_or_demo)
):
    """Update an academic year."""
    result = await db.execute(
        select(AcademicYear).where(
            AcademicYear.id == year_id,
            AcademicYear.org_id == current_user.org_id
        )
    )
    existing_year = result.scalar_one_or_none()
    
    if not existing_year:
        raise HTTPException(status_code=404, detail="Academic year not found")
    
    update_data = year.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(existing_year, field, value)
    
    await db.commit()
    await db.refresh(existing_year)
    
    return AcademicYearResponse(
        id=existing_year.id,
        org_id=existing_year.org_id,
        name=existing_year.name,
        start_date=existing_year.start_date,
        end_date=existing_year.end_date
    )

@router.delete("/years/{year_id}")
async def delete_academic_year(
    year_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user_or_demo)
):
    """Delete an academic year."""
    result = await db.execute(
        select(AcademicYear).where(
            AcademicYear.id == year_id,
            AcademicYear.org_id == current_user.org_id
        )
    )
    existing_year = result.scalar_one_or_none()
    
    if not existing_year:
        raise HTTPException(status_code=404, detail="Academic year not found")
    
    await db.delete(existing_year)
    await db.commit()
    
    return {"message": "Academic year deleted successfully"}

# Term response models
class TermResponse(BaseModel):
    term_id: int
    org_id: int
    academic_year_id: int
    name: str
    start_date: date
    end_date: date

class TermCreate(BaseModel):
    org_id: int
    academic_year_id: int
    name: str
    start_date: date
    end_date: date

class TermUpdate(BaseModel):
    name: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None

# Terms endpoints
@router.get("/terms", response_model=List[TermResponse])
async def get_terms(
    skip: int = 0,
    limit: int = 100,
    academic_year_id: Optional[int] = None,
    is_active: Optional[bool] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user_or_demo)
):
    """Get terms with pagination."""
    query = select(Term).where(Term.org_id == current_user.org_id)
    
    if academic_year_id:
        query = query.where(Term.academic_year_id == academic_year_id)
    
    query = query.offset(skip).limit(limit)
    
    result = await db.execute(query)
    terms = result.scalars().all()
    
    return [
        TermResponse(
            term_id=term.term_id,
            org_id=term.org_id,
            academic_year_id=term.academic_year_id,
            name=term.name,
            start_date=term.start_date,
            end_date=term.end_date
        )
        for term in terms
    ]

@router.post("/terms", response_model=TermResponse)
async def create_term(
    term: TermCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user_or_demo)
):
    """Create a new term."""
    new_term = Term(
        org_id=term.org_id,
        academic_year_id=term.academic_year_id,
        name=term.name,
        start_date=term.start_date,
        end_date=term.end_date
    )
    
    db.add(new_term)
    await db.commit()
    await db.refresh(new_term)
    
    return TermResponse(
        term_id=new_term.term_id,
        org_id=new_term.org_id,
        academic_year_id=new_term.academic_year_id,
        name=new_term.name,
        start_date=new_term.start_date,
        end_date=new_term.end_date
    )

@router.patch("/terms/{term_id}", response_model=TermResponse)
async def update_term(
    term_id: int,
    term: TermUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user_or_demo)
):
    """Update a term."""
    result = await db.execute(
        select(Term).where(
            Term.term_id == term_id,
            Term.org_id == current_user.org_id
        )
    )
    existing_term = result.scalar_one_or_none()
    
    if not existing_term:
        raise HTTPException(status_code=404, detail="Term not found")
    
    update_data = term.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(existing_term, field, value)
    
    await db.commit()
    await db.refresh(existing_term)
    
    return TermResponse(
        term_id=existing_term.term_id,
        org_id=existing_term.org_id,
        academic_year_id=existing_term.academic_year_id,
        name=existing_term.name,
        start_date=existing_term.start_date,
        end_date=existing_term.end_date
    )

@router.delete("/terms/{term_id}")
async def delete_term(
    term_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user_or_demo)
):
    """Delete a term."""
    result = await db.execute(
        select(Term).where(
            Term.term_id == term_id,
            Term.org_id == current_user.org_id
        )
    )
    existing_term = result.scalar_one_or_none()
    
    if not existing_term:
        raise HTTPException(status_code=404, detail="Term not found")
    
    await db.delete(existing_term)
    await db.commit()
    
    return {"message": "Term deleted successfully"}
