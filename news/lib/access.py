from functools import update_wrapper, wraps

from flask_login import current_user
from werkzeug.exceptions import abort


def feed_admin_required(func):
    """
    View decorator which requires user to be logged in and be admin of feed which is being viewed
    :param func: func to protect, must take feed as first argument
    :return: decorated function
    """
    @wraps(func)
    def check(feed, *args, **kwargs):
        if not current_user.is_authenticated or not (current_user.is_feed_admin(feed) or current_user.is_god()):
            abort(403)
        return func(feed, *args, **kwargs)
    return check

def not_banned(func):
    """
    Check that user is not banned from given feed
    :param func: view to wrap
    :return: wrapped view
    """
    @wraps(func)
    def check(feed, *args, **kwargs):
        from news.models.ban import Ban
        if current_user.is_authenticated and Ban.by_user_and_feed(current_user, feed) is not None:
            abort(403)
        return func(feed, *args, **kwargs)
    return check