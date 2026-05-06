from sqlalchemy import text
from app import db


def teardown_db():
    db.session.remove()
    if db.engine.dialect.name == "postgresql":
        with db.engine.connect() as conn:
            conn.execute(text(
                "SELECT pg_terminate_backend(pid) FROM pg_stat_activity "
                "WHERE datname = current_database() AND pid <> pg_backend_pid()"
            ))
        db.engine.dispose()
    db.drop_all()
    # alembic_version is not a SQLAlchemy-declared table so drop_all() misses it;
    # leaving it causes flask_migrate.upgrade() to skip migrations on a fresh DB.
    with db.engine.connect() as conn:
        conn.execute(text("DROP TABLE IF EXISTS alembic_version"))
        if db.engine.dialect.name == "postgresql":
            conn.execute(text("DROP TYPE IF EXISTS corpus_status"))
        conn.commit()
    db.engine.dispose()
