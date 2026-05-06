"""Add status and created_at to corpus

Revision ID: f1a2b3c4d5e6
Revises: e5f6a7b8c9d0
Create Date: 2026-05-06

"""
import sqlalchemy as sa
from alembic import op

revision = 'f1a2b3c4d5e6'
down_revision = 'e5f6a7b8c9d0'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    if conn.dialect.name == 'postgresql':
        conn.execute(sa.text(
            "DO $$ BEGIN "
            "CREATE TYPE corpus_status AS ENUM ('pending', 'active'); "
            "EXCEPTION WHEN duplicate_object THEN null; "
            "END $$"
        ))
    op.add_column('corpus', sa.Column(
        'status',
        sa.Enum('pending', 'active', name='corpus_status', create_type=False),
        nullable=False,
        server_default='active',
    ))
    op.add_column('corpus', sa.Column(
        'created_at',
        sa.DateTime(),
        nullable=False,
        server_default=sa.func.now(),
    ))


def downgrade():
    op.drop_column('corpus', 'created_at')
    op.drop_column('corpus', 'status')
    # Drop the enum type (PostgreSQL only — SQLite ignores this)
    op.execute("DROP TYPE IF EXISTS corpus_status")
