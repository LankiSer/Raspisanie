#!/bin/bash
set -e

# Verify script is executable
if [ ! -x "$0" ]; then
    echo "❌ Error: entrypoint.sh is not executable"
    exit 1
fi

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
    
    # Ensure we're in the correct directory
    cd /app || exit 1
    
    # Temporarily disable exit on error for seed script
    set +e
    
    # Try to run Python seed script
    if [ -f "scripts/seed.py" ]; then
        echo "📝 Running Python seed script (scripts/seed.py)..."
        python3 scripts/seed.py
        SEED_EXIT_CODE=$?
        if [ $SEED_EXIT_CODE -eq 0 ]; then
            echo "✅ Seed data created successfully!"
        else
            echo "⚠️  Seed script failed with exit code $SEED_EXIT_CODE, but continuing..."
            echo "   You can manually run: docker compose exec backend python3 scripts/seed.py"
        fi
    elif [ -f "create_test_account.py" ]; then
        echo "📝 Running test account creation script..."
        python3 create_test_account.py
        if [ $? -eq 0 ]; then
            echo "✅ Test account created successfully!"
        else
            echo "⚠️  Test account creation failed, but continuing..."
        fi
    else
        echo "⚠️  No seed script found. Database will be empty."
        echo "   Available scripts: scripts/seed.py or create_test_account.py"
        echo "   You can manually create test data after container starts."
    fi
    
    # Re-enable exit on error
    set -e
else
    echo "📊 Database already contains data, skipping seed."
fi

echo "🎯 Starting FastAPI application..."
exec "$@"
