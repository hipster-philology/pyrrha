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
