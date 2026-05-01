"""Add token_reference to word_token

Revision ID: a1b2c3d4e5f6
Revises: c87a47d9b583
Create Date: 2026-05-01

"""
from alembic import op
import sqlalchemy as sa

revision = 'a1b2c3d4e5f6'
down_revision = 'c87a47d9b583'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('word_token', schema=None) as batch_op:
        batch_op.add_column(sa.Column('token_reference', sa.String(length=512), nullable=True))


def downgrade():
    with op.batch_alter_table('word_token', schema=None) as batch_op:
        batch_op.drop_column('token_reference')
