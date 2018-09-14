from flask import jsonify, request, abort
from flask_login import current_user

from news.models.ban import Ban
from news.models.link import Link
from news.models.vote import vote_type_from_string, LinkVote


def api_link_vote():
    link = Link.by_id(request.json['Id'])

    if current_user.is_authenticated and Ban.by_user_and_feed_id(current_user.id, link.feed_id) is not None:
        abort(403)

    if link.archived:
        abort(405)

    vote = vote_type_from_string(request.json['VoteType'])
    vote = LinkVote(user_id=current_user.id, link_id=link.id, vote_type=vote)
    vote.apply()

    return jsonify({'status': 'ok'})