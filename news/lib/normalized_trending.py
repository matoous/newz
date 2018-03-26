import heapq
from datetime import datetime
from math import log

import itertools

from news.lib.utils.time_utils import epoch_seconds
from news.models.link import Link

MAX_LINKS = 1000


def hot(score, date):
    order = log(max(abs(score), 1), 10)
    sign = 1 if score > 0 else -1 if score < 0 else 0
    seconds = epoch_seconds(date) - 1134028003
    return round(sign * order + seconds / 45000, 7)


# returns links as tuples so they can be effectively merged/sorted with heapq
def trending_tuples(fid):
    links = Link.get_by_feed_id(fid, 'trending')
    return [(-hot(link.score, link.created_at), link) for link in links]


def trending_links(ids):
    links_by_fids = {}

    # get sorted links for individual feeds
    for fid in ids:
        links_by_fids[fid] = trending_tuples(fid)

    # merge already sorted arrays of links of individual feeds
    merged = heapq.merge(*links_by_fids.values())
    ret = list(itertools.islice((link for _, link in merged), MAX_LINKS))
    return ret
