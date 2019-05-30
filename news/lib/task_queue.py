import os

from redis import StrictRedis
from rq import Queue

redis_conn = StrictRedis.from_url(os.getenv("REDIS_URL") or "localhost:6379")
q = Queue(connection=redis_conn, is_async=os.getenv("DEBUG") == "False")
