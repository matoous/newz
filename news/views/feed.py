from flask import Blueprint, redirect, render_template, Response, request, abort
from flask_login import login_required, current_user

from news.lib.db.query import LinkQuery
from news.lib.filters import min_score_filter
from news.lib.normalized_trending import trending_links
from news.lib.pagination import paginate
from news.models.comment import CommentForm, SortedComments, Comment
from news.models.feed import FeedForm, Feed
from news.models.link import LinkForm, Link
from news.models.vote import LinkVote, vote_type_from_string, CommentVote

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
@feed_blueprint.route('/f/<slug>/<any(trending, new, best):sort>')
def get_feed(slug=None, sort=None):
    if slug is None:
        abort(404)

    feed = Feed.by_slug(slug)
    if feed is None:
        abort(404)

    if (sort is None or sort not in ['trending', 'new', 'best']) and current_user.is_authenticated:
        sort = current_user.preferred_sort
    if sort is None:
        sort = feed.default_sort

    lids, has_less, has_more = paginate(LinkQuery(feed_id=feed.id, sort=sort).fetch_ids(), 20)
    links = [Link.by_id(link_id) for link_id in lids]

    if sort == 'new':
        links = filter(min_score_filter(current_user.p_min_link_score), links)

    feed.links = links
    return render_template("feed.html",
                           feed=feed,
                           less_links=has_less,
                           more_links=has_more,
                           sort=sort)


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
            link.commit()

            return redirect('/f/{feed}'.format(feed=feed.slug))

    return render_template("new_link.html", form=form, feed=feed, md_parser=True)


@feed_blueprint.route("/l/<link>/vote/<vote_str>")
@login_required
def do_vote(link=None, vote_str=None):
    link = Link.where('slug', link).first()
    vote = vote_type_from_string(vote_str)
    if link is None or vote is None:
        abort(404)

    vote = LinkVote(user_id=current_user.id, link_id=link.id, vote_type=vote)
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


@feed_blueprint.route("/f/<path:feed_slug>/<link_slug>")
def link_view(feed_slug=None, link_slug=None):
    feed = Feed.where('slug', feed_slug).first()
    if feed is None or link_slug is None:
        abort(404)

    link = Link.where('slug', link_slug).first()
    if link is None:
        abort(404)

    comment_form = CommentForm()

    sorted_comments = SortedComments(link).get_full_tree()
    return render_template('link.html', link=link, feed=feed, comment_form=comment_form, comments=sorted_comments,
                           get_comment=Comment.by_id)


@login_required
@feed_blueprint.route("/f/<path:feed_slug>/<link_slug>/comment", methods=['POST'])
def comment_link(feed_slug=None, link_slug=None):
    feed = Feed.where('slug', feed_slug).first()
    if feed is None or link_slug is None:
        abort(404)

    link = Link.where('slug', link_slug).first()
    if link is None:
        abort(404)

    comment_form = CommentForm()
    if comment_form.validate(current_user, link):
        comment = comment_form.comment
        comment.commit()
    return redirect('/f/{}/{}'.format(feed_slug, link_slug))


@feed_blueprint.route("/c/<comment_id>/vote/<vote_str>")
@login_required
def do_comment_vote(comment_id=None, vote_str=None):
    comment = Comment.by_id(comment_id)
    vote = vote_type_from_string(vote_str)
    if comment is None or vote is None:
        abort(404)

    vote = CommentVote(user_id=current_user.id, comment_id=comment.id, vote_type=vote)
    vote.apply()

    return "voted"
