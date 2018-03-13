from rq.decorators import job

from news.lib.cache import cache
from news.lib.queue import redis_conn
from news.lib.sorts import default_sorts


@job('medium', connection=redis_conn)
def add_to_queries(link):
    # for 'new' all we need is to prepend
    cache_key = 'fs:{}.{}'.format(link.feed_id.to_bytes(8, 'big'), 'new')
    data = cache.get(cache_key)
    if data is not None:
        data.insert(0, link)
        cache.set(cache_key, data)

    # for the rest, sort the data in cache on insert
    for sort in ['trending', 'best']:  # no need to update 'new' because it doesn't depend on score
        cache_key = 'fs:{}.{}'.format(link.feed_id.to_bytes(8, 'big'), sort)
        data = cache.get(cache_key)
        if data is None:
            continue
        data.append(link)
        data = default_sorts(data, sort)
        cache.set(cache_key, data)
    return None
