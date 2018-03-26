from datetime import datetime
from math import ceil


def time_ago(time):
    now = datetime.utcnow()
    ago = now - time
    if ago.seconds < 60:
        return "Less than minute ago"
    if ago.seconds < 120:
        return "Minute ago"
    if ago.seconds < 60 * 60:
        return "{} minutes ago".format(ceil(ago.seconds / 60))
    if ago.seconds < 60*60*2:
        return "Hour ago"
    if ago.days < 2:
        return "{} hours ago".format(ceil(ago.seconds / (60 * 60)))
    if ago.days < 8:
        return "{} days ago".format(ago.days)
    if time.year == now.year:
        return time.strftime('%d. %B')
    else:
        return time.strftime('%d. %B %Y')


epoch = datetime(1970, 1, 1)


def epoch_seconds(date):
    td = date - epoch
    return td.total_seconds()