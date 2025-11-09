"""Add test data for МГТУ organization (org_id: 1)."""

import asyncio
from datetime import time, date
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.models.educational import Group, Teacher, Course, CourseAssignment, Enrollment, HoursUnit
from app.models.academic import AcademicYear, Term
from app.models.facilities import Room, TimeTableSlot, TeacherAvailability, Holiday
from app.models.lessons import Lesson
from app.models.scheduling import LessonInstance, ChangeLog, GenerationJob

async def add_data_for_mgtu():
    engine = create_async_engine(settings.DATABASE_URL, echo=True)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # Use existing organization МГТУ (org_id: 1)
        org_id = 1
        
        # Create academic year for МГТУ
        academic_year = AcademicYear(
            org_id=org_id,
            name="2024-2025",
            start_date=date(2024, 9, 1),
            end_date=date(2025, 6, 30)
        )
        session.add(academic_year)
        await session.flush()
        
        # Create term
        term = Term(
            org_id=org_id,
            academic_year_id=academic_year.id,
            name="Осенний семестр 2024",
            start_date=date(2024, 9, 1),
            end_date=date(2024, 12, 31)
        )
        session.add(term)
        await session.flush()
        
        # Create groups with different generation types
        groups = []
        group_data = [
            ("Группа МГТУ-1", 25, 1, 2),  # 2 pairs in a row
            ("Группа МГТУ-2", 30, 1, 2),  # 2 pairs in a row
            ("Группа МГТУ-3", 28, 2, 3),  # 3 pairs in a row
            ("Группа МГТУ-4", 32, 2, 3),  # 3 pairs in a row
            ("Группа МГТУ-5", 35, 3, 5),  # 5 pairs in a row
        ]
        
        for name, size, year_level, generation_type in group_data:
            group = Group(
                org_id=org_id,
                name=name,
                size=size,
                year_level=year_level,
                generation_type=generation_type,
                is_active=True
            )
            session.add(group)
            groups.append(group)
        await session.flush()
        
        # Create teachers
        teachers = []
        teacher_data = [
            ("Александр", "Иванов", "ivanov@mgtu.ru", "+7-900-200-2000"),
            ("Екатерина", "Петрова", "petrova@mgtu.ru", "+7-900-201-2001"),
            ("Михаил", "Сидоров", "sidorov@mgtu.ru", "+7-900-202-2002"),
            ("Анна", "Козлова", "kozlova@mgtu.ru", "+7-900-203-2003"),
            ("Сергей", "Морозов", "morozov@mgtu.ru", "+7-900-204-2004"),
        ]
        
        for first_name, last_name, email, phone in teacher_data:
            teacher = Teacher(
                org_id=org_id,
                first_name=first_name,
                last_name=last_name,
                email=email,
                phone=phone,
                is_active=True
            )
            session.add(teacher)
            teachers.append(teacher)
        await session.flush()
        
        # Create courses
        courses = []
        course_data = [
            ("Высшая математика", "lecture"),
            ("Физика", "lecture"),
            ("Химия", "lecture"),
            ("Программирование", "lecture"),
            ("Английский язык", "lecture"),
        ]
        
        for name, course_type in course_data:
            course = Course(
                org_id=org_id,
                name=name,
                type=course_type,
                is_active=True
            )
            session.add(course)
            courses.append(course)
        await session.flush()
        
        # Create course assignments (each teacher teaches all courses)
        assignments = []
        for teacher in teachers:
            for course in courses:
                assignment = CourseAssignment(
                    org_id=org_id,
                    course_id=course.course_id,
                    teacher_id=teacher.teacher_id
                )
                session.add(assignment)
                assignments.append(assignment)
        await session.flush()
        
        # Create enrollments (each group studies all courses)
        for group in groups:
            for assignment in assignments:
                enrollment = Enrollment(
                    org_id=org_id,
                    assignment_id=assignment.assignment_id,
                    group_id=group.group_id,
                    planned_hours=120,
                    unit=HoursUnit.PER_TERM.value
                )
                session.add(enrollment)
        await session.flush()
        
        # Create rooms
        rooms = []
        room_data = [
            ("Аудитория МГТУ-101", 30, "lecture_hall", "Главный корпус"),
            ("Аудитория МГТУ-102", 35, "lecture_hall", "Главный корпус"),
            ("Аудитория МГТУ-201", 25, "lecture_hall", "Главный корпус"),
            ("Компьютерный класс МГТУ-1", 20, "computer_lab", "Главный корпус"),
            ("Лаборатория МГТУ-химии", 15, "lab", "Главный корпус"),
        ]
        
        for number, capacity, kind, building in room_data:
            room = Room(
                org_id=org_id,
                number=number,
                capacity=capacity,
                kind=kind,
                building=building,
                is_active=True
            )
            session.add(room)
            rooms.append(room)
        await session.flush()
        
        # Create time slots
        time_slots = []
        slot_data = [
            (time(9, 0), time(10, 30), "1-я пара", 10),
            (time(10, 40), time(12, 10), "2-я пара", 10),
            (time(12, 20), time(13, 50), "3-я пара", 10),
            (time(14, 0), time(15, 30), "4-я пара", 10),
            (time(15, 40), time(17, 10), "5-я пара", 0),
        ]
        
        for start, end, label, break_minutes in slot_data:
            slot = TimeTableSlot(
                org_id=org_id,
                start_time=start,
                end_time=end,
                break_minutes=break_minutes,
                label=label,
                weekday_mask=31  # Monday-Friday
            )
            session.add(slot)
            time_slots.append(slot)
        await session.flush()
        
        # Create teacher availabilities (Monday-Friday, 9:00-18:00)
        for teacher in teachers:
            for weekday in range(1, 6):  # Monday to Friday
                availability = TeacherAvailability(
                    org_id=org_id,
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
            (date(2025, 2, 23), "День защитника Отечества"),
        ]
        
        for holiday_date, name in holidays:
            holiday = Holiday(
                org_id=org_id,
                date=holiday_date,
                name=name
            )
            session.add(holiday)
        
        await session.commit()
        print("Test data for МГТУ created successfully!")
        print(f"Organization ID: {org_id}")
        print(f"Groups: {len(groups)}")
        print(f"Teachers: {len(teachers)}")
        print(f"Courses: {len(courses)}")
        print(f"Rooms: {len(rooms)}")
        print(f"Time slots: {len(time_slots)}")
    
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(add_data_for_mgtu())
