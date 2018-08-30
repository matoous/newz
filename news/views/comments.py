from flask import render_template, flash
from flask_login import login_required, current_user
from werkzeug.exceptions import abort
from werkzeug.utils import redirect

from news.lib.utils.redirect import redirect_back
from news.models.report import ReportForm
from news.models.vote import CommentVote, vote_type_from_string


@login_required
def comment_report(comment):
    """
    Report comment
    :param comment: comment to report
    :return:
    """
    return render_template('report.html', thing=comment, feed=comment.link.feed, report_form=ReportForm())


@login_required
def post_comment_report(comment):
    """
    Handle comment report
    :param comment: comment
    :return:
    """
    if comment.link.archived:
        abort(405)

    report_form = ReportForm()
    if report_form.validate():
        report = report_form.result()
        report.user_id = current_user.id
        report.feed_id = comment.link.feed.id

        comment.reports().save(report)
        comment.incr('reported', 1)

        flash('Thanks for your feedback!')
        return redirect(comment.link.route)

    return render_template('report.html', thing=comment, feed=comment.link.feed, report_form=report_form)


def remove_comment(comment):
    """
    Remove comment
    :param comment: comment
    :return:
    """
    if not current_user.is_feed_admin(comment.link.feed) and not current_user.is_god():
        abort(405)

    if comment.link.archived:
        abort(405)

    comment.remove()

    return redirect(redirect_back(comment.route))


@login_required
def do_comment_vote(comment, vote_str=None):
    """
    Vote on comment
    :param comment_id: comment id
    :param vote_str: vote type
    :return:
    """
    if comment.link.archived:
        abort(405)

    vote = vote_type_from_string(vote_str)
    if comment is None or vote is None:
        abort(404)

    vote = CommentVote(user_id=current_user.id, comment_id=comment.id, vote_type=vote)
    vote.apply()

    return redirect(redirect_back(comment.link.route))
