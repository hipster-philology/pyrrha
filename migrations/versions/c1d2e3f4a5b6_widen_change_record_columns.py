"""Widen change_record and token_history columns to match word_token

Revision ID: c1d2e3f4a5b6
Revises: da12c0ab7bb6
Create Date: 2026-11-19

"""
from alembic import op
import sqlalchemy as sa

revision = 'c1d2e3f4a5b6'
down_revision = 'da12c0ab7bb6'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('change_record') as batch_op:
        batch_op.alter_column('morph', existing_type=sa.String(128), type_=sa.String(1024), existing_nullable=True)
        batch_op.alter_column('morph_new', existing_type=sa.String(128), type_=sa.String(1024), existing_nullable=True)
        batch_op.alter_column('gloss', existing_type=sa.String(512), type_=sa.String(1024), existing_nullable=True)
        batch_op.alter_column('gloss_new', existing_type=sa.String(512), type_=sa.String(1024), existing_nullable=True)
    with op.batch_alter_table('token_history') as batch_op:
        batch_op.alter_column('new', existing_type=sa.String(100), type_=sa.String(1024), existing_nullable=True)
        batch_op.alter_column('old', existing_type=sa.String(100), type_=sa.String(1024), existing_nullable=True)


def downgrade():
    with op.batch_alter_table('token_history') as batch_op:
        batch_op.alter_column('old', existing_type=sa.String(1024), type_=sa.String(100), existing_nullable=True)
        batch_op.alter_column('new', existing_type=sa.String(1024), type_=sa.String(100), existing_nullable=True)
    with op.batch_alter_table('change_record') as batch_op:
        batch_op.alter_column('gloss_new', existing_type=sa.String(1024), type_=sa.String(512), existing_nullable=True)
        batch_op.alter_column('gloss', existing_type=sa.String(1024), type_=sa.String(512), existing_nullable=True)
        batch_op.alter_column('morph_new', existing_type=sa.String(1024), type_=sa.String(128), existing_nullable=True)
        batch_op.alter_column('morph', existing_type=sa.String(1024), type_=sa.String(128), existing_nullable=True)
