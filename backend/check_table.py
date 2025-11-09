"""Check table structure."""

import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from app.core.config import settings

async def check_table():
    engine = create_async_engine(settings.DATABASE_URL)
    async with engine.begin() as conn:
        # Check table structure
        result = await conn.execute(text("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'enrollments' AND column_name = 'unit'"))
        columns = result.fetchall()
        print('Unit column info:', columns)
        
        # Check enum type
        result = await conn.execute(text("SELECT unnest(enum_range(NULL::hoursunit))"))
        enum_values = result.fetchall()
        print('Enum values:', enum_values)
        
        # Check sample data
        result = await conn.execute(text("SELECT unit FROM enrollments LIMIT 5"))
        sample_data = result.fetchall()
        print('Sample data:', sample_data)
    
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(check_table())
