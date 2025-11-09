#!/usr/bin/env python3
"""Initialize database with all tables."""

import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from app.core.config import settings
from app.models.organization import Organization
from app.models.user import User, UserRole
from app.models.academic import AcademicYear, Term
from app.models.educational import Group, Teacher, Course, CourseAssignment, Enrollment
from app.models.facilities import Room, TimeTableSlot, TeacherAvailability, Holiday
from app.models.scheduling import LessonInstance, LessonStatus, ChangeLog, GenerationJob, GenerationStatus
from app.models.lessons import Lesson

async def create_tables():
    """Create all database tables."""
    engine = create_async_engine(settings.DATABASE_URL)
    
    async with engine.begin() as conn:
        # Import all models to register them
        from app.models import organization, user, academic, educational, facilities, scheduling, lessons
        
        # Create all tables
        await conn.run_sync(lambda conn: conn.execute("""
            CREATE TABLE IF NOT EXISTS organizations (
                org_id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                locale VARCHAR(10) DEFAULT 'ru',
                tz VARCHAR(50) DEFAULT 'Europe/Moscow',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """))
        
        await conn.run_sync(lambda conn: conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id SERIAL PRIMARY KEY,
                org_id INTEGER REFERENCES organizations(org_id),
                email VARCHAR(255) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                role VARCHAR(50) NOT NULL,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """))
        
        await conn.run_sync(lambda conn: conn.execute("""
            CREATE TABLE IF NOT EXISTS academic_years (
                id SERIAL PRIMARY KEY,
                org_id INTEGER REFERENCES organizations(org_id),
                name VARCHAR(100) NOT NULL,
                start_date DATE NOT NULL,
                end_date DATE NOT NULL
            );
        """))
        
        await conn.run_sync(lambda conn: conn.execute("""
            CREATE TABLE IF NOT EXISTS terms (
                term_id SERIAL PRIMARY KEY,
                org_id INTEGER REFERENCES organizations(org_id),
                academic_year_id INTEGER REFERENCES academic_years(id),
                name VARCHAR(100) NOT NULL,
                start_date DATE NOT NULL,
                end_date DATE NOT NULL
            );
        """))
        
        await conn.run_sync(lambda conn: conn.execute("""
            CREATE TABLE IF NOT EXISTS groups (
                group_id SERIAL PRIMARY KEY,
                org_id INTEGER REFERENCES organizations(org_id),
                name VARCHAR(100) NOT NULL,
                size INTEGER DEFAULT 25,
                year_level INTEGER,
                generation_type INTEGER DEFAULT 2,
                is_active BOOLEAN DEFAULT TRUE,
                UNIQUE(org_id, name)
            );
        """))
        
        await conn.run_sync(lambda conn: conn.execute("""
            CREATE TABLE IF NOT EXISTS teachers (
                teacher_id SERIAL PRIMARY KEY,
                org_id INTEGER REFERENCES organizations(org_id),
                first_name VARCHAR(100) NOT NULL,
                last_name VARCHAR(100) NOT NULL,
                email VARCHAR(255),
                phone VARCHAR(50),
                is_active BOOLEAN DEFAULT TRUE,
                UNIQUE(org_id, email)
            );
        """))
        
        await conn.run_sync(lambda conn: conn.execute("""
            CREATE TABLE IF NOT EXISTS courses (
                course_id SERIAL PRIMARY KEY,
                org_id INTEGER REFERENCES organizations(org_id),
                name VARCHAR(200) NOT NULL,
                type VARCHAR(50),
                is_active BOOLEAN DEFAULT TRUE
            );
        """))
        
        await conn.run_sync(lambda conn: conn.execute("""
            CREATE TABLE IF NOT EXISTS course_assignments (
                assignment_id SERIAL PRIMARY KEY,
                org_id INTEGER REFERENCES organizations(org_id),
                course_id INTEGER REFERENCES courses(course_id),
                teacher_id INTEGER REFERENCES teachers(teacher_id)
            );
        """))
        
        await conn.run_sync(lambda conn: conn.execute("""
            CREATE TABLE IF NOT EXISTS enrollments (
                enrollment_id SERIAL PRIMARY KEY,
                org_id INTEGER REFERENCES organizations(org_id),
                assignment_id INTEGER REFERENCES course_assignments(assignment_id),
                group_id INTEGER REFERENCES groups(group_id),
                planned_hours INTEGER NOT NULL,
                unit VARCHAR(20) DEFAULT 'per_week'
            );
        """))
        
        await conn.run_sync(lambda conn: conn.execute("""
            CREATE TABLE IF NOT EXISTS rooms (
                room_id SERIAL PRIMARY KEY,
                org_id INTEGER REFERENCES organizations(org_id),
                number VARCHAR(50) NOT NULL,
                capacity INTEGER DEFAULT 30,
                is_active BOOLEAN DEFAULT TRUE
            );
        """))
        
        await conn.run_sync(lambda conn: conn.execute("""
            CREATE TABLE IF NOT EXISTS time_slots (
                slot_id SERIAL PRIMARY KEY,
                org_id INTEGER REFERENCES organizations(org_id),
                start_time TIME NOT NULL,
                end_time TIME NOT NULL,
                name VARCHAR(100)
            );
        """))
        
        await conn.run_sync(lambda conn: conn.execute("""
            CREATE TABLE IF NOT EXISTS teacher_availability (
                id SERIAL PRIMARY KEY,
                org_id INTEGER REFERENCES organizations(org_id),
                teacher_id INTEGER REFERENCES teachers(teacher_id),
                weekday INTEGER NOT NULL,
                start_time TIME NOT NULL,
                end_time TIME NOT NULL,
                is_available BOOLEAN DEFAULT TRUE
            );
        """))
        
        await conn.run_sync(lambda conn: conn.execute("""
            CREATE TABLE IF NOT EXISTS holidays (
                id SERIAL PRIMARY KEY,
                org_id INTEGER REFERENCES organizations(org_id),
                date DATE NOT NULL,
                name VARCHAR(255) NOT NULL
            );
        """))
        
        await conn.run_sync(lambda conn: conn.execute("""
            CREATE TABLE IF NOT EXISTS lessons (
                lesson_id SERIAL PRIMARY KEY,
                org_id INTEGER REFERENCES organizations(org_id),
                date DATE NOT NULL,
                slot_id INTEGER REFERENCES time_slots(slot_id),
                room_id INTEGER REFERENCES rooms(room_id),
                enrollment_id INTEGER REFERENCES enrollments(enrollment_id),
                status VARCHAR(50) DEFAULT 'scheduled',
                is_active BOOLEAN DEFAULT TRUE
            );
        """))
        
        await conn.run_sync(lambda conn: conn.execute("""
            CREATE TABLE IF NOT EXISTS lesson_instances (
                lesson_id SERIAL PRIMARY KEY,
                org_id INTEGER REFERENCES organizations(org_id),
                term_id INTEGER REFERENCES terms(term_id),
                date DATE NOT NULL,
                slot_id INTEGER REFERENCES time_slots(slot_id),
                room_id INTEGER REFERENCES rooms(room_id),
                enrollment_id INTEGER REFERENCES enrollments(enrollment_id),
                status VARCHAR(50) DEFAULT 'planned',
                reason TEXT,
                created_by INTEGER REFERENCES users(user_id),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_by INTEGER REFERENCES users(user_id),
                updated_at TIMESTAMP,
                version INTEGER DEFAULT 1
            );
        """))
        
        await conn.run_sync(lambda conn: conn.execute("""
            CREATE TABLE IF NOT EXISTS change_logs (
                id SERIAL PRIMARY KEY,
                org_id INTEGER REFERENCES organizations(org_id),
                lesson_id INTEGER REFERENCES lesson_instances(lesson_id),
                user_id INTEGER REFERENCES users(user_id),
                action TEXT NOT NULL,
                payload_json JSONB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """))
        
        await conn.run_sync(lambda conn: conn.execute("""
            CREATE TABLE IF NOT EXISTS generation_jobs (
                job_id SERIAL PRIMARY KEY,
                org_id INTEGER REFERENCES organizations(org_id),
                term_id INTEGER REFERENCES terms(term_id),
                scope VARCHAR(20) NOT NULL,
                from_date DATE NOT NULL,
                to_date DATE NOT NULL,
                ruleset_json JSONB NOT NULL,
                status VARCHAR(20) DEFAULT 'pending',
                progress FLOAT DEFAULT 0.0,
                created_by INTEGER REFERENCES users(user_id),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                finished_at TIMESTAMP,
                error TEXT,
                result_json JSONB
            );
        """))
        
        print("All tables created successfully!")
    
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(create_tables())
