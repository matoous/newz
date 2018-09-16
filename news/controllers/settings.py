from PIL import Image
from flask import render_template, redirect, request, flash, url_for
from flask_login import current_user, login_required
from werkzeug.utils import secure_filename

from news.lib.amazons3 import S3
from news.lib.ratelimit import rate_limit
from news.lib.utils.file_type import imagefile
from news.lib.utils.redirect import redirect_back
from news.lib.utils.resize import square_crop
from news.models.user import PreferencesForm, ProfileForm, PasswordForm, EmailForm, DeactivateForm, User


@login_required
def settings():
    return redirect(url_for('profile_settings'))

@login_required
def profile_settings():
    form = ProfileForm()
    if request.method == 'POST':
        if form.validate():
            current_user.full_name = form.full_name.data
            current_user.bio = form.bio.data
            current_user.url = form.url.data
            if form.img.data:
                filename = secure_filename(form.img.data.filename)
                if imagefile(filename):
                    img = Image.open(form.img.data)
                    img = square_crop(img)
                    new_filename = '{}.png'.format(current_user.username)
                    S3.upload_to_s3(img, new_filename)
                    current_user.profile_pic = 'https://s3.eu-central-1.amazonaws.com/newspublic/{}'.format(new_filename)
            current_user.update_with_cache()
            flash('Profile successfully updated', 'info')
            return redirect('/settings/profile')
    else:
        form.full_name.data = current_user.full_name
        form.bio.data = current_user.bio
        form.url.data = current_user.url
    return render_template('settings-profile.html', form=form, active_tab='profile')


@login_required
def account_settings():
    pw_form = PasswordForm()
    email_form = EmailForm()
    email_form.fill(current_user)
    deactivate_form = DeactivateForm()
    return render_template('settings-account.html', pw_form=pw_form, email_form=email_form, deactivate_form=deactivate_form, active_tab='account')

@login_required
def post_deactivate():
    pw_form = PasswordForm()
    email_form = EmailForm()
    email_form.fill(current_user)
    deactivate_form = DeactivateForm()

    if deactivate_form.validate(current_user):
        for feed in current_user.subscribed_feeds():
            current_user.unsubscribe(feed)
        User.destroy(current_user.id)
        current_user.logout()
        flash('You account was successfully deactivated', 'success')
        redirect('/')

    return render_template('settings-account.html', pw_form=pw_form, email_form=email_form, deactivate_form=deactivate_form)

@login_required
@rate_limit('mail-action', 5, 60 * 60, limit_user=True, limit_ip=True)
def post_change_email():
    pw_form = PasswordForm()
    email_form = EmailForm()
    deactivate_form = DeactivateForm()

    if email_form.validate():
        if email_form.email.data != current_user.email:
            current_user.change_email(email_form.email.data)
            flash('Email successfully changed', 'success')
    if email_form.public.data != current_user.email_public:
        current_user.set('email_public', email_form.public.data)


    return render_template('settings-account.html', pw_form=pw_form, email_form=email_form, deactivate_form=deactivate_form)


@login_required
@rate_limit('pwchange', 5, 60 * 60, limit_user=True, limit_ip=False)
def post_new_password():
    pw_form = PasswordForm()
    email_form = EmailForm()
    email_form.fill(current_user)
    deactivate_form = DeactivateForm()

    if pw_form.validate():
        current_user.set_password(pw_form.new_password.data)
        current_user.update_with_cache()
        flash('Password successfully changed', 'success')

    return render_template('settings-account.html', pw_form=pw_form, email_form=email_form, deactivate_form=deactivate_form)


@login_required
def preferences_setting():
    form = PreferencesForm()
    return render_template("settings-preferences.html", form=form, active_tab='preferences')


@login_required
def remove_avatar():
    current_user.profile_pic = None
    current_user.update_with_cache()
    return redirect(redirect_back(current_user.route))
