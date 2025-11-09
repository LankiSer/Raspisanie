"""Fix unit column to be string instead of enum."""

import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from app.core.config import settings

async def fix_unit_column():
    engine = create_async_engine(settings.DATABASE_URL)
    async with engine.begin() as conn:
        # Change unit column from enum to string
        await conn.execute(text("ALTER TABLE enrollments ALTER COLUMN unit TYPE VARCHAR(20)"))
        
        # Check the result
        result = await conn.execute(text("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'enrollments' AND column_name = 'unit'"))
        columns = result.fetchall()
        print('Unit column after fix:', columns)
        
        # Check sample data
        result = await conn.execute(text("SELECT unit FROM enrollments LIMIT 5"))
        sample_data = result.fetchall()
        print('Sample data after fix:', sample_data)
    
    await engine.dispose()
    print("Unit column fixed successfully!")

if __name__ == "__main__":
    asyncio.run(fix_unit_column())
