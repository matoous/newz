from flask import Flask

from news.config.config import load_config, register_functions
from news.lib.cache import cache
from news.lib.db.db import db
from news.lib.csrf import csrf
from news.lib.login import login_manager
from news.lib.mail import mail
from news.lib.sentry import sentry
from news.lib.solr import solr
from news.views.auth import auth
from news.views.feed import feed_blueprint
from news.views.settings import settings
from news.views.user import user_blueprint
from news.views.web import web
from news.views.search import search_blueprint

def make_app():
    app = Flask(__name__, static_url_path='/static', static_folder="../static")

    load_config(app)

    register_functions(app)

    db.init_app(app)

    solr.init_app(app)

    csrf.init_app(app)

    cache.init_app(app)

    login_manager.init_app(app)

    mail.init_app(app)

    #loadVotes()

    app.register_blueprint(web)
    app.register_blueprint(auth)
    app.register_blueprint(feed_blueprint)
    app.register_blueprint(settings)
    app.register_blueprint(user_blueprint)
    app.register_blueprint(search_blueprint)

    #create_tables(app)


    #sentry.init_app(app)
    #importHN()

    #for feed in Feed.get():
     #   feed.commit()

    return app
