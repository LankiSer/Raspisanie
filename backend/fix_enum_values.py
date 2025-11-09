"""Fix enum values in database."""

import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from app.core.config import settings

async def fix_enum_values():
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
    
    await engine.dispose()
    print("Enum values fixed successfully!")

if __name__ == "__main__":
    asyncio.run(fix_enum_values())
