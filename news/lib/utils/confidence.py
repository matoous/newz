from math import sqrt


def confidence(ups, downs):
    n = ups + downs
    if n == 0:
        return 0

    z = 1.96
    phat = float(ups) / n
    return (phat + z * z / (2 * n) - z * sqrt((phat * (1 - phat) + z * z / (4 * n)) / n)) / (1 + z * z / n)