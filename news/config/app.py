from flask_dotenv import DotEnv
from os import urandom

from news.lib.cache import cache
from news.lib.csrf import csrf
from news.lib.db.db import db
from news.lib.login import login_manager
from news.lib.limiter import limiter
from news.models.feed import Feed
from news.models.link import Link
from news.models.user import User
from news.models.vote import Vote
from news.views.auth import auth
from news.views.feed import feed_blueprint
from news.views.web import web
import news.models
from flask import Flask


def make_app():
    env = DotEnv()

    app = Flask(__name__, static_url_path='/static', static_folder="../static")
    app.config['SECRET_KEY'] = urandom(16)
    app.config['ORATOR_DATABASES'] = {
        'development': {
            'driver': 'sqlite',
            'database': '/tmp/test.db'
        }
    }
    app.register_blueprint(web)
    app.register_blueprint(auth)
    app.register_blueprint(feed_blueprint)

    env.init_app(app)
    db.init_app(app)
    csrf.init_app(app)
    limiter.init_app(app)
    cache.init_app(app)
    login_manager.init_app(app)

    with app.app_context():
        Feed.create_table()
        User.create_table()
        Link.create_table()
        Vote.create_table()

    return app