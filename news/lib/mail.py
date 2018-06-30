from flask import render_template, current_app
from flask_mail import Mail, Message
from rq.decorators import job

from news.lib.task_queue import redis_conn

# TODO create own Mail class, this source has last update 6 years ago
mail = Mail()


@job('medium', connection=redis_conn)
def send_mail(msg):
    """
    Consumes and send emails from email queue
    :param msg: 
    """
    mail.send(msg)


def registration_email(user, url):
    """
    Send registration email to user with email verification link
    :param user: user
    :param url: verification url
    :return: prepared email
    """
    msg = Message("Please confirm your account",
                  sender=current_app.config['MAIL_DEFAULT_SENDER'],
                  recipients=[user.email])
    msg.body = render_template("mails/registration.txt", user=user, url=url)
    return msg

def reset_email(user, url):
    """
    Send email with link to reset password to the user
    :param user: user
    :param url: reset url
    :return: prepared email
    """
    msg = Message("You can reset your password on following link",
                  sender=current_app.config['MAIL_DEFAULT_SENDER'],
                  recipients=[user.email])
    msg.body = render_template("mails/reset.txt", user=user, url=url, new_reset=current_app.config['ME'] + "/reset_password")
    return msg
