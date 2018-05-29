from flask import Blueprint, render_template, redirect, abort, flash, request
from flask_login import login_required, current_user

from news.lib.ratelimit import rate_limit
from news.lib.verifications import EmailVerification
from news.models.user import SignUpForm, LoginForm, User, ResetForm, PasswordReset, SetPasswordForm

auth = Blueprint('auth', __name__, template_folder='/templates')


@auth.route("/join", methods=['GET', 'POST'])
@rate_limit("join", 3, 60*60, limit_user=False, limit_ip=True)
def signup():
    """
    Sign Up new user
    :return:
    """
    if current_user.is_authenticated:
        return redirect("/")

    form = SignUpForm()
    if form.validate_on_submit():
        user = form.user
        user.register()
        return redirect('/')
    return render_template("signup.html", form=form, show_logo=True, hide_menues=True)


@auth.route("/login")
def login():
    """
    Login existing user
    :return:
    """
    if current_user.is_authenticated:
        return redirect("/")

    form = LoginForm()
    return render_template("login.html", form=form, show_logo=True, hide_menues=True)

@auth.route("/login", methods=["POST"])
@rate_limit("login", 10, 300, limit_user=False, limit_ip=True)
def post_login():
    """
    Login existing user
    :return:
    """
    if current_user.is_authenticated:
        return redirect("/")

    form = LoginForm()
    if form.validate():
        form.user.login(form.remember_me.data)
        return redirect('/')
    return render_template("login.html", form=form, show_logo=True, hide_menues=True)


@auth.route("/logout")
@login_required
def logout():
    """
    Logout current user
    :return:
    """
    current_user.logout()
    return redirect('/')


@auth.route("/reset_password")
def reset():
    """
    Request password reset
    :return:
    """
    if current_user.is_authenticated:
        return redirect("/")

    form = ResetForm()
    if form.validate_on_submit():
        user = User.where('email', form.email.data).first()
        if user is None:
            abort(404)
        pr = PasswordReset(user=user)
        pr.create()
        return render_template('reset_confirm.html')
    return render_template('reset.html', form=form)


@auth.route("/reset_password", methods=["POST"])
@rate_limit("mailaction", 5, 60*60, limit_user=False, limit_ip=True)
def post_reset():
    """
    Request password reset
    :return:
    """
    if current_user.is_authenticated:
        return redirect("/")

    form = ResetForm()
    if form.validate():
        user = User.where('email', form.email.data).first()
        if user is None:
            abort(404)
        pr = PasswordReset(user=user)
        pr.create()
        return render_template('reset_confirm.html')
    return render_template('reset.html', form=form)


@auth.route("/reset_password/<token>", methods=['GET', 'POST'])
def get_set_password(token):
    """
    Set password after receiving reset email
    :return:
    """
    if current_user.is_authenticated:
        return redirect("/")

    if token is None:
        abort(404)

    form = SetPasswordForm()
    if form.validate_on_submit():
        pr = PasswordReset(token=token)
        if pr.verify():
            user = User.by_id(pr.user_id)
            if user is None:
                abort(404)
            user.set_password(form.password.data)
            user.save()
            return redirect("/login")

    return render_template('reset_password.html', form=form, token=token)


@auth.route("/verify/resend", methods=["POST"])
@rate_limit("mailaction", 5, 60*60, limit_user=False, limit_ip=True)
def resend_verify():
    pass

@auth.route("/verify/<token>")
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
