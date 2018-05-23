from datetime import datetime

epoch = datetime(1970, 1, 1)


def epoch_seconds(date):
    """
    Gets epoch seconds from date
    :param date: date
    :return: epoch seconds
    """
    td = date - epoch
    return td.total_seconds()