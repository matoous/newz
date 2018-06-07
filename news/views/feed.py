from flask import Blueprint, redirect, render_template, Response, request, abort, flash
from flask_login import login_required, current_user
from feedgen.feed import FeedGenerator

from news.lib.access import feed_admin_required
from news.lib.db.query import LinkQuery
from news.lib.filters import min_score_filter
from news.lib.pagination import paginate
from news.lib.ratelimit import rate_limit
from news.lib.rss import rss_entries, rss_feed_builder, rss_page
from news.lib.utils.redirect import redirect_back
from news.models.comment import CommentForm, SortedComments, Comment
from news.models.feed import FeedForm, Feed
from news.models.feed_admin import FeedAdmin
from news.models.link import LinkForm, Link, SavedLink
from news.models.report import ReportForm, Report
from news.models.user import User
from news.models.vote import LinkVote, vote_type_from_string, CommentVote

feed_blueprint = Blueprint('feed', __name__, template_folder='/templates')


@feed_blueprint.route("/new_feed", methods=['GET', 'POST'])
@login_required
def new_feed():
    form = FeedForm()
    if request.method == 'POST' and form.validate():
        feed = form.feed
        feed.commit()
        return redirect('/f/{feed}'.format(feed=feed.slug))
    return render_template("new_feed.html", form=form)


@feed_blueprint.route('/f/<feed:feed>')
@feed_blueprint.route('/f/<feed:feed>/<any(trending, new, best):sort>')
def get_feed(feed, sort=None):
    if (sort is None or sort not in ['trending', 'new', 'best']) and current_user.is_authenticated:
        sort = current_user.preferred_sort
    if sort is None:
        sort = feed.default_sort

    ids, has_less, has_more = paginate(LinkQuery(feed_id=feed.id, sort=sort).fetch_ids(), 20)
    links = Link.by_ids(ids)

    if sort == 'new':
        links = filter(min_score_filter(current_user.p_min_link_score), links)

    feed.links = links
    return render_template("feed.html",
                           feed=feed,
                           less_links=has_less,
                           more_links=has_more,
                           sort=sort)

@feed_blueprint.route('/f/<feed:feed>/rss')
def get_feed_rss(feed):
    ids, _, _ = paginate(LinkQuery(feed_id=feed.id, sort='trending').fetch_ids(), 30)
    links = Link.by_ids(ids)
    return rss_page(feed, links)


@feed_blueprint.route("/f/<feed:feed>/add")
@login_required
def add_link(feed):
    form = LinkForm()
    return render_template("new_link.html", form=form, feed=feed, md_parser=True)


@feed_blueprint.route("/f/<feed:feed>/add", methods=['POST'])
@login_required
@rate_limit("submit", 5, 5*60, limit_user=True, limit_ip=False)
def post_add_link(feed):
    form = LinkForm()
    if form.validate(feed, current_user):
        link = form.link
        link.commit()
        return redirect('/f/{feed}'.format(feed=feed.slug))

    return render_template("new_link.html", form=form, feed=feed, md_parser=True)


@feed_blueprint.route("/f/<feed:feed>/<link_slug>/remove", methods=['POST'])
@feed_admin_required
def remove_link(feed, link_slug):
    link = Link.by_slug(link_slug)
    if link is None:
        abort(404)
    link.delete()
    return redirect('/f/{feed}'.format(feed=feed.slug))


@feed_blueprint.route("/l/<link>/vote/<vote_str>")
@login_required
@rate_limit("vote", 20, 100, limit_user=True, limit_ip=False)
def do_vote(link=None, vote_str=None):
    link = Link.where('slug', link).first()
    vote = vote_type_from_string(vote_str)
    if link is None or vote is None:
        abort(404)

    vote = LinkVote(user_id=current_user.id, link_id=link.id, vote_type=vote)
    vote.apply()

    return redirect(redirect_back(link.route))


@feed_blueprint.route("/f/<feed:feed>/subscribe")
@login_required
@rate_limit("subscription", 20, 180, limit_user=True, limit_ip=False)
def subscribe(feed):
    current_user.subscribe(feed)
    return redirect(redirect_back(feed.route))


@feed_blueprint.route("/f/<feed:feed>/unsubscribe")
@login_required
@rate_limit("subscription", 20, 180, limit_user=True, limit_ip=False)
def unsubscribe(feed):
    current_user.unsubscribe(feed)
    return redirect(redirect_back(feed.route))


@feed_blueprint.route("/f/<feed:feed>/<link_slug>")
def link_view(feed, link_slug=None):
    link = Link.where('slug', link_slug).first()
    if link is None:
        abort(404)

    comment_form = CommentForm()

    sorted_comments = SortedComments(link).get_full_tree()
    return render_template('link.html', link=link, feed=feed, comment_form=comment_form, comments=sorted_comments,
                           get_comment=Comment.by_id)


@feed_blueprint.route("/f/<feed:feed>/<link_slug>/report")
@login_required
def link_report(feed, link_slug=None):
    link = Link.where('slug', link_slug).first()
    if link is None:
        abort(404)

    report_form = ReportForm()
    return render_template('report.html', thing=link, feed=feed, report_form=report_form)


@feed_blueprint.route("/f/<feed:feed>/<link_slug>/report", methods=['POST'])
@login_required
@rate_limit("report", 5, 180, limit_user=True, limit_ip=False)
def link_report_handle(feed, link_slug=None):
    link = Link.where('slug', link_slug).first()
    if link is None:
        abort(404)

    report_form = ReportForm()
    if report_form.validate():
        report = Report(reason=report_form.reason.data, comment=report_form.comment.data, user_id=current_user.id,
                        feed_id=link.feed.id)
        link.reports().save(report)
        link.incr('reported', 1)
        flash("Thanks for your feedback!")
        return redirect(link.route)

    return render_template('report.html', thing=link, feed=feed, report_form=report_form)


@login_required
@feed_blueprint.route("/f/<feed:feed>/<link_slug>/comment", methods=['POST'])
def comment_link(feed, link_slug=None):
    link = Link.where('slug', link_slug).first()
    if link is None:
        abort(404)
    comment_form = CommentForm()
    if comment_form.validate(current_user, link):
        comment = comment_form.comment
        comment.commit()
    return redirect('/f/{}/{}'.format(feed.slug, link_slug))


@feed_blueprint.route("/f/<feed:feed>/<link_slug>/save")
@login_required
def save_link(feed, link_slug=None):
    link = Link.by_slug(link_slug)
    if link is None:
        abort(404)
    saved_link = SavedLink(user_id=current_user.id, link_id=link.id)
    saved_link.commit()
    return redirect(redirect_back(link.route))

@feed_blueprint.route("/c/<id>/report")
@login_required
def comment_report(id):
    comment = Comment.by_id(id)
    if comment is None:
        abort(404)

    report_form = ReportForm()
    return render_template('report.html', thing=comment, feed=comment.link.feed, report_form=report_form)


@feed_blueprint.route("/c/<id>/report", methods=['POST'])
@login_required
def comment_report_handle(id):
    comment = Comment.by_id(id)
    if comment is None:
        abort(404)

    report_form = ReportForm()
    if report_form.validate():
        report = Report(reason=report_form.reason.data, comment=report_form.comment.data, user_id=current_user.id,
                        feed_id=comment.link.feed.id)
        comment.reports().save(report)
        comment.incr('reported', 1)
        flash("Thanks for your feedback!")
        return redirect(comment.link.route)

    return render_template('report.html', thing=comment, feed=comment.link.feed, report_form=report_form)


@feed_blueprint.route("/c/remove/<id>", methods=['POST'])
@feed_admin_required
def remove_comment(id):
    comment = Comment.by_id(id)
    if comment is None:
        abort(404)
    comment.delete()
    return redirect('/f/{}/{}'.format(comment.link.feed.slug, comment.link.slug)) if comment else abort(404)


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
    admins = FeedAdmin.by_feed_id(feed.id)
    return render_template("feed_admins.html", admins=admins, feed=feed)


@feed_blueprint.route("/f/<feed:feed>/admin")
@feed_admin_required
def get_feed_admin(feed):
    form = FeedForm()
    form.fill(feed)
    return render_template("feed_admin.html", feed=feed, form=form)


@feed_blueprint.route("/f/<feed:feed>/admin", methods=['POST'])
@feed_admin_required
def post_feed_admin(feed):
    form = FeedForm()
    if form.validate():
        feed.name = form.name.data
        feed.description = form.description.data
        feed.rules = form.rules.data
        feed.update()
        feed.write_to_cache()
        return redirect('/f/{}/admin'.format(feed.slug))
    return render_template("feed_admin.html", feed=feed, form=form)


@feed_blueprint.route("/f/<feed:feed>/bans")
@feed_admin_required
def get_feed_bans(feed):
    return render_template("feed_bans.html", feed=feed)

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

@feed_blueprint.route("/f/<feed:feed>/ban", methods=['POST'])
@feed_admin_required
def ban_user(feed):
    pass