#!/usr/bin/env python3
"""Initialize database and seed with test data."""

import asyncio
import sys
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from app.core.config import settings

async def check_db_tables():
    """Check if database tables exist."""
    engine = create_async_engine(settings.DATABASE_URL)
    async with engine.begin() as conn:
        result = await conn.execute(text(
            "SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public'"
        ))
        table_count = result.scalar()
        return table_count > 0

async def run_migrations():
    """Run Alembic migrations."""
    import subprocess
    result = subprocess.run(["alembic", "upgrade", "head"], capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Migration failed: {result.stderr}")
        return False
    print("Migrations completed successfully")
    return True

async def seed_database():
    """Seed database with test data."""
    try:
        # Import and run the seeder
        from create_test_data import create_test_data
        await create_test_data()
        return True
    except Exception as e:
        print(f"Seeding failed: {e}")
        return False

async def main():
    """Main initialization function."""
    print("Checking database state...")
    
    # Check if tables exist
    has_tables = await check_db_tables()
    
    if not has_tables:
        print("No tables found, running migrations...")
        if not await run_migrations():
            sys.exit(1)
        
        print("Seeding database with test data...")
        if not await seed_database():
            print("Warning: Failed to seed database, but continuing...")
    else:
        print("Database already initialized, skipping setup")
    
    print("Database initialization complete!")

if __name__ == "__main__":
    asyncio.run(main())
