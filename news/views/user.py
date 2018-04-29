from flask import Blueprint, abort, render_template

from news.lib.pagination import paginate
from news.models.comment import Comment
from news.models.feed_admin import FeedAdmin
from news.models.link import Link
from news.models.user import User

user_blueprint = Blueprint('user', __name__, template_folder='/templates')


@user_blueprint.route("/u/<username>")
def get_users_profile(username):
    user = User.by_username(username)
    if user is None:
        abort(404)
    links = Link.where('user_id', user.id).order_by_raw('ups - downs DESC').limit(11).get()
    comments = Comment.where('user_id', user.id).order_by_raw('ups - downs DESC').limit(11).get()
    administrations = FeedAdmin.by_user_id(user.id)
    return render_template("profile.html",
                           user=user,
                           links=links[:min(len(links), 10)],
                           has_more_links=len(links) > 10,
                           comments=comments[:min(len(comments), 10)],
                           has_more_comments=len(comments) > 10,
                           administrations=administrations)


@user_blueprint.route("/u/<username>/comments")
def get_users_comments(username):
    user = User.by_username(username)
    if user is None:
        abort(404)
    comments, less, more = paginate(user.comments, 20)
    return render_template("profile_comments.html", user=user, comments=comments, less_comments=less, more_comments=more)


@user_blueprint.route("/u/<username>/posts")
def get_users_posts(username):
    user = User.by_username(username)
    if user is None:
        abort(404)
    links, less, more = paginate(user.links, 20)
    return render_template("profile_posts.html", user=user, links=links, less_links=less, more_links=more)

# TODO turnoff / turnon amdin tools