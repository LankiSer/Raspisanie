"""Fix enrollments unit values to use proper enum format."""

import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from app.core.config import settings

async def fix_enrollments():
    engine = create_async_engine(settings.DATABASE_URL)
    async with engine.begin() as conn:
        # Check current values
        result = await conn.execute(text("SELECT DISTINCT unit FROM enrollments"))
        units = result.fetchall()
        print('Current units in DB:', units)
        
        # Update all enrollments to use proper enum values
        await conn.execute(text("UPDATE enrollments SET unit = 'PER_TERM' WHERE unit = 'per_term'"))
        await conn.execute(text("UPDATE enrollments SET unit = 'PER_WEEK' WHERE unit = 'per_week'"))
        
        # Check the result
        result = await conn.execute(text("SELECT DISTINCT unit FROM enrollments"))
        units = result.fetchall()
        print('Units after fix:', units)
        
        # Check a few enrollments
        result = await conn.execute(text("SELECT enrollment_id, group_id, assignment_id, unit FROM enrollments LIMIT 5"))
        enrollments = result.fetchall()
        print('Sample enrollments after fix:', enrollments)
    
    await engine.dispose()
    print("Enrollments fixed successfully!")

if __name__ == "__main__":
    asyncio.run(fix_enrollments())
