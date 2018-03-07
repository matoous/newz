from datetime import datetime
from math import ceil


def time_ago(time):
    ago = datetime.utcnow() - time
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
    else:
        return str(time)