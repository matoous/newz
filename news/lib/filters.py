def min_score_filter(min_score):
    return lambda x: x.score > min_score
