from orator import Model
from redis_lock import Lock

from news.lib.cache import conn, cache
from news.lib.db.db import db


class Base(Model):

    @classmethod
    def _cache_prefix(cls):
        return cls.__name__ + '_'

    @property
    def _cache_key(self):
        prefix = self._cache_prefix()
        return "{prefix}{id}".format(prefix=prefix, id=self.id)

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
        return Lock(conn, self._cache_key)

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
        cache.set(self._cache_key, self.serialize())

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
