from datetime import datetime
from math import log

from news.lib.utils.time_utils import epoch_seconds

epoch = datetime(1970, 1, 1)


def hot(score, date):
    order = log(max(abs(score), 1), 10)
    sign = 1 if score > 0 else -1 if score < 0 else 0
    seconds = epoch_seconds(date) - 1134028003
    return round(sign * order + seconds / 45000, 7)


def sort_tuples(data):
    return sorted(data, key=lambda x: x[1:], reverse=True)


def default_sorts(data, sort):
    if sort == 'trending':
        return sorted(data, key=lambda x: hot(x.score, x.created_at), reverse=True)
    if sort == 'new':
        return sorted(data, key=lambda x: x.created_at, reverse=True)
    if sort == 'best':
        return sorted(data, key=lambda x: x.score, reverse=True)
    return data
