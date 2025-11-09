#!/bin/bash
set -e

echo "🚀 Starting application setup..."

# Wait for database to be ready
echo "⏳ Waiting for database..."
while ! pg_isready -h database -p 5432 -U schedule_user; do
    echo "Database is unavailable - sleeping..."
    sleep 1
done
echo "✅ Database is ready!"

# Prepare sync DB URL for psql (strip +asyncpg if present)
SYNC_DATABASE_URL=${DATABASE_URL/+asyncpg/}

# Run migrations
echo "🔧 Running database migrations..."
alembic upgrade head

# Check if database is empty (no organizations)
echo "🔍 Checking if database needs seeding..."
RESULT=$(python3 -c "
import asyncio
from app.core.database import AsyncSessionLocal
from app.models.organization import Organization
from sqlalchemy import select

async def check_db():
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Organization))
        return result.first() is None

print('true' if asyncio.run(check_db()) else 'false')
" 2>/dev/null || echo "true")

if [ "$RESULT" = "true" ]; then
    echo "🌱 Database is empty, creating seed data..."
    if [ -z "$SYNC_DATABASE_URL" ]; then
        echo "❌ DATABASE_URL is not set. Cannot run seed SQL."
        exit 1
    fi
    psql "$SYNC_DATABASE_URL" -v ON_ERROR_STOP=1 -f sql/admin_seed.sql
    echo "✅ Seed data created successfully from SQL script!"
else
    echo "📊 Database already contains data, skipping seed."
fi

echo "🎯 Starting FastAPI application..."
exec "$@"
