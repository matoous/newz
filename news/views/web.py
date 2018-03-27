from flask import Blueprint, render_template, request
from flask_login import login_required, current_user

from news.lib.normalized_best import best_links
from news.lib.normalized_new import new_links
from news.lib.normalized_trending import trending_links
from news.models.link import Link

web = Blueprint('web', __name__, template_folder='/templates')

DEFAULT_FEEDS = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]


@web.route('/')
def home():
    if current_user.is_authenticated:
        links = trending_links(current_user.subscribed_feed_ids())
    else:
        links = trending_links(DEFAULT_FEEDS)
    return render_template("index.html", links=[Link.by_id(link_id) for link_id in links], show_logo=True)


@web.route('/new')
@login_required
def get_new_links():
    links = new_links(DEFAULT_FEEDS)
    return render_template("index.html", links=[Link.by_id(link_id) for link_id in links])


@web.route('/best')
@login_required
def get_best_links():
    time = request.args.get('time')
    links = best_links(DEFAULT_FEEDS, time_limit=time if time else 'all')
    return render_template("index.html", links=[Link.by_id(link_id) for link_id in links])


@web.route('/trending')
@login_required
def get_trending_links():
    links = trending_links(DEFAULT_FEEDS)
    return render_template("index.html", links=[Link.by_id(link_id) for link_id in links])