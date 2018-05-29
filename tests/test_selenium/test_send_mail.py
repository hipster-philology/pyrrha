import os

import unittest

from app.email import send_email
from app.models import User
from config import config
from tests.test_selenium.base import TestBase


class TestSendMail(TestBase):

    @classmethod
    def setUpClass(cls):
        os.environ["FLASK_CONFIG"] = "test"
        super().setUpClass()

    def test_send_mail(self):

        with self.app.app_context():

            new_user = User(first_name="John", last_name="Doe", email="johndoe@ppa.fr", role_id=1)
            TestSendMail.db.session.add(new_user)
            TestSendMail.db.session.commit()

            send_email("julien.pilla@chartes.psl.eu", "hello world", "account/email/reset_password",
                       user=User.query.first(),
                       reset_link="test",
                       config=config["dev"])


if __name__ == '__main__':
    unittest.main()
