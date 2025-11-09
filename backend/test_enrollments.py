"""Test enrollments API directly."""

import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from app.core.config import settings
from app.models.educational import Enrollment, Group, CourseAssignment, Teacher, Course
from app.models.user import User
from app.models.organization import Organization
from app.models.lessons import Lesson
from app.models.scheduling import LessonInstance, ChangeLog, GenerationJob

async def test_enrollments():
    engine = create_async_engine(settings.DATABASE_URL, echo=True)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # Get first user
        result = await session.execute(select(User).where(User.user_id == 1))
        user = result.scalar_one_or_none()
        print(f"User: {user.user_id}, org_id: {user.org_id}")
        
        # Get enrollments for this user's organization
        result = await session.execute(
            select(Enrollment)
            .where(Enrollment.org_id == user.org_id)
            .limit(5)
        )
        enrollments = result.scalars().all()
        
        print(f"Found {len(enrollments)} enrollments")
        for enrollment in enrollments:
            print(f"Enrollment {enrollment.enrollment_id}: group_id={enrollment.group_id}, assignment_id={enrollment.assignment_id}, unit={enrollment.unit}")
            
            # Get related data
            group_result = await session.execute(select(Group).where(Group.group_id == enrollment.group_id))
            group = group_result.scalar_one_or_none()
            
            assignment_result = await session.execute(select(CourseAssignment).where(CourseAssignment.assignment_id == enrollment.assignment_id))
            assignment = assignment_result.scalar_one_or_none()
            
            if assignment:
                course_result = await session.execute(select(Course).where(Course.course_id == assignment.course_id))
                course = course_result.scalar_one_or_none()
                
                teacher_result = await session.execute(select(Teacher).where(Teacher.teacher_id == assignment.teacher_id))
                teacher = teacher_result.scalar_one_or_none()
                
                print(f"  Group: {group.name if group else 'None'}")
                print(f"  Course: {course.name if course else 'None'}")
                print(f"  Teacher: {teacher.first_name + ' ' + teacher.last_name if teacher else 'None'}")
    
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(test_enrollments())
