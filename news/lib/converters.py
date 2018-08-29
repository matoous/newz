from typing import Optional

from werkzeug.exceptions import abort
from werkzeug.routing import BaseConverter

from news.models.comment import Comment
from news.models.feed import Feed
from news.models.link import Link


class FeedConverter(BaseConverter):
    """
    Converter for feed
    If converting from URL then converter takes feed slug as param and returns feed if found and aborts with
    status not found if feed is not found
    """

    def to_python(self, value: str) -> Optional[Feed]:
        if value == "":
            abort(404)
        feed = Feed.by_slug(value)
        if feed is None:
            abort(404)
        return feed

    def to_url(self, value):
        return value.slug


class LinkConverter(BaseConverter):
    """
    Converter for link
    If converting from URL then converter takes link slug as param and returns link if found and aborts with
    status not found if link is not found
    """

    def to_python(self, value: str) -> Optional[Link]:
        if value == "":
            abort(404)
        link = Link.by_id(value)
        if link is None:
            abort(404)
        return link

    def to_url(self, value):
        return value.id


class CommentConverter(BaseConverter):
    """
    Converter for comment
    If converting from URL then converter takes link slug as param and returns link if found and aborts with
    status not found if link is not found
    """

    def to_python(self, value: str) -> Optional[Comment]:
        if value == "":
            abort(404)
        comment = Comment.by_id(value)
        if comment is None:
            abort(404)
        return comment

    def to_url(self, value):
        return value.id


class FeedsConverter(BaseConverter):
    def to_python(self, value):
        from news.models.feed import Feed
        feeds = []
        for feed_id in value.split("+"):
            feed = Feed.by_id(feed_id)
            if feed is not None:
                feeds.append(feed)
