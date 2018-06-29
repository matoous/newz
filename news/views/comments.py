from flask import render_template, flash
from flask_login import login_required, current_user
from werkzeug.exceptions import abort
from werkzeug.utils import redirect

from news.lib.access import feed_admin_required
from news.lib.utils.redirect import redirect_back
from news.models.report import Report, ReportForm
from news.models.vote import CommentVote, vote_type_from_string


@login_required
def comment_report(comment):
    """
    Report comment
    :param id: comment id
    :return:
    """
    return render_template('report.html', thing=comment, feed=comment.link.feed, report_form=ReportForm())


@login_required
def post_comment_report(comment):
    """
    Handle comment report
    :param id: comment id
    :return:
    """
    report_form = ReportForm()
    if report_form.validate():
        report = Report(reason=report_form.reason.data, comment=report_form.comment.data, user_id=current_user.id,
                        feed_id=comment.link.feed.id)

        # todo do this in one function (same as link report)
        comment.reports().save(report)
        comment.incr('reported', 1)

        flash('Thanks for your feedback!')
        return redirect(comment.link.route)

    return render_template('report.html', thing=comment, feed=comment.link.feed, report_form=report_form)


@feed_admin_required
def remove_comment(comment):
    """
    Remove comment
    :param id: comment id
    :return:
    """

    # save the path where to go
    redirect_to = redirect_back(comment.route)
    comment.delete()

    return redirect(redirect_to)


@login_required
def do_comment_vote(comment, vote_str=None):
    """
    Vote on comment
    :param comment_id: comment id
    :param vote_str: vote type
    :return:
    """

    vote = vote_type_from_string(vote_str)
    if comment is None or vote is None:
        abort(404)

    vote = CommentVote(user_id=current_user.id, comment_id=comment.id, vote_type=vote)
    vote.apply()

    return redirect(redirect_back(comment.link.route))