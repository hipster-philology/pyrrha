"""Add needs_review and review_comment to word_token

Revision ID: c87a47d9b583
Revises: 1033432bf435
Create Date: 2026-04-30

"""
from alembic import op
import sqlalchemy as sa

revision = 'c87a47d9b583'
down_revision = '1033432bf435'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('word_token', schema=None) as batch_op:
        batch_op.add_column(sa.Column('needs_review', sa.Boolean(), nullable=False,
                                      server_default='0'))
        batch_op.add_column(sa.Column('review_comment', sa.String(length=512), nullable=True))


def downgrade():
    with op.batch_alter_table('word_token', schema=None) as batch_op:
        batch_op.drop_column('review_comment')
        batch_op.drop_column('needs_review')
