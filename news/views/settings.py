from flask import render_template, redirect, request
from flask_login import current_user, login_required

from news.lib.ratelimit import rate_limit
from news.models.user import PreferencesForm, ProfileForm, PasswordForm, EmailForm, DeactivateForm, User


@login_required
def settings():
    form = PreferencesForm()
    if request.method == 'POST' and form.validate():
        return redirect('/settings')
    return render_template("settings.html", form=form)

@login_required
def profile_settings():
    form = ProfileForm()
    if request.method == 'POST':
        if form.validate():
            current_user.full_name = form.full_name.data
            current_user.bio = form.bio.data
            current_user.url = form.url.data
            current_user.update_with_cache()
            return redirect('/settings/profile')
    else:
        form.full_name.data = current_user.full_name
        form.bio.data = current_user.bio
        form.url.data = current_user.url
    return render_template('settings-profile.html', form=form)


@login_required
def account_settings():
    pw_form = PasswordForm(current_user)
    email_form = EmailForm(current_user)
    deactivate_form = DeactivateForm()
    return render_template('settings-account.html', pw_form=pw_form, email_form=email_form, deactivate_form=deactivate_form)

@login_required
def post_deactivate():
    pw_form = PasswordForm(current_user)
    email_form = EmailForm(current_user)
    deactivate_form = DeactivateForm()

    if deactivate_form.validate(current_user):
        User.destroy(current_user.id)
        current_user.logout()
        redirect('/')
        # maybe some cleanup after user?

    return render_template('settings-account.html', pw_form=pw_form, email_form=email_form, deactivate_form=deactivate_form)

@login_required
def post_change_email():
    pw_form = PasswordForm(current_user)
    email_form = EmailForm(current_user)
    deactivate_form = DeactivateForm()
    return render_template('settings-account.html', pw_form=pw_form, email_form=email_form, deactivate_form=deactivate_form)


@login_required
@rate_limit('pwchange', 5, 60 * 60, limit_user=True, limit_ip=False)
def post_new_password():
    pw_form = PasswordForm(current_user)
    email_form = EmailForm(current_user)
    deactivate_form = DeactivateForm()
    if pw_form.validate():
        current_user.set_password(pw_form.new_password.data)
        current_user.update_with_cache()
    return render_template('settings-account.html', pw_form=pw_form, email_form=email_form, deactivate_form=deactivate_form)


@login_required
def preferences_setting():
    form = PreferencesForm()
    return render_template("settings-preferences.html", form=form)

