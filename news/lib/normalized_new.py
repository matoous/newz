# returns links as tuples so they can be effectively merged/sorted with heapq
import heapq

import itertools

from news.lib.sorts import epoch_seconds
from news.models.link import Link

MAX_LINKS = 1000


def new_tuples(fid):
    links = Link.get_by_feed_id(fid, 'new')
    return [(-epoch_seconds(link.created_at), link) for link in links]


def new_links(ids):
    links_by_fids = {}

    # get sorted links for individual feeds
    for fid in ids:
        links_by_fids[fid] = new_tuples(fid)

    # merge already sorted arrays of links of individual feeds
    merged = heapq.merge(*links_by_fids.values())
    ret = list(itertools.islice((link for _, link in merged), MAX_LINKS))
    return ret
