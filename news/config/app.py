import argparse
import time

from flask import Flask, g
from orator import Schema

from news.config.config import load_config, register_functions
from news.config.routes import register_routes
from news.lib.cache import cache
from news.lib.db.db import db, create_tables
from news.lib.csrf import csrf
from news.lib.login import login_manager
from news.lib.mail import mail
from news.lib.metrics import REQUEST_TIME
from news.lib.sentry import sentry
from news.lib.solr import solr
from news.models.ban import Ban
from news.models.comment import Comment
from news.models.feed import Feed
from news.models.feed_admin import FeedAdmin
from news.models.link import Link
from news.models.report import Report
from news.models.subscriptions import create_subscriptions_table
from news.models.token import DisposableToken
from news.models.vote import CommentVote, LinkVote
from news.scripts.create_testing_data import importHN, create_stories


def make_app():
    app = Flask(__name__, static_url_path='/static', static_folder='../static', template_folder='../templates')

    # load config
    load_config(app)

    db.init_app(app)

    solr.init_app(app)

    csrf.init_app(app)

    cache.init_app(app)

    login_manager.init_app(app)

    mail.init_app(app)

    if not app.config['DEBUG']:
        sentry.init_app(app, dsn=app.config['DSN'])

    # register view function and other utilities for templates
    register_functions(app)

    register_routes(app)


    #archive_links()
    #loadVotes()
    #create_tables(app)

    #from news.scripts.create_testing_data import create_stories
    #create_stories()
    #sentry.init_app(app)
    #importHN()

    #for feed in Feed.get():
    #   feed.commit()

    # with app.app_context():
    #     from news.models.report import Report
    #     Report.create_table()


    @app.before_request
    def before_request():
        g.start = time.time()

    @app.teardown_request
    def teardown_request(exception=None):
        if g.start:
            diff = time.time() - g.start
            REQUEST_TIME.observe(diff)

    return app
