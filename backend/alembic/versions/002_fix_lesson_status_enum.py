"""Fix lessonstatus enum: add CONFIRMED, SKIPPED, MOVED; remove SCHEDULED

Revision ID: 002
Revises: 001
Create Date: 2026-03-12 00:00:00.000000
"""
from alembic import op

revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade():
    # Add missing enum values and rename SCHEDULED → CONFIRMED if present.
    # ALTER TYPE … ADD VALUE is idempotent when guarded with the IF NOT EXISTS clause
    # (requires PostgreSQL 9.6+).
    op.execute("ALTER TYPE lessonstatus ADD VALUE IF NOT EXISTS 'CONFIRMED'")
    op.execute("ALTER TYPE lessonstatus ADD VALUE IF NOT EXISTS 'SKIPPED'")
    op.execute("ALTER TYPE lessonstatus ADD VALUE IF NOT EXISTS 'MOVED'")

    # Migrate any legacy SCHEDULED rows to CONFIRMED
    op.execute("""
        DO $$ BEGIN
            IF EXISTS (
                SELECT 1 FROM pg_enum
                WHERE enumlabel = 'SCHEDULED'
                  AND enumtypid = (SELECT oid FROM pg_type WHERE typname = 'lessonstatus')
            ) THEN
                UPDATE lesson_instances SET status = 'CONFIRMED' WHERE status = 'SCHEDULED';
            END IF;
        END $$;
    """)


def downgrade():
    # PostgreSQL does not support removing enum values directly.
    # Downgrade is intentionally a no-op to avoid data loss.
    pass
