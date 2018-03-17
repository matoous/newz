from flask_caching import Cache
from redis import StrictRedis

cache = Cache(config={'CACHE_TYPE': 'redis', 'CACHE_REDIS_URL': 'redis://localhost:6379/10'})
conn = StrictRedis.from_url('redis://localhost:6379/10')