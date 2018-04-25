from flask import Blueprint, render_template, redirect, abort, flash, request
from flask_login import login_required, current_user

from news.lib.verifications import EmailVerification
from news.models.user import SignUpForm, LoginForm, User, ResetForm, PasswordReset, SetPasswordForm

auth = Blueprint('auth', __name__, template_folder='/templates')


@auth.route("/join", methods=['GET', 'POST'])
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


@auth.route("/login", methods=["GET", "POST"])
def login():
    """
    Login existing user
    :return:
    """
    if current_user.is_authenticated:
        return redirect("/")

    form = LoginForm()
    if form.validate_on_submit():
        form.user.login()
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


@auth.route("/password_reset", methods=["GET", "POST"])
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


@auth.route("/reset_password", methods=['GET', 'POST'])
def get_set_password():
    if current_user.is_authenticated:
        return redirect("/")

    if request.method == 'GET':
        token = request.args.get('t')
        if token is None:
            abort(404)

        pr = PasswordReset(token=token)
        if pr.verify():
            user = User.by_id(pr.user_id)
            if user is None:
                abort(404)

            form = SetPasswordForm()
            form.user_id.data = user.id
            return render_template('reset_password.html', form=form)
        else:
            abort(404)
    else:
        form = SetPasswordForm()
        if form.validate_on_submit():
            user = User.by_id(form.user_id.data)
            if user is None:
                abort(404)
            user.set_password(form.password.data)
            user.save()
            return redirect('/')
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
