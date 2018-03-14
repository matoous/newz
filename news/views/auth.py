import os
from pathlib import Path

from flask import Blueprint, render_template, redirect
from flask_login import login_user, logout_user, login_required, current_user

from news.models.user import SignUpForm, LoginForm

auth = Blueprint('auth', __name__, template_folder='/templates')


@auth.route("/join", methods=['GET', 'POST'])
def signup():
    form = SignUpForm()
    if form.validate():
        user = form.user
        user.save()
        return redirect('/')
    return render_template("signup.html", form=form)


@auth.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate():
        form.user.login()
        return redirect('/')
    return render_template("login.html", form=form)


@auth.route("/logout")
@login_required
def logout():
    current_user.logout()
    return redirect('/')

