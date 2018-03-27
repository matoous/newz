import heapq
import itertools

from news.lib.db.query import LinkQuery
from news.lib.utils.time_utils import epoch_seconds
from news.models.link import Link
from datetime import datetime

MAX_LINKS = 1000


def get_time_filter(cutoff):
    now = epoch_seconds(datetime.utcnow())
    time_filters = {
        'all': lambda x: True,
        'day': lambda x: now - x <= 1 * 24 * 60 * 60,
        'week': lambda x: now - x <= 7 * 24 * 60 * 60,
        'month': lambda x: now - x <= 30 * 24 * 60 * 60,
        'year': lambda x: now - x <= 365 * 30 * 24 * 60 * 60,
    }
    return time_filters[cutoff]


# returns links as tuples so they can be effectively merged/sorted with heapq
def best_tuples(fid, time_filter):
    query = LinkQuery(fid, 'best', time=time_filter)
    return [(-score, link_id) for link_id, score, time in query.fetch() if time_filter(time)]


def best_links(ids, time_limit='all'):

    links_by_fids = {}

    # get sorted links for individual feeds
    for fid in ids:
        links_by_fids[fid] = best_tuples(fid, get_time_filter(time_limit))

    # merge already sorted arrays of links of individual feeds
    merged = heapq.merge(*links_by_fids.values())
    ret = list(itertools.islice((link for _, link in merged), MAX_LINKS))
    return ret
