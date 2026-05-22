"""Simplify bookmark primary key to (corpus_id, user_id)

Removes token_id from the primary key so that re-bookmarking the same
corpus is a plain UPDATE instead of a DELETE + INSERT, eliminating the
concurrent-request UniqueViolation.

Revision ID: 9ade058f6015
Revises: 06ee9da93d69
Create Date: 2026-05-22

"""
import sqlalchemy as sa
from alembic import op

revision = '9ade058f6015'
down_revision = '06ee9da93d69'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    dialect = bind.dialect.name

    if dialect == 'postgresql':
        # Deduplicate: keep only the most recent bookmark per (corpus_id, user_id).
        op.execute("""
            DELETE FROM bookmark
            WHERE ctid NOT IN (
                SELECT DISTINCT ON (corpus_id, user_id) ctid
                FROM bookmark
                ORDER BY corpus_id, user_id, token_id DESC
            )
        """)
        op.drop_constraint('bookmark_token_id_fkey', 'bookmark', type_='foreignkey')
        op.drop_constraint('bookmark_pkey', 'bookmark', type_='primary')
        op.create_primary_key('bookmark_pkey', 'bookmark', ['corpus_id', 'user_id'])
        op.create_foreign_key(
            'bookmark_token_id_fkey', 'bookmark',
            'word_token', ['token_id'], ['id'],
            ondelete='CASCADE',
        )
    else:
        # SQLite requires full table reconstruction to change the PK.
        with op.batch_alter_table('bookmark') as batch_op:
            batch_op.create_primary_key('bookmark_pkey', ['corpus_id', 'user_id'])


def downgrade():
    bind = op.get_bind()
    dialect = bind.dialect.name

    if dialect == 'postgresql':
        op.drop_constraint('bookmark_token_id_fkey', 'bookmark', type_='foreignkey')
        op.drop_constraint('bookmark_pkey', 'bookmark', type_='primary')
        op.create_primary_key(
            'bookmark_pkey', 'bookmark', ['corpus_id', 'user_id', 'token_id']
        )
        op.create_foreign_key(
            'bookmark_token_id_fkey', 'bookmark',
            'word_token', ['token_id'], ['id'],
            ondelete='CASCADE',
        )
    else:
        with op.batch_alter_table('bookmark') as batch_op:
            batch_op.create_primary_key('bookmark_pkey', ['corpus_id', 'user_id', 'token_id'])
