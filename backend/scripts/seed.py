#!/usr/bin/env python3
"""Seed script to populate database with demo data."""

import asyncio
import sys
import os
from datetime import date, time, datetime, timedelta

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from app.core.config import settings
from app.core.database import Base
from app.core.auth import get_password_hash
from app.models import (
    Organization, User, UserRole, AcademicYear, Term,
    Group, Teacher, Course, CourseAssignment, Enrollment, HoursUnit,
    Room, TimeTableSlot, TeacherAvailability, Holiday,
    LessonInstance, LessonStatus
)


async def create_seed_data():
    """Create demo data for the application."""
    
    print("🌱 Starting seed data creation...")
    
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    
    # Create session
    async_session = async_sessionmaker(engine, expire_on_commit=False)
    
    async with async_session() as session:
        try:
            # 1. Create demo organization
            print("📚 Creating organization...")
            org = Organization(
                name="Московский технический университет",
                locale="ru",
                tz="Europe/Moscow"
            )
            session.add(org)
            await session.flush()  # Get org_id
            
            # 2. Create demo users
            print("👥 Creating users...")
            admin_user = User(
                org_id=org.org_id,
                email="admin@university.edu",
                password_hash=get_password_hash("admin123"),
                role=UserRole.ADMIN,
                is_active=True
            )
            
            methodist_user = User(
                org_id=org.org_id,
                email="methodist@university.edu",
                password_hash=get_password_hash("methodist123"),
                role=UserRole.METHODIST,
                is_active=True
            )
            
            teacher1_user = User(
                org_id=org.org_id,
                email="teacher1@university.edu", 
                password_hash=get_password_hash("teacher123"),
                role=UserRole.TEACHER,
                is_active=True
            )
            
            session.add_all([admin_user, methodist_user, teacher1_user])
            await session.flush()
            
            # 3. Create academic year and term
            print("📅 Creating academic year and term...")
            academic_year = AcademicYear(
                org_id=org.org_id,
                name="2024-2025",
                start_date=date(2024, 9, 1),
                end_date=date(2025, 6, 30)
            )
            session.add(academic_year)
            await session.flush()
            
            fall_term = Term(
                org_id=org.org_id,
                academic_year_id=academic_year.id,
                name="Осенний семестр 2024",
                start_date=date(2024, 9, 1),
                end_date=date(2024, 12, 31)
            )
            session.add(fall_term)
            await session.flush()
            
            # 4. Create time slots
            print("⏰ Creating time slots...")
            time_slots = [
                TimeTableSlot(
                    org_id=org.org_id,
                    start_time=time(9, 0),
                    end_time=time(10, 30),
                    break_minutes=10,
                    label="1 пара",
                    weekday_mask=31  # Mon-Fri
                ),
                TimeTableSlot(
                    org_id=org.org_id,
                    start_time=time(10, 40),
                    end_time=time(12, 10),
                    break_minutes=30,
                    label="2 пара",
                    weekday_mask=31
                ),
                TimeTableSlot(
                    org_id=org.org_id,
                    start_time=time(12, 40),
                    end_time=time(14, 10),
                    break_minutes=10,
                    label="3 пара",
                    weekday_mask=31
                ),
                TimeTableSlot(
                    org_id=org.org_id,
                    start_time=time(14, 20),
                    end_time=time(15, 50),
                    break_minutes=10,
                    label="4 пара",
                    weekday_mask=31
                ),
                TimeTableSlot(
                    org_id=org.org_id,
                    start_time=time(16, 0),
                    end_time=time(17, 30),
                    break_minutes=0,
                    label="5 пара",
                    weekday_mask=31
                )
            ]
            session.add_all(time_slots)
            await session.flush()
            
            # 5. Create groups
            print("🎓 Creating groups...")
            groups = [
                Group(
                    org_id=org.org_id,
                    name="ИУ5-61Б",
                    size=25,
                    year_level=3,
                    generation_type=2,
                    is_active=True
                ),
                Group(
                    org_id=org.org_id,
                    name="ИУ5-62Б",
                    size=28,
                    year_level=3,
                    generation_type=2,
                    is_active=True
                ),
                Group(
                    org_id=org.org_id,
                    name="ИУ6-61Б",
                    size=30,
                    year_level=3,
                    generation_type=3,
                    is_active=True
                )
            ]
            session.add_all(groups)
            await session.flush()
            
            # 6. Create teachers
            print("👨‍🏫 Creating teachers...")
            teachers = [
                Teacher(
                    org_id=org.org_id,
                    first_name="Иван",
                    last_name="Петров",
                    email="petrov@university.edu",
                    phone="+7-499-123-45-67",
                    is_active=True
                ),
                Teacher(
                    org_id=org.org_id,
                    first_name="Елена",
                    last_name="Сидорова",
                    email="sidorova@university.edu",
                    phone="+7-499-765-43-21",
                    is_active=True
                ),
                Teacher(
                    org_id=org.org_id,
                    first_name="Александр",
                    last_name="Козлов",
                    email="kozlov@university.edu",
                    phone="+7-499-555-12-34",
                    is_active=True
                )
            ]
            session.add_all(teachers)
            await session.flush()
            
            # 7. Create teacher availability
            print("📋 Creating teacher availability...")
            availabilities = []
            for teacher in teachers:
                # Monday to Friday, 9:00-18:00
                for weekday in range(1, 6):  # 1=Monday, 5=Friday
                    availabilities.append(
                        TeacherAvailability(
                            org_id=org.org_id,
                            teacher_id=teacher.teacher_id,
                            weekday=weekday,
                            start_time=time(9, 0),
                            end_time=time(18, 0),
                            is_available=True
                        )
                    )
            session.add_all(availabilities)
            
            # 8. Create courses
            print("📖 Creating courses...")
            courses = [
                Course(
                    org_id=org.org_id,
                    name="Математический анализ",
                    type="lecture",
                    is_active=True
                ),
                Course(
                    org_id=org.org_id,
                    name="Программирование на Python",
                    type="practical",
                    is_active=True
                ),
                Course(
                    org_id=org.org_id,
                    name="Базы данных",
                    type="lecture",
                    is_active=True
                ),
                Course(
                    org_id=org.org_id,
                    name="Компьютерная графика",
                    type="lab",
                    is_active=True
                ),
                Course(
                    org_id=org.org_id,
                    name="Английский язык",
                    type="practical",
                    is_active=True
                )
            ]
            session.add_all(courses)
            await session.flush()
            
            # 9. Create course assignments (who teaches what)
            print("🎯 Creating course assignments...")
            assignments = [
                CourseAssignment(org_id=org.org_id, course_id=courses[0].course_id, teacher_id=teachers[0].teacher_id),
                CourseAssignment(org_id=org.org_id, course_id=courses[1].course_id, teacher_id=teachers[1].teacher_id),
                CourseAssignment(org_id=org.org_id, course_id=courses[2].course_id, teacher_id=teachers[2].teacher_id),
                CourseAssignment(org_id=org.org_id, course_id=courses[3].course_id, teacher_id=teachers[1].teacher_id),
                CourseAssignment(org_id=org.org_id, course_id=courses[4].course_id, teacher_id=teachers[2].teacher_id),
            ]
            session.add_all(assignments)
            await session.flush()
            
            # 10. Create enrollments (group takes course assignment)
            print("📝 Creating enrollments...")
            enrollments = []
            for group in groups:
                for assignment in assignments:
                    hours = 3 if assignment.course.type == "lecture" else 2
                    enrollments.append(
                        Enrollment(
                            org_id=org.org_id,
                            assignment_id=assignment.assignment_id,
                            group_id=group.group_id,
                            planned_hours=hours,
                            unit=HoursUnit.per_week
                        )
                    )
            session.add_all(enrollments)
            await session.flush()
            
            # 11. Create rooms
            print("🏢 Creating rooms...")
            rooms = [
                Room(org_id=org.org_id, number="101", capacity=40, kind="lecture hall", building="ГУК", is_active=True),
                Room(org_id=org.org_id, number="102", capacity=30, kind="classroom", building="ГУК", is_active=True),
                Room(org_id=org.org_id, number="201", capacity=20, kind="computer lab", building="ГУК", is_active=True),
                Room(org_id=org.org_id, number="202", capacity=35, kind="classroom", building="ГУК", is_active=True),
                Room(org_id=org.org_id, number="301", capacity=25, kind="seminar room", building="ГУК", is_active=True),
                Room(org_id=org.org_id, number="302", capacity=50, kind="lecture hall", building="ГУК", is_active=True)
            ]
            session.add_all(rooms)
            await session.flush()
            
            # 12. Create holidays
            print("🎉 Creating holidays...")
            holidays = [
                Holiday(org_id=org.org_id, date=date(2024, 11, 4), name="День народного единства"),
                Holiday(org_id=org.org_id, date=date(2024, 12, 31), name="Новый год"),
                Holiday(org_id=org.org_id, date=date(2025, 1, 1), name="Новогодние каникулы"),
                Holiday(org_id=org.org_id, date=date(2025, 1, 2), name="Новогодние каникулы"),
                Holiday(org_id=org.org_id, date=date(2025, 1, 3), name="Новогодние каникулы"),
                Holiday(org_id=org.org_id, date=date(2025, 1, 6), name="Новогодние каникулы"),
                Holiday(org_id=org.org_id, date=date(2025, 1, 7), name="Новогодние каникулы"),
                Holiday(org_id=org.org_id, date=date(2025, 1, 8), name="Новогодние каникулы"),
            ]
            session.add_all(holidays)
            
            # 13. Create some sample lessons
            print("📅 Creating sample lessons...")
            sample_lessons = [
                LessonInstance(
                    org_id=org.org_id,
                    term_id=fall_term.term_id,
                    date=date(2024, 11, 11),  # Monday
                    slot_id=time_slots[0].slot_id,
                    room_id=rooms[0].room_id,
                    enrollment_id=enrollments[0].enrollment_id,
                    status=LessonStatus.PLANNED,
                    created_by=admin_user.user_id,
                    version=1
                ),
                LessonInstance(
                    org_id=org.org_id,
                    term_id=fall_term.term_id,
                    date=date(2024, 11, 11),
                    slot_id=time_slots[1].slot_id,
                    room_id=rooms[1].room_id,
                    enrollment_id=enrollments[1].enrollment_id,
                    status=LessonStatus.SCHEDULED,
                    created_by=admin_user.user_id,
                    version=1
                ),
                LessonInstance(
                    org_id=org.org_id,
                    term_id=fall_term.term_id,
                    date=date(2024, 11, 12),  # Tuesday
                    slot_id=time_slots[0].slot_id,
                    room_id=rooms[2].room_id,
                    enrollment_id=enrollments[2].enrollment_id,
                    status=LessonStatus.PLANNED,
                    created_by=admin_user.user_id,
                    version=1
                )
            ]
            session.add_all(sample_lessons)
            
            # Commit all changes
            await session.commit()
            
            print("\n✅ Seed data created successfully!")
            print(f"📊 Statistics:")
            print(f"   🏛️  Organization: {org.name}")
            print(f"   👤 Users: {len([admin_user, methodist_user, teacher1_user])}")
            print(f"   👥 Groups: {len(groups)}")
            print(f"   👨‍🏫 Teachers: {len(teachers)}")
            print(f"   📚 Courses: {len(courses)}")
            print(f"   🏢 Rooms: {len(rooms)}")
            print(f"   ⏰ Time slots: {len(time_slots)}")
            print(f"   📝 Enrollments: {len(enrollments)}")
            print(f"   📅 Sample lessons: {len(sample_lessons)}")
            
            print(f"\n🔑 Login credentials:")
            print(f"   Admin: admin@university.edu / admin123")
            print(f"   Methodist: methodist@university.edu / methodist123")
            print(f"   Teacher: teacher1@university.edu / teacher123")
            
        except Exception as e:
            print(f"❌ Error creating seed data: {e}")
            await session.rollback()
            raise
    
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(create_seed_data())