import pytest

from app import create_app, db
from app.email import send_email_async
from app.models import User, Role
from tests.conftest import teardown_db


@pytest.fixture
def app():
    flask_app = create_app("test")
    ctx = flask_app.app_context()
    ctx.push()
    db.drop_all()
    db.create_all()
    Role.add_default_roles()
    User.add_default_users()
    yield flask_app
    teardown_db()
    ctx.pop()


class TestSendMail:
    @pytest.fixture(autouse=True)
    def setup(self, app):
        self.app = app

    def test_send_mail(self):
        new_user = User(first_name="John", last_name="Doe", email="johndoe@ppa.fr", role_id=1)
        db.session.add(new_user)
        db.session.commit()

        send_email_async(
            self.app,
            recipient="julien.pilla@chartes.psl.eu",
            subject="hello world",
            template="account/email/reset_password",
            user=User.query.first(),
            reset_link="test",
            config=self.app.config,
        )
