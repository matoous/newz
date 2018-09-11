from flask import render_template
from flask_login import current_user
from werkzeug.utils import redirect


def admin():
    if not current_user.is_authenticated:
        return redirect('/login')

    if not current_user.is_god:
        return redirect('/')

    return render_template("admin.html")

def add_testing_data():
    from news.scripts.create_testing_data import create_stories
    create_stories()

    return redirect('/admin')