from functools import update_wrapper

from flask import request
from flask_login import current_user
from werkzeug.exceptions import abort

from news.lib.cache import conn


def rate_limit(prefix, limit, seconds, limit_user=True, limit_ip=True):
    def decorator(f):
        def rate_limited(*args, **kwargs):
            # construct keys
            to_limit = []
            if limit_ip:
                to_limit.append('rl:{}@{}'.format(prefix, request.remote_addr or '127.0.0.1'))
            if limit_user and current_user.is_authenticated:
                to_limit.append('rl:{}.{}'.format(prefix, current_user.username))

            # check limits
            for limit_key in to_limit:
                val = conn.incr(limit_key)

                # limit is new or expired before
                if val == 1:
                    conn.expire(limit_key, seconds)

                # limit surpassed
                elif val > limit:
                    abort(429)

            return f(*args, **kwargs)
        return update_wrapper(rate_limited, f)
    return decorator
