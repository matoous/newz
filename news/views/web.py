from feedgen.feed import FeedGenerator
from flask import Blueprint, render_template, request
from flask_login import current_user

from news.lib.normalized_listing import trending_links, best_links, new_links
from news.lib.pagination import paginate
from news.lib.rss import rss_entries
from news.models.forms import ContactUsForm
from news.models.link import Link

web = Blueprint('web', __name__, template_folder='/templates')

DEFAULT_FEEDS = [i for i in range(50)]


@web.route('/')
def get_home():
    if current_user.is_authenticated:
        links = trending_links(current_user.subscribed_feed_ids)
    else:
        links = trending_links(DEFAULT_FEEDS)
    paginated_ids, has_less, has_more = paginate(links, 20)
    links = Link.by_ids(paginated_ids)
    return render_template("index.html",
                           links=links,
                           show_logo=True,
                           less_links=has_less,
                           more_links=has_more,
                           title="Home")


@web.route('/rss')
def get_home_rss():
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


@web.route('/new')
def get_new_links():
    links = new_links(DEFAULT_FEEDS)
    paginated_ids, has_less, has_more = paginate(links, 20)
    links = Link.by_ids(paginated_ids)

    return render_template("index.html",
                           links=links,
                           less_links=has_less,
                           more_links=has_more,
                           title="New")


@web.route('/best')
def get_best_links():
    time = request.args.get('time')
    links = best_links(DEFAULT_FEEDS, time_limit=time if time else 'all')
    paginated_ids, has_less, has_more = paginate(links, 20)
    links = Link.by_ids(paginated_ids)

    return render_template("index.html",
                           links=links,
                           less_links=has_less,
                           more_links=has_more,
                           title="Best")


@web.route('/trending')
def get_trending_links():
    links = trending_links(DEFAULT_FEEDS)
    paginated_ids, has_less, has_more = paginate(links, 20)
    links = Link.by_ids(paginated_ids)

    return render_template("index.html",
                           links=links,
                           less_links=has_less,
                           more_links=has_more,
                           title="Trending")


@web.route('/how-it-works')
def get_how_it_works():
    return render_template("how_it_works.html")


@web.route('/contact')
def get_contact():
    form = ContactUsForm()
    return render_template("contact.html", form=form)


@web.route('/contact', methods=['POST'])
def post_contact():
    form = ContactUsForm()
    if form.validate_on_submit():
        pass
    return render_template("contact.html", form=form)


@web.route('/help')
def get_help():
    return render_template("help.html")


@web.route('/terms')
def get_terms():
    return render_template("terms.html")


@web.route('/privacy')
def get_privacy():
    return render_template("privacy.html")


@web.route('/rules')
def get_rules():
    return render_template("rules.html")


@web.route('/jobs')
def get_jobs():
    return render_template("jobs.html")
