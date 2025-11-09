"""Tests for schedule generation."""

import pytest
from datetime import date, time
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    Group, Teacher, Course, CourseAssignment, Enrollment, 
    Room, TimeTableSlot, Term, AcademicYear, HoursUnit
)


@pytest.fixture
async def test_basic_data(db_session: AsyncSession, test_organization):
    """Create basic test data for generation."""
    
    # Academic year and term
    academic_year = AcademicYear(
        org_id=test_organization.org_id,
        name="2024-2025",
        start_date=date(2024, 9, 1),
        end_date=date(2025, 6, 30)
    )
    db_session.add(academic_year)
    await db_session.flush()
    
    term = Term(
        org_id=test_organization.org_id,
        academic_year_id=academic_year.id,
        name="Fall 2024",
        start_date=date(2024, 9, 1),
        end_date=date(2024, 12, 31)
    )
    db_session.add(term)
    await db_session.flush()
    
    # Time slots
    time_slots = [
        TimeTableSlot(
            org_id=test_organization.org_id,
            start_time=time(9, 0),
            end_time=time(10, 30),
            break_minutes=10,
            weekday_mask=31
        ),
        TimeTableSlot(
            org_id=test_organization.org_id,
            start_time=time(10, 40),
            end_time=time(12, 10),
            break_minutes=30,
            weekday_mask=31
        )
    ]
    db_session.add_all(time_slots)
    await db_session.flush()
    
    # Groups
    group = Group(
        org_id=test_organization.org_id,
        name="Test Group",
        size=25,
        year_level=1
    )
    db_session.add(group)
    await db_session.flush()
    
    # Teachers
    teacher = Teacher(
        org_id=test_organization.org_id,
        first_name="Test",
        last_name="Teacher",
        email="teacher@test.edu"
    )
    db_session.add(teacher)
    await db_session.flush()
    
    # Courses
    course = Course(
        org_id=test_organization.org_id,
        name="Test Subject",
        type="lecture"
    )
    db_session.add(course)
    await db_session.flush()
    
    # Assignment
    assignment = CourseAssignment(
        org_id=test_organization.org_id,
        course_id=course.course_id,
        teacher_id=teacher.teacher_id
    )
    db_session.add(assignment)
    await db_session.flush()
    
    # Enrollment
    enrollment = Enrollment(
        org_id=test_organization.org_id,
        assignment_id=assignment.assignment_id,
        group_id=group.group_id,
        planned_hours=2,
        unit=HoursUnit.per_week
    )
    db_session.add(enrollment)
    await db_session.flush()
    
    # Rooms
    room = Room(
        org_id=test_organization.org_id,
        number="101",
        capacity=30,
        kind="classroom"
    )
    db_session.add(room)
    await db_session.flush()
    
    await db_session.commit()
    
    return {
        "term": term,
        "time_slots": time_slots,
        "group": group,
        "teacher": teacher,
        "course": course,
        "assignment": assignment,
        "enrollment": enrollment,
        "room": room
    }


@pytest.mark.asyncio
async def test_generation_preview(
    client: AsyncClient,
    methodist_auth_headers,
    test_organization,
    test_basic_data
):
    """Test schedule generation preview."""
    
    response = await client.post(
        "/api/v1/generation/preview",
        headers=methodist_auth_headers,
        json={
            "org_id": test_organization.org_id,
            "term_id": test_basic_data["term"].term_id,
            "scope": "week",
            "from_date": "2024-11-11",
            "to_date": "2024-11-17",
            "ruleset": {
                "respect_availability": True,
                "max_lessons_per_day_group": 6,
                "max_lessons_per_day_teacher": 8,
                "room_capacity_check": True,
                "soft_weights": {
                    "minimize_gaps_group": 1.0,
                    "minimize_gaps_teacher": 1.0,
                    "balance_days": 1.0,
                    "preferred_rooms": 0.5
                }
            }
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert "proposals" in data
    assert "stats" in data
    assert "success" in data
    assert isinstance(data["proposals"], list)


@pytest.mark.asyncio
async def test_generation_unauthorized(
    client: AsyncClient,
    test_organization,
    test_basic_data
):
    """Test generation without authentication."""
    
    response = await client.post(
        "/api/v1/generation/preview",
        json={
            "org_id": test_organization.org_id,
            "term_id": test_basic_data["term"].term_id,
            "scope": "week",
            "from_date": "2024-11-11",
            "to_date": "2024-11-17",
            "ruleset": {
                "respect_availability": True,
                "max_lessons_per_day_group": 6,
                "max_lessons_per_day_teacher": 8,
                "room_capacity_check": True
            }
        }
    )
    
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_generation_wrong_organization(
    client: AsyncClient,
    methodist_auth_headers,
    test_basic_data
):
    """Test generation for wrong organization."""
    
    response = await client.post(
        "/api/v1/generation/preview",
        headers=methodist_auth_headers,
        json={
            "org_id": 999,  # Wrong org_id
            "term_id": test_basic_data["term"].term_id,
            "scope": "week",
            "from_date": "2024-11-11",
            "to_date": "2024-11-17",
            "ruleset": {
                "respect_availability": True,
                "max_lessons_per_day_group": 6,
                "max_lessons_per_day_teacher": 8,
                "room_capacity_check": True
            }
        }
    )
    
    assert response.status_code == 403
