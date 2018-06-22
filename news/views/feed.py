from datetime import datetime, timedelta

from flask import Blueprint, redirect, render_template, request, abort, flash
from flask_login import login_required, current_user

from news.lib.access import feed_admin_required, not_banned
from news.lib.db.query import LinkQuery
from news.lib.filters import min_score_filter
from news.lib.pagination import paginate
from news.lib.ratelimit import rate_limit
from news.lib.rss import rss_page
from news.lib.utils.redirect import redirect_back
from news.models.ban import BanForm, Ban
from news.models.comment import CommentForm, SortedComments, Comment
from news.models.feed import FeedForm
from news.models.feed_admin import FeedAdmin
from news.models.link import LinkForm, Link, SavedLink
from news.models.report import ReportForm, Report
from news.models.user import User
from news.models.vote import LinkVote, vote_type_from_string, CommentVote

feed_blueprint = Blueprint('feed', __name__, template_folder='/templates')


@feed_blueprint.route("/new_feed", methods=['GET', 'POST'])
@login_required
def new_feed():
    """
    Creates new feed
    :return:
    """
    form = FeedForm()
    if request.method == 'POST' and form.validate():
        feed = form.feed
        feed.commit()
        return redirect('/f/{feed}'.format(feed=feed.slug))
    return render_template("new_feed.html", form=form)


@feed_blueprint.route('/f/<feed:feed>')
@feed_blueprint.route('/f/<feed:feed>/<any(trending, new, best):sort>')
@not_banned
def get_feed(feed, sort=None):
    """
    Default feed page
    Sort can be specified by user or default to user's preferred sort or to feed default sort
    :param feed: feed
    :param sort: sort
    :return:
    """
    if (sort is None or sort not in ['trending', 'new', 'best']) and current_user.is_authenticated:
        sort = current_user.preferred_sort
    if sort is None:
        sort = feed.default_sort

    ids, has_less, has_more = paginate(LinkQuery(feed_id=feed.id, sort=sort).fetch_ids(), 20)
    links = Link.by_ids(ids)

    if sort == 'new' and current_user.is_authenticated  :
        links = filter(min_score_filter(current_user.p_min_link_score), links)

    feed.links = links
    return render_template("feed.html",
                           feed=feed,
                           less_links=has_less,
                           more_links=has_more,
                           sort=sort)

@feed_blueprint.route('/f/<feed:feed>/rss')
@not_banned
def get_feed_rss(feed):
    """
    Returns the feed in rss form
    TODO add support for different sort
    :param feed: feed
    :return:
    """
    ids, _, _ = paginate(LinkQuery(feed_id=feed.id, sort='trending').fetch_ids(), 30)
    links = Link.by_ids(ids)
    return rss_page(feed, links)


@feed_blueprint.route("/f/<feed:feed>/add")
@login_required
@not_banned
def add_link(feed):
    form = LinkForm()
    return render_template("new_link.html", form=form, feed=feed, md_parser=True)


@feed_blueprint.route("/f/<feed:feed>/add", methods=['POST'])
@login_required
@not_banned
@rate_limit("submit", 5, 5*60, limit_user=True, limit_ip=False)
def post_add_link(feed):
    """
    Post link to given feed
    :param feed: feed
    :return:
    """
    form = LinkForm()
    if form.validate(feed, current_user):
        link = form.link
        link.commit()
        return redirect('/f/{feed}'.format(feed=feed.slug))

    return render_template("new_link.html", form=form, feed=feed, md_parser=True)


@feed_blueprint.route("/f/<feed:feed>/<link_slug>/remove", methods=['POST'])
@feed_admin_required
def remove_link(feed, link_slug):
    """
    Removes link from given feed
    This is a hard delete, so be careful
    :param feed: feed
    :param link_slug: link slug
    :return:
    """
    link = Link.by_slug(link_slug)
    if link is None:
        abort(404)
    link.delete()
    return redirect(redirect_back(feed.route))


@feed_blueprint.route("/l/<link>/vote/<vote_str>")
@login_required
@rate_limit("vote", 20, 100, limit_user=True, limit_ip=False)
def do_vote(link=None, vote_str=None):
    """
    Vote on link
    All kinds of votes are handled here (up, down, unvote)
    TODO don't do it only by link slug but by feed+link slug so we can change the PK to feed+slug
    :param link: link
    :param vote_str:  vote type
    :return:
    """
    link = Link.where('slug', link).first()
    vote = vote_type_from_string(vote_str)
    if link is None or vote is None:
        abort(404)

    vote = LinkVote(user_id=current_user.id, link_id=link.id, vote_type=vote)
    vote.apply()

    return redirect(redirect_back(link.route))


@feed_blueprint.route("/f/<feed:feed>/subscribe")
@login_required
@not_banned
@rate_limit("subscription", 20, 180, limit_user=True, limit_ip=False)
def subscribe(feed):
    """
    Subscribe user to given feed
    :param feed: feed to subscribe to
    :return:
    """
    current_user.subscribe(feed)
    return redirect(redirect_back(feed.route))


@feed_blueprint.route("/f/<feed:feed>/unsubscribe")
@login_required
@not_banned
@rate_limit("subscription", 20, 180, limit_user=True, limit_ip=False)
def unsubscribe(feed):
    """
    Unsubscribe user from given feed
    :param feed: feed to unsubscribe from
    :return:
    """
    current_user.unsubscribe(feed)
    return redirect(redirect_back(feed.route))


@feed_blueprint.route("/f/<feed:feed>/<link_slug>")
@not_banned
def get_link(feed, link_slug=None):
    """
    Default view page for link
    :param feed: feed
    :param link_slug: link slug
    :return:
    """
    link = Link.where('slug', link_slug).first()
    if link is None:
        abort(404)

    # Currently supports only one type of sorting for comments
    sorted_comments = SortedComments(link).get_full_tree()

    return render_template('link.html', link=link, feed=feed, comment_form=CommentForm(), comments=sorted_comments,
                           get_comment=Comment.by_id)


@feed_blueprint.route("/f/<feed:feed>/<link_slug>/report")
@login_required
@not_banned
def link_report(feed, link_slug=None):
    """
    Report given link for breaking the rules or being a dick
    :param feed: feed
    :param link_slug: link slug
    :return:
    """
    link = Link.where('slug', link_slug).first()
    if link is None:
        abort(404)

    return render_template('report.html', thing=link, feed=feed, report_form=ReportForm())


@feed_blueprint.route("/f/<feed:feed>/<link_slug>/report", methods=['POST'])
@login_required
@not_banned
@rate_limit("report", 5, 180, limit_user=True, limit_ip=False)
def link_report_handle(feed, link_slug=None):
    """
    Handle the link report
    Redirect to link on successful report
    Show the form if there are some mistakes
    :param feed: feed
    :param link_slug: link slug
    :return:
    """
    link = Link.where('slug', link_slug).first()
    if link is None:
        abort(404)

    report_form = ReportForm()

    if report_form.validate():
        report = Report(reason=report_form.reason.data, comment=report_form.comment.data, user_id=current_user.id,
                        feed_id=link.feed.id)

        # TODO do it all in one function in report
        link.reports().save(report)
        link.incr('reported', 1)

        flash("Thanks for your feedback!")
        return redirect(redirect_back(link.route))

    return render_template('report.html', thing=link, feed=feed, report_form=report_form)


@login_required
@not_banned
@feed_blueprint.route("/f/<feed:feed>/<link_slug>/comment", methods=['POST'])
def comment_link(feed, link_slug=None):
    """
    Handle comment on link

    :param feed:
    :param link_slug:
    :return:
    """
    link = Link.where('slug', link_slug).first()
    if link is None:
        abort(404)

    comment_form = CommentForm()
    if comment_form.validate(current_user, link):
        # TODO one universal style for doing this in whole app, maybe form.get_model()
        comment = comment_form.comment
        comment.commit()

    return redirect(link.route)


@feed_blueprint.route("/f/<feed:feed>/<link_slug>/save")
@login_required
@not_banned
def save_link(feed, link_slug=None):
    """
    Save link to saved links
    :param feed: feed
    :param link_slug: link slug
    :return:
    """
    link = Link.by_slug(link_slug)
    if link is None:
        abort(404)

    # save the link
    saved_link = SavedLink(user_id=current_user.id, link_id=link.id)
    saved_link.commit()

    return redirect(redirect_back(link.route))

@feed_blueprint.route("/c/<id>/report")
@login_required
def comment_report(id):
    """
    Report comment
    :param id: comment id
    :return:
    """
    comment = Comment.by_id(id)
    if comment is None:
        abort(404)

    return render_template('report.html', thing=comment, feed=comment.link.feed, report_form=ReportForm())


@feed_blueprint.route("/c/<id>/report", methods=['POST'])
@login_required
def comment_report_handle(id):
    """
    Handle comment report
    :param id: comment id
    :return:
    """
    comment = Comment.by_id(id)
    if comment is None:
        abort(404)

    report_form = ReportForm()
    if report_form.validate():
        report = Report(reason=report_form.reason.data, comment=report_form.comment.data, user_id=current_user.id,
                        feed_id=comment.link.feed.id)

        # todo do this in one function (same as link report)
        comment.reports().save(report)
        comment.incr('reported', 1)

        flash("Thanks for your feedback!")
        return redirect(comment.link.route)

    return render_template('report.html', thing=comment, feed=comment.link.feed, report_form=report_form)


@feed_blueprint.route("/c/remove/<id>", methods=['POST'])
@feed_admin_required
def remove_comment(id):
    """
    Remove comment
    :param id: comment id
    :return:
    """
    comment = Comment.by_id(id)
    if comment is None:
        abort(404)

    # save the path where to go
    redirect_to = redirect_back(comment.route)
    comment.delete()

    return redirect(redirect_to)


@feed_blueprint.route("/c/<comment_id>/vote/<vote_str>")
@login_required
def do_comment_vote(comment_id=None, vote_str=None):
    """
    Vote on comment
    :param comment_id: comment id
    :param vote_str: vote type
    :return:
    """
    comment = Comment.by_id(comment_id)

    vote = vote_type_from_string(vote_str)
    if comment is None or vote is None:
        abort(404)

    vote = CommentVote(user_id=current_user.id, comment_id=comment.id, vote_type=vote)
    vote.apply()

    return redirect(redirect_back(comment.link.route))


@feed_blueprint.route("/f/<feed:feed>/add_admin", methods=['POST'])
@feed_admin_required
def do_add_admin(feed):
    #get new admin username
    username = request.form.get('username')
    if not username or username == "":
        abort(404)

    # check privileges
    if current_user.is_god() or current_user.is_feed_god(feed):
        user = User.by_username(username)
        if user is None:
            abort(404)
        feed_admin = FeedAdmin.create(user_id=user.id,
                                      feed_id=feed.id)
        return redirect("/f/{}/admins".format(feed.slug))
    else:
        abort(403)


@feed_blueprint.route("/f/<feed:feed>/admins/")
@feed_admin_required
def get_feed_admins(feed):
    """
    Get all feed admins
    :param feed: feed
    :return:
    """
    admins = FeedAdmin.by_feed_id(feed.id)
    return render_template("feed_admins.html", admins=admins, feed=feed)


@feed_blueprint.route("/f/<feed:feed>/admin")
@feed_admin_required
def get_feed_admin(feed):
    """
    Get administration page
    User can change rules/description here etc
    :param feed: feed
    :return:
    """
    form = FeedForm()
    form.fill(feed)
    return render_template("feed_admin.html", feed=feed, form=form)


@feed_blueprint.route("/f/<feed:feed>/admin", methods=['POST'])
@feed_admin_required
def post_feed_admin(feed):
    """
    Handle feed info change
    :param feed: feed
    :return:
    """
    form = FeedForm()

    if form.validate():
        needs_update = False

        if feed.description != form.description.data:
            feed.description = form.description.data
            needs_update = True

        if feed.rules != form.rules.data:
            feed.rules = form.rules.data
            needs_update = True

        if needs_update:
            feed.update()

        return redirect('/f/{}/admin'.format(feed.slug))

    return render_template("feed_admin.html", feed=feed, form=form)


@feed_blueprint.route("/f/<feed:feed>/bans")
@feed_admin_required
def get_feed_bans(feed):
    """
    Get bans on given feed
    :param feed: feed
    :return:
    """
    bans = Ban.where('feed_id', feed.id).get()

    return render_template("feed_bans.html", feed=feed, bans=bans)

@feed_blueprint.route("/f/<feed:feed>/reports")
@feed_admin_required
def get_feed_reports(feed):
    reports = []

    q = request.args.get('q', None)
    if q is not None:
        q_data = q.split(':')
        if len(q_data) != 2:
            abort(404)
        t, d = q_data
        reports = Report.where('feed_id', feed.id).where('reportable_type', "comments" if t == "c" else "links").where('reportable_id', d).order_by('created_at', 'desc').get()
    else:
        reports = Report.where('feed_id', feed.id).order_by('created_at', 'desc').get()

    return render_template("feed_reports.html", feed=feed, reports=reports)


@feed_blueprint.route("/f/<feed:feed>/ban/<username>")
@feed_admin_required
def ban_user(feed, username):
    user = User.by_username(username)
    if user is None:
        abort(404)

    ban_form = BanForm()
    ban_form.fill(user)

    return render_template("ban_user.html", feed=feed, form=ban_form, user=user)


@feed_blueprint.route("/f/<feed:feed>/ban/<username>", methods=['POST'])
@feed_admin_required
def handle_ban_user(feed, username):
    user = User.by_username(username)
    if user is None:
        abort(404)

    ban_form = BanForm()
    ban_form.fill(user)

    if ban_form.validate():
        expire = datetime.utcnow() + timedelta(seconds=ban_form.get_duration())
        ban = Ban(reason=ban_form.reason.data, user_id=ban_form.user_id.data, feed_id=feed.id, until=expire)
        ban.apply()
        return redirect(feed.route + "/bans")

    return render_template("ban_user.html", feed=feed, form=ban_form, user=user)