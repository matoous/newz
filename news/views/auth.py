import os
from pathlib import Path

from flask import Blueprint, render_template, redirect, request, abort, flash
from flask_login import login_user, logout_user, login_required, current_user

from news.lib.limiter import limiter
from news.lib.verifications import EmailVerification
from news.models.user import SignUpForm, LoginForm, User, ResetForm, PasswordReset

auth = Blueprint('auth', __name__, template_folder='/templates')


@auth.route("/join", methods=['GET', 'POST'])
def signup():
    form = SignUpForm()
    if form.validate_on_submit():
        user = form.user
        user.register()
        return redirect('/')
    return render_template("signup.html", form=form, show_logo=True, hide_menues=True)


@auth.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        form.user.login()
        return redirect('/')
    return render_template("login.html", form=form, show_logo=True, hide_menues=True)


@auth.route("/logout")
@login_required
def logout():
    current_user.logout()
    return redirect('/')


@auth.route("/reset", methods=["GET", "POST"])
def reset():
    form = ResetForm()
    if form.validate_on_submit():
        user = User.where('email', form.email.data)
        if user is None:
            abort(404)
        pr = PasswordReset(user=user)
        pr.create()
    return render_template('reset_password.html', form=form)


@auth.route("/verify/resend", methods=["POST"])
def resend_verify():
    pass

@auth.route("/verify/<token>", methods=["GET"])
def verify(token):
    """
    Verify users email
    :param token: verification token
    :return:
    """
    if token == '':
        abort(404)
    verification = EmailVerification(token=token)

    # verify
    if verification.verify():

        # update user
        user = User.by_id(verification.user_id)
        user.email_verified = True
        user.update_with_cache()

        flash('Email successfully verified!', 'success')
        return redirect('/')

    abort(404)
