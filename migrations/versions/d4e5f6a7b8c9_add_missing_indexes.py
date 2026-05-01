"""Add missing indexes on change_record and column tables

Revision ID: d4e5f6a7b8c9
Revises: c87a47d9b583
Create Date: 2026-05-01

"""
from alembic import op

revision = 'd4e5f6a7b8c9'
down_revision = 'c87a47d9b583'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('change_record', schema=None) as batch_op:
        batch_op.create_index('ix_change_record_corpus', ['corpus'])
        batch_op.create_index('ix_change_record_corpus_date', ['corpus', 'created_on'])
        batch_op.create_index('ix_change_record_word_token_id', ['word_token_id'])
    with op.batch_alter_table('column', schema=None) as batch_op:
        batch_op.create_index('ix_column_corpus_id', ['corpus_id'])


def downgrade():
    with op.batch_alter_table('change_record', schema=None) as batch_op:
        batch_op.drop_index('ix_change_record_corpus')
        batch_op.drop_index('ix_change_record_corpus_date')
        batch_op.drop_index('ix_change_record_word_token_id')
    with op.batch_alter_table('column', schema=None) as batch_op:
        batch_op.drop_index('ix_column_corpus_id')
