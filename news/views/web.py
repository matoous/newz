from flask import Blueprint, render_template, request
from flask_login import login_required, current_user

from news.lib.normalized_best import best_links
from news.lib.normalized_new import new_links
from news.lib.normalized_trending import trending_links
from news.lib.pagination import paginate
from news.lib.ratelimit import rate_limit
from news.models.link import Link

web = Blueprint('web', __name__, template_folder='/templates')

DEFAULT_FEEDS = [i for i in range(50)]


@web.route('/')
def get_home():
    if current_user.is_authenticated:
        links = trending_links(current_user.subscribed_feed_ids())
    else:
        links = trending_links(DEFAULT_FEEDS)
    paginated_ids, has_less, has_more = paginate(links, 20)
    return render_template("index.html",
                           links=[Link.by_id(link_id) for link_id in paginated_ids],
                           show_logo=True,
                           less_links=has_less,
                           more_links=has_more)


@web.route('/new')
def get_new_links():
    links = new_links(DEFAULT_FEEDS)
    paginated_ids, has_less, has_more = paginate(links, 20)
    return render_template("index.html",
                           links=[Link.by_id(link_id) for link_id in paginated_ids],
                           less_links=has_less,
                           more_links=has_more)


@web.route('/best')
def get_best_links():
    time = request.args.get('time')
    links = best_links(DEFAULT_FEEDS, time_limit=time if time else 'all')
    paginated_ids, has_less, has_more = paginate(links, 20)
    return render_template("index.html",
                           links=[Link.by_id(link_id) for link_id in paginated_ids],
                           less_links=has_less,
                           more_links=has_more)


@web.route('/trending')
def get_trending_links():
    links = trending_links(DEFAULT_FEEDS)
    paginated_ids, has_less, has_more = paginate(links, 20)
    return render_template("index.html",
                           links=[Link.by_id(link_id) for link_id in paginated_ids],
                           less_links=has_less,
                           more_links=has_more)


@web.route('/how-it-works')
def get_how_it_works():
    return render_template("how_it_works.html")


@web.route('/contact')
def get_contact():
    return render_template("contact.html")


@web.route('/help')
def get_help():
    return render_template("help.html")


@web.route('/terms')
def get_terms():
    return render_template("terms.html")


@web.route('/privacy')
def get_privacy():
    return render_template("privacy.html")
