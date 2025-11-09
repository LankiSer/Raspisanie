"""Create test data for the application."""

import asyncio
from datetime import time, date
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.models.organization import Organization
from app.models.user import User, UserRole
from app.models.educational import Group, Teacher, Course, CourseAssignment, Enrollment
from app.models.academic import AcademicYear, Term
from app.models.facilities import Room, TimeTableSlot, TeacherAvailability, Holiday
from app.models.scheduling import LessonInstance, ChangeLog, GenerationJob
from app.core.auth import get_password_hash

async def create_test_data():
    engine = create_async_engine(settings.DATABASE_URL, echo=True)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # Create organization
        org = Organization(
            name="МГТУ",
            locale="ru",
            tz="Europe/Moscow"
        )
        session.add(org)
        await session.flush()

        # Create admin user
        admin_user = User(
            org_id=org.org_id,
            email="admin@mgtu.ru",
            password_hash=get_password_hash("admin123"),
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
        group_names = [
            "ИСП-422П",  # Информационные системы и программирование
            "ПСО-421П",  # Программное обеспечение
            "ИБ-423П",   # Информационная безопасность
            "СА-424П",   # Системное администрирование
            "КС-425П"    # Компьютерные сети
        ]
        for i, name in enumerate(group_names, 1):
            group = Group(
                org_id=org.org_id,
                name=name,
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
            ("Иван", "Иванов"),
            ("Мария", "Петрова"),
            ("Сергей", "Сидоров"),
            ("Елена", "Кузнецова"),
            ("Алексей", "Смирнов")
        ]
        for i, (first_name, last_name) in enumerate(teacher_names, 1):
            teacher = Teacher(
                org_id=org.org_id,
                first_name=first_name,
                last_name=last_name,
                email=f"{first_name.lower()}.{last_name.lower()}@mgtu.ru",
                phone=f"+7-900-{i:03d}-00-00",
                is_active=True
            )
            session.add(teacher)
            teachers.append(teacher)
        await session.flush()

        # Create courses
        courses = []
        course_names = ["Математика", "Физика", "Химия", "Программирование", "Английский язык"]
        for i, name in enumerate(course_names, 1):
            course = Course(
                org_id=org.org_id,
                name=name,
                type="Лекция",
                is_active=True
            )
            session.add(course)
            courses.append(course)
        await session.flush()

        # Create rooms
        rooms = []
        room_data = [
            ("101", 30, "Лекционная"),
            ("102", 25, "Практическая"),
            ("103", 35, "Лекционная"),
            ("201", 20, "Компьютерная"),
            ("202", 40, "Лекционная")
        ]
        for number, capacity, kind in room_data:
            room = Room(
                org_id=org.org_id,
                number=number,
                capacity=capacity,
                kind=kind,
                building="Главный корпус",
                is_active=True
            )
            session.add(room)
            rooms.append(room)
        await session.flush()

        # Create time slots
        time_slots = []
        times = [
            (time(9, 0), time(10, 30), "1-я пара"),
            (time(10, 40), time(12, 10), "2-я пара"),
            (time(12, 20), time(13, 50), "3-я пара"),
            (time(14, 0), time(15, 30), "4-я пара"),
            (time(15, 40), time(17, 10), "5-я пара")
        ]
        for start_time, end_time, label in times:
            slot = TimeTableSlot(
                org_id=org.org_id,
                start_time=start_time,
                end_time=end_time,
                break_minutes=10,
                label=label,
                weekday_mask=31  # All weekdays
            )
            session.add(slot)
            time_slots.append(slot)
        await session.flush()

        # Create course assignments
        assignments = []
        for i in range(5):
            assignment = CourseAssignment(
                org_id=org.org_id,
                course_id=courses[i].course_id,
                teacher_id=teachers[i].teacher_id
            )
            session.add(assignment)
            assignments.append(assignment)
        await session.flush()

        # Create enrollments
        for group in groups:
            for assignment in assignments:
                enrollment = Enrollment(
                    org_id=org.org_id,
                    assignment_id=assignment.assignment_id,
                    group_id=group.group_id,
                    planned_hours=120,
                    unit="per_term"
                )
                session.add(enrollment)
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
        await session.flush()

        # Create holidays
        holidays = [
            (date(2024, 11, 4), "День народного единства"),
            (date(2024, 12, 31), "Новый год"),
            (date(2025, 1, 1), "Новый год"),
            (date(2025, 1, 7), "Рождество Христово"),
            (date(2025, 2, 23), "День защитника Отечества")
        ]
        for holiday_date, holiday_name in holidays:
            holiday = Holiday(
                org_id=org.org_id,
                date=holiday_date,
                name=holiday_name
            )
            session.add(holiday)
        await session.flush()

        await session.commit()
        print("Test data created successfully!")
        print(f"Organization: {org.name} (ID: {org.org_id})")
        print(f"Admin user: {admin_user.email}")
        print(f"Groups: {len(groups)}")
        print(f"Teachers: {len(teachers)}")
        print(f"Courses: {len(courses)}")
        print(f"Rooms: {len(rooms)}")
        print(f"Time slots: {len(time_slots)}")
        print(f"Course assignments: {len(assignments)}")

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(create_test_data())
