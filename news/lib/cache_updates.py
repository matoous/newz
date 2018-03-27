from redis_lock import Lock
from rq.decorators import job

from news.lib.cache import cache, conn
from news.lib.db.query import LinkQuery
from news.lib.queue import redis_conn
from news.lib.sorts import default_sorts


@job('medium', connection=redis_conn)
def update_link(updated_link):
    for sort in ['trending', 'best']:  # no need to update 'new' because it doesn't depend on score
        LinkQuery(feed_id=updated_link.feed_id, sort=sort).insert([updated_link])
    return None
