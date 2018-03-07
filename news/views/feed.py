from flask import Blueprint, redirect, render_template, Response
from flask_login import login_required, current_user

from news.models.feed import FeedForm, Feed
from news.models.link import LinkForm, Link
from news.models.vote import Vote

feed_blueprint = Blueprint('feed', __name__, template_folder='/templates')


@feed_blueprint.route("/new_feed", methods=['GET', 'POST'])
@login_required
def new_feed():
    form = FeedForm()
    if form.validate():
        feed = form.feed
        feed.save()
        return redirect('/f/{feed}'.format(feed=feed.slug))
    return render_template("new_feed.html", form=form)


@feed_blueprint.route("/f/<path:slug>")
def get_feed(slug=None):
    if slug is None:
        return Response("Feed not found", status=404)
    else:
        feed = Feed.by_slug(slug)
        if feed is None:
            return Response("Feed not found", status=404)
        return render_template("feed.html", feed=feed)


@feed_blueprint.route("/f/<path:slug>/add", methods=['POST', 'GET'])
@login_required
def add_link(slug=None):
    feed = Feed.query.filter(Feed.slug == slug).first()
    if feed is None:
        return Response("Feed not found", status=404)
    form = LinkForm()
    if form.validate(feed, current_user):
        link = form.link
        link.commit()
        return redirect('/f/{feed}'.format(feed=feed.slug))
    return render_template("new_link.html", form=form, feed=feed)


@feed_blueprint.route("/f/<path:slug>/<path:link>/upvote")
@login_required
def like(slug=None, link=None):
    if slug is None or link is None:
        return Response("Not found", status=404)
    else:
        feed = Feed.query.filter(Feed.slug == slug).first()
        if feed is None:
            return Response("Not found", status=404)
        link = Link.query.filter(Link.slug == link).first()
        if link is None:
            return Response("Not found", status=404)
        vote = Vote(current_user, link, 1)

