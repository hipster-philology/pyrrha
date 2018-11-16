
from flask import render_template
from flask_mail import Message
from smtplib import SMTPDataError
from threading import Thread

from app import mail
import logging


logger = logging.getLogger(__name__)


def _async(app, msg):
    with app.app_context():
        try:
            mail.send(msg)
        except SMTPDataError as e:
            logger.warning(str(e))


def send_email_async(app, recipient, subject, template, **kwargs):
    msg = Message(
        app.config['EMAIL_SUBJECT_PREFIX'] + ' ' + subject,
        sender=app.config['EMAIL_SENDER'],
        recipients=[recipient])
    msg.body = render_template(template + '.txt', **kwargs)
    msg.html = render_template(template + '.html', **kwargs)
    Thread(target=_async, args=(app, msg)).start()
