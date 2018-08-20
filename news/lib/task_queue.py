from redis import StrictRedis
from rq import Queue

redis_conn = StrictRedis.from_url('redis://localhost:6379/10')
q = Queue(connection=redis_conn, async=False)
