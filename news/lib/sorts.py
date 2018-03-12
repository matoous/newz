from datetime import datetime
from math import log
from news.models.link import Link

epoch = datetime(1970, 1, 1)


def epoch_seconds(date):
    td = date - epoch
    return td.days * 86400 + td.seconds + (float(td.microseconds) / 1000000)


def hot(score, date):
    order = log(max(abs(score), 1), 10)
    sign = 1 if score > 0 else -1 if score < 0 else 0
    seconds = epoch_seconds(date) - 1134028003
    return round(sign * order + seconds / 45000, 7)


def trending_links(ids):
    all_links = []
    for lid in ids:
        all_links.extend(Link.get_by_feed_id(lid, 'trending', 'day'))

    links = sorted(all_links, key=lambda x: hot(x.score(), x.created_at), reverse=True)

    return links