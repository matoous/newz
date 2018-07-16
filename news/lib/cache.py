from redis import StrictRedis
from pickle import loads, dumps

DEFAULT_CACHE_TTL= 12 * 60 * 60 # 12 hours

class Cache:
    def __init__(self, app=None):
        self.conn = None
        self._config = None

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

    def set(self, key, val, ttl=DEFAULT_CACHE_TTL, raw=False):
        if ttl == 0:
            return self.conn.set(key, val if raw else dumps(val))
        else:
            pipe = self.pipeline()
            pipe.set(key, val if raw else dumps(val))
            pipe.expire(key, ttl)
            pipe.execute()

    def clear(self):
        return self.conn.flushdb()

    def __getattr__(self, name):
        return getattr(self.conn, name)

    def __getitem__(self, name):
        return self.conn[name]

    def __setitem__(self, name, value):
        self.conn[name] = value

    def __delitem__(self, name):
        del self.conn[name]

cache = Cache()