from redis import StrictRedis
from pickle import loads, dumps

class Cache:
    def __init__(self, app=None):
        self.conn = None

        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        if 'REDIS' not in app.config:
            raise RuntimeError('Missing "REDIS" configuration')

        self._config = app.config['REDIS']
        self.conn = StrictRedis.from_url(self._config['URL'])

    def get(self, key, raw=False):
        data = self.conn.get(key)
        if raw:
            return data
        return loads(data) if data else None

    def set(self, key, val, raw=False):
        return self.conn.set(key, val if raw else dumps(val))

    def expire(self, key, time):
        return self.conn.expire(key, time)

    def pipeline(self):
        return self.conn.pipeline()

    def incr(self, key):
        return self.conn.incr(key)

    def clear(self):
        return self.conn.flushdb()

cache = Cache()