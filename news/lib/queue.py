from redis import Redis
from rq import Queue

redis_conn = Redis(host='localhost', port=6379)
q = Queue(connection=redis_conn, async=False)