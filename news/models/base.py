from datetime import datetime

from orator import Model
from redis_lock import Lock

from news.lib.cache import conn, cache
from news.lib.db.db import db
from news.lib.queue import redis_conn
import timeago

CACHE_EXPIRE_TIME = 12 * 60 * 60

class Base(Model):
    """
    Base class for all models which handles queries and caching

    All models should use methods from this class to access and write to cache,
    If model-specific methods for cache access are needed be really careful
    when implementing them and try to use as much code from this class as possible
    """

    @classmethod
    def _cache_prefix(cls):
        """
        Cache prefix for model, must be unique to prevent conflicts
        :return: cache prefix
        """
        return cls.__name__ + '_'

    @property
    def _cache_key(self):
        """
        Cache key for model
        :return: cache key for object
        """
        prefix = self._cache_prefix()
        return "{prefix}{id}".format(prefix=prefix, id=self.id)

    @property
    def _lock_key(self):
        return "lock:".format(self._cache_key)

    @classmethod
    def _cache_key_from_id(cls, id):
        """
        Generate cache key from thing id
        :param id: thing id
        :return: cache key
        """
        prefix = cls._cache_prefix()
        return "{prefix}{id}".format(prefix=prefix, id=id)

    def get_read_modify_write_lock(self):
        """
        Gets read/modify/write lock for given things
        Used when updating in cache or database
        :return: RedisLock
        """
        return Lock(conn, self._lock_key)

    def update_from_cache(self):
        """
        Update model from redis
        This is usually performed before updates or when updating for data consistency
        """
        cached = cache.get(self._cache_key)
        if cached is not None:
            self.set_raw_attributes(cached)

    def write_to_cache(self):
        """
        Write self to cache
        What should and what shouldn't be written can be modified by
        __hidden__ attribute on class (more in documentation of orator)
        """
        # save token to redis for limited time
        pipe = redis_conn.pipeline()
        pipe.set(self._cache_key, self.serialize())
        pipe.expire(self._cache_key, CACHE_EXPIRE_TIME)
        pipe.execute()

    @classmethod
    def load_from_cache(cls, id):
        """
        Load model from cache
        :param id: id
        :return: model if found else None
        """
        data = cache.get(cls._cache_key_from_id(id))
        if data is None:
            return None
        obj = cls()
        obj.set_raw_attributes(data)
        obj.set_exists(True)
        return obj

    def incr(self, attr, amp=1):
        """
        Increment given attribute
        Increments model in both database and redis
        :param attr: attribute
        :param amp: amplitude
        """
        with self.get_read_modify_write_lock():
            self.update_from_cache()
            new_val = getattr(self, attr) + amp
            self.set_attribute(attr, new_val)
            with db.transaction():
                self.__class__.where('id', self.id).increment(attr, amp)
                self.write_to_cache()

    def decr(self, attr, amp=1):
        """
        Decrement given attribute
        Decrements model in both database and redis
        :param attr: attribute
        :param amp: amplitude
        """
        with self.get_read_modify_write_lock():
            self.update_from_cache()
            new_val = getattr(self, attr) - amp
            self.set_attribute(attr, new_val)
            with db.transaction():
                self.__class__.where('id', self.id).decrement(attr, amp)
                self.write_to_cache()

    def to_solr(self):
        assert self.__class__.__searchable__
        return {x : self.get_attribute(x) for x in self.__class__.__searchable__}

    def time_ago(self):
        return timeago.format(self.created_at, datetime.utcnow())

    @property
    def route(self):
        raise NotImplemented

    @classmethod
    def by_id(cls, id):
        """
        Tries to load the item from cache and if it fails from DB
        items that are permanently stored in cache should overwrite this method
        :param id:
        :return:
        """
        # try to load from cache
        item = cls.load_from_cache(id)
        if item is not None:
            return item

        # check db on fail
        item = cls.where('id', id).first()
        if item is not None:
            item.write_to_cache()

        return item

    @classmethod
    def by_ids(cls, ids):
        # pipe the ids so we get results faster
        pipe = conn.pipeline()
        for id in ids:
            pipe.get(id)
        items = pipe.execute()

        # fetch missing items
        for idx, id in enumerate(ids):
            if items[idx] is None:
                items[idx] = cls.by_id(id)

        return items