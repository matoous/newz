import heapq
import itertools

from news.lib.db.query import LinkQuery

MAX_LINKS = 1000

# returns links as tuples so they can be effectively merged/sorted with heapq
def trending_tuples(fid):
    query = LinkQuery(fid, 'trending')
    return [(-hot_score, link) for link, hot_score in query.fetch()]


def trending_links(ids):
    links_by_fids = {}

    # get sorted links for individual feeds
    for fid in ids:
        links_by_fids[fid] = trending_tuples(fid)

    # merge already sorted arrays of links of individual feeds
    merged = heapq.merge(*links_by_fids.values())
    ret = list(itertools.islice((link for _, link in merged), MAX_LINKS))
    return ret
