from news.lib.db.db import db
from news.lib.cache import cache
from news.lib.csrf import csrf
from news.lib.login import login_manager
from news.lib.limiter import limiter
from news.lib.mail import mail
from news.lib.sentry import sentry
from news.lib.utils.confidence import confidence
from news.models.comment import Comment
from news.models.feed import Feed
from news.models.feed_admin import FeedAdmin
from news.models.link import Link
from news.models.subscriptions import create_subscriptions_table
from news.models.token import DisposableToken
from news.models.user import User
from news.models.vote import LinkVote, CommentVote
from news.scripts.create_testing_data import create_default_feeds
from news.views.auth import auth
from news.views.feed import feed_blueprint
from news.views.settings import settings
from news.views.user import user_blueprint
from news.views.web import web
from news.views.search import search_blueprint
from flask import Flask


def make_app():
    from news.lib.app import app

    app.register_blueprint(web)
    app.register_blueprint(auth)
    app.register_blueprint(feed_blueprint)
    app.register_blueprint(settings)
    app.register_blueprint(user_blueprint)
    app.register_blueprint(search_blueprint)

    csrf.init_app(app)
    limiter.init_app(app)
    cache.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)
    #sentry.init_app(app)
    #cache.clear()


    #cache.clear()

    with app.app_context():
        #DisposableToken.create_table()
        #Feed.create_table()
        #User.create_table()
        #Link.create_table()
        #LinkVote.create_table()
        #Comment.create_table()
        #CommentVote.create_table()
        #create_subscriptions_table()
        #create_default_feeds()
        #FeedAdmin.create_table()
        pass

    return app
