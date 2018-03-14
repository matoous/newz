from rq.decorators import job

from news.lib.cache import cache
from news.lib.queue import redis_conn
from news.lib.sorts import default_sorts


@job('medium', connection=redis_conn)
def update_link(updated_link):
    print("updating links")
    for sort in ['trending', 'best']:  # no need to update 'new' because it doesn't depend on score
        cache_key = 'fs:{}.{}'.format(updated_link.feed.b_id, sort)
        data = cache.get(cache_key)
        if not data:  # links are not in cache, they will get there on first query
            continue
        data = default_sorts([updated_link if x == updated_link else x for x in data], sort)
        cache.set(cache_key, data)
    return None


@job('medium', connection=redis_conn)
def update_subs(user, feed_id):
    pass