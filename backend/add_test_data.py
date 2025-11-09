"""Add test data to the database."""

import asyncio
from datetime import time, date
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
# Import all models to ensure relationships are properly configured
from app.models.organization import Organization
from app.models.user import User, UserRole
from app.models.educational import Group, Teacher, Course, CourseAssignment, Enrollment, HoursUnit
from app.models.academic import AcademicYear, Term
from app.models.facilities import Room, TimeTableSlot, TeacherAvailability, Holiday
from app.models.lessons import Lesson
from app.models.scheduling import LessonInstance, ChangeLog, GenerationJob

async def add_test_data():
    engine = create_async_engine(settings.DATABASE_URL, echo=True)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # Create organization
        org = Organization(
            name="Тестовый университет",
            locale="ru",
            tz="Europe/Moscow"
        )
        session.add(org)
        await session.flush()
        
        # Create admin user
        admin_user = User(
            org_id=org.org_id,
            email="admin@test.ru",
            password_hash="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/8Qz8K2",  # password: admin123
            role=UserRole.ADMIN,
            is_active=True
        )
        session.add(admin_user)
        await session.flush()
        
        # Create academic year
        academic_year = AcademicYear(
            org_id=org.org_id,
            name="2024-2025",
            start_date=date(2024, 9, 1),
            end_date=date(2025, 6, 30)
        )
        session.add(academic_year)
        await session.flush()
        
        # Create term
        term = Term(
            org_id=org.org_id,
            academic_year_id=academic_year.id,
            name="Осенний семестр 2024",
            start_date=date(2024, 9, 1),
            end_date=date(2024, 12, 31)
        )
        session.add(term)
        await session.flush()
        
        # Create groups
        groups = []
        for i in range(1, 6):
            group = Group(
                org_id=org.org_id,
                name=f"Группа {i}",
                size=25,
                year_level=1,
                generation_type=2 if i <= 2 else 3 if i <= 4 else 5,
                is_active=True
            )
            session.add(group)
            groups.append(group)
        await session.flush()
        
        # Create teachers
        teachers = []
        teacher_names = [
            ("Иван", "Петров"),
            ("Мария", "Сидорова"),
            ("Алексей", "Козлов"),
            ("Елена", "Морозова"),
            ("Дмитрий", "Волков")
        ]
        
        for i, (first_name, last_name) in enumerate(teacher_names):
            teacher = Teacher(
                org_id=org.org_id,
                first_name=first_name,
                last_name=last_name,
                email=f"teacher{i+1}@test.ru",
                phone=f"+7-900-{100+i:03d}-{1000+i:04d}",
                is_active=True
            )
            session.add(teacher)
            teachers.append(teacher)
        await session.flush()
        
        # Create courses
        courses = []
        course_names = [
            "Математика",
            "Физика", 
            "Химия",
            "Информатика",
            "Английский язык"
        ]
        
        for i, name in enumerate(course_names):
            course = Course(
                org_id=org.org_id,
                name=name,
                type="lecture",
                is_active=True
            )
            session.add(course)
            courses.append(course)
        await session.flush()
        
        # Create course assignments
        assignments = []
        for i, teacher in enumerate(teachers):
            for j, course in enumerate(courses):
                assignment = CourseAssignment(
                    org_id=org.org_id,
                    course_id=course.course_id,
                    teacher_id=teacher.teacher_id
                )
                session.add(assignment)
                assignments.append(assignment)
        await session.flush()
        
        # Create enrollments
        for i, group in enumerate(groups):
            for j, assignment in enumerate(assignments):
                if j % 5 == i:  # Each group gets one course per teacher
                    enrollment = Enrollment(
                        org_id=org.org_id,
                        assignment_id=assignment.assignment_id,
                        group_id=group.group_id,
                        planned_hours=120,
                        unit=HoursUnit.PER_TERM.value
                    )
                    session.add(enrollment)
        await session.flush()
        
        # Create rooms
        rooms = []
        for i in range(1, 6):
            room = Room(
                org_id=org.org_id,
                number=f"Аудитория {i}",
                capacity=30,
                kind="lecture_hall",
                building="Главный корпус",
                is_active=True
            )
            session.add(room)
            rooms.append(room)
        await session.flush()
        
        # Create time slots
        time_slots = []
        slot_times = [
            (time(9, 0), time(10, 30), "1-я пара"),
            (time(10, 40), time(12, 10), "2-я пара"),
            (time(12, 20), time(13, 50), "3-я пара"),
            (time(14, 0), time(15, 30), "4-я пара"),
            (time(15, 40), time(17, 10), "5-я пара")
        ]
        
        for i, (start, end, label) in enumerate(slot_times):
            slot = TimeTableSlot(
                org_id=org.org_id,
                start_time=start,
                end_time=end,
                break_minutes=10,
                label=label,
                weekday_mask=31  # Monday-Friday
            )
            session.add(slot)
            time_slots.append(slot)
        await session.flush()
        
        # Create teacher availabilities
        for teacher in teachers:
            for weekday in range(1, 6):  # Monday to Friday
                availability = TeacherAvailability(
                    org_id=org.org_id,
                    teacher_id=teacher.teacher_id,
                    weekday=weekday,
                    start_time=time(9, 0),
                    end_time=time(18, 0),
                    is_available=True
                )
                session.add(availability)
        
        # Create holidays
        holidays = [
            (date(2024, 11, 4), "День народного единства"),
            (date(2024, 12, 31), "Новый год"),
            (date(2025, 1, 1), "Новый год"),
            (date(2025, 1, 7), "Рождество Христово"),
            (date(2025, 2, 23), "День защитника Отечества")
        ]
        
        for holiday_date, name in holidays:
            holiday = Holiday(
                org_id=org.org_id,
                date=holiday_date,
                name=name
            )
            session.add(holiday)
        
        await session.commit()
        print("Test data added successfully!")
    
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(add_test_data())
