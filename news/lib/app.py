import babel as babel
from flask import Flask
from babel import dates

from news.lib.converters import FeedConverter

app = Flask(__name__, static_url_path='/static', static_folder="../static")
app.config['DEBUG'] = True
app.config['SECRET_KEY'] = 'WubbaLubbaDubDub!Pickle!12354112#yolo!'

app.config['URL'] = 'localhost:5000'
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_USERNAME'] = 'matoousmaster@gmail.com'
app.config['MAIL_PASSWORD'] = 'wfrylwazkglasodn'
app.config['MAIL_DEFAULT_SENDER'] = 'matoousmaster@gmail.com'
app.config['MAIL_URL'] = app.config['URL']
app.config['CONTACT_EMAIL'] = 'contact' + "@" + app.config['MAIL_URL']

app.config['DSN'] = 'https://12a16a3e55454d369b85ae76b8d70db2:32c22327ed7a407baa89f5e212f86cd0@sentry.io/1186847'
app.config['ME'] = 'http://localhost:5000'
app.config['SOLR_URL'] = 'http://localhost:8983/solr'


app.config['NAME'] = 'Never Ending News'


app.config['ORATOR_DATABASES'] = {
        'default': 'postgres',
        'postgres': {
            'driver': 'postgres',
            'host': 'localhost',
            'database': 'newsfeed',
            'user': 'postgres',
            'password': 'postgres',
            'prefix': '',
        },
    }

app.config['REDIS'] = {
        'URL': 'redis://localhost:6379/10',
    }