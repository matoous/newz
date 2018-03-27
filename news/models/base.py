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
        prefix = cls._cache_prefix()
        return "{prefix}{id}".format(prefix=prefix, id=id)

    def get_read_modify_write_lock(self):
        return Lock(conn, self._cache_key)

    def update_from_cache(self):
        cached = cache.get(self._cache_key)
        if cached is not None:
            self.set_raw_attributes(cached.attributes_to_dict())

    def write_to_cache(self):
        cache.set(self._cache_key, self)

    def new_to_cache(self):
        cache.set(self._cache_key, self)

    def incr(self, property, amp=1):
        with self.get_read_modify_write_lock():
            self.update_from_cache()
            new_val = getattr(self, property) + amp
            self.set_attribute(property, new_val)
            with db.transaction():
                self.__class__.where('id', self.id).increment(property, amp)
                self.write_to_cache()

    def decr(self, property, amp=1):
        with self.get_read_modify_write_lock():
            self.update_from_cache()
            new_val = getattr(self, property) - amp
            self.set_attribute(property, new_val)
            with db.transaction():
                self.__class__.where('id', self.id).decrement(property, amp)
                self.write_to_cache()