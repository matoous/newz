from flask import Blueprint, redirect, render_template, Response, request, abort
from flask_login import login_required, current_user

from news.models.feed import FeedForm, Feed
from news.models.link import LinkForm, Link
from news.models.vote import Vote, VoteType

feed_blueprint = Blueprint('feed', __name__, template_folder='/templates')


@feed_blueprint.route("/new_feed", methods=['GET', 'POST'])
@login_required
def new_feed():
    form = FeedForm()
    if request.method == 'POST' and form.validate():
        feed = form.feed
        feed.save()
        return redirect('/f/{feed}'.format(feed=feed.slug))
    return render_template("new_feed.html", form=form)


@feed_blueprint.route("/f/<slug>")
def get_feed(slug=None):
    if slug is None:
        abort(404)

    feed = Feed.by_slug(slug)
    if feed is None:
        abort(404)

    return render_template("feed.html", feed=feed)


@feed_blueprint.route("/f/<path:slug>/add", methods=['POST', 'GET'])
@login_required
def add_link(slug=None):
    feed = Feed.where('slug', slug).first()
    if feed is None:
        abort(404)

    form = LinkForm()
    if request.method == 'POST':
        if form.validate(feed, current_user):
            link = form.link
            link.save()
            return redirect('/f/{feed}'.format(feed=feed.slug))

    return render_template("new_link.html", form=form, feed=feed)


@feed_blueprint.route("/l/<link>/vote/<vote_str>")
@login_required
def do_vote(link=None, vote_str=None):
    link = Link.where('slug', link).first()
    vote = VoteType.from_string(vote_str)
    if link is None or vote is None:
        abort(404)

    vote = Vote(user_id=current_user.id, link_id=link.id, vote_type=vote)
    vote.apply()

    return "voted"


@feed_blueprint.route("/f/<path:slug>/subscribe")
@login_required
def subscribe(slug=None):
    feed = Feed.where('slug', slug).first()
    if feed is None:
        abort(404)

    subscribed = current_user.subscribe(feed)
    if not subscribed:
        return "Subscribe NOT OK"
    return "Subscribed"


@feed_blueprint.route("/f/<path:slug>/unsubscribe")
@login_required
def unsubscribe(slug=None):
    feed = Feed.where('slug', slug).first()
    if feed is None:
        abort(404)

    current_user.unsubscribe(feed)
    return "Unsubscribed"
