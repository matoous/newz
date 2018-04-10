import os
from pathlib import Path

from flask import Blueprint, render_template, redirect, request
from flask_login import current_user

from news.models.user import PreferencesForm, ProfileForm, PasswordForm, EmailForm

settings = Blueprint('settings', __name__, template_folder=Path(os.path.dirname(os.path.realpath(__file__))).parent.__str__() + "/templates")


@settings.route("/settings", methods=['GET', 'POST'])
def index():
    form = PreferencesForm()
    if request.method == 'POST' and form.validate():
        return redirect('/settings')
    return render_template("settings.html", form=form)


@settings.route("/settings/profile")
def get_profile_settings():
    form = ProfileForm()
    form.full_name.data = current_user.full_name
    form.bio.data = current_user.bio
    form.url.data = current_user.url
    return render_template("settings-profile.html", form=form)


@settings.route("/settings/profile", methods=['POST'])
def post_profile_settings():
    form = ProfileForm()
    if form.validate():
        current_user.full_name = form.full_name.data
        current_user.bio = form.bio.data
        current_user.url = form.url.data
        current_user.update_with_cache()
        return redirect('/settings')
    return render_template("settings-profile.html", form=form)


@settings.route("/settings/account")
def get_account_settings():
    pw_form = PasswordForm(current_user)
    email_form = EmailForm(current_user)
    return render_template("settings-account.html", pw_form=pw_form, email_form=email_form)


@settings.route("/settings/password", methods=['POST'])
def post_new_password():
    # TODO rate limit
    pw_form = PasswordForm(current_user)
    if pw_form.validate():
        current_user.set_password(pw_form.new_password.data)
        current_user.update_with_cache()
    email_form = EmailForm(current_user)
    return render_template("settings-account.html", pw_form=pw_form, email_form=email_form)


@settings.route("/settings/account", methods=['POST'])
def post_account_settings():
    pw_form = PasswordForm(current_user)
    email_form = EmailForm(current_user)
    return render_template("settings-account.html", pw_form=pw_form, email_form=email_form)


@settings.route("/settings/preferences")
def get_preferences_settings():
    form = PreferencesForm()
    return render_template("settings-preferences.html", form=form)


@settings.route("/settings/preferences", methods=['POST'])
def post_preferences_settings():
    form = PreferencesForm()
    return render_template("settings-preferences.html", form=form)
