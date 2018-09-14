import logging

from flask import Flask

from news.config.config import load_config, register_functions
from news.config.routes import register_routes
from news.lib.amazons3 import S3
from news.lib.cache import cache
from news.lib.csrf import csrf
from news.lib.db.db import db
from news.lib.login import login_manager
from news.lib.sentry import sentry


def make_app():
    app = Flask(__name__, static_url_path='/static', static_folder='../static', template_folder='../templates')

    app.logger.setLevel(logging.INFO)

    # load config
    load_config(app)

    db.init_app(app)

    csrf.init_app(app)

    cache.init_app(app)

    login_manager.init_app(app)

    S3.init_app(app)

    # init sentry only if not in DEBUG mode
    if not app.config['DEBUG']:
        sentry.init_app(app, dsn=app.config['DSN'])

    # register view function and other utilities for templates
    register_functions(app)

    # register all routes
    register_routes(app)

    app.logger.info(f"eSource news: running on URL: {app.config['NAME']}, DB: {app.config['ORATOR_DATABASES'][app.config['ORATOR_DATABASES']['default']]['host']}, redis: {app.config['REDIS_URL']}")

    return app
