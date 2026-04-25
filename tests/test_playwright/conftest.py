import threading

import flask_login
import pytest
from flask import url_for as flask_url_for
from sqlalchemy_utils import create_database, database_exists

from app import create_app, db
from app.models import Role, User

PORT = 8943


class _AuthenticatedUser(flask_login.UserMixin):
    def __init__(self, app):
        self._app = app
        self._user = None

    def __getattr__(self, item):
        if not self._user:
            self._user = db.session.get(User, 1)
        return getattr(self._user, item)


def _force_authenticated(app):
    @app.before_request
    def set_identity():
        user = _AuthenticatedUser(app)
        flask_login.login_user(user)


@pytest.fixture
def auto_login():
    return True


@pytest.fixture
def app(auto_login):
    flask_app = create_app("test")
    flask_app.config.update(JSONIFY_PRETTYPRINT_REGULAR=False, LIVESERVER_PORT=PORT)
    flask_app.DEBUG = True
    flask_app.client = flask_app.test_client()
    if auto_login:
        _force_authenticated(flask_app)
    return flask_app


@pytest.fixture
def app_ctx(app):
    ctx = app.app_context()
    ctx.push()
    yield
    ctx.pop()


@pytest.fixture(autouse=True)
def setup_db(app, app_ctx):
    if not database_exists(db.engine.url):
        create_database(db.engine.url)
    db.session.commit()
    db.drop_all()
    db.create_all()
    db.session.commit()
    Role.add_default_roles()
    User.add_default_users()
    yield
    if db.engine.dialect.name == "postgresql":
        db.session.close()
        db.engine.dispose()
    db.drop_all()


@pytest.fixture
def live_server(app, setup_db):
    from werkzeug.serving import make_server

    server = make_server("localhost", PORT, app)
    thread = threading.Thread(target=server.serve_forever)
    thread.daemon = True
    thread.start()
    yield f"http://localhost:{PORT}"
    server.shutdown()
    thread.join(timeout=5)


@pytest.fixture
def page(playwright, live_server):
    browser = playwright.chromium.launch(headless=True, args=["--no-sandbox", "--disable-gpu"])
    context = browser.new_context(viewport={"width": 1920, "height": 1080})
    pg = context.new_page()
    pg.goto(live_server)
    yield pg
    context.close()
    browser.close()


@pytest.fixture
def url_for_port(app):
    def _url_for(*args, **kwargs):
        with app.test_request_context():
            kwargs["_external"] = True
            url = flask_url_for(*args, **kwargs)
            return url.replace("://localhost/", f"://localhost:{PORT}/")

    return _url_for
