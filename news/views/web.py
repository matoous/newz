from flask import Blueprint, render_template
from flask_login import login_required, current_user

from news.lib.normalized_trending import trending_links
from news.models.link import Link

web = Blueprint('web', __name__, template_folder='/templates')


@web.route('/')
def home():
    links = Link.order_by('created_at', 'desc').limit(10).get()
    return render_template("index.html", links=links, show_logo=True)


@web.route('/my')
@login_required
def my_feeds():
    fids = current_user.subscribed_feed_ids()
    links = trending_links(fids)
    return render_template("index.html", links=links)
