from feedgen.feed import FeedGenerator
from flask import render_template, request
from flask.views import View
from flask_login import current_user
from prometheus_client import core
from prometheus_client.exposition import generate_latest

from news.lib.normalized_listing import trending_links, best_links, new_links
from news.lib.pagination import paginate
from news.lib.rss import rss_entries
from news.models.link import Link

DEFAULT_FEEDS = [3, 4, 5, 7, 78, 79, 80, 81, 2, 82, 6, 83, 1, 84, 85, 86, 87, 88, 89, 90]

class LinksListing(View):
    def dispatch_request(self):
        pass

    def feed_ids(self):
        return current_user.subscribed_feed_ids if current_user.is_authenticated else DEFAULT_FEEDS

    def get(self):
        pass

class CommonListing(LinksListing):
    def feed_ids(self):
        return DEFAULT_FEEDS


def index():
    if current_user.is_authenticated:
        links = trending_links(current_user.subscribed_feed_ids)
    else:
        links = trending_links(DEFAULT_FEEDS)
    paginated_ids, has_less, has_more = paginate(links, 20)
    links = Link.by_ids(paginated_ids)
    return render_template('index.html',
                           links=links,
                           show_logo=True,
                           less_links=has_less,
                           more_links=has_more,
                           title="Home")

def index_rss():
    if current_user.is_authenticated:
        links = trending_links(current_user.subscribed_feed_ids)
    else:
        links = trending_links(DEFAULT_FEEDS)
    paginated_ids, _, _ = paginate(links, 30)
    links = Link.by_ids(paginated_ids)

    # TODO maybe do through fake feed (that's what reddit does and it actually makes sense)
    fg = FeedGenerator()
    fg.id("https://localhost:5000/")
    fg.title("Newsfeed")
    fg.link(href="http://localhost:5000/", rel='self')
    fg.description("Global news agrregator!")
    fg.language("en")

    for entry in rss_entries(links):
        fg.add_entry(entry)

    return fg.rss_str(pretty=True)


def new():
    links = new_links(DEFAULT_FEEDS)
    paginated_ids, has_less, has_more = paginate(links, 20)
    links = Link.by_ids(paginated_ids)

    return render_template("index.html",
                           links=links,
                           less_links=has_less,
                           more_links=has_more,
                           title="New")


def best():
    time = request.args.get('time')
    links = best_links(DEFAULT_FEEDS, time_limit=time if time else 'all')
    paginated_ids, has_less, has_more = paginate(links, 20)
    links = Link.by_ids(paginated_ids)

    return render_template("index.html",
                           links=links,
                           less_links=has_less,
                           more_links=has_more,
                           title="Best")


def trending():
    links = trending_links(DEFAULT_FEEDS)
    paginated_ids, has_less, has_more = paginate(links, 20)
    links = Link.by_ids(paginated_ids)

    return render_template("index.html",
                           links=links,
                           less_links=has_less,
                           more_links=has_more,
                           title="Trending")


def how_it_works():
    return render_template("how_it_works.html")

def contact():
    return render_template("contact.html")

def get_help():
    return render_template("help.html")

def terms():
    return render_template("terms.html")

def privacy():
    return render_template("privacy.html")

def rules():
    return render_template("rules.html")

def jobs():
    return render_template("jobs.html")

def suggest_feed():
    return render_template("suggest_feed.html")

def metrics():
    registry = core.REGISTRY
    output = generate_latest(registry)
    return(output)
