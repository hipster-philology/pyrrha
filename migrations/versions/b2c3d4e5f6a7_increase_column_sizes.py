"""Increase column sizes for morph, gloss, review_comment, context, and allowed_morph fields

Revision ID: b2c3d4e5f6a7
Revises: f1a2b3c4d5e6
Create Date: 2026-05-06

"""
from alembic import op
import sqlalchemy as sa

revision = 'b2c3d4e5f6a7'
down_revision = 'f1a2b3c4d5e6'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('word_token') as batch_op:
        batch_op.alter_column('morph',
            existing_type=sa.String(128), type_=sa.String(1024), existing_nullable=True)
        batch_op.alter_column('gloss',
            existing_type=sa.String(512), type_=sa.String(1024), existing_nullable=True)
        batch_op.alter_column('review_comment',
            existing_type=sa.String(512), type_=sa.String(1024), existing_nullable=True)
        batch_op.alter_column('left_context',
            existing_type=sa.String(512), type_=sa.String(1024), existing_nullable=True)
        batch_op.alter_column('right_context',
            existing_type=sa.String(512), type_=sa.String(1024), existing_nullable=True)

    with op.batch_alter_table('allowed_morph') as batch_op:
        batch_op.alter_column('label',
            existing_type=sa.String(128), type_=sa.String(1024), existing_nullable=True)
        batch_op.alter_column('readable',
            existing_type=sa.String(256), type_=sa.String(1024), existing_nullable=True)


def downgrade():
    with op.batch_alter_table('word_token') as batch_op:
        batch_op.alter_column('morph',
            existing_type=sa.String(1024), type_=sa.String(128), existing_nullable=True)
        batch_op.alter_column('gloss',
            existing_type=sa.String(1024), type_=sa.String(512), existing_nullable=True)
        batch_op.alter_column('review_comment',
            existing_type=sa.String(1024), type_=sa.String(512), existing_nullable=True)
        batch_op.alter_column('left_context',
            existing_type=sa.String(1024), type_=sa.String(512), existing_nullable=True)
        batch_op.alter_column('right_context',
            existing_type=sa.String(1024), type_=sa.String(512), existing_nullable=True)

    with op.batch_alter_table('allowed_morph') as batch_op:
        batch_op.alter_column('label',
            existing_type=sa.String(1024), type_=sa.String(128), existing_nullable=True)
        batch_op.alter_column('readable',
            existing_type=sa.String(1024), type_=sa.String(256), existing_nullable=True)
