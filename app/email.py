
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


def send_email_async(app, recipient, subject, template, bcc=None, mailTriggerStatus=False, **kwargs):
    if (mailTriggerStatus):
        if not isinstance(recipient, list):
            recipient = [recipient]
        msg = Message(
            app.config['EMAIL_SUBJECT_PREFIX'] + ' ' + subject,
            sender=app.config['EMAIL_SENDER'],
            recipients=recipient, bcc=bcc)
        msg.body = render_template(template + '.txt', **kwargs)
        msg.html = render_template(template + '.html', **kwargs)
        Thread(target=_async, args=(app, msg)).start()
    else:
        logger.info('Warning, you are using Pyrrha without mail confirmation.' 
        ' If you are running it locally or for development purposes, do not worry'
        ' about this message. If you are using an online version, well, worry about it.')
