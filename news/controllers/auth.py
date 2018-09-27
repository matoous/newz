from flask import render_template, redirect, abort, flash, request, current_app
from flask_login import login_required, current_user

from news.lib.ratelimit import rate_limit
from news.lib.utils.redirect import redirect_back
from news.lib.verifications import EmailVerification
from news.models.user import SignUpForm, LoginForm, User, ResetForm, PasswordReset, SetPasswordForm


def signup():
    """
    Sign Up new user
    :return:
    """
    if current_user.is_authenticated:
        return redirect('/')

    return render_template('signup.html', form=SignUpForm(), show_logo=True, hide_menues=True)


@rate_limit('join', 10, 3600, limit_user=False, limit_ip=True)
def post_signup():
    """
    Sign Up new user
    :return:
    """
    if current_user.is_authenticated:
        return redirect("/")

    form = SignUpForm()
    if form.validate():
        user = form.result()
        user.register()
        current_app.logger.info('new user registered: {} ({})'.format(user.username, user.id))
        user.login(remember_me=True)
        return redirect('/')

    return render_template('signup.html', form=form, show_logo=True, hide_menues=True)

def login():
    """
    Get login form
    :return:
    """
    if current_user.is_authenticated:
        return redirect('/')

    return render_template('login.html', form=LoginForm(), show_logo=True, hide_menues=True,
                           next=request.args.get('next'))


@rate_limit('login', 10, 300, limit_user=False, limit_ip=True)
def post_login():
    """
    Login existing user
    :return:
    """
    if current_user.is_authenticated:
        return redirect('/')

    form = LoginForm()
    if form.validate():
        user = form.user()
        user.login(form.remember_me.data)
        return redirect(redirect_back('/'))

    return render_template("login.html", form=form, show_logo=True, hide_menues=True)


@login_required
def logout():
    """
    Logout current user
    :return:
    """
    current_user.logout()
    return redirect('/')


def reset_password():
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


@rate_limit('mail-action', 3, 3600, limit_user=False, limit_ip=True)
def post_reset_password():
    """
    Request password reset
    :return:
    """
    if current_user.is_authenticated:
        return redirect('/')

    form = ResetForm()
    if form.validate():
        user = User.where('email', form.email.data).first()
        if user is None:
            abort(404)
        pr = PasswordReset(user=user)
        pr.create()
        return render_template('reset_confirm.html')
    return render_template('reset.html', form=form)


def set_password(token):
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
            pr.delete()
            return redirect("/login")

    return render_template('reset_password.html', form=form, token=token)


@rate_limit('mail-action', 3, 3600, limit_user=True, limit_ip=True)
def resend_verify():
    # create and send verification
    verification = EmailVerification(current_user)
    verification.create()

    flash('We have send you email with verification link.', 'info')

    return redirect('/settings/account')

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

        flash('Email successfully verified!', 'info')

        return redirect('/')

    abort(404)
