import os

from redis import StrictRedis
from rq import Queue

redis_conn = StrictRedis.from_url(os.getenv("REDIS_URL"))
q = Queue(connection=redis_conn, is_async=os.getenv("DEBUG") == "False")
