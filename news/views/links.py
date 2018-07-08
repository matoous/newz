from flask import render_template, flash, abort
from flask_login import login_required, current_user
from werkzeug.utils import redirect

from news.lib.access import not_banned
from news.lib.ratelimit import rate_limit
from news.lib.utils.redirect import redirect_back
from news.models.ban import Ban
from news.models.comment import SortedComments, Comment, CommentForm
from news.models.link import SavedLink
from news.models.report import ReportForm, Report
from news.models.vote import vote_type_from_string, LinkVote


def get_link(link, link_slug=''):
    """
    Default view page for link
    :param link_slug: link slug
    :return:
    """
    if current_user.is_authenticated and Ban.by_user_and_feed(current_user, link.feed) is not None:
        abort(403)

    # Currently supports only one type of sorting for comments
    sorted_comments = SortedComments(link).get_full_tree()

    return render_template('link.html', link=link, feed=link.feed, comment_form=CommentForm(), comments=sorted_comments,
                           get_comment=Comment.by_id)


@login_required
@rate_limit('vote', 20, 100, limit_user=True, limit_ip=False)
def do_vote(link, vote_str=None):
    """
    Vote on link
    All kinds of votes are handled here (up, down, unvote)
    :param link: link
    :param vote_str:  vote type
    :return:
    """
    if current_user.is_authenticated and Ban.by_user_and_feed(current_user, link.feed) is not None:
        abort(403)

    vote = vote_type_from_string(vote_str)
    vote = LinkVote(user_id=current_user.id, link_id=link.id, vote_type=vote)
    vote.apply()

    return redirect(redirect_back(link.route))


@login_required
def link_report(link):
    """
    Report given link for breaking the rules or being a dick
    :param feed: feed
    :param link_slug: link slug
    :return:
    """
    if current_user.is_authenticated and Ban.by_user_and_feed(current_user, link.feed) is not None:
        abort(403)

    return render_template('report.html', thing=link, feed=link.feed, report_form=ReportForm())


@login_required
@rate_limit("report", 5, 180, limit_user=True, limit_ip=False)
def post_link_report(link):
    """
    Handle the link report
    Redirect to link on successful report
    Show the form if there are some mistakes
    :param feed: feed
    :param link_slug: link slug
    :return:
    """
    if current_user.is_authenticated and Ban.by_user_and_feed(current_user, link.feed) is not None:
        abort(403)

    report_form = ReportForm()

    if report_form.validate():
        report = Report(reason=report_form.reason.data, comment=report_form.comment.data, user_id=current_user.id,
                        feed_id=link.feed.id)

        # TODO do it all in one function in report
        link.reports().save(report)
        link.incr('reported', 1)

        flash('Thanks for your feedback!')
        return redirect(link.route) # todo safe users origin through the form to redirect him back

    return render_template('report.html', thing=link, feed=link.feed, report_form=report_form)


@login_required
def comment_link(link):
    """
    Handle comment on link

    :param feed:
    :param link_slug:
    :return:
    """
    if current_user.is_authenticated and Ban.by_user_and_feed(current_user, link.feed) is not None:
        abort(403)

    comment_form = CommentForm()
    if comment_form.validate(current_user, link):
        # TODO one universal style for doing this in whole app, maybe form.get_model()
        comment = comment_form.comment
        comment.commit()

    return redirect(link.route)


@login_required
def save_link(link):
    """
    Save link to saved links
    :param link_slug: link slug
    :return:
    """
    if current_user.is_authenticated and Ban.by_user_and_feed(current_user, link.feed) is not None:
        abort(403)

    # save the link
    saved_link = SavedLink(user_id=current_user.id, link_id=link.id)
    saved_link.commit()

    return redirect(redirect_back(link.route))