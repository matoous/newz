from flask import Blueprint, abort, render_template

from news.models.user import User

user_blueprint = Blueprint('user', __name__, template_folder='/templates')


@user_blueprint.route("/u/<username>")
def get_users_profile(username):
    user = User.by_username(username)
    if user is None:
        abort(404)
    return render_template("profile.html", user=user)


@user_blueprint.route("/u/<username>/comments")
def get_users_comments(username):
    user = User.by_username(username)
    if user is None:
        abort(404)
    return render_template("profile_comments.html", user=user)


@user_blueprint.route("/u/<username>/posts")
def get_users_posts(username):
    user = User.by_username(username)
    if user is None:
        abort(404)
    return render_template("profile_posts.html", user=user)
