import binascii
import json
import os

from babel import dates


def get_bool(env_name, default):
    return bool(os.getenv(env_name)) if os.getenv(env_name) else default


def get_int(env_name, default):
    return int(os.getenv(env_name)) if os.getenv(env_name) else default


def get_string(env_name, default=None):
    return os.getenv(env_name, default)


def load_config(app):
    app.config['DEBUG'] = get_bool('DEBUG', True)
    app.config['SECRET_KEY'] = get_string('SECRET_KEY', binascii.hexlify(os.urandom(24)))
    app.config['ME'] = get_string('ME', 'http://localhost:5000')
    app.config['NAME'] = get_string('ME_NAME')
    app.config['NAME'] = 'News'
    assert app.config['NAME'] is not None
    app.config['URL'] = get_string('URL', 'localhost:5000')

    app.config['GODS'] = {'matoous'}

    # MAIL CONFIG
    app.config['MAIL_SERVER'] = get_string('MAIL_SERVER', 'smtp.gmail.com')
    app.config['MAIL_PORT'] = get_int('MAIL_PORT', 465)
    app.config['MAIL_USE_SSL'] = get_bool('MAIL_USE_SSL', True)
    app.config['MAIL_USERNAME'] = get_string('MAIL_USERNAME', 'matoousmaster@gmail.com')
    app.config['MAIL_PASSWORD'] = get_string('MAIL_PASSWORD', 'wfrylwazkglasodn')
    app.config['MAIL_DEFAULT_SENDER'] = get_string('MAIL_DEFAULT_SENDER', 'matoousmaster@gmail.com')
    app.config['MAIL_URL'] = get_string('MAIL_URL', app.config['URL'])
    app.config['CONTACT_EMAIL'] = "{}@{}".format(get_string('CONTACT_EMAIL', 'contact'), app.config['MAIL_URL'])

    app.config['FEED_LOGO_SIZE'] = 200, 160


    # SENTRY CONFIG
    app.config['DSN'] = get_string('SENTRY_URL', 'https://12a16a3e55454d369b85ae76b8d70db2:32c22327ed7a407baa89f5e212f86cd0@sentry.io/1186847')

    # DATABASE CONFIG
    app.config['ORATOR_DATABASES'] = {
            'default': 'postgres',
            'postgres': {
                'driver': 'postgres',
                'host': 'localhost',
                'database': 'newsfeed',
                'user': 'postgres',
                'password': 'admin',
                'prefix': '',
            },
        }

    # REDIS CONFIG
    app.config['REDIS'] = {
            'URL': 'redis://localhost:6379/10',
        }

    # SOLR CONFIG
    app.config['SOLR'] = {
        'URL': 'http://localhost:8983/solr',
    }
    app.config['DEFAULT_FEEDS'] = json.loads(os.getenv('DEFAULT_FEEDS') if os.getenv('DEFAULT_FEEDS') else '[]')


def register_functions(app):
    def format_datetime(value, format='medium'):
        if format == 'full':
            format = "d. MMMM y 'at' HH:mm"
        elif format == 'medium':
            format = "dd.MM.y HH:mm"
        return dates.format_datetime(value, format)
    app.jinja_env.filters['datetime'] = format_datetime

    from news.lib.converters import FeedConverter, LinkConverter, CommentConverter
    app.url_map.converters['feed'] = FeedConverter
    app.url_map.converters['link'] = LinkConverter
    app.url_map.converters['comment'] = CommentConverter