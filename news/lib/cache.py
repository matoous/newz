from pickle import loads, dumps

from redis import StrictRedis

DEFAULT_CACHE_TTL = 12 * 60 * 60  # 12 hours


class Cache:
    """
    Cache serves as universal object for access to Redis
    """

    def __init__(self, app=None):
        self.conn = None
        self._url = None

        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        """
        Init Redis Cache and add config
        :param app: application
        """
        if "REDIS_URL" not in app.config:
            raise RuntimeError('Missing "REDIS_URL" configuration')

        self._url = app.config["REDIS_URL"]
        self.conn = StrictRedis.from_url(self._url)

    def get(self, key: str, raw: bool = False) -> object:
        """
        Get object from cache
        :rtype: object
        """
        data = self.conn.get(key)
        if raw:
            return data
        return loads(data) if data else None

    def mget(self, ids: [str], raw: bool = False) -> [object]:
        """
        Get multiple objects
        :param ids: ids to get
        :param raw: get objects raw or pickle-load them
        :return: objects
        """
        if not ids:
            return []

        data = self.conn.mget(ids)

        if raw:
            return data
        if data:
            return [loads(x) if x else None for x in data]
        return None

    def set(
        self, key: str, val: object, ttl: int = DEFAULT_CACHE_TTL, raw: bool = False
    ):
        """
        Put key-value pair into the cache
        :param key: key
        :param val: value
        :param ttl: time to live in seconds
        :param raw: raw object or use pickle
        :return:
        """
        if ttl == 0:
            return self.conn.set(key, val if raw else dumps(val))
        else:
            return self.conn.setex(key, ttl, val if raw else dumps(val))

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
