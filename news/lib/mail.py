import os

import requests
from flask import render_template, current_app
from rq.decorators import job

from news.lib.task_queue import redis_conn


@job("medium", connection=redis_conn)
def JOB_send_mail(msg):
    """
    Consumes and send emails from email queue
    :param msg: 
    """
    debug = os.getenv("DEBUG") != "False"
    if debug:
        print(msg)
    else:
        requests.post(
            "{}/messages".format(os.getenv("MAILGUN_API_HOST")),
            auth=("api", os.getenv("MAILGUN_API_KEY")),
            data=msg,
        )


def registration_email(user, url):
    """
    Send registration email to user with email verification link
    :param user: user
    :param url: verification url
    :return: prepared email
    """
    msg = {
        "subject": "Please confirm your account",
        "from": current_app.config["MAIL_DEFAULT_SENDER"],
        "to": [user.email],
        "text": render_template("mails/registration.txt", user=user, url=url),
    }
    return msg


def reset_email(user, url):
    """
    Send email with link to reset password to the user
    :param user: user
    :param url: reset url
    :return: prepared email
    """
    msg = {
        "subject": "You can reset your password on following link",
        "from": current_app.config["MAIL_DEFAULT_SENDER"],
        "to": [user.email],
        "text": render_template(
            "mails/reset.txt",
            user=user,
            url=url,
            new_reset=current_app.config["URL"] + "/reset_password",
        ),
    }
    return msg
