from datetime import datetime
from math import log

epoch = datetime(1970, 1, 1)


def epoch_seconds(date):
    td = date - epoch
    return td.total_seconds()


def hot(score, date):
    order = log(max(abs(score), 1), 10)
    sign = 1 if score > 0 else -1 if score < 0 else 0
    seconds = epoch_seconds(date) - 1134028003
    print(round(sign * order + seconds / 45000, 7))
    return round(sign * order + seconds / 45000, 7)


def default_sorts(data, sort):
    if sort == 'trending':
        return sorted(data, key=lambda x: hot(x.score, x.created_at), reverse=True)
    if sort == 'new':
        return sorted(data, key=lambda x: x.created_at, reverse=True)
    if sort == 'best':
        return sorted(data, key=lambda x: x.score, reverse=True)
    return data
