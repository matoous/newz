def min_score_filter(min_score):
    """
    Filters links base on min score as specified in user preferences or otherwise
    :param min_score:
    :return:
    """
    return lambda x: x.score > min_score
