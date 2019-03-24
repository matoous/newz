from flask import abort, render_template
from flask_login import login_required, current_user

from news.lib.pagination import paginate
from news.models.comment import Comment
from news.models.feed_admin import FeedAdmin
from news.models.link import Link, SavedLink
from news.models.user import User


def users_profile(username):
    user = User.by_username(username)
    if user is None:
        abort(404)
    if user.id == 12345:
        return render_template("autoposter_profile.html", user=user)
    links = (
        Link.where("user_id", user.id).order_by_raw("ups - downs DESC").limit(9).get()
    )
    comments = (
        Comment.where("user_id", user.id)
        .order_by_raw("ups - downs DESC")
        .limit(6)
        .get()
    )
    administrations = FeedAdmin.by_user_id(user.id)
    return render_template(
        "profile.html",
        user=user,
        links=links[: min(len(links), 8)],
        has_more_links=len(links) > 8,
        comments=comments[: min(len(comments), 5)],
        has_more_comments=len(comments) > 5,
        administrations=administrations,
        active_section="about",
    )


def users_comments(username):
    user = User.by_username(username)
    if user is None:
        abort(404)
    comments, less, more = paginate(user.comments, 20)
    return render_template(
        "profile_comments.html",
        user=user,
        comments=comments,
        less_comments=less,
        more_comments=more,
        active_section="comments",
    )


def users_posts(username):
    user = User.by_username(username)
    if user is None:
        abort(404)
    links, less, more = paginate(user.links, 20)
    return render_template(
        "profile_posts.html",
        user=user,
        links=links,
        less_links=less,
        more_links=more,
        active_section="posts",
    )


@login_required
def saved_links():
    links = SavedLink.by_user(current_user)
    links, less, more = paginate(links, 20)
    return render_template(
        "saved_links.html",
        user=current_user,
        links=links,
        less_links=less,
        more_links=more,
    )
