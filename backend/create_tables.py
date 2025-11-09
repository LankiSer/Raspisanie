"""Create all tables directly using SQLAlchemy."""

import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from app.core.config import settings
from app.core.database import Base
from app.models.organization import Organization
from app.models.user import User
from app.models.educational import Group, Teacher, Course, CourseAssignment, Enrollment
from app.models.academic import AcademicYear, Term
from app.models.facilities import Room, TimeTableSlot, TeacherAvailability, Holiday
from app.models.lessons import Lesson
from app.models.scheduling import LessonInstance, ChangeLog, GenerationJob

async def create_tables():
    engine = create_async_engine(settings.DATABASE_URL, echo=True)
    async with engine.begin() as conn:
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)
        print("All tables created successfully!")
    
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(create_tables())
