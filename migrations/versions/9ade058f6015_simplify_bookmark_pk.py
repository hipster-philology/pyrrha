"""Simplify bookmark primary key to (corpus_id, user_id)

Removes token_id from the primary key so that re-bookmarking the same
corpus is a plain UPDATE instead of a DELETE + INSERT, eliminating the
concurrent-request UniqueViolation.

Revision ID: 9ade058f6015
Revises: f1a2b3c4d5e6
Create Date: 2026-05-22

"""
import sqlalchemy as sa
from alembic import op

revision = '9ade058f6015'
down_revision = 'f1a2b3c4d5e6'
branch_labels = None
depends_on = None


def upgrade():
    # Deduplicate: keep only the most recent bookmark per (corpus_id, user_id)
    # before dropping the old PK.
    op.execute("""
        DELETE FROM bookmark
        WHERE ctid NOT IN (
            SELECT DISTINCT ON (corpus_id, user_id) ctid
            FROM bookmark
            ORDER BY corpus_id, user_id, token_id DESC
        )
    """)

    # Drop the FK constraint on token_id (recreated below as a plain FK).
    op.drop_constraint('bookmark_token_id_fkey', 'bookmark', type_='foreignkey')

    # Replace the three-column PK with a two-column PK.
    op.drop_constraint('bookmark_pkey', 'bookmark', type_='primary')
    op.create_primary_key('bookmark_pkey', 'bookmark', ['corpus_id', 'user_id'])

    # Re-add the FK on token_id as a plain (non-PK) constraint.
    op.create_foreign_key(
        'bookmark_token_id_fkey', 'bookmark',
        'word_token', ['token_id'], ['id'],
        ondelete='CASCADE',
    )


def downgrade():
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
