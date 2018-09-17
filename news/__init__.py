import os

from apscheduler.schedulers.blocking import BlockingScheduler
from redis import StrictRedis
from rq import Queue

from news.config.app import real_make_app
from news.lib.tasks.tasks import import_feeds_fqs


def make_app():
    return real_make_app()


def make_scheduler():
    app = real_make_app()
    sched = BlockingScheduler()

    redis_conn = StrictRedis.from_url(os.getenv('REDIS_URL'))
    q = Queue(connection=redis_conn, async=False if os.getenv('DEBUG', True) else True)

    @sched.scheduled_job('interval', minutes=1)
    def timed_job():
        print("scheduling import fqs")
        q.enqueue(import_feeds_fqs(), result_ttl=0)

    return sched
