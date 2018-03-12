from flask import Blueprint, render_template
from flask_login import login_required

from news.models.link import Link

web = Blueprint('web', __name__, template_folder='/templates')


@web.route('/')
def home():
    links = Link.with_('feed').order_by('created_at', 'desc').limit(10).get()
    return render_template("index.html", links=links)


@web.route('/hello')
@login_required
def hello_world():
    return 'Hello World!'
