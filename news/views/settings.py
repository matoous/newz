import os
from pathlib import Path

from flask import Blueprint, render_template, redirect, request

from news.models.user import SettingsForm

settings = Blueprint('settings', __name__, template_folder=Path(os.path.dirname(os.path.realpath(__file__))).parent.__str__() + "/templates")


@settings.route("/settings", methods=['GET', 'POST'])
def index():
    form = SettingsForm()
    if request.method == 'POST' and form.validate():
        return redirect('/settings')
    return render_template("settings.html", form=form)
