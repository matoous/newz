from flask import Blueprint, abort, render_template

from news.models.user import User

user_blueprint = Blueprint('user', __name__, template_folder='/templates')


@user_blueprint.route("/u/<username>")
def get_feed(username=None):
    if username is None:
        abort(404)
    user = User.by_username(username)
    if user is None:
        abort(404)
    return render_template("profile.html", user=user)
