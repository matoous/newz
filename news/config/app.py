from flask_dotenv import DotEnv

from news.lib.cache import cache
from news.lib.csrf import csrf
from news.lib.db.db import db
from news.lib.login import login_manager
from news.lib.limiter import limiter
from news.models.feed import Feed
from news.models.link import Link
from news.models.subscriptions import create_subscriptions_table
from news.models.user import User
from news.models.vote import Vote
from news.views.auth import auth
from news.views.feed import feed_blueprint
from news.views.settings import settings
from news.views.user import user_blueprint
from news.views.web import web
from flask import Flask


def make_app():
    env = DotEnv()
    app = Flask(__name__, static_url_path='/static', static_folder="../static")
    app.config['SECRET_KEY'] = 'secretpico'
    app.register_blueprint(web)
    app.register_blueprint(auth)
    app.register_blueprint(feed_blueprint)
    app.register_blueprint(settings)
    app.register_blueprint(user_blueprint)

    env.init_app(app)

    app.config['ORATOR_DATABASES'] = {
        'default': 'postgres',
        'postgres': {
            'driver': 'postgres',
            'host': 'localhost',
            'database': 'newsfeed',
            'user': 'postgres',
            'password': '',
            'prefix': ''
        },
    }

    db.init_app(app)
    csrf.init_app(app)
    limiter.init_app(app)
    cache.init_app(app)
    login_manager.init_app(app)

    with app.app_context():
        pass
        #Feed.create_table()
        #User.create_table()
        #Link.create_table()
        #Vote.create_table()
        #create_subscriptions_table()

    return app