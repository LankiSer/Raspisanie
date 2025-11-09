"""Debug generation preview logic."""

import asyncio
from datetime import date, timedelta
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from app.core.config import settings
from app.models.educational import Group, Teacher, Course, CourseAssignment, Enrollment
from app.models.facilities import Room, TimeTableSlot
from app.models.user import User
from app.models.organization import Organization
from app.models.lessons import Lesson
from app.models.scheduling import LessonInstance, ChangeLog, GenerationJob
from app.models.academic import AcademicYear, Term

async def debug_generation():
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # Get first user
        result = await session.execute(select(User).where(User.user_id == 1))
        user = result.scalar_one_or_none()
        org_id = user.org_id if user else 1
        
        print(f"Debug for org_id: {org_id}")
        
        # Load data from database
        groups_result = await session.execute(select(Group).where(Group.org_id == org_id))
        groups = groups_result.scalars().all()
        print(f"Groups: {len(groups)}")
        for group in groups:
            print(f"  - Group {group.group_id}: {group.name}, generation_type: {group.generation_type}")
        
        teachers_result = await session.execute(select(Teacher).where(Teacher.org_id == org_id))
        teachers = teachers_result.scalars().all()
        print(f"Teachers: {len(teachers)}")
        
        rooms_result = await session.execute(select(Room).where(Room.org_id == org_id))
        rooms = rooms_result.scalars().all()
        print(f"Rooms: {len(rooms)}")
        
        slots_result = await session.execute(select(TimeTableSlot).where(TimeTableSlot.org_id == org_id))
        slots = slots_result.scalars().all()
        print(f"Time slots: {len(slots)}")
        for slot in slots:
            print(f"  - Slot {slot.slot_id}: {slot.label} ({slot.start_time} - {slot.end_time})")
        
        enrollments_result = await session.execute(select(Enrollment).where(Enrollment.org_id == org_id))
        enrollments = enrollments_result.scalars().all()
        print(f"Enrollments: {len(enrollments)}")
        
        # Load course assignments
        assignment_ids = [e.assignment_id for e in enrollments]
        if assignment_ids:
            assignments_result = await session.execute(
                select(CourseAssignment).where(CourseAssignment.assignment_id.in_(assignment_ids))
            )
            assignments = assignments_result.scalars().all()
            print(f"Course assignments: {len(assignments)}")
            
            # Load courses
            course_ids = [a.course_id for a in assignments]
            if course_ids:
                courses_result = await session.execute(select(Course).where(Course.course_id.in_(course_ids)))
                courses = courses_result.scalars().all()
                print(f"Courses: {len(courses)}")
        
        # Test generation logic
        print("\n--- Testing generation logic ---")
        
        # Calculate lessons per week for each enrollment
        lessons_per_week_per_enrollment = {}
        for enrollment in enrollments:
            weekly_hours = enrollment.planned_hours / 18
            lessons_per_week = min(6, max(1, int(weekly_hours)))
            lessons_per_week_per_enrollment[enrollment.enrollment_id] = lessons_per_week
            print(f"Enrollment {enrollment.enrollment_id}: {enrollment.planned_hours} hours -> {lessons_per_week} lessons/week")
        
        # Test date range
        from_date = date.today()
        to_date = from_date + timedelta(days=7)
        print(f"\nDate range: {from_date} to {to_date}")
        
        current_date = from_date
        while current_date <= to_date:
            if current_date.weekday() < 5:  # Monday=0, Sunday=6
                print(f"\nProcessing {current_date} (weekday {current_date.weekday()})")
                
                # Group enrollments by group
                group_enrollments = {}
                for enrollment in enrollments:
                    if enrollment.group_id not in group_enrollments:
                        group_enrollments[enrollment.group_id] = []
                    group_enrollments[enrollment.group_id].append(enrollment)
                
                print(f"Group enrollments: {len(group_enrollments)} groups")
                
                for group_id, group_enrollments_list in group_enrollments.items():
                    group = next((g for g in groups if g.group_id == group_id), None)
                    if not group:
                        print(f"  Group {group_id}: Not found!")
                        continue
                    
                    print(f"  Group {group_id} ({group.name}): {len(group_enrollments_list)} enrollments")
                    
                    # Calculate total lessons for this group this week
                    total_group_lessons = sum(lessons_per_week_per_enrollment[e.enrollment_id] for e in group_enrollments_list)
                    print(f"    Total lessons per week: {total_group_lessons}")
                    
                    # Distribute lessons across weekdays
                    weekday = current_date.weekday()
                    if total_group_lessons > 0:
                        base_lessons_per_day = total_group_lessons // 5
                        extra_lessons = total_group_lessons % 5
                        
                        if weekday < extra_lessons:
                            lessons_this_day = base_lessons_per_day + 1
                        else:
                            lessons_this_day = base_lessons_per_day
                        
                        print(f"    Lessons for {current_date}: {lessons_this_day}")
                    else:
                        print(f"    No lessons for {current_date}")
            
            current_date += timedelta(days=1)
    
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(debug_generation())
