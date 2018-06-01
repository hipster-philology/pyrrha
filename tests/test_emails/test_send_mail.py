
import unittest

from app.email import send_email_async
from app.models import User
from tests.test_selenium.base import TestBase


class TestSendMail(TestBase):

    def test_send_mail(self):
        with self.app.app_context():
            new_user = User(first_name="John", last_name="Doe", email="johndoe@ppa.fr", role_id=1)
            TestSendMail.db.session.add(new_user)
            TestSendMail.db.session.commit()

            send_email_async(
                self.app,
                recipient="julien.pilla@chartes.psl.eu",
                subject="hello world",
                template="account/email/reset_password",
                user=User.query.first(),
                reset_link="test",
                config=self.app.config
            )

    if __name__ == '__main__':
        unittest.main()
