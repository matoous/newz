from functools import update_wrapper

from flask import request
from flask_login import current_user
from werkzeug.exceptions import abort

from news.lib.cache import cache


def rate_limit(prefix, limit, seconds, limit_user=True, limit_ip=True, key_func=None):
    """
    Ratelimiting middleware
    :param prefix: ratelimiting prefix to use in redis
    :param limit: number of requests
    :param seconds: timespan in seconds
    :param limit_user: limit by user if user is logged in
    :param limit_ip: limit by ip
    :param key_func: custom key func
    :return: wrapped function with ratelimiting
    """
    def decorator(f):
        def rate_limited(*args, **kwargs):
            # construct keys
            to_limit = []
            if limit_ip:
                to_limit.append('rl:{}@{}'.format(prefix, request.remote_addr or '127.0.0.1'))
            if limit_user and current_user.is_authenticated:
                to_limit.append('rl:{}.{}'.format(prefix, current_user.username))
            if key_func is not None:
                to_limit.append('rl:{}_{}'.format(prefix, key_func))

            # check limits
            for limit_key in to_limit:
                val = cache.incr(limit_key)

                # limit is new or expired before
                if val == 1:
                    cache.expire(limit_key, seconds)

                # limit surpassed
                elif val > limit:
                    abort(429)

            return f(*args, **kwargs)
        return update_wrapper(rate_limited, f)
    return decorator

def rate_limit_ok(prefix, limit, seconds, limit_user=True, limit_ip=True, key_func=None):
    # construct keys
    to_limit = []
    if limit_ip:
        to_limit.append('rl:{}@{}'.format(prefix, request.remote_addr or '127.0.0.1'))
    if limit_user and current_user.is_authenticated:
        to_limit.append('rl:{}.{}'.format(prefix, current_user.username))
    if key_func is not None:
        to_limit.append('rl:{}_{}'.format(prefix, key_func))

    # check limits
    for limit_key in to_limit:
        val = cache.incr(limit_key)

        # limit is new or expired before
        if val == 1:
            cache.expire(limit_key, seconds)

        # limit surpassed
        elif val > limit:
            abort(429)

    return True