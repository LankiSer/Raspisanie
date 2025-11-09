"""Create unified tables with all fixes

Revision ID: 001
Revises: 
Create Date: 2024-09-18 18:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Create enum types only if they don't exist
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE userrole AS ENUM ('SUPERADMIN', 'ADMIN', 'METHODIST', 'TEACHER', 'STUDENT');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    
    
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE lessonstatus AS ENUM ('PLANNED', 'CONFIRMED', 'COMPLETED', 'CANCELLED', 'SKIPPED', 'MOVED');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE generationscope AS ENUM ('FULL', 'PARTIAL');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE generationstatus AS ENUM ('PENDING', 'RUNNING', 'COMPLETED', 'FAILED', 'CANCELLED');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    
    # Create organizations table
    op.create_table('organizations',
        sa.Column('org_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('locale', sa.String(length=10), nullable=False, server_default='ru'),
        sa.Column('tz', sa.String(length=50), nullable=False, server_default='Europe/Moscow'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('org_id')
    )
    op.create_index(op.f('ix_organizations_org_id'), 'organizations', ['org_id'], unique=False)

    # Create users table
    op.create_table('users',
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('org_id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('role', postgresql.ENUM('SUPERADMIN', 'ADMIN', 'METHODIST', 'TEACHER', 'STUDENT', name='userrole', create_type=False), nullable=False, server_default='STUDENT'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['org_id'], ['organizations.org_id'], ),
        sa.PrimaryKeyConstraint('user_id'),
        sa.UniqueConstraint('email')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=False)
    op.create_index(op.f('ix_users_org_id'), 'users', ['org_id'], unique=False)
    op.create_index(op.f('ix_users_role'), 'users', ['role'], unique=False)
    op.create_index(op.f('ix_users_user_id'), 'users', ['user_id'], unique=False)

    # Create academic_years table
    op.create_table('academic_years',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('org_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('end_date', sa.Date(), nullable=False),
        sa.ForeignKeyConstraint(['org_id'], ['organizations.org_id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_academic_years_id'), 'academic_years', ['id'], unique=False)
    op.create_index(op.f('ix_academic_years_org_id'), 'academic_years', ['org_id'], unique=False)

    # Create terms table
    op.create_table('terms',
        sa.Column('term_id', sa.Integer(), nullable=False),
        sa.Column('org_id', sa.Integer(), nullable=False),
        sa.Column('academic_year_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('end_date', sa.Date(), nullable=False),
        sa.ForeignKeyConstraint(['academic_year_id'], ['academic_years.id'], ),
        sa.ForeignKeyConstraint(['org_id'], ['organizations.org_id'], ),
        sa.PrimaryKeyConstraint('term_id')
    )
    op.create_index(op.f('ix_terms_academic_year_id'), 'terms', ['academic_year_id'], unique=False)
    op.create_index(op.f('ix_terms_org_id'), 'terms', ['org_id'], unique=False)
    op.create_index(op.f('ix_terms_term_id'), 'terms', ['term_id'], unique=False)

    # Create groups table
    op.create_table('groups',
        sa.Column('group_id', sa.Integer(), nullable=False),
        sa.Column('org_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('size', sa.Integer(), nullable=False, server_default='25'),
        sa.Column('year_level', sa.Integer(), nullable=True),
        sa.Column('generation_type', sa.Integer(), nullable=False, server_default='2'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.ForeignKeyConstraint(['org_id'], ['organizations.org_id'], ),
        sa.PrimaryKeyConstraint('group_id'),
        sa.UniqueConstraint('org_id', 'name', name='uq_org_group_name')
    )
    op.create_index(op.f('ix_groups_group_id'), 'groups', ['group_id'], unique=False)
    op.create_index(op.f('ix_groups_name'), 'groups', ['name'], unique=False)
    op.create_index(op.f('ix_groups_org_id'), 'groups', ['org_id'], unique=False)

    # Create teachers table
    op.create_table('teachers',
        sa.Column('teacher_id', sa.Integer(), nullable=False),
        sa.Column('org_id', sa.Integer(), nullable=False),
        sa.Column('first_name', sa.String(length=100), nullable=False),
        sa.Column('last_name', sa.String(length=100), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=True),
        sa.Column('phone', sa.String(length=50), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.ForeignKeyConstraint(['org_id'], ['organizations.org_id'], ),
        sa.PrimaryKeyConstraint('teacher_id'),
        sa.UniqueConstraint('org_id', 'email', name='uq_org_teacher_email')
    )
    op.create_index(op.f('ix_teachers_email'), 'teachers', ['email'], unique=False)
    op.create_index(op.f('ix_teachers_org_id'), 'teachers', ['org_id'], unique=False)
    op.create_index(op.f('ix_teachers_teacher_id'), 'teachers', ['teacher_id'], unique=False)

    # Create courses table
    op.create_table('courses',
        sa.Column('course_id', sa.Integer(), nullable=False),
        sa.Column('org_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('type', sa.String(length=50), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.ForeignKeyConstraint(['org_id'], ['organizations.org_id'], ),
        sa.PrimaryKeyConstraint('course_id')
    )
    op.create_index(op.f('ix_courses_course_id'), 'courses', ['course_id'], unique=False)
    op.create_index(op.f('ix_courses_org_id'), 'courses', ['org_id'], unique=False)

    # Create course_assignments table
    op.create_table('course_assignments',
        sa.Column('assignment_id', sa.Integer(), nullable=False),
        sa.Column('org_id', sa.Integer(), nullable=False),
        sa.Column('course_id', sa.Integer(), nullable=False),
        sa.Column('teacher_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['course_id'], ['courses.course_id'], ),
        sa.ForeignKeyConstraint(['org_id'], ['organizations.org_id'], ),
        sa.ForeignKeyConstraint(['teacher_id'], ['teachers.teacher_id'], ),
        sa.PrimaryKeyConstraint('assignment_id')
    )
    op.create_index(op.f('ix_course_assignments_assignment_id'), 'course_assignments', ['assignment_id'], unique=False)
    op.create_index(op.f('ix_course_assignments_course_id'), 'course_assignments', ['course_id'], unique=False)
    op.create_index(op.f('ix_course_assignments_org_id'), 'course_assignments', ['org_id'], unique=False)
    op.create_index(op.f('ix_course_assignments_teacher_id'), 'course_assignments', ['teacher_id'], unique=False)

    # Create enrollments table
    op.create_table('enrollments',
        sa.Column('enrollment_id', sa.Integer(), nullable=False),
        sa.Column('org_id', sa.Integer(), nullable=False),
        sa.Column('assignment_id', sa.Integer(), nullable=False),
        sa.Column('group_id', sa.Integer(), nullable=False),
        sa.Column('planned_hours', sa.Integer(), nullable=False),
        sa.Column('unit', sa.String(length=20), nullable=False, server_default='per_week'),
        sa.ForeignKeyConstraint(['assignment_id'], ['course_assignments.assignment_id'], ),
        sa.ForeignKeyConstraint(['group_id'], ['groups.group_id'], ),
        sa.ForeignKeyConstraint(['org_id'], ['organizations.org_id'], ),
        sa.PrimaryKeyConstraint('enrollment_id')
    )
    op.create_index(op.f('ix_enrollments_assignment_id'), 'enrollments', ['assignment_id'], unique=False)
    op.create_index(op.f('ix_enrollments_enrollment_id'), 'enrollments', ['enrollment_id'], unique=False)
    op.create_index(op.f('ix_enrollments_group_id'), 'enrollments', ['group_id'], unique=False)
    op.create_index(op.f('ix_enrollments_org_id'), 'enrollments', ['org_id'], unique=False)

    # Create rooms table
    op.create_table('rooms',
        sa.Column('room_id', sa.Integer(), nullable=False),
        sa.Column('org_id', sa.Integer(), nullable=False),
        sa.Column('number', sa.String(length=50), nullable=False),
        sa.Column('capacity', sa.Integer(), nullable=False, server_default='30'),
        sa.Column('kind', sa.String(length=50), nullable=True),
        sa.Column('building', sa.String(length=100), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.ForeignKeyConstraint(['org_id'], ['organizations.org_id'], ),
        sa.PrimaryKeyConstraint('room_id')
    )
    op.create_index(op.f('ix_rooms_org_id'), 'rooms', ['org_id'], unique=False)
    op.create_index(op.f('ix_rooms_room_id'), 'rooms', ['room_id'], unique=False)

    # Create time_slots table
    op.create_table('time_slots',
        sa.Column('slot_id', sa.Integer(), nullable=False),
        sa.Column('org_id', sa.Integer(), nullable=False),
        sa.Column('start_time', sa.Time(), nullable=False),
        sa.Column('end_time', sa.Time(), nullable=False),
        sa.Column('break_minutes', sa.Integer(), nullable=False, server_default='10'),
        sa.Column('label', sa.String(length=50), nullable=True),
        sa.Column('weekday_mask', sa.SmallInteger(), nullable=False, server_default='31'),
        sa.ForeignKeyConstraint(['org_id'], ['organizations.org_id'], ),
        sa.PrimaryKeyConstraint('slot_id')
    )
    op.create_index(op.f('ix_time_slots_org_id'), 'time_slots', ['org_id'], unique=False)
    op.create_index(op.f('ix_time_slots_slot_id'), 'time_slots', ['slot_id'], unique=False)

    # Create teacher_availabilities table
    op.create_table('teacher_availabilities',
        sa.Column('availability_id', sa.Integer(), nullable=False),
        sa.Column('org_id', sa.Integer(), nullable=False),
        sa.Column('teacher_id', sa.Integer(), nullable=False),
        sa.Column('weekday', sa.Integer(), nullable=False),
        sa.Column('start_time', sa.Time(), nullable=False),
        sa.Column('end_time', sa.Time(), nullable=False),
        sa.Column('is_available', sa.Boolean(), nullable=False, server_default='true'),
        sa.ForeignKeyConstraint(['org_id'], ['organizations.org_id'], ),
        sa.ForeignKeyConstraint(['teacher_id'], ['teachers.teacher_id'], ),
        sa.PrimaryKeyConstraint('availability_id')
    )
    op.create_index(op.f('ix_teacher_availabilities_availability_id'), 'teacher_availabilities', ['availability_id'], unique=False)
    op.create_index(op.f('ix_teacher_availabilities_org_id'), 'teacher_availabilities', ['org_id'], unique=False)
    op.create_index(op.f('ix_teacher_availabilities_teacher_id'), 'teacher_availabilities', ['teacher_id'], unique=False)

    # Create holidays table
    op.create_table('holidays',
        sa.Column('holiday_id', sa.Integer(), nullable=False),
        sa.Column('org_id', sa.Integer(), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.ForeignKeyConstraint(['org_id'], ['organizations.org_id'], ),
        sa.PrimaryKeyConstraint('holiday_id'),
        sa.UniqueConstraint('org_id', 'date', name='uq_org_holiday_date')
    )
    op.create_index(op.f('ix_holidays_date'), 'holidays', ['date'], unique=False)
    op.create_index(op.f('ix_holidays_holiday_id'), 'holidays', ['holiday_id'], unique=False)
    op.create_index(op.f('ix_holidays_org_id'), 'holidays', ['org_id'], unique=False)

    # Create lesson_instances table
    op.create_table('lesson_instances',
        sa.Column('lesson_id', sa.Integer(), nullable=False),
        sa.Column('org_id', sa.Integer(), nullable=False),
        sa.Column('term_id', sa.Integer(), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('slot_id', sa.Integer(), nullable=False),
        sa.Column('room_id', sa.Integer(), nullable=True),
        sa.Column('enrollment_id', sa.Integer(), nullable=False),
        sa.Column('status', postgresql.ENUM('PLANNED', 'SCHEDULED', 'CANCELLED', 'COMPLETED', name='lessonstatus', create_type=False), nullable=False, server_default='PLANNED'),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_by', sa.Integer(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.ForeignKeyConstraint(['created_by'], ['users.user_id'], ),
        sa.ForeignKeyConstraint(['enrollment_id'], ['enrollments.enrollment_id'], ),
        sa.ForeignKeyConstraint(['org_id'], ['organizations.org_id'], ),
        sa.ForeignKeyConstraint(['room_id'], ['rooms.room_id'], ),
        sa.ForeignKeyConstraint(['slot_id'], ['time_slots.slot_id'], ),
        sa.ForeignKeyConstraint(['term_id'], ['terms.term_id'], ),
        sa.ForeignKeyConstraint(['updated_by'], ['users.user_id'], ),
        sa.PrimaryKeyConstraint('lesson_id'),
        sa.UniqueConstraint('org_id', 'date', 'slot_id', 'room_id', name='uq_org_date_slot_room')
    )
    op.create_index(op.f('ix_lesson_instances_date'), 'lesson_instances', ['date'], unique=False)
    op.create_index(op.f('ix_lesson_instances_enrollment_id'), 'lesson_instances', ['enrollment_id'], unique=False)
    op.create_index(op.f('ix_lesson_instances_lesson_id'), 'lesson_instances', ['lesson_id'], unique=False)
    op.create_index(op.f('ix_lesson_instances_org_id'), 'lesson_instances', ['org_id'], unique=False)
    op.create_index(op.f('ix_lesson_instances_room_id'), 'lesson_instances', ['room_id'], unique=False)
    op.create_index(op.f('ix_lesson_instances_slot_id'), 'lesson_instances', ['slot_id'], unique=False)
    op.create_index(op.f('ix_lesson_instances_status'), 'lesson_instances', ['status'], unique=False)
    op.create_index(op.f('ix_lesson_instances_term_id'), 'lesson_instances', ['term_id'], unique=False)

    # Create change_logs table
    op.create_table('change_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('org_id', sa.Integer(), nullable=False),
        sa.Column('lesson_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('action', sa.Text(), nullable=False),
        sa.Column('payload_json', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['lesson_id'], ['lesson_instances.lesson_id'], ),
        sa.ForeignKeyConstraint(['org_id'], ['organizations.org_id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.user_id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_change_logs_created_at'), 'change_logs', ['created_at'], unique=False)
    op.create_index(op.f('ix_change_logs_id'), 'change_logs', ['id'], unique=False)
    op.create_index(op.f('ix_change_logs_lesson_id'), 'change_logs', ['lesson_id'], unique=False)
    op.create_index(op.f('ix_change_logs_org_id'), 'change_logs', ['org_id'], unique=False)
    op.create_index(op.f('ix_change_logs_user_id'), 'change_logs', ['user_id'], unique=False)

    # Create generation_jobs table
    op.create_table('generation_jobs',
        sa.Column('job_id', sa.Integer(), nullable=False),
        sa.Column('org_id', sa.Integer(), nullable=False),
        sa.Column('term_id', sa.Integer(), nullable=False),
        sa.Column('scope', postgresql.ENUM('FULL', 'PARTIAL', name='generationscope', create_type=False), nullable=False),
        sa.Column('from_date', sa.Date(), nullable=False),
        sa.Column('to_date', sa.Date(), nullable=False),
        sa.Column('ruleset_json', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('status', postgresql.ENUM('PENDING', 'RUNNING', 'COMPLETED', 'FAILED', 'CANCELLED', name='generationstatus', create_type=False), nullable=False, server_default='PENDING'),
        sa.Column('progress', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('created_by', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('finished_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('error', sa.Text(), nullable=True),
        sa.Column('result_json', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(['created_by'], ['users.user_id'], ),
        sa.ForeignKeyConstraint(['org_id'], ['organizations.org_id'], ),
        sa.ForeignKeyConstraint(['term_id'], ['terms.term_id'], ),
        sa.PrimaryKeyConstraint('job_id')
    )
    op.create_index(op.f('ix_generation_jobs_job_id'), 'generation_jobs', ['job_id'], unique=False)
    op.create_index(op.f('ix_generation_jobs_org_id'), 'generation_jobs', ['org_id'], unique=False)
    op.create_index(op.f('ix_generation_jobs_scope'), 'generation_jobs', ['scope'], unique=False)
    op.create_index(op.f('ix_generation_jobs_status'), 'generation_jobs', ['status'], unique=False)
    op.create_index(op.f('ix_generation_jobs_term_id'), 'generation_jobs', ['term_id'], unique=False)


def downgrade():
    # Drop all tables
    op.drop_table('generation_jobs')
    op.drop_table('change_logs')
    op.drop_table('lesson_instances')
    op.drop_table('holidays')
    op.drop_table('teacher_availabilities')
    op.drop_table('time_slots')
    op.drop_table('rooms')
    op.drop_table('enrollments')
    op.drop_table('course_assignments')
    op.drop_table('courses')
    op.drop_table('teachers')
    op.drop_table('groups')
    op.drop_table('terms')
    op.drop_table('academic_years')
    op.drop_table('users')
    op.drop_table('organizations')
    
    # Drop enum types
    op.execute("DROP TYPE IF EXISTS userrole")
    op.execute("DROP TYPE IF EXISTS lessonstatus")
    op.execute("DROP TYPE IF EXISTS generationscope")
    op.execute("DROP TYPE IF EXISTS generationstatus")