import os

from apscheduler.schedulers.blocking import BlockingScheduler
from redis import StrictRedis
from rq import Queue
from rq.decorators import job

from news.scripts.import_fqs import import_fqs

sched = BlockingScheduler()

redis_conn = StrictRedis.from_url(os.getenv('REDIS_URL'))
q = Queue(connection=redis_conn, async=False if os.getenv('DEBUG', True) else True)


@job('medium', connection=redis_conn)
def import_feeds_fqs():
    import_fqs()


@sched.scheduled_job('interval', minutes=1)
def timed_job():
    print("scheduling import fqs")
    q.enqueue(import_feeds_fqs(), result_ttl=0)


sched.start()
