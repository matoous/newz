from werkzeug.exceptions import abort
from werkzeug.routing import BaseConverter


class FeedConverter(BaseConverter):
    """
    Converter for feed
    If converting from URL then converter takes feed slug as param and returns feed if found and aborts with
    status not found if feed is not found
    """
    def to_python(self, value):
        from news.models.feed import Feed
        if value == "":
            abort(404)
        f = Feed.by_slug(value)
        if f is None:
            abort(404)
        return f

    def to_url(self, value):
        return value.slug


class FeedsConverter(BaseConverter):
    def to_python(self, value):
        from news.models.feed import Feed
        feeds = []
        for feed_id in value.split("+"):
            feed = Feed.by_id(feed_id)
            if feed is not None:
                feeds.append(feed)
