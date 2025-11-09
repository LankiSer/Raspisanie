"""Check organizations in database."""

import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import select, text
from app.core.config import settings

async def check_orgs():
    engine = create_async_engine(settings.DATABASE_URL)
    async with engine.begin() as conn:
        result = await conn.execute(text("SELECT org_id, name FROM organizations"))
        orgs = result.fetchall()
        print('Organizations:', orgs)
        
        result = await conn.execute(text("SELECT user_id, email, org_id, role, password_hash FROM users"))
        users = result.fetchall()
        print('Users:', users)
        
        result = await conn.execute(text("SELECT group_id, name, org_id FROM groups"))
        groups = result.fetchall()
        print('Groups:', groups)
        
        result = await conn.execute(text("SELECT teacher_id, first_name, last_name, org_id FROM teachers"))
        teachers = result.fetchall()
        print('Teachers:', teachers)
        
        result = await conn.execute(text("SELECT course_id, name, org_id FROM courses"))
        courses = result.fetchall()
        print('Courses:', courses)
        
        result = await conn.execute(text("SELECT room_id, number, org_id FROM rooms"))
        rooms = result.fetchall()
        print('Rooms:', rooms)
        
        result = await conn.execute(text("SELECT slot_id, label, org_id FROM time_slots"))
        slots = result.fetchall()
        print('Time slots:', slots)
        
        result = await conn.execute(text("SELECT assignment_id, course_id, teacher_id, org_id FROM course_assignments"))
        assignments = result.fetchall()
        print('Course assignments:', assignments)
        
        result = await conn.execute(text("SELECT enrollment_id, group_id, assignment_id, org_id FROM enrollments"))
        enrollments = result.fetchall()
        print('Enrollments:', enrollments)
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(check_orgs())
