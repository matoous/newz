# returns links as tuples so they can be effectively merged/sorted with heapq
import heapq

import itertools

from news.lib.db.query import LinkQuery
from news.lib.sorts import epoch_seconds
from news.models.link import Link

MAX_LINKS = 1000


def new_tuples(fid):
    query = LinkQuery(fid, 'new')
    return [(-time, link) for link, time in query.fetch()]


def new_links(ids):
    links_by_fids = {}

    # get sorted links for individual feeds
    for fid in ids:
        links_by_fids[fid] = new_tuples(fid)

    # merge already sorted arrays of links of individual feeds
    merged = heapq.merge(*links_by_fids.values())
    ret = list(itertools.islice((link for _, link in merged), MAX_LINKS))
    return ret
