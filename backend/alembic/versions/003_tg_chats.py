"""Add tg_chats and tg_messages tables

Revision ID: 003
Revises: 002
Create Date: 2026-03-12 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'tg_chats',
        sa.Column('id',          sa.Integer(),     primary_key=True),
        sa.Column('org_id',      sa.Integer(),     sa.ForeignKey('organizations.org_id'), nullable=False),
        sa.Column('tg_user_id',  sa.String(64),    nullable=False),
        sa.Column('tg_username', sa.String(255),   nullable=True),
        sa.Column('full_name',   sa.String(255),   nullable=True),
        sa.Column('is_resolved', sa.Boolean(),     nullable=False, server_default='false'),
        sa.Column('created_at',  sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at',  sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_tg_chats_id',         'tg_chats', ['id'])
    op.create_index('ix_tg_chats_org_id',      'tg_chats', ['org_id'])
    op.create_index('ix_tg_chats_tg_user_id',  'tg_chats', ['tg_user_id'])

    op.create_table(
        'tg_messages',
        sa.Column('id',         sa.Integer(),    primary_key=True),
        sa.Column('chat_id',    sa.Integer(),    sa.ForeignKey('tg_chats.id'), nullable=False),
        sa.Column('direction',  sa.String(10),   nullable=False),
        sa.Column('text',       sa.Text(),       nullable=False),
        sa.Column('is_read',    sa.Boolean(),    nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    op.create_index('ix_tg_messages_id',      'tg_messages', ['id'])
    op.create_index('ix_tg_messages_chat_id', 'tg_messages', ['chat_id'])


def downgrade():
    op.drop_table('tg_messages')
    op.drop_table('tg_chats')
