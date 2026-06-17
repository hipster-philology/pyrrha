"""Fix corpus child FK constraints missing ON DELETE CASCADE

Several deployed databases have corpus_id/corpus FK constraints that were
never created with ON DELETE CASCADE, even though the model and the
initial_schema migration script both declare it. Deleting a corpus whose
children still reference it (e.g. abandoned 'pending' corpora cleaned up in
/corpus/new/init) raises psycopg.errors.ForeignKeyViolation instead of
cascading, which surfaces to users as an HTML 500 page on a JSON endpoint.

This re-creates each constraint with ON DELETE CASCADE so the live schema
matches what the application has always assumed.

Revision ID: da12c0ab7bb6
Revises: 9ade058f6015
Create Date: 2026-06-17

"""
from alembic import op

revision = 'da12c0ab7bb6'
down_revision = '9ade058f6015'
branch_labels = None
depends_on = None

# (constraint_name, table, local_column)
CORPUS_FKS = [
    ('column_corpus_id_fkey', 'column', 'corpus_id'),
    ('corpus_custom_dictionary_corpus_fkey', 'corpus_custom_dictionary', 'corpus'),
    ('corpus_user_corpus_id_fkey', 'corpus_user', 'corpus_id'),
    ('favorite_corpus_id_fkey', 'favorite', 'corpus_id'),
    ('word_token_corpus_fkey', 'word_token', 'corpus'),
    ('bookmark_corpus_id_fkey', 'bookmark', 'corpus_id'),
    ('change_record_corpus_fkey', 'change_record', 'corpus'),
    ('token_history_corpus_fkey', 'token_history', 'corpus'),
]


def upgrade():
    bind = op.get_bind()
    if bind.dialect.name != 'postgresql':
        return

    for constraint_name, table, column in CORPUS_FKS:
        op.drop_constraint(constraint_name, table, type_='foreignkey')
        op.create_foreign_key(
            constraint_name, table, 'corpus', [column], ['id'],
            ondelete='CASCADE',
        )


def downgrade():
    bind = op.get_bind()
    if bind.dialect.name != 'postgresql':
        return

    for constraint_name, table, column in CORPUS_FKS:
        op.drop_constraint(constraint_name, table, type_='foreignkey')
        op.create_foreign_key(
            constraint_name, table, 'corpus', [column], ['id'],
        )
